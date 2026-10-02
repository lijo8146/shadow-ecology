"""
Week 4 — Baseline map package generator
=========================================
Generates the four baseline maps defined in
results/baseline_maps/baseline_map_spec.yaml and updates
results/baseline_maps/map_manifest.csv.

Maps produced:
  01  AOI and hydrography context
  02  Seasonal Sentinel-2 valid-observation coverage
  03  Public monitoring inventory (public-inventory-only caption required)
  04  NLCD land-cover labels and irrigation-confounder context

Usage (from project root, shadow-ecology conda env active):
    python src/generate_baseline_maps.py [--map {01,02,03,04,all}]

Prerequisites:
  - AOI geometry:      data/catalog/aoi_final.geojson
  - Hydrography:       data/raw/hydrography/
  - Sentinel-2 tiles:  data/raw/sentinel2/
  - Coverage rasters:  results/coverage/sentinel2_valid_obs_*.tif
  - USGS inventory:    results/coverage/public_monitoring_inventory.csv
  - NLCD clipped:      data/raw/nlcd/nlcd_{year}_lower_walker_aoi.tif
  - LANID:             data/raw/lanid/

Governance:
  Map 03 must carry the required caption:
    "Shows only the public inventory examined; it is not a map of all
     monitoring or local knowledge."
  Before external release of any map that identifies locations on or
  immediately adjacent to Tribal lands/waters, follow
  governance_boundary_register.md.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    aoi_bbox,
    imagery_years,
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    season_windows,
    sha256,
)
from src.settings import PROJECT_ROOT

MAP_SPEC = PROJECT_ROOT / "results" / "baseline_maps" / "baseline_map_spec.yaml"
MAP_MANIFEST_CSV = PROJECT_ROOT / "results" / "baseline_maps" / "map_manifest.csv"
OUTPUT_DIR = PROJECT_ROOT / "results" / "baseline_maps"

REQUIRED_MONITORING_CAPTION = (
    "Shows only the public inventory examined; "
    "it is not a map of all monitoring or local knowledge."
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--map", default="all",
        choices=["01", "02", "03", "04", "all"],
        help="Which map(s) to generate (default: all).",
    )
    return p


# ── Map 01 — AOI / hydrography context ───────────────────────────────────────

def map_01_aoi_hydrography(output_path: Path) -> dict:
    """Generate the AOI and hydrography context map."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    aoi_path = PROJECT_ROOT / "data" / "catalog" / "aoi_final.geojson"

    try:
        import geopandas as gpd
    except ImportError:
        print("ERROR: geopandas required for map generation.", file=sys.stderr)
        sys.exit(1)

    fig, ax = plt.subplots(figsize=(9, 11))
    bbox = aoi_bbox()

    # AOI boundary
    if aoi_path.exists():
        aoi = gpd.read_file(aoi_path)
        aoi.boundary.plot(ax=ax, color="#2c5f8a", linewidth=1.5, label="Analysis AOI")

    # Hydrography layers
    hydro_dir = PROJECT_ROOT / "data" / "raw" / "hydrography"
    for layer_file, color, label, lw in [
        ("flowlines_streams_lower_walker.gpkg", "#4a90d9", "Streams/rivers", 1.0),
        ("canals_ditches_lower_walker.gpkg",    "#7fb3e0", "Canals/ditches",  0.8),
        ("waterbodies_lower_walker.gpkg",        "#b3d4ef", "Waterbodies",    0.5),
        ("springs_lower_walker.gpkg",            "#1a6b3c", "Springs (NHD mapped)", 3.0),
    ]:
        lf = hydro_dir / layer_file
        if lf.exists():
            gdf = gpd.read_file(lf)
            if not gdf.empty:
                gdf.plot(ax=ax, color=color, linewidth=lw, label=label)

    # USGS monitoring stations (streamflow)
    gw_sites = PROJECT_ROOT / "data" / "raw" / "usgs_waterdata" / "streamflow_sites_aoi.csv"
    if gw_sites.exists():
        import pandas as pd
        df = pd.read_csv(gw_sites, comment="#")
        if "dec_lat_va" in df.columns and "dec_long_va" in df.columns:
            df = df.dropna(subset=["dec_lat_va", "dec_long_va"])
            ax.scatter(df["dec_long_va"], df["dec_lat_va"],
                       s=18, color="#e87722", zorder=5, label="USGS streamflow gages", marker="^")

    # Anchors
    from src.settings import study_area
    sa = study_area()
    ax.plot(sa["upstream_anchor"]["longitude"], sa["upstream_anchor"]["latitude"],
            "k*", markersize=12, zorder=10, label="Wabuska gage (upstream anchor)")
    ax.plot(sa["downstream_anchor"]["longitude"], sa["downstream_anchor"]["latitude"],
            "k^", markersize=10, zorder=10, label="Walker Lake (downstream anchor)")

    ax.set_xlim(bbox[0] - 0.02, bbox[2] + 0.02)
    ax.set_ylim(bbox[1] - 0.02, bbox[3] + 0.02)
    ax.set_xlabel("Longitude (WGS 84)")
    ax.set_ylabel("Latitude (WGS 84)")
    ax.set_title(
        "Lower Walker River–Walker Lake\nAnalysis extent and NHDPlus HR hydrography",
        fontsize=12, pad=12,
    )
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)
    ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.7)
    fig.text(0.5, 0.01,
             "Sources: USGS NHDPlus HR; USGS NWIS. "
             "AOI is a desktop-analysis polygon, not a jurisdictional boundary.",
             ha="center", fontsize=7, color="#555555")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"status": "generated", "output": str(output_path)}


