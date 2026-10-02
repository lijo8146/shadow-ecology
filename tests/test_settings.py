"""Week 1 configuration and catalog smoke tests.

Run with:  pytest -q
All tests use only configuration files and manifest templates; no data files
are required.
"""
from pathlib import Path
import yaml
import pytest

from src.settings import study_area, imagery_years, catalog_manifest, PROJECT_ROOT

# ── Study-area / bbox ────────────────────────────────────────────────────────

def test_study_area_bbox_is_valid():
    bbox = study_area()["provisional_bbox_wgs84"]
    assert len(bbox) == 4
    assert bbox[0] < bbox[2], "west must be less than east"
    assert bbox[1] < bbox[3], "south must be less than north"


def test_study_area_anchors_inside_bbox():
    sa = study_area()
    bbox = sa["provisional_bbox_wgs84"]
    west, south, east, north = bbox

    wabuska_lon = sa["upstream_anchor"]["longitude"]
    wabuska_lat = sa["upstream_anchor"]["latitude"]
    assert west <= wabuska_lon <= east, "Wabuska anchor longitude outside bbox"
    assert south <= wabuska_lat <= north, "Wabuska anchor latitude outside bbox"

    walker_lake_lon = sa["downstream_anchor"]["longitude"]
    walker_lake_lat = sa["downstream_anchor"]["latitude"]
    assert west <= walker_lake_lon <= east, "Walker Lake anchor longitude outside bbox"
    assert south <= walker_lake_lat <= north, "Walker Lake anchor latitude outside bbox"


def test_study_area_crs_fields_present():
    sa = study_area()
    assert sa.get("crs_analysis") == "EPSG:32611"
    assert sa.get("crs_source") == "EPSG:4326"


def test_study_area_boundary_frozen():
    """Geometry method must be recorded as frozen."""
    sa = study_area()
    assert sa.get("boundary_frozen_date"), "boundary_frozen_date must be set"
    assert sa.get("aoi_decision_note"), "aoi_decision_note path must be set"


# ── Imagery years ────────────────────────────────────────────────────────────

def test_imagery_years_are_set():
    years = imagery_years()
    assert isinstance(years["imagery_target_year"], int)
    assert isinstance(years["reference_label_year"], int)


def test_imagery_years_are_plausible():
    years = imagery_years()
    assert 2017 <= years["imagery_target_year"] <= 2030, \
        "imagery_target_year should be a recent complete year"
    assert 2017 <= years["reference_label_year"] <= 2030, \
        "reference_label_year should be within NLCD annual series range"


def test_imagery_year_decision_date_present():
    sa = study_area()
    assert sa.get("imagery_year_decision_date"), \
        "imagery_year_decision_date must be recorded before any download"


# ── Manifest templates ────────────────────────────────────────────────────────

CORE_DATASET_IDS = [
    "sentinel2_l2a",
    "landsat_c2_l2",
    "nlcd",
    "usgs_waterdata",
    "nhdplus_hr_wbd",
    "ssurgo_gssurgo",
    "daymet",
    "lanid",
]


@pytest.mark.parametrize("dataset_id", CORE_DATASET_IDS)
def test_manifest_template_exists(dataset_id):
    """Every core dataset must have a manifest template in data/catalog/."""
    manifest = catalog_manifest(dataset_id)
    assert manifest is not None, f"manifest for {dataset_id} loaded as None"


@pytest.mark.parametrize("dataset_id", CORE_DATASET_IDS)
def test_manifest_template_has_required_fields(dataset_id):
    """Each manifest template must declare the fields required by data/catalog/README.md."""
    manifest = catalog_manifest(dataset_id)
    required = ["dataset_id", "role", "status", "source_url", "access_method", "license"]
    for field in required:
        assert field in manifest, f"manifest for {dataset_id} missing field '{field}'"


@pytest.mark.parametrize("dataset_id", CORE_DATASET_IDS)
def test_manifest_dataset_id_matches(dataset_id):
    manifest = catalog_manifest(dataset_id)
    assert manifest["dataset_id"] == dataset_id, \
        f"manifest dataset_id '{manifest['dataset_id']}' does not match '{dataset_id}'"


# ── AOI decision note ────────────────────────────────────────────────────────

def test_aoi_decision_note_exists():
    sa = study_area()
    note_path = PROJECT_ROOT / sa["aoi_decision_note"]
    assert note_path.exists(), f"AOI decision note not found at {note_path}"


def test_aoi_decision_note_references_both_anchors():
    sa = study_area()
    note_path = PROJECT_ROOT / sa["aoi_decision_note"]
    text = note_path.read_text(encoding="utf-8")
    assert "Wabuska" in text, "AOI decision note must reference the Wabuska anchor"
    assert "Walker Lake" in text, "AOI decision note must reference the Walker Lake anchor"


# ── Dataset catalog CSV ───────────────────────────────────────────────────────

def test_dataset_catalog_csv_exists():
    catalog_path = PROJECT_ROOT / "data" / "catalog" / "dataset_catalog.csv"
    assert catalog_path.exists()


def test_core_datasets_in_catalog():
    import csv
    catalog_path = PROJECT_ROOT / "data" / "catalog" / "dataset_catalog.csv"
    with catalog_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        ids = {row["dataset_id"] for row in reader}
    for dataset_id in CORE_DATASET_IDS:
        assert dataset_id in ids, \
            f"Core dataset '{dataset_id}' missing from dataset_catalog.csv"
