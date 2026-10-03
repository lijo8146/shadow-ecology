"""
Week 2 — NLCD acquisition
==========================
Downloads the NLCD 2021 Land Cover L48 product for the AOI and writes a
filled manifest at data/catalog/manifest_nlcd.yaml.

MRLC no longer allows anonymous programmatic downloads of NLCD land cover
rasters (S3 bucket policy blocks direct access; WCS GetCoverage returns 404
for land cover layers).

Two supported approaches:

  A) earthaccess (recommended, fully automated):
       conda install -c conda-forge earthaccess
       python src/acquire_nlcd.py

     earthaccess authenticates via NASA Earthdata Login (free account required)
     and downloads the file automatically.

  B) Manual download (fallback, no extra dependencies):
     1. Go to https://www.mrlc.gov/data and select:
          Product:    NLCD 2021 Land Cover (CONUS)
          Layer Name: NLCD_2021_Land_Cover_L48
          Format:     GeoTIFF
     2. Draw a bounding box or enter the AOI coordinates:
          West: -119.20   South: 38.50   East: -118.55   North: 39.22
     3. Download the resulting zip to:
          data/raw/nlcd/
     4. Run this script with --register to record it in the manifest:
          python src/acquire_nlcd.py --register data/raw/nlcd/<downloaded_file>.zip

Usage:
    python src/acquire_nlcd.py               # uses earthaccess (auto)
    python src/acquire_nlcd.py --dry-run     # show what would be downloaded
    python src/acquire_nlcd.py --register <zip_path>   # register manual download

Governance:
    NLCD 2021 Products v2.0 is CC0 1.0.  Cite USGS/MRLC.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
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

# Earthdata short name and version for NLCD 2021 Land Cover L48
EARTHDATA_SHORT_NAME = "NLCD_LANDCOVER_ESP_CONUS_2021"
EARTHDATA_VERSION = "1"

# Fallback: known concept ID on NASA CMR for NLCD 2021 Land Cover CONUS
CMR_CONCEPT_ID = "C2763265063-LPCLOUD"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be downloaded without downloading.")
    p.add_argument("--register", metavar="ZIP_PATH",
                   help="Register a manually downloaded zip file in the manifest.")
    return p


# ── earthaccess download ──────────────────────────────────────────────────────

def download_via_earthaccess(bbox: list[float], out_dir: Path, dry_run: bool) -> Path | None:
    """Download NLCD 2021 Land Cover L48 via NASA earthaccess."""
    try:
        import earthaccess
    except ImportError:
        print("earthaccess is not installed.", file=sys.stderr)
        print("Install with:  conda install -c conda-forge earthaccess", file=sys.stderr)
        return None

    print("Authenticating with NASA Earthdata Login via earthaccess…")
    try:
        earthaccess.login(strategy="netrc")
    except Exception:
        try:
            earthaccess.login(strategy="environment")
        except Exception:
            earthaccess.login(strategy="interactive")

    west, south, east, north = bbox
    print(f"Searching for NLCD 2021 Land Cover (CONUS) over AOI bbox…")
    results = earthaccess.search_data(
        short_name=EARTHDATA_SHORT_NAME,
        version=EARTHDATA_VERSION,
        bounding_box=(west, south, east, north),
    )
    if not results:
        # Try by concept ID
        results = earthaccess.search_data(concept_id=CMR_CONCEPT_ID)

    if not results:
        print("ERROR: No NLCD 2021 results found on NASA Earthdata.", file=sys.stderr)
        print("Try the manual download approach described in the script header.",
              file=sys.stderr)
        return None

    print(f"Found {len(results)} granule(s).")
    if dry_run:
        for r in results:
            print(f"  [dry-run] {r}")
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded = earthaccess.download(results, str(out_dir))
    if downloaded:
        return Path(downloaded[0])
    return None


# ── Manual registration ───────────────────────────────────────────────────────

def register_manual_download(zip_path: Path, label_year: int, bbox: list[float]) -> Path:
    """Unzip a manually downloaded NLCD file and return the .img or .tif path."""
    if not zip_path.exists():
        print(f"ERROR: file not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {zip_path.name} …")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(out_dir)

    # Find the extracted raster
    for ext in ("*.img", "*.tif", "*.tiff"):
        matches = sorted(out_dir.glob(ext))
        if matches:
            return matches[0]

    print("WARNING: no .img/.tif found after extraction. "
          "Check the contents of the zip manually.", file=sys.stderr)
    return zip_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = build_parser().parse_args()

    years = imagery_years()
    label_year = years["reference_label_year"]
    bbox = aoi_bbox()

    manifest = load_or_init_manifest("nlcd")
    manifest["label_year"] = label_year
    manifest["download_date"] = datetime.utcnow().strftime("%Y-%m-%d")

    # ── Manual registration path ──────────────────────────────────────────────
    if args.register:
        zip_path = Path(args.register)
        raster = register_manual_download(zip_path, label_year, bbox)
        cksum = sha256(raster)
        manifest["local_path"] = str(raster.relative_to(PROJECT_ROOT))
        manifest["source_url"] = "https://www.mrlc.gov/data (manual download)"
        manifest["checksum_sha256"] = cksum
        record_processing_step(manifest, {
            "step": "manual_download_registration",
            "script": "src/acquire_nlcd.py --register",
            "parameters": {
                "source_zip": str(zip_path),
                "label_year": label_year,
            },
        })
        save_manifest("nlcd", manifest)
        print(f"Registered: {raster.name}  SHA-256: {cksum[:12]}…")
        print("Manifest written to data/catalog/manifest_nlcd.yaml")
        return

    # ── Dry-run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        print(f"[dry-run] Label year      : {label_year}")
        print(f"[dry-run] AOI bbox (WGS84): {bbox}")
        print(f"[dry-run] Output dir      : {OUTPUT_DIR}")
        print()
        _print_manual_instructions(bbox)
        return

    # ── earthaccess automated download ───────────────────────────────────────
    result = download_via_earthaccess(bbox, OUTPUT_DIR, dry_run=False)

    if result is None:
        print()
        print("Automated download failed or earthaccess is not installed.")
        print("Use the manual download approach:")
        _print_manual_instructions(bbox)
        sys.exit(1)

    cksum = sha256(result)
    manifest["local_path"] = str(result.relative_to(PROJECT_ROOT))
    manifest["source_url"] = "NASA Earthdata / earthaccess"
    manifest["checksum_sha256"] = cksum
    record_processing_step(manifest, {
        "step": "earthaccess_download",
        "script": "src/acquire_nlcd.py",
        "parameters": {
            "short_name": EARTHDATA_SHORT_NAME,
            "label_year": label_year,
            "aoi_bbox_wgs84": bbox,
        },
    })
    save_manifest("nlcd", manifest)
    print(f"Downloaded: {result.name}  SHA-256: {cksum[:12]}…")
    print("Manifest written to data/catalog/manifest_nlcd.yaml")


def _print_manual_instructions(bbox: list[float]) -> None:
    west, south, east, north = bbox
    print("─" * 60)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("─" * 60)
    print("MRLC requires authenticated download. Two options:\n")
    print("Option A — earthaccess (free NASA Earthdata account):")
    print("  1. Register at https://urs.earthdata.nasa.gov/")
    print("  2. conda install -c conda-forge earthaccess")
    print("  3. python src/acquire_nlcd.py\n")
    print("Option B — MRLC web tool (no account required):")
    print("  1. Go to https://www.mrlc.gov/data")
    print("  2. Select: National Land Cover Database > NLCD 2021 Land Cover > CONUS")
    print(f"  3. Enter bbox:  West={west}  South={south}  East={east}  North={north}")
    print("  4. Download the zip to data/raw/nlcd/")
    print("  5. Register it:  python src/acquire_nlcd.py --register data/raw/nlcd/<file>.zip")
    print("─" * 60)


if __name__ == "__main__":
    main()
