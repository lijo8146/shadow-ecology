"""
Week 2 — Landsat Collection 2 Level-2 acquisition script
=========================================================
Downloads Landsat Collection 2 Level-2 scenes for the primary target year and
historical context (2000–target_year) from the USGS STAC endpoint via
pystac-client, and writes a filled manifest at
data/catalog/manifest_landsat_c2_l2.yaml.

Usage (from project root, shadow-ecology conda env active):
    python src/acquire_landsat.py [--dry-run]

Options:
    --dry-run   Print STAC results without downloading.

Prerequisites:
    pip install pystac-client

Governance: P1 public data only.  AOI and year from config/study_area.yaml.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    aoi_bbox,
    imagery_years,
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    sha256,
)
from src.settings import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "landsat"

# USGS Landsat C2 L2 on Planetary Computer
PLANETARY_COMPUTER_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
LANDSAT_COLLECTIONS = ["landsat-c2-l2"]   # covers LS 4-9 as available

MAX_CLOUD_PCT = 70


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    return p


def query_landsat(bbox: list[float], date_range: str) -> list:
    try:
        import pystac_client
        import planetary_computer
    except ImportError:
        print("ERROR: pystac-client and planetary-computer are required.", file=sys.stderr)
        sys.exit(1)

    catalog = pystac_client.Client.open(
        PLANETARY_COMPUTER_URL,
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=LANDSAT_COLLECTIONS,
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": MAX_CLOUD_PCT}},
    )
    return list(search.items())


def scene_record(item) -> dict:
    props = item.properties
    return {
        "product_id": item.id,
        "path_row": f"{int(props['landsat:wrs_path']):03d}/{int(props['landsat:wrs_row']):03d}"
        if props.get("landsat:wrs_path") else None,
        "sensing_date": props.get("datetime", "")[:10],
        "sensor": props.get("platform"),
        "collection": "Collection 2",
        "product_level": "Level-2",
        "cloud_cover_pct": props.get("eo:cloud_cover"),
        "slc_off": props.get("platform") == "landsat-7"
        and props.get("datetime", "") > "2003-05-31",
        "quality_mask_bands": ["QA_PIXEL", "QA_RADSAT"],
        "checksum_sha256": None,
        "local_path": None,
    }


def main() -> None:
    args = build_parser().parse_args()
    dry_run: bool = args.dry_run

    bbox = aoi_bbox()
    years = imagery_years()
    target_year = years["imagery_target_year"]
    # Primary year + historical context
    date_range_primary = f"{target_year}-01-01/{target_year}-12-31"
    date_range_historical = f"2000-01-01/{target_year - 1}-12-31"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_or_init_manifest("landsat_c2_l2")
    manifest["download_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    manifest["query_aoi_bbox_wgs84"] = bbox
    manifest["target_years"]["primary"] = target_year
    manifest["target_years"]["historical_end"] = target_year

    all_scenes: list[dict] = []

    for label, date_range in [("primary", date_range_primary),
                               ("historical", date_range_historical)]:
        print(f"\n── Landsat {label}: {date_range} ──")
        items = query_landsat(bbox, date_range)
        print(f"   {len(items)} scene(s) found (cloud < {MAX_CLOUD_PCT}%)")
        for item in items:
            rec = scene_record(item)
            print(f"   {rec['product_id']}  sensor={rec['sensor']}  "
                  f"date={rec['sensing_date']}  cloud={rec['cloud_cover_pct']}")
            if not dry_run:
                # Download surface reflectance bands + QA
                scene_dir = OUTPUT_DIR / item.id
                scene_dir.mkdir(parents=True, exist_ok=True)
                import urllib.request
                for asset_key, asset in item.assets.items():
                    if asset.media_type and "image/tiff" not in asset.media_type:
                        continue
                    local_file = scene_dir / Path(asset.href).name
                    if not local_file.exists():
                        print(f"    Downloading {local_file.name} …")
                        urllib.request.urlretrieve(asset.href, local_file)
                rec["local_path"] = str(scene_dir)
            all_scenes.append(rec)

    # Group by sensor
    sensors: dict[str, list] = {}
    for rec in all_scenes:
        sensors.setdefault(rec["sensor"], []).append(rec)

    manifest["sensors_acquired"] = [
        {
            "sensor": sensor,
            "collection": "Collection 2",
            "product_level": "Level-2",
            "quality_mask_bands": ["QA_PIXEL", "QA_RADSAT"],
            "scenes": scenes,
        }
        for sensor, scenes in sensors.items()
    ]

    record_processing_step(manifest, {
        "step": "stac_query_and_download",
        "script": "src/acquire_landsat.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "collections": LANDSAT_COLLECTIONS,
            "max_cloud_pct": MAX_CLOUD_PCT,
            "imagery_target_year": target_year,
            "dry_run": dry_run,
        },
    })

    if not dry_run:
        save_manifest("landsat_c2_l2", manifest)
        print(f"\nManifest written to data/catalog/manifest_landsat_c2_l2.yaml")
    else:
        print("\n[dry-run] Manifest NOT written.")


if __name__ == "__main__":
    main()
