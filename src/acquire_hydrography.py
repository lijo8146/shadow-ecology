"""
Week 2 — NHDPlus HR / WBD acquisition and AOI geometry script
==============================================================
Downloads the NHDPlus High Resolution GPKG for HUC-4 region 1605,
extracts HUC-8 subbasin 16050302 from the WBD, applies a 2 km valley-floor
buffer in EPSG:32611, and writes the final AOI geometry to
data/catalog/aoi_final.geojson.

Also extracts:
  - NHDFlowline (streams, canals/ditches)
  - NHDWaterbody (lakes, reservoirs)
  - NHDPoint (springs / seeps)
  - WBD HUC-8 watershed context

Usage (from project root, shadow-ecology conda env active):
    python src/acquire_hydrography.py [--dry-run]

Prerequisites (conda env already includes these):
    geopandas, shapely, pyproj, fiona

Governance: P1 public data only.  AOI geometry method frozen in
data/catalog/aoi_decision_note.md; do not change the buffer or HUC without
a dated amendment.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    aoi_bbox,
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    sha256,
)
from src.settings import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "hydrography"
AOI_OUT = PROJECT_ROOT / "data" / "catalog" / "aoi_final.geojson"

# NHDPlus HR HUC-4 region 1605 GPKG — The National Map download URL.
# Verify current URL at: https://www.usgs.gov/national-hydrography/access-national-hydrography-products
NHDPLUS_HR_URL = (
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHDPlusHR/"
    "Beta/GDB/NHDPLUS_H_1605_HU4_GPKG.zip"
)
WBD_HUC8 = "16050302"
BUFFER_KM = 2.0
ANALYSIS_CRS = "EPSG:32611"

# NHDFlowline FCode ranges
FCODE_CANAL_DITCH = {33600, 33601, 33603}
FCODE_SPRING_SEEP = {45800}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    return p


def download_nhdplus(url: str, out_zip: Path) -> None:
    import urllib.request
    print(f"Downloading NHDPlus HR HUC-4 1605 …\n  {url}")
    urllib.request.urlretrieve(url, out_zip)


def extract_zip(zip_path: Path, out_dir: Path) -> Path:
    import zipfile
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out_dir)
    gpkgs = sorted(out_dir.glob("*.gpkg"))
    if not gpkgs:
        raise FileNotFoundError(f"No .gpkg found in {out_dir}")
    return gpkgs[0]


def build_aoi(gpkg_path: Path, buffer_km: float = BUFFER_KM) -> "GeoDataFrame":
    import geopandas as gpd

    # Load WBD HUC-8 and select the subbasin
    wbd = gpd.read_file(gpkg_path, layer="WBDHU8")
    subbasin = wbd[wbd["huc8"] == WBD_HUC8].copy()
    if subbasin.empty:
        raise ValueError(f"HUC-8 {WBD_HUC8} not found in {gpkg_path}")

    # Project to UTM 11N for metric buffer
    subbasin_utm = subbasin.to_crs(ANALYSIS_CRS)
    aoi_utm = subbasin_utm.copy()
    aoi_utm["geometry"] = aoi_utm.geometry.buffer(buffer_km * 1000)

    # Confirm anchors are contained
    from shapely.geometry import Point
    from src.settings import study_area
    sa = study_area()
    wabuska = Point(sa["upstream_anchor"]["longitude"], sa["upstream_anchor"]["latitude"])
    walker_lake = Point(sa["downstream_anchor"]["longitude"], sa["downstream_anchor"]["latitude"])

    aoi_wgs84 = aoi_utm.to_crs("EPSG:4326")
    aoi_union = aoi_wgs84.union_all() if hasattr(aoi_wgs84, "union_all") else aoi_wgs84.unary_union

    for name, pt in [("Wabuska", wabuska), ("Walker Lake", walker_lake)]:
        if not aoi_union.contains(pt):
            print(f"  WARNING: {name} anchor {pt} is outside the buffered AOI geometry. "
                  f"Review aoi_decision_note.md §3.", file=sys.stderr)

    return aoi_utm.to_crs("EPSG:4326")


def extract_hydrography_layers(gpkg_path: Path, aoi_geom) -> dict[str, "GeoDataFrame"]:
    """Extract relevant NHD feature layers clipped to the AOI."""
    import geopandas as gpd

    layers = {}
    aoi_bounds = aoi_geom.total_bounds   # minx, miny, maxx, maxy

    for layer_name, out_key, fcode_filter in [
        ("NHDFlowline", "flowlines_streams", set()),
        ("NHDFlowline", "canals_ditches", FCODE_CANAL_DITCH),
        ("NHDWaterbody", "waterbodies", set()),
        ("NHDPoint", "springs", FCODE_SPRING_SEEP),
    ]:
        try:
            gdf = gpd.read_file(gpkg_path, layer=layer_name, bbox=tuple(aoi_bounds))
        except Exception as exc:
            print(f"  WARNING: Could not read layer {layer_name}: {exc}", file=sys.stderr)
            continue

        if fcode_filter:
            gdf = gdf[gdf["FCode"].isin(fcode_filter)]

        # Clip to AOI
        gdf_clipped = gdf[gdf.intersects(aoi_geom.union_all()
                                         if hasattr(aoi_geom, "union_all")
                                         else aoi_geom.unary_union)]
        layers[out_key] = gdf_clipped
        print(f"  {out_key}: {len(gdf_clipped)} features")

    return layers


def main() -> None:
    args = build_parser().parse_args()
    dry_run: bool = args.dry_run

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_or_init_manifest("nhdplus_hr_wbd")
    manifest["download_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    zip_path = OUTPUT_DIR / "NHDPLUS_H_1605_HU4_GPKG.zip"
    gpkg_dir = OUTPUT_DIR / "NHDPLUS_H_1605_HU4"

    if dry_run:
        print(f"[dry-run] Would download: {NHDPLUS_HR_URL}")
        print(f"[dry-run] Would extract to: {gpkg_dir}")
        print(f"[dry-run] Would write AOI to: {AOI_OUT}")
        print("[dry-run] Manifest NOT written.")
        return

    if not zip_path.exists():
        download_nhdplus(NHDPLUS_HR_URL, zip_path)
    manifest["checksum_sha256_nhdplus"] = sha256(zip_path)

    gpkg_dir.mkdir(exist_ok=True)
    if not list(gpkg_dir.glob("*.gpkg")):
        print("Extracting …")
        gpkg_path = extract_zip(zip_path, gpkg_dir)
    else:
        gpkg_path = sorted(gpkg_dir.glob("*.gpkg"))[0]
    print(f"GPKG: {gpkg_path.name}")
    manifest["nhdplus_hr_version"] = gpkg_path.name
    manifest["local_path_nhdplus"] = str(gpkg_path.relative_to(PROJECT_ROOT))

    # Build frozen AOI geometry
    print(f"\nBuilding AOI from WBD HUC-8 {WBD_HUC8} + {BUFFER_KM} km buffer …")
    import geopandas as gpd
    aoi_gdf = build_aoi(gpkg_path, BUFFER_KM)
    area_km2 = aoi_gdf.to_crs(ANALYSIS_CRS).area.sum() / 1e6
    print(f"AOI area: {area_km2:.1f} km²")

    aoi_gdf.to_file(AOI_OUT, driver="GeoJSON")
    manifest["aoi_checksum_sha256"] = sha256(AOI_OUT)
    manifest["aoi_area_km2"] = round(area_km2, 1)

    # Check anchors
    from shapely.geometry import Point
    from src.settings import study_area
    sa = study_area()
    aoi_union = aoi_gdf.union_all() if hasattr(aoi_gdf, "union_all") else aoi_gdf.unary_union
    manifest["aoi_contains_wabuska_anchor"] = aoi_union.contains(
        Point(sa["upstream_anchor"]["longitude"], sa["upstream_anchor"]["latitude"]))
    manifest["aoi_contains_walker_lake_anchor"] = aoi_union.contains(
        Point(sa["downstream_anchor"]["longitude"], sa["downstream_anchor"]["latitude"]))
    print(f"Wabuska anchor inside AOI: {manifest['aoi_contains_wabuska_anchor']}")
    print(f"Walker Lake anchor inside AOI: {manifest['aoi_contains_walker_lake_anchor']}")

    # Extract hydrography feature layers
    print("\nExtracting hydrography layers …")
    layers = extract_hydrography_layers(gpkg_path, aoi_gdf)
    for out_key, gdf in layers.items():
        out_path = OUTPUT_DIR / f"{out_key}_lower_walker.gpkg"
        gdf.to_file(out_path, driver="GPKG", layer=out_key)
        # Update manifest layers_extracted
        for layer_rec in manifest.get("layers_extracted", []):
            if layer_rec.get("layer") == out_key:
                layer_rec["output_file"] = str(out_path.relative_to(PROJECT_ROOT))
                layer_rec["checksum_sha256"] = sha256(out_path)
                break

    print(f"\nFrozen AOI written to: {AOI_OUT}")

    record_processing_step(manifest, {
        "step": "download_extract_and_build_aoi",
        "script": "src/acquire_hydrography.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "source_url": NHDPLUS_HR_URL,
            "huc4_region": "1605",
            "huc8_subbasin": WBD_HUC8,
            "buffer_km": BUFFER_KM,
            "analysis_crs": ANALYSIS_CRS,
        },
    })
    save_manifest("nhdplus_hr_wbd", manifest)
    print("Manifest written to data/catalog/manifest_nhdplus_hr_wbd.yaml")


if __name__ == "__main__":
    main()
