"""
Acquisition utilities shared across Week 2 download scripts.

All functions read the authoritative configuration from src.settings; no
study-area constants are hard-coded here.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from src.settings import PROJECT_ROOT, catalog_manifest, study_area, imagery_years


# ── Checksum ─────────────────────────────────────────────────────────────────

def sha256(path: Path, chunk: int = 1 << 20) -> str:
    """Return the hex SHA-256 digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


# ── AOI helpers ───────────────────────────────────────────────────────────────

def aoi_bbox() -> list[float]:
    """Return [west, south, east, north] from the authoritative config."""
    return study_area()["provisional_bbox_wgs84"]


def aoi_geojson_path() -> Path:
    """Return the path to aoi_final.geojson (may not yet exist)."""
    return PROJECT_ROOT / study_area()["aoi_vector_file"]


# ── Season window definitions ─────────────────────────────────────────────────

def season_windows(year: int | None = None) -> dict[str, dict[str, str]]:
    """Return ISO-8601 date ranges for the three required seasons.

    Defaults to imagery_target_year from config/study_area.yaml.
    """
    if year is None:
        year = imagery_years()["imagery_target_year"]
    return {
        "spring": {
            "start": f"{year}-04-01",
            "end": f"{year}-05-31",
        },
        "peak_growing": {
            "start": f"{year}-07-01",
            "end": f"{year}-08-31",
        },
        "late_season": {
            "start": f"{year}-09-01",
            "end": f"{year}-10-31",
        },
    }


# ── Manifest helpers ──────────────────────────────────────────────────────────

def load_or_init_manifest(dataset_id: str) -> dict:
    """Load a filled manifest if it exists; otherwise copy the template."""
    filled_path = PROJECT_ROOT / "data" / "catalog" / f"manifest_{dataset_id}.yaml"
    if filled_path.exists():
        with filled_path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    return catalog_manifest(dataset_id)


def save_manifest(dataset_id: str, manifest: dict) -> None:
    """Write the filled manifest to data/catalog/manifest_{dataset_id}.yaml."""
    filled_path = PROJECT_ROOT / "data" / "catalog" / f"manifest_{dataset_id}.yaml"
    with filled_path.open("w", encoding="utf-8") as fh:
        yaml.dump(manifest, fh, default_flow_style=False, sort_keys=False, allow_unicode=True)


def record_processing_step(manifest: dict, step: dict) -> None:
    """Append a processing-step record to *manifest* in-place."""
    if "processing_steps" not in manifest or manifest["processing_steps"] is None:
        manifest["processing_steps"] = []
    step.setdefault("timestamp", datetime.utcnow().isoformat(timespec="seconds") + "Z")
    manifest["processing_steps"].append(step)


# ── Coverage helpers ──────────────────────────────────────────────────────────

def valid_obs_threshold() -> float:
    """Pre-declared valid-observation threshold (fraction) from manifest template."""
    m = catalog_manifest("sentinel2_l2a")
    return float(m.get("valid_obs_threshold_pct", 80)) / 100.0
