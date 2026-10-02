"""
Week 3 — Label feasibility audit
==================================
Calculates per-protocol-class label area, pixel count, and spatial-block
representation, and identifies which classes cannot support five buffered
spatial folds (per pre_analysis_protocol.md §Spatial cross-validation).

The feasibility rule: a class must appear in at least five spatially distinct
5 km × 5 km blocks (post 1 km buffer exclusion) to support the required
nested spatial block cross-validation.  Classes below this threshold are
flagged; no merge/split is permitted after this point without a protocol
amendment.

Usage:
    python src/label_feasibility.py

Outputs:
    results/coverage/label_feasibility_memo.csv
    results/coverage/label_feasibility_memo.md

Prerequisites:
    Clipped NLCD raster must exist (run acquire_nlcd.py first).
    Crosswalk module: src/nlcd_crosswalk.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nlcd_crosswalk import PROTOCOL_CLASSES, get_crosswalk, excluded_nlcd_codes
from src.acquisition import load_or_init_manifest, imagery_years
from src.settings import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "results" / "coverage"
BLOCK_SIZE_M = 5000        # 5 km × 5 km blocks
BUFFER_M = 1000            # 1 km between test and training blocks
MIN_BLOCKS = 5             # minimum blocks required per class

# Pixel area at NLCD native resolution (30 m)
PIXEL_AREA_HA = (30 * 30) / 10_000  # 0.09 ha


def load_nlcd_clipped() -> "tuple[numpy.ndarray, dict]":
    """Load the clipped NLCD raster. Returns (data_array, rasterio_profile)."""
    import numpy as np
    try:
        import rasterio
    except ImportError:
        print("ERROR: rasterio is required.", file=sys.stderr)
        sys.exit(1)

    years = imagery_years()
    label_year = years["reference_label_year"]
    nlcd_path = (PROJECT_ROOT / "data" / "raw" / "nlcd"
                 / f"nlcd_{label_year}_lower_walker_aoi.tif")
    if not nlcd_path.exists():
        print(f"NLCD clipped file not found: {nlcd_path}")
        print("Run src/acquire_nlcd.py first.")
        sys.exit(1)

    with rasterio.open(nlcd_path) as src:
        data = src.read(1)
        profile = src.profile.copy()
    return data, profile


def count_label_blocks(data: "np.ndarray", profile: dict,
                        nlcd_codes: list[int]) -> int:
    """
    Count distinct 5 km × 5 km blocks that contain at least one pixel
    matching any of *nlcd_codes*.  Blocks are post-buffer (inner cells only).
    """
    import numpy as np
    res = profile.get("transform", None)
    if res is None:
        return 0
    pixel_m = abs(profile["transform"].a)   # pixel width in CRS units

    block_px = max(1, int(BLOCK_SIZE_M / pixel_m))
    buffer_px = max(1, int(BUFFER_M / pixel_m))
    inner = slice(buffer_px, -buffer_px or None)

    mask = np.isin(data, nlcd_codes)
    # Count non-overlapping blocks with at least one matching pixel
    nrows, ncols = mask.shape
    count = 0
    for r in range(buffer_px, nrows - buffer_px, block_px):
        for c in range(buffer_px, ncols - buffer_px, block_px):
            block = mask[r:r + block_px, c:c + block_px]
            if block.any():
                count += 1
    return count


def main() -> None:
    import numpy as np

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    crosswalk = get_crosswalk()
    excl = set(excluded_nlcd_codes())

    # Group NLCD codes by protocol class
    protocol_to_nlcd: dict[int, list[int]] = {}
    for row in crosswalk:
        if row["excluded"] or row["protocol_class_id"] is None:
            continue
        protocol_to_nlcd.setdefault(row["protocol_class_id"], []).append(row["nlcd_code"])

    print("Loading NLCD …")
    data, profile = load_nlcd_clipped()
    total_pixels = data.size

    rows: list[dict] = []
    for cls_id in sorted(PROTOCOL_CLASSES):
        nlcd_codes = protocol_to_nlcd.get(cls_id, [])
        if not nlcd_codes:
            rows.append({
                "protocol_class_id": cls_id,
                "protocol_class_name": PROTOCOL_CLASSES[cls_id],
                "nlcd_source_codes": "",
                "pixel_count": 0,
                "area_ha": 0.0,
                "area_pct_total": 0.0,
                "n_5km_blocks": 0,
                "min_blocks_required": MIN_BLOCKS,
                "feasible_for_5_folds": False,
                "notes": "No NLCD codes mapped to this class.",
            })
            continue

        mask = np.isin(data, nlcd_codes) & ~np.isin(data, list(excl))
        px_count = int(mask.sum())
        area_ha = px_count * PIXEL_AREA_HA
        n_blocks = count_label_blocks(data, profile, nlcd_codes)
        feasible = n_blocks >= MIN_BLOCKS

        rows.append({
            "protocol_class_id": cls_id,
            "protocol_class_name": PROTOCOL_CLASSES[cls_id],
            "nlcd_source_codes": ",".join(str(c) for c in nlcd_codes),
            "pixel_count": px_count,
            "area_ha": round(area_ha, 1),
            "area_pct_total": round(100 * px_count / total_pixels, 2) if total_pixels else 0,
            "n_5km_blocks": n_blocks,
            "min_blocks_required": MIN_BLOCKS,
            "feasible_for_5_folds": feasible,
            "notes": "" if feasible else
                     f"INSUFFICIENT BLOCKS ({n_blocks} < {MIN_BLOCKS}): "
                     "protocol amendment required before modeling.",
        })
        flag = "" if feasible else "  ⚠  AMENDMENT REQUIRED"
        print(f"  Class {cls_id} ({PROTOCOL_CLASSES[cls_id][:40]}): "
              f"{px_count:>8,} px  {area_ha:>10.1f} ha  {n_blocks:>3} blocks{flag}")

    # Write CSV
    csv_out = OUTPUT_DIR / "label_feasibility_memo.csv"
    with csv_out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nFeasibility memo CSV → {csv_out}")

    # Write Markdown summary
    infeasible = [r for r in rows if not r["feasible_for_5_folds"]]
    md_out = OUTPUT_DIR / "label_feasibility_memo.md"
    with md_out.open("w", encoding="utf-8") as fh:
        fh.write("# Label Feasibility Memo\n\n")
        fh.write(f"**Date:** {__import__('datetime').date.today().isoformat()}  \n")
        fh.write("**Status:** Frozen after this date — "
                 "no merge/split without a protocol amendment.\n\n")
        fh.write("## Summary\n\n")
        fh.write(f"- Minimum blocks required for 5 spatial folds: {MIN_BLOCKS}\n")
        fh.write(f"- Classes meeting feasibility: {sum(r['feasible_for_5_folds'] for r in rows)}"
                 f" / {len(rows)}\n")
        if infeasible:
            fh.write(f"- **Classes below threshold (amendment required):** "
                     f"{len(infeasible)}\n\n")
            fh.write("## Classes requiring a protocol amendment\n\n")
            for r in infeasible:
                fh.write(f"- **Class {r['protocol_class_id']}: "
                         f"{r['protocol_class_name']}** — "
                         f"{r['n_5km_blocks']} blocks (need {MIN_BLOCKS}), "
                         f"{r['pixel_count']:,} pixels, {r['area_ha']:.1f} ha\n")
        else:
            fh.write("- All classes meet the 5-fold feasibility threshold.\n")
        fh.write("\n## Full table\n\n")
        cols = ["protocol_class_id", "protocol_class_name", "pixel_count",
                "area_ha", "n_5km_blocks", "feasible_for_5_folds"]
        header = " | ".join(cols)
        fh.write(f"| {header} |\n")
        fh.write("|" + "|".join(["---"] * len(cols)) + "|\n")
        for r in rows:
            fh.write("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
    print(f"Feasibility memo Markdown → {md_out}")


if __name__ == "__main__":
    main()
