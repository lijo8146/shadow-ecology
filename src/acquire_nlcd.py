"""
Week 2 — NLCD acquisition script
==================================
Downloads the NLCD annual land-cover product for the reference label year from
the MRLC / USGS ScienceBase, clips it to the frozen AOI bbox, and writes a
filled manifest at data/catalog/manifest_nlcd.yaml.

Usage (from project root, shadow-ecology conda env active):
    python src/acquire_nlcd.py [--dry-run]

Prerequisites (in addition to the conda env):
    pip install requests  (usually already present)

Governance:
    NLCD 2021 Products v2.0 is CC0 1.0.  Cite USGS/MRLC.
    Label year must match reference_label_year from config/study_area.yaml.
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

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "nlcd"

# NLCD annual series download root on MRLC.  The exact filename changes by
# release; update this URL after verifying the current product at:
# https://www.mrlc.gov/data
# Format: nlcd_YYYY_land_cover_l48_YYYYMMDD.img or .tif (varies by year)
NLCD_CONUS_BASE_URL = "https://s3-us-west-2.amazonaws.com/mrlc/nlcd_{year}_land_cover_l48_20230630.img"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    return p


def download_nlcd(url: str, out_path: Path) -> bool:
    """Download the NLCD CONUS file.  Returns True on success."""
    import urllib.request
    import urllib.error
    try:
        print(f"Downloading NLCD from {url} …")
        urllib.request.urlretrieve(url, out_path)
        return True
    except urllib.error.HTTPError as exc:
        print(f"ERROR downloading NLCD: {exc}", file=sys.stderr)
        print("Check the MRLC download page for the current URL:", file=sys.stderr)
        print("  https://www.mrlc.gov/data", file=sys.stderr)
        return False


def clip_to_aoi(in_path: Path, out_path: Path, bbox: list[float]) -> None:
    """Clip the NLCD raster to the AOI bounding box using rasterio."""
    try:
        import rasterio
        from rasterio.mask import mask as rio_mask
        from shapely.geometry import box
        import json
    except ImportError:
        print("ERROR: rasterio and shapely are required for clipping.", file=sys.stderr)
        sys.exit(1)

    west, south, east, north = bbox
    geom = box(west, south, east, north)
    with rasterio.open(in_path) as src:
        # Re-project geometry to source CRS
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", src.crs.to_epsg()
                                           if src.crs.to_epsg() else src.crs.to_wkt(),
                                           always_xy=True)
        coords = list(geom.exterior.coords)
        xs, ys = zip(*[transformer.transform(x, y) for x, y in coords])
        from shapely.geometry import Polygon
        geom_proj = Polygon(zip(xs, ys))

        out_image, out_transform = rio_mask(
            src, [geom_proj.__geo_interface__], crop=True
        )
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "compress": "lzw",
        })
        with rasterio.open(out_path, "w", **out_meta) as dst:
            dst.write(out_image)


def main() -> None:
    args = build_parser().parse_args()
    dry_run: bool = args.dry_run

    years = imagery_years()
    label_year = years["reference_label_year"]
    bbox = aoi_bbox()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_or_init_manifest("nlcd")
    manifest["download_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    manifest["label_year"] = label_year

    url = NLCD_CONUS_BASE_URL.format(year=label_year)
    conus_file = OUTPUT_DIR / f"nlcd_{label_year}_land_cover_l48_conus.img"
    clipped_file = OUTPUT_DIR / f"nlcd_{label_year}_lower_walker_aoi.tif"

    manifest["local_path"] = str(clipped_file.relative_to(PROJECT_ROOT))

    if dry_run:
        print(f"[dry-run] Would download: {url}")
        print(f"[dry-run] Would clip to:  {clipped_file}")
        print("[dry-run] Manifest NOT written.")
        return

    if not conus_file.exists():
        success = download_nlcd(url, conus_file)
        if not success:
            print("\nDownload failed. Verify the URL at https://www.mrlc.gov/data "
                  "and update NLCD_CONUS_BASE_URL in this script.", file=sys.stderr)
            sys.exit(1)

    manifest["checksum_sha256"] = sha256(conus_file)
    print(f"CONUS file SHA-256: {manifest['checksum_sha256']}")

    print(f"Clipping to AOI bbox {bbox} …")
    clip_to_aoi(conus_file, clipped_file, bbox)
    manifest["local_path"] = str(clipped_file.relative_to(PROJECT_ROOT))
    print(f"Clipped NLCD written to {clipped_file}")

    record_processing_step(manifest, {
        "step": "download_and_clip",
        "script": "src/acquire_nlcd.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "label_year": label_year,
            "source_url": url,
            "clip_bbox_wgs84": bbox,
            "output_crs": "EPSG:32611 (after reprojection in modeling pipeline)",
        },
    })
    save_manifest("nlcd", manifest)
    print(f"\nManifest written to data/catalog/manifest_nlcd.yaml")


if __name__ == "__main__":
    main()
