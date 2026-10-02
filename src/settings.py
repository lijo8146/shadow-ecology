"""Load and validate project configuration without embedding study-area constants."""
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_CATALOG_DIR = PROJECT_ROOT / "data" / "catalog"


def load_yaml(name: str) -> dict:
    """Load a named YAML configuration file from the project config directory."""
    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def study_area() -> dict:
    """Return the authoritative study-area configuration."""
    config = load_yaml("study_area.yaml")
    sa = config["study_area"]
    bbox = sa["provisional_bbox_wgs84"]
    if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError("study_area.provisional_bbox_wgs84 must be [west, south, east, north]")
    return sa


def imagery_years() -> dict:
    """Return the frozen imagery and reference-label years.

    Raises ValueError if either year is not recorded in study_area.yaml,
    ensuring downstream scripts fail loudly rather than silently using defaults.
    """
    sa = study_area()
    target = sa.get("imagery_target_year")
    label = sa.get("reference_label_year")
    if target is None or label is None:
        raise ValueError(
            "imagery_target_year and reference_label_year must be set in "
            "config/study_area.yaml before any imagery download."
        )
    return {"imagery_target_year": int(target), "reference_label_year": int(label)}


def catalog_manifest(dataset_id: str) -> dict:
    """Load a filled or template manifest YAML from data/catalog/ by dataset_id."""
    # Prefer a filled manifest; fall back to the template.
    filled = DATA_CATALOG_DIR / f"manifest_{dataset_id}.yaml"
    template = DATA_CATALOG_DIR / f"manifest_template_{dataset_id}.yaml"
    for candidate in (filled, template):
        if candidate.exists():
            with candidate.open(encoding="utf-8") as handle:
                return yaml.safe_load(handle)
    raise FileNotFoundError(
        f"No manifest found for dataset_id='{dataset_id}' in {DATA_CATALOG_DIR}"
    )
