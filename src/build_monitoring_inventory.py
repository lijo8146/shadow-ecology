"""
Week 3 — Public monitoring inventory table builder
====================================================
Reads the USGS NWIS site files produced by acquire_usgs_water.py and builds
a structured public monitoring inventory table, separating groundwater,
streamflow, weather, water quality, and spring-related observations by
period of record and variable coverage.

Outputs:
    results/coverage/public_monitoring_inventory.csv
    data/catalog/manifest_usgs_waterdata.yaml (coverage_report_path updated)

Caption compliance:
    Every output referencing this table must state:
    "Shows only the public inventory examined; it is not a map of all
    monitoring or local knowledge."

Governance:
    P1 raw; P2 for place-specific release near Tribal lands.
    See governance_boundary_register.md.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    sha256,
)
from src.settings import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "usgs_waterdata"
OUTPUT_DIR = PROJECT_ROOT / "results" / "coverage"
REQUIRED_CAPTION = (
    "Shows only the public inventory examined; "
    "it is not a map of all monitoring or local knowledge."
)


def classify_site(row: dict) -> str:
    """Assign a monitoring category from NWIS site metadata."""
    site_type = row.get("site_tp_cd", "").strip()
    station_nm = row.get("station_nm", "").lower()
    type_map = {
        "GW": "groundwater",
        "ST": "streamflow",
        "AT": "weather_climate",
        "WE": "weather_climate",
        "WQ": "water_quality",
        "SP": "spring",
    }
    cat = type_map.get(site_type, "other")
    # Heuristic: spring in name → spring category even if site_tp_cd differs
    if "spring" in station_nm or "seep" in station_nm:
        cat = "spring"
    return cat


def period_of_record_category(begin: str, end: str) -> str:
    """Bin a period of record into broad categories."""
    try:
        b = int(begin[:4]) if begin else None
        e = int(end[:4]) if end else None
    except (ValueError, TypeError):
        return "unknown"
    if b is None:
        return "unknown"
    span = (e or 2024) - b
    if span >= 30:
        return "long_record_30plus_yr"
    elif span >= 10:
        return "medium_record_10_30_yr"
    elif span >= 1:
        return "short_record_lt_10_yr"
    return "single_year_or_less"


def build_inventory(source_files: dict[str, Path]) -> list[dict]:
    """Merge site files into a unified monitoring inventory."""
    rows = []
    for category, path in source_files.items():
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            # Skip comment lines
            lines = [l for l in fh if not l.startswith("#")]
        if not lines:
            continue
        reader = csv.DictReader(lines)
        for site_row in reader:
            cat = classify_site(site_row)
            rows.append({
                "site_no": site_row.get("site_no", "").strip(),
                "station_nm": site_row.get("station_nm", "").strip(),
                "agency_cd": site_row.get("agency_cd", "USGS").strip(),
                "dec_lat_va": site_row.get("dec_lat_va", "").strip(),
                "dec_long_va": site_row.get("dec_long_va", "").strip(),
                "site_tp_cd": site_row.get("site_tp_cd", "").strip(),
                "monitoring_category": cat,
                "begin_date": site_row.get("begin_date", "").strip(),
                "end_date": site_row.get("end_date", "").strip(),
                "period_of_record_category": period_of_record_category(
                    site_row.get("begin_date", ""),
                    site_row.get("end_date", ""),
                ),
                "source_file": path.name,
                "inventory_note": REQUIRED_CAPTION,
            })
    return rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_files = {
        "groundwater": RAW_DIR / "gw_sites_aoi.csv",
        "streamflow": RAW_DIR / "streamflow_sites_aoi.csv",
        "water_quality": RAW_DIR / "wq_sites_aoi.csv",
    }

    any_exist = any(p.exists() for p in source_files.values())
    if not any_exist:
        print("No NWIS site files found in data/raw/usgs_waterdata/.")
        print("Run src/acquire_usgs_water.py first.")
        sys.exit(0)

    print("Building public monitoring inventory …")
    inventory = build_inventory(source_files)
    print(f"  Total sites: {len(inventory)}")

    # Category summary
    from collections import Counter
    counts = Counter(r["monitoring_category"] for r in inventory)
    for cat, n in sorted(counts.items()):
        print(f"  {cat}: {n} sites")

    out_csv = OUTPUT_DIR / "public_monitoring_inventory.csv"
    if inventory:
        with out_csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(inventory[0].keys()))
            writer.writeheader()
            writer.writerows(inventory)
        cksum = sha256(out_csv)
        print(f"\nInventory written to {out_csv}")
        print(f"SHA-256: {cksum}")
        print(f'\nCAPTION REQUIRED on any map using this table:\n"{REQUIRED_CAPTION}"')
    else:
        out_csv.write_text("# No inventory records built\n", encoding="utf-8")
        cksum = None

    # Update manifest
    manifest = load_or_init_manifest("usgs_waterdata")
    manifest["coverage_report_path"] = str(out_csv.relative_to(PROJECT_ROOT))
    manifest["coverage_pass"] = len(inventory) > 0

    record_processing_step(manifest, {
        "step": "build_public_monitoring_inventory",
        "script": "src/build_monitoring_inventory.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "source_files": {k: str(v) for k, v in source_files.items()},
            "required_caption": REQUIRED_CAPTION,
        },
        "output": str(out_csv.relative_to(PROJECT_ROOT)),
        "output_checksum_sha256": cksum,
        "site_counts_by_category": dict(counts),
    })
    save_manifest("usgs_waterdata", manifest)
    print("\nManifest updated.")


if __name__ == "__main__":
    main()
