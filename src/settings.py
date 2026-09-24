"""Load and validate project configuration without embedding study-area constants."""
from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml(name: str) -> dict:
    """Load a named YAML configuration file from the project config directory."""
    path = CONFIG_DIR / name
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def study_area() -> dict:
    """Return the authoritative study-area configuration."""
    config = load_yaml("study_area.yaml")
    bbox = config["study_area"]["provisional_bbox_wgs84"]
    if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
        raise ValueError("study_area.provisional_bbox_wgs84 must be [west, south, east, north]")
    return config["study_area"]
