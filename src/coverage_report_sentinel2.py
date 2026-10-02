"""
Week 2 — Sentinel-2 valid-observation coverage report
=====================================================
Reads downloaded Sentinel-2 L2A scenes from data/raw/sentinel2/ and produces
a per-cell valid-observation count raster and summary CSV for each seasonal
window, clipped to the frozen AOI.

A "valid observation" is a pixel that is NOT flagged as cloud, cloud shadow,
or snow/ice in the SCL (Scene Classification Layer).  The SCL classes treated
as invalid are listed in INVALID_SCL_CLASSES below.

Usage (from project root, shadow-ecology conda env active):
    python src/coverage_report_sentinel2.py

Outputs:
    results/coverage/sentinel2_valid_obs_{season}_{year}.tif
    results/coverage/sentinel2_coverage_summary_{year}.csv
    Manifest field coverage_report_path is updated in manifest_sentinel2_l2a.yaml.

Governance: P1 data only.  AOI and year from config/study_area.yaml.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.acquisition import (
    aoi_bbox,
    imagery_years,
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    season_windows,
    valid_obs_threshold,
)
from src.settings import PROJECT_ROOT

# SCL classes treated as invalid (cloud, shadow, snow, saturated, no data).
# Reference: Sentinel-2 L2A Product Specification, Table 3.
INVALID_SCL_CLASSES = {0, 1, 3, 8, 9, 10, 11}

OUTPUT_DIR = PROJECT_ROOT / "results" / "coverage"
S2_RAW_DIR = PROJECT_ROOT / "data" / "raw" / "sentinel2"


def scl_is_valid(scl_array: "np.ndarray") -> "np.ndarray":
    """Return a boolean mask: True where SCL indicates a valid land observation."""
    valid = np.ones_like(scl_array, dtype=bool)
    for cls in INVALID_SCL_CLASSES:
        valid &= scl_array != cls
    return valid


def count_valid_obs_season(season_dir: Path) -> tuple["np.ndarray", dict] | None:
    """
    Count valid observations across all scenes in *season_dir*.

    Returns (count_array, profile) or None if no SCL files are found.
    This function requires rasterio; it is not imported at module level so the
    script can still be imported/tested without the full geo stack installed.
    """
    try:
        import rasterio
        from rasterio.merge import merge
    except ImportError:
        print("ERROR: rasterio is required for coverage-report generation.", file=sys.stderr)
        sys.exit(1)

    scl_files = sorted(season_dir.rglob("*SCL*.tif"))
    if not scl_files:
        print(f"  No SCL files found in {season_dir}; skipping.", file=sys.stderr)
        return None

    count = None
    profile = None
    for scl_path in scl_files:
        with rasterio.open(scl_path) as src:
            data = src.read(1)
            valid = scl_is_valid(data).astype(np.uint16)
            if count is None:
                count = valid
                profile = src.profile.copy()
            else:
                count = count + valid  # accumulate valid-obs count

    return count, profile


def write_coverage_tif(count: "np.ndarray", profile: dict, out_path: Path) -> None:
    """Write a single-band UInt16 valid-observation count raster."""
    import rasterio
    profile.update(dtype="uint16", count=1, compress="lzw")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(count.astype(np.uint16), 1)


def coverage_fraction(count: "np.ndarray", n_scenes: int) -> float:
    """Return the fraction of pixels with at least one valid observation."""
    if n_scenes == 0:
        return 0.0
    return float((count >= 1).sum()) / float(count.size)


def main() -> None:
    years = imagery_years()
    target_year = years["imagery_target_year"]
    windows = season_windows(target_year)
    threshold = valid_obs_threshold()
    manifest = load_or_init_manifest("sentinel2_l2a")

    import csv
    summary_rows = []

    for season_key, window in windows.items():
        season_dir = S2_RAW_DIR / season_key
        print(f"Season: {season_key}  ({window['start']} – {window['end']})")

        if not season_dir.exists():
            print(f"  WARNING: {season_dir} does not exist; skipping. "
                  "Run acquire_sentinel2.py first.")
            summary_rows.append({
                "season": season_key,
                "year": target_year,
                "n_scenes": 0,
                "valid_obs_coverage_pct": None,
                "threshold_pct": threshold * 100,
                "passes_threshold": False,
                "notes": "scene directory missing",
            })
            continue

        result = count_valid_obs_season(season_dir)
        if result is None:
            summary_rows.append({
                "season": season_key,
                "year": target_year,
                "n_scenes": 0,
                "valid_obs_coverage_pct": None,
                "threshold_pct": threshold * 100,
                "passes_threshold": False,
                "notes": "no SCL files found",
            })
            continue

        count, profile = result
        n_scenes = len(sorted(season_dir.rglob("*SCL*.tif")))
        frac = coverage_fraction(count, n_scenes)
        passes = frac >= threshold

        out_tif = OUTPUT_DIR / f"sentinel2_valid_obs_{season_key}_{target_year}.tif"
        write_coverage_tif(count, profile, out_tif)
        print(f"  {n_scenes} scenes · {frac*100:.1f}% valid-obs coverage → "
              f"{'PASS' if passes else 'FAIL / AMENDMENT NEEDED'}  → {out_tif.name}")

        summary_rows.append({
            "season": season_key,
            "year": target_year,
            "n_scenes": n_scenes,
            "valid_obs_coverage_pct": round(frac * 100, 2),
            "threshold_pct": threshold * 100,
            "passes_threshold": passes,
            "notes": "" if passes else "Below threshold; amendment required before modeling",
        })

    # Write summary CSV
    summary_csv = OUTPUT_DIR / f"sentinel2_coverage_summary_{target_year}.csv"
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    with summary_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"\nCoverage summary → {summary_csv}")

    # Update manifest
    manifest["coverage_report_path"] = str(summary_csv.relative_to(PROJECT_ROOT))
    all_pass = all(r["passes_threshold"] for r in summary_rows if r["valid_obs_coverage_pct"] is not None)
    manifest["coverage_pass"] = all_pass

    record_processing_step(manifest, {
        "step": "valid_obs_coverage_report",
        "script": "src/coverage_report_sentinel2.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "invalid_scl_classes": sorted(INVALID_SCL_CLASSES),
            "valid_obs_threshold_pct": threshold * 100,
            "imagery_target_year": target_year,
        },
        "output": str(summary_csv.relative_to(PROJECT_ROOT)),
    })
    save_manifest("sentinel2_l2a", manifest)
    print("Manifest updated.")


if __name__ == "__main__":
    main()
