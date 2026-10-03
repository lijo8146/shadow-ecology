"""
Week 2 — Sentinel-2 Level-2A acquisition script
================================================
Queries the Microsoft Planetary Computer STAC API for Sentinel-2 L2A scenes
over the frozen AOI for the three required seasons, downloads them to
data/raw/sentinel2/, and writes a filled manifest at
data/catalog/manifest_sentinel2_l2a.yaml.

Usage (from project root, with shadow-ecology conda env active):
    python src/acquire_sentinel2.py [--dry-run]

Options:
    --dry-run   Print the STAC query results without downloading files.

Prerequisites:
    pip install pystac-client planetary-computer

Governance:
    Uses P1 public data only (Copernicus open access via Planetary Computer).
    AOI bbox and imagery year are read from config/study_area.yaml; do NOT
    hand-enter coordinates or dates in this script.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure the project root is on sys.path when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    aoi_bbox,
    imagery_years,
    record_processing_step,
    save_manifest,
    season_windows,
    sha256,
    load_or_init_manifest,
)
from src.settings import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "sentinel2"
COLLECTION = "sentinel-2-l2a"
PLANETARY_COMPUTER_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

# Maximum cloud cover accepted per scene (%).
MAX_CLOUD_PCT = 80


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="Print STAC results only; do not download.")
    return p


def query_scenes(bbox: list[float], date_range: str, max_cloud: int) -> list[dict]:
    """Search Planetary Computer STAC for Sentinel-2 L2A scenes."""
    try:
        import pystac_client
        import planetary_computer
    except ImportError:
        print("ERROR: pystac-client and planetary-computer must be installed.\n"
              "  pip install pystac-client planetary-computer", file=sys.stderr)
        sys.exit(1)

    catalog = pystac_client.Client.open(
        PLANETARY_COMPUTER_URL,
        modifier=planetary_computer.sign_inplace,
    )
    search = catalog.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": max_cloud}},
    )
    return list(search.items())


def download_scene(item: "pystac.Item", output_dir: Path, dry_run: bool) -> dict | None:
    """Download all bands of a STAC item; return a scene record dict."""
    scene_dir = output_dir / item.id
    if not dry_run:
        scene_dir.mkdir(parents=True, exist_ok=True)

    assets_downloaded = []
    for asset_key, asset in item.assets.items():
        if asset.media_type and "image/tiff" not in asset.media_type:
            continue
        href = asset.href
        # Strip query string from signed URL before using as a filename
        local_file = scene_dir / Path(href.split("?")[0]).name
        if not dry_run:
            import urllib.request
            if not local_file.exists():
                print(f"  Downloading {local_file.name} …")
                urllib.request.urlretrieve(href, local_file)
            checksum = sha256(local_file)
        else:
            local_file = None
            checksum = None
        assets_downloaded.append({
            "asset_key": asset_key,
            "href": href,
            "local_file": str(local_file) if local_file else None,
            "checksum_sha256": checksum,
        })

    props = item.properties
    return {
        "product_id": item.id,
        "tile_id": props.get("s2:mgrs_tile"),
        "sensing_datetime": props.get("datetime"),
        "processing_baseline": props.get("s2:processing_baseline"),
        "cloud_cover_pct": props.get("eo:cloud_cover"),
        "snow_ice_cover_pct": props.get("s2:snow_ice_percentage"),
        "local_path": str(scene_dir) if not dry_run else None,
        "assets": assets_downloaded,
        "checksum_sha256": None,  # per-scene checksum computed separately if needed
    }


def main() -> None:
    args = build_parser().parse_args()
    dry_run: bool = args.dry_run

    bbox = aoi_bbox()
    years = imagery_years()
    target_year = years["imagery_target_year"]
    windows = season_windows(target_year)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_or_init_manifest("sentinel2_l2a")
    manifest["download_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    manifest["query_aoi_bbox_wgs84"] = bbox
    manifest["query_aoi_source"] = "data/catalog/aoi_final.geojson"

    for season_key, window in windows.items():
        date_range = f"{window['start']}/{window['end']}"
        print(f"\n── Season: {season_key}  ({date_range}) ──")
        items = query_scenes(bbox, date_range, MAX_CLOUD_PCT)
        print(f"   {len(items)} scene(s) found (cloud < {MAX_CLOUD_PCT}%)")

        scene_records = []
        for item in items:
            print(f"   {item.id}  cloud={item.properties.get('eo:cloud_cover'):.1f}%")
            if not dry_run:
                record = download_scene(item, OUTPUT_DIR, dry_run=False)
                scene_records.append(record)
            else:
                scene_records.append({"product_id": item.id, "dry_run": True})

        # Update the manifest seasons block
        for season_block in manifest.get("seasons", []):
            if season_block.get("season") == season_key:
                season_block["date_range_start"] = window["start"]
                season_block["date_range_end"] = window["end"]
                season_block["scenes"] = scene_records
                break

    record_processing_step(manifest, {
        "step": "stac_query_and_download",
        "script": "src/acquire_sentinel2.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "collection": COLLECTION,
            "max_cloud_pct": MAX_CLOUD_PCT,
            "imagery_target_year": target_year,
            "dry_run": dry_run,
        },
    })

    if not dry_run:
        save_manifest("sentinel2_l2a", manifest)
        print(f"\nManifest written to data/catalog/manifest_sentinel2_l2a.yaml")
    else:
        print("\n[dry-run] Manifest NOT written.")

    print("\nNext step: run src/coverage_report_sentinel2.py to generate")
    print("the valid-observation coverage report for each seasonal window.")


if __name__ == "__main__":
    main()
