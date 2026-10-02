"""
Week 3 — NLCD-to-protocol class crosswalk
==========================================
Defines the authoritative mapping from NLCD 2021 class codes to the eight
locked protocol classes from pre_analysis_protocol.md, and documents
excluded/ambiguous classes and expected error modes.

This module can be imported by downstream scripts (labeling, feasibility
audit) or run directly to print the crosswalk as CSV.

Usage:
    python src/nlcd_crosswalk.py [--csv]

    --csv   Write data/catalog/nlcd_to_protocol_crosswalk.csv

Governance:
    The eight locked protocol classes may NOT be merged, split, or dropped
    after examining residual results without a dated amendment to
    pre_analysis_protocol.md (§Fixed land-cover classes).
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.settings import PROJECT_ROOT

# ── Eight locked protocol classes (from pre_analysis_protocol.md) ────────────
PROTOCOL_CLASSES = {
    1: "Riparian/phreatophytic vegetation",
    2: "Wet meadow/emergent wetland",
    3: "Irrigated agriculture",
    4: "Shrubland",
    5: "Herbaceous grassland/pasture",
    6: "Barren, playa, saline, or sparsely vegetated surface",
    7: "Woodland/pinyon-juniper",
    8: "Developed, transportation, or disturbed land",
}

# ── NLCD 2021 → Protocol class crosswalk ─────────────────────────────────────
# Columns: nlcd_code, nlcd_class_name, protocol_class_id, protocol_class_name,
#          crosswalk_confidence, ambiguous, excluded, notes
# confidence: high / medium / low
# ambiguous: True if confusion with another protocol class is likely
# excluded: True if this NLCD class is excluded from the confirmatory domain
#   (per pre_analysis_protocol.md §Analysis domain)
CROSSWALK = [
    # ── Open water ────────────────────────────────────────────────────────────
    (11, "Open Water",
     None, None,
     None, False, True,
     "Excluded from primary interpretation (open water)."),

    # ── Perennial/ice/snow ────────────────────────────────────────────────────
    (12, "Perennial Ice/Snow",
     None, None,
     None, False, True,
     "Not present in AOI; excluded if encountered."),

    # ── Developed ─────────────────────────────────────────────────────────────
    (21, "Developed, Open Space",
     8, "Developed, transportation, or disturbed land",
     "medium", True, False,
     "Ambiguous with herbaceous grassland/pasture at low intensity; "
     "include unless explicitly excluded as urban core."),
    (22, "Developed, Low Intensity",
     8, "Developed, transportation, or disturbed land",
     "high", False, False,
     ""),
    (23, "Developed, Medium Intensity",
     8, "Developed, transportation, or disturbed land",
     "high", False, True,
     "Urban cores excluded from primary interpretation per protocol §Domain."),
    (24, "Developed, High Intensity",
     8, "Developed, transportation, or disturbed land",
     "high", False, True,
     "Urban cores excluded from primary interpretation per protocol §Domain."),

    # ── Barren ────────────────────────────────────────────────────────────────
    (31, "Barren Land",
     6, "Barren, playa, saline, or sparsely vegetated surface",
     "high", False, False,
     "Includes active mine sites; active mines excluded as disturbance stratum "
     "unless analyzed separately."),

    # ── Forest ────────────────────────────────────────────────────────────────
    (41, "Deciduous Forest",
     1, "Riparian/phreatophytic vegetation",
     "medium", True, False,
     "Deciduous forest in the AOI is predominantly riparian cottonwood/willow; "
     "confirm with NDVI phenology. Ambiguous with Woodland/pinyon-juniper."),
    (42, "Evergreen Forest",
     7, "Woodland/pinyon-juniper",
     "high", False, False,
     "Dominant evergreen is pinyon-juniper at higher elevations."),
    (43, "Mixed Forest",
     7, "Woodland/pinyon-juniper",
     "medium", True, False,
     "Ambiguous between riparian/phreatophytic and woodland; "
     "verify with elevation and NDVI timing."),

    # ── Shrubland ─────────────────────────────────────────────────────────────
    (51, "Dwarf Scrub",
     4, "Shrubland",
     "high", False, False,
     ""),
    (52, "Shrub/Scrub",
     4, "Shrubland",
     "high", False, False,
     "Most common upland class in the AOI."),

    # ── Grassland/Herbaceous ──────────────────────────────────────────────────
    (71, "Grassland/Herbaceous",
     5, "Herbaceous grassland/pasture",
     "medium", True, False,
     "Ambiguous with wet meadow/emergent wetland where mesic; "
     "ambiguous with irrigated pasture where water-managed."),
    (72, "Sedge/Herbaceous",
     2, "Wet meadow/emergent wetland",
     "high", False, False,
     "Strong indicator of wet meadow in Great Basin context."),
    (73, "Lichens",
     6, "Barren, playa, saline, or sparsely vegetated surface",
     "low", True, False,
     "Rare in AOI; likely playa or sparsely vegetated if present."),
    (74, "Moss",
     2, "Wet meadow/emergent wetland",
     "low", True, False,
     "Rare; treat as wet meadow/emergent if present."),

    # ── Agriculture ───────────────────────────────────────────────────────────
    (81, "Pasture/Hay",
     5, "Herbaceous grassland/pasture",
     "medium", True, False,
     "Ambiguous with irrigated agriculture; cross-check with LANID. "
     "Irrigated hay likely maps to protocol class 3."),
    (82, "Cultivated Crops",
     3, "Irrigated agriculture",
     "high", False, False,
     "Dominant irrigated class in Walker Valley."),

    # ── Wetlands ─────────────────────────────────────────────────────────────
    (90, "Woody Wetlands",
     1, "Riparian/phreatophytic vegetation",
     "high", False, False,
     "Mapped riparian/phreatophytic in Great Basin valley floors."),
    (95, "Emergent Herbaceous Wetlands",
     2, "Wet meadow/emergent wetland",
     "high", False, False,
     "Direct match to protocol class 2."),
]

OUTPUT_CSV = PROJECT_ROOT / "data" / "catalog" / "nlcd_to_protocol_crosswalk.csv"

FIELDNAMES = [
    "nlcd_code", "nlcd_class_name",
    "protocol_class_id", "protocol_class_name",
    "crosswalk_confidence", "ambiguous", "excluded", "notes",
]


def get_crosswalk() -> list[dict]:
    """Return the crosswalk as a list of dicts for programmatic use."""
    return [
        dict(zip(FIELDNAMES, row))
        for row in CROSSWALK
    ]


def write_csv(out_path: Path = OUTPUT_CSV) -> None:
    rows = get_crosswalk()
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Crosswalk written to {out_path}")


def protocol_classes_for_nlcd(nlcd_code: int) -> dict | None:
    """Return the protocol mapping for a given NLCD code, or None if excluded."""
    for row in get_crosswalk():
        if row["nlcd_code"] == nlcd_code:
            return row
    return None


def excluded_nlcd_codes() -> list[int]:
    return [r["nlcd_code"] for r in get_crosswalk() if r["excluded"]]


def ambiguous_nlcd_codes() -> list[int]:
    return [r["nlcd_code"] for r in get_crosswalk() if r["ambiguous"] and not r["excluded"]]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", action="store_true", help="Write the crosswalk CSV.")
    return p


def main() -> None:
    args = build_parser().parse_args()
    rows = get_crosswalk()

    print("NLCD → Protocol class crosswalk")
    print("=" * 70)
    for r in rows:
        status = "EXCLUDED" if r["excluded"] else ("AMBIGUOUS" if r["ambiguous"] else "")
        label = f"→ Protocol {r['protocol_class_id']}: {r['protocol_class_name']}" \
            if r["protocol_class_id"] else "→ EXCLUDED"
        print(f"  NLCD {r['nlcd_code']:3d}  {r['nlcd_class_name']:<35s}  "
              f"{label}  [{r['crosswalk_confidence'] or ''}]  {status}")
        if r["notes"]:
            print(f"         {r['notes']}")

    print(f"\nExcluded NLCD codes: {excluded_nlcd_codes()}")
    print(f"Ambiguous NLCD codes (not excluded): {ambiguous_nlcd_codes()}")

    from collections import Counter
    by_protocol = Counter(
        r["protocol_class_id"] for r in rows if not r["excluded"] and r["protocol_class_id"]
    )
    print("\nNLCD codes mapped per protocol class:")
    for cls_id in sorted(by_protocol):
        print(f"  Class {cls_id} ({PROTOCOL_CLASSES[cls_id]}): "
              f"{by_protocol[cls_id]} NLCD source code(s)")

    if args.csv:
        OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        write_csv()


if __name__ == "__main__":
    main()