# ── Map 02 — Sentinel-2 valid-observation coverage ───────────────────────────

def map_02_sentinel2_coverage(output_path: Path) -> dict:
    """Generate valid-observation coverage map for each season."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np

    try:
        import rasterio
    except ImportError:
        print("ERROR: rasterio required.", file=sys.stderr)
        sys.exit(1)

    years = imagery_years()
    target_year = years["imagery_target_year"]
    windows = season_windows(target_year)
    coverage_dir = PROJECT_ROOT / "results" / "coverage"

    seasons = list(windows.keys())
    n = len(seasons)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 7))
    if n == 1:
        axes = [axes]

    for ax, season_key in zip(axes, seasons):
        tif_path = coverage_dir / f"sentinel2_valid_obs_{season_key}_{target_year}.tif"
        if tif_path.exists():
            with rasterio.open(tif_path) as src:
                data = src.read(1).astype(float)
                data[data == src.nodata] = np.nan if src.nodata else data
            im = ax.imshow(data, cmap="YlGn", interpolation="nearest")
            plt.colorbar(im, ax=ax, fraction=0.03, label="Valid observations")
            ax.set_title(f"{season_key.replace('_', ' ').title()}\n{target_year}",
                         fontsize=11)
        else:
            ax.text(0.5, 0.5, f"Coverage raster\nnot yet available\n({tif_path.name})",
                    ha="center", va="center", transform=ax.transAxes,
                    fontsize=9, color="#888888")
            ax.set_title(f"{season_key.replace('_', ' ').title()}\n{target_year}",
                         fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])

    fig.suptitle(
        f"Sentinel-2 L2A Valid-Observation Coverage by Season — {target_year}",
        fontsize=13, y=1.01,
    )
    fig.text(0.5, -0.01,
             "Valid observation: SCL not flagged as cloud, cloud shadow, snow, "
             "saturated, or no-data.",
             ha="center", fontsize=8, color="#555555")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"status": "generated", "output": str(output_path)}


# ── Map 03 — Public monitoring inventory ─────────────────────────────────────

def map_03_monitoring_inventory(output_path: Path) -> dict:
    """Generate public monitoring inventory map. Required caption enforced."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    inv_path = PROJECT_ROOT / "results" / "coverage" / "public_monitoring_inventory.csv"
    aoi_path = PROJECT_ROOT / "data" / "catalog" / "aoi_final.geojson"
    bbox = aoi_bbox()

    fig, ax = plt.subplots(figsize=(9, 11))

    # AOI background
    if aoi_path.exists():
        import geopandas as gpd
        aoi = gpd.read_file(aoi_path)
        aoi.plot(ax=ax, color="#f0f4fa", edgecolor="#2c5f8a", linewidth=1.2)

    category_styles = {
        "groundwater":   {"marker": "o", "color": "#1a6b9a", "size": 20, "label": "Groundwater site"},
        "streamflow":    {"marker": "^", "color": "#e87722", "size": 22, "label": "Streamflow gage"},
        "weather_climate": {"marker": "s", "color": "#6a3d9a", "size": 18, "label": "Weather/climate station"},
        "water_quality": {"marker": "D", "color": "#2ca02c", "size": 16, "label": "Water quality site"},
        "spring":        {"marker": "*", "color": "#17becf", "size": 28, "label": "Spring (NHD/NWIS mapped)"},
        "other":         {"marker": "x", "color": "#888888", "size": 14, "label": "Other public site"},
    }

    period_alpha = {
        "long_record_30plus_yr":    1.0,
        "medium_record_10_30_yr":   0.65,
        "short_record_lt_10_yr":    0.40,
        "single_year_or_less":      0.25,
        "unknown":                  0.20,
    }

    if inv_path.exists():
        import pandas as pd
        df = pd.read_csv(inv_path)
        df = df.dropna(subset=["dec_lat_va", "dec_long_va"])
        df["dec_lat_va"] = pd.to_numeric(df["dec_lat_va"], errors="coerce")
        df["dec_long_va"] = pd.to_numeric(df["dec_long_va"], errors="coerce")
        df = df.dropna(subset=["dec_lat_va", "dec_long_va"])

        for cat, style in category_styles.items():
            sub = df[df["monitoring_category"] == cat]
            for por_cat, alpha in period_alpha.items():
                sub_por = sub[sub["period_of_record_category"] == por_cat]
                if sub_por.empty:
                    continue
                ax.scatter(
                    sub_por["dec_long_va"], sub_por["dec_lat_va"],
                    marker=style["marker"], c=style["color"],
                    s=style["size"], alpha=alpha, zorder=6,
                )
        # Legend for categories
        legend_handles = []
        for cat, style in category_styles.items():
            if not df[df["monitoring_category"] == cat].empty:
                legend_handles.append(
                    plt.scatter([], [], marker=style["marker"], c=style["color"],
                                s=style["size"] * 2, label=style["label"])
                )
        ax.legend(handles=legend_handles, loc="lower right", fontsize=8, framealpha=0.9)
    else:
        ax.text(0.5, 0.5,
                "Monitoring inventory CSV\nnot yet available\nRun acquire_usgs_water.py + "
                "build_monitoring_inventory.py",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=9, color="#888888")

    ax.set_xlim(bbox[0] - 0.02, bbox[2] + 0.02)
    ax.set_ylim(bbox[1] - 0.02, bbox[3] + 0.02)
    ax.set_xlabel("Longitude (WGS 84)")
    ax.set_ylabel("Latitude (WGS 84)")
    ax.set_title(
        "Publicly Documented Monitoring Inventory\n"
        "Lower Walker River–Walker Lake AOI — Period-of-Record Categories",
        fontsize=11, pad=10,
    )
    ax.grid(True, linestyle=":", linewidth=0.4, alpha=0.7)

    # Required caption — enforced
    fig.text(
        0.5, 0.01, REQUIRED_MONITORING_CAPTION,
        ha="center", fontsize=8, color="#333333",
        style="italic", wrap=True,
    )
    fig.text(
        0.5, -0.02,
        "Sources: USGS Water Data for the Nation (NWIS). "
        "Marker opacity reflects period-of-record length.",
        ha="center", fontsize=7, color="#555555",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"status": "generated", "output": str(output_path),
            "caption_enforced": REQUIRED_MONITORING_CAPTION}


# ── Map 04 — NLCD / irrigation-confounder context ────────────────────────────

def map_04_nlcd_irrigation(output_path: Path) -> dict:
    """Generate land-cover labels + irrigation-confounder context map.

    Irrigation (LANID / irrigated-agriculture label) is shown as a
    COMPETING EXPLANATION, not a hydrologic result.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    try:
        import rasterio
    except ImportError:
        print("ERROR: rasterio required.", file=sys.stderr)
        sys.exit(1)

    from src.nlcd_crosswalk import PROTOCOL_CLASSES, get_crosswalk

    years = imagery_years()
    label_year = years["reference_label_year"]
    nlcd_path = (PROJECT_ROOT / "data" / "raw" / "nlcd"
                 / f"nlcd_{label_year}_lower_walker_aoi.tif")
    lanid_dir = PROJECT_ROOT / "data" / "raw" / "lanid"

    # Protocol class color palette
    CLASS_COLORS = {
        1: "#2e7d32",   # Riparian
        2: "#81c784",   # Wet meadow
        3: "#ff8f00",   # Irrigated ag — warm orange = competing explanation
        4: "#bcaaa4",   # Shrubland
        5: "#aed581",   # Herbaceous/pasture
        6: "#cfd8dc",   # Barren/playa
        7: "#5d4037",   # Woodland
        8: "#b0bec5",   # Developed
    }

    fig, (ax_nlcd, ax_irr) = plt.subplots(1, 2, figsize=(14, 9))
    bbox = aoi_bbox()

    # Panel 1: NLCD re-classified to protocol classes
    if nlcd_path.exists():
        crosswalk = {r["nlcd_code"]: r["protocol_class_id"] for r in get_crosswalk()
                     if not r["excluded"] and r["protocol_class_id"]}
        with rasterio.open(nlcd_path) as src:
            nlcd_data = src.read(1).astype(np.float32)
        protocol_data = np.full_like(nlcd_data, np.nan)
        for nlcd_code, proto_id in crosswalk.items():
            protocol_data[nlcd_data == nlcd_code] = proto_id

        cmap = matplotlib.colors.ListedColormap(
            [CLASS_COLORS.get(i, "#eeeeee") for i in range(1, 9)]
        )
        bounds = list(range(1, 10))
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
        ax_nlcd.imshow(np.ma.masked_invalid(protocol_data), cmap=cmap, norm=norm,
                       interpolation="nearest")
        legend_patches = [
            mpatches.Patch(color=CLASS_COLORS[i], label=f"{i}: {PROTOCOL_CLASSES[i][:28]}")
            for i in sorted(CLASS_COLORS)
        ]
        ax_nlcd.legend(handles=legend_patches, loc="lower right", fontsize=6,
                       framealpha=0.9, title="Protocol class")
    else:
        ax_nlcd.text(0.5, 0.5, "NLCD clipped raster\nnot yet available",
                     ha="center", va="center", transform=ax_nlcd.transAxes,
                     fontsize=9, color="#888888")
    ax_nlcd.set_title(f"NLCD {label_year} → 8 Protocol Classes", fontsize=11)
    ax_nlcd.set_xticks([])
    ax_nlcd.set_yticks([])

    # Panel 2: Irrigation confounder layer
    lanid_files = sorted(lanid_dir.glob("*.tif")) if lanid_dir.exists() else []
    if lanid_files:
        with rasterio.open(lanid_files[-1]) as src:
            irr_data = src.read(1).astype(np.float32)
        ax_irr.imshow(irr_data, cmap="OrRd", interpolation="nearest", vmin=0, vmax=1)
        ax_irr.set_title("LANID Irrigated Land (competing explanation)\nNOT a hydrologic result",
                         fontsize=10, color="#8b0000")
    else:
        ax_irr.text(0.5, 0.5,
                    "LANID data not yet available\nRun acquire scripts first",
                    ha="center", va="center", transform=ax_irr.transAxes,
                    fontsize=9, color="#888888")
        ax_irr.set_title("LANID Irrigated Land (competing explanation)\nNOT a hydrologic result",
                         fontsize=10, color="#8b0000")
    ax_irr.set_xticks([])
    ax_irr.set_yticks([])

    fig.suptitle(
        "Land-Cover Labels and Irrigation-Confounder Context\n"
        "Lower Walker River–Walker Lake AOI",
        fontsize=12, y=1.01,
    )
    fig.text(
        0.5, -0.01,
        "Irrigation (LANID) is a pre-specified competing explanation for residual patterns. "
        "It is NOT interpreted as a hydrologic signal.\n"
        "Sources: NLCD 2021 Products v2.0 (CC0); LANID-US (Zenodo).",
        ha="center", fontsize=8, color="#333333",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return {"status": "generated", "output": str(output_path)}


# ── Map manifest update ───────────────────────────────────────────────────────

def update_map_manifest(map_id: str, result: dict, source_script: str) -> None:
    """Update map_manifest.csv with generation result."""
    existing: list[dict] = []
    if MAP_MANIFEST_CSV.exists():
        with MAP_MANIFEST_CSV.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            existing = list(reader)

    out_path = result.get("output")
    cksum = sha256(Path(out_path)) if out_path and Path(out_path).exists() else ""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    updated = False
    for row in existing:
        if row["map_id"] == map_id:
            row["status"] = "generated"
            row["output_path"] = str(Path(out_path).relative_to(PROJECT_ROOT)) if out_path else ""
            row["source_manifest"] = source_script
            row["review_status"] = "pending_review"
            row["checksum_sha256"] = cksum
            row["generated_at"] = now
            row["caption_enforced"] = result.get("caption_enforced", "")
            updated = True
            break

    if not updated:
        existing.append({
            "map_id": map_id,
            "status": "generated",
            "source_manifest": source_script,
            "output_path": str(Path(out_path).relative_to(PROJECT_ROOT)) if out_path else "",
            "review_status": "pending_review",
            "checksum_sha256": cksum,
            "generated_at": now,
            "caption_enforced": result.get("caption_enforced", ""),
            "notes": "",
        })

    if existing:
        with MAP_MANIFEST_CSV.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(existing[0].keys()))
            writer.writeheader()
            writer.writerows(existing)


# ── Main ──────────────────────────────────────────────────────────────────────

MAP_FUNCTIONS = {
    "01": (map_01_aoi_hydrography,
           OUTPUT_DIR / "01_aoi_hydrography_context.png",
           "aoi_hydrography_context"),
    "02": (map_02_sentinel2_coverage,
           OUTPUT_DIR / "02_sentinel2_observation_coverage.png",
           "imagery_observation_coverage"),
    "03": (map_03_monitoring_inventory,
           OUTPUT_DIR / "03_public_monitoring_inventory.png",
           "public_monitoring_inventory"),
    "04": (map_04_nlcd_irrigation,
           OUTPUT_DIR / "04_land_cover_irrigation_context.png",
           "land_cover_and_irrigation_context"),
}


def main() -> None:
    args = build_parser().parse_args()
    to_run = list(MAP_FUNCTIONS.keys()) if args.map == "all" else [args.map]

    for key in to_run:
        fn, out_path, map_id = MAP_FUNCTIONS[key]
        print(f"\n── Map {key}: {map_id} ──")
        result = fn(out_path)
        if result.get("output") and Path(result["output"]).exists():
            cksum = sha256(Path(result["output"]))
            print(f"  Saved to {out_path.name}  SHA-256: {cksum[:12]}…")
        else:
            print(f"  Output not written (inputs may be missing).")
        update_map_manifest(map_id, result, f"src/generate_baseline_maps.py --map {key}")

    print(f"\nMap manifest updated: {MAP_MANIFEST_CSV}")
    print("\nGOVERNANCE: Before releasing any map externally that identifies")
    print("locations on or immediately adjacent to Tribal lands/waters,")
    print("follow the review and release workflow in governance_boundary_register.md.")


if __name__ == "__main__":
    main()
