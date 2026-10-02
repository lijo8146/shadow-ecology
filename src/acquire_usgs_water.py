"""
Week 3 — USGS/NGWMN well and water-level metadata acquisition
==============================================================
Queries the USGS Water Data for the Nation REST API for groundwater sites,
groundwater levels, streamflow sites, and water-quality sites within the
frozen AOI.  Optionally queries NGWMN as a supplement.

Outputs:
    data/raw/usgs_waterdata/gw_sites_aoi.csv
    data/raw/usgs_waterdata/gw_levels_aoi.csv
    data/raw/usgs_waterdata/streamflow_sites_aoi.csv
    data/raw/usgs_waterdata/wq_sites_aoi.csv
    data/catalog/manifest_usgs_waterdata.yaml (filled)

Usage:
    python src/acquire_usgs_water.py [--dry-run]

Governance:
    Raw data are P1 (public).  Before any map that identifies locations on or
    immediately adjacent to Tribal lands/waters is released externally, follow
    the P2 release workflow in governance_boundary_register.md.
    Public-inventory records describe USGS/public-agency data only; they do
    NOT represent Tribal monitoring capacity or local environmental knowledge.
"""
from __future__ import annotations

import argparse
import csv
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    aoi_bbox,
    load_or_init_manifest,
    record_processing_step,
    save_manifest,
    sha256,
)
from src.settings import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "usgs_waterdata"
NWIS_BASE = "https://waterservices.usgs.gov/nwis"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    return p


def _nwis_url(service: str, params: dict) -> str:
    return f"{NWIS_BASE}/{service}/?{urllib.parse.urlencode(params)}"


NWIS_RETRIES = 3
NWIS_RETRY_DELAY_S = 10


def _urlopen_with_retry(url: str, retries: int = NWIS_RETRIES,
                        delay: int = NWIS_RETRY_DELAY_S) -> "http.client.HTTPResponse":
    """Open *url*, retrying on 503 (service temporarily unavailable)."""
    import time
    import http.client
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return urllib.request.urlopen(url, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code != 503:
                raise
            last_exc = exc
            print(f"  NWIS returned HTTP 503 (attempt {attempt}/{retries}). "
                  f"Waiting {delay}s before retry…")
            time.sleep(delay)
    raise RuntimeError(
        f"NWIS returned HTTP 503 after {retries} attempts.\n"
        f"The USGS Water Data for the Nation service is temporarily unavailable.\n"
        f"Check https://waterservices.usgs.gov/ for status, then re-run.\n"
        f"URL: {url}"
    ) from last_exc


def fetch_nwis_sites(bbox: list[float], site_type: str, output_type: str = "rdb") -> tuple[str, str]:
    """Return (url, response_text) for a NWIS site query.

    NWIS enforces a bounding-box size limit for some site types (notably WQ).
    For those, fall back to a stateCd query scoped to Nevada (NV) instead of
    a bbox, then filter to the AOI bbox client-side.
    Retries automatically on HTTP 503 (service temporarily unavailable).
    """
    west, south, east, north = bbox

    # Try bbox first; fall back to stateCd=NV on HTTP 400 (bbox too large or
    # unsupported for this service type).
    params_bbox = {
        "bBox": f"{west},{south},{east},{north}",
        "siteType": site_type,
        "outputDataTypeCd": "all",
        "format": output_type,
    }
    url = _nwis_url("site", params_bbox)
    try:
        with _urlopen_with_retry(url) as resp:
            return url, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise
        # bbox rejected — fall back to stateCd with client-side AOI filter
        print(f"  bbox query returned HTTP 400 for siteType={site_type}; "
              f"falling back to stateCd=NV query.")

    params_state = {
        "stateCd": "NV",
        "siteType": site_type,
        "outputDataTypeCd": "all",
        "format": output_type,
    }
    url_state = _nwis_url("site", params_state)
    with _urlopen_with_retry(url_state) as resp:
        text = resp.read().decode("utf-8")

    # Filter rows to AOI bbox client-side
    filtered = _filter_rdb_to_bbox(text, west, south, east, north)
    return url_state + f" [filtered to bbox {west},{south},{east},{north}]", filtered


def _filter_rdb_to_bbox(rdb_text: str, west: float, south: float,
                         east: float, north: float) -> str:
    """Keep only RDB rows whose lat/lon fall inside the bbox."""
    lines = rdb_text.splitlines(keepends=True)
    header_lines = [l for l in lines if l.startswith("#")]
    data_lines   = [l for l in lines if not l.startswith("#")]
    if len(data_lines) < 2:
        return rdb_text

    col_line = data_lines[0]
    headers = col_line.rstrip("\n").split("\t")
    fmt_line = data_lines[1]   # format descriptor row — keep as-is

    try:
        lat_idx = headers.index("dec_lat_va")
        lon_idx = headers.index("dec_long_va")
    except ValueError:
        # Columns not present — return unchanged
        return rdb_text

    kept = []
    for line in data_lines[2:]:
        fields = line.rstrip("\n").split("\t")
        try:
            lat = float(fields[lat_idx])
            lon = float(fields[lon_idx])
        except (ValueError, IndexError):
            continue
        if south <= lat <= north and west <= lon <= east:
            kept.append(line)

    return "".join(header_lines) + col_line + fmt_line + "".join(kept)


def fetch_nwis_gw_levels(site_numbers: list[str]) -> tuple[str, str]:
    """Return (url, response_text) for NWIS groundwater-level records."""
    # Batch up to 100 sites per query
    batch = site_numbers[:100]
    params = {
        "sites": ",".join(batch),
        "format": "rdb",
    }
    url = _nwis_url("gwlevels", params)
    with urllib.request.urlopen(url) as resp:
        return url, resp.read().decode("utf-8")


def rdb_to_rows(rdb_text: str) -> list[dict]:
    """Parse USGS RDB (tab-separated with comment/type header) into dicts."""
    lines = [l for l in rdb_text.splitlines() if not l.startswith("#")]
    if len(lines) < 2:
        return []
    headers = lines[0].split("\t")
    # Line 1 is the format descriptor row (5s, 15s, etc.) — skip it
    data_lines = lines[2:]
    rows = []
    for line in data_lines:
        if line.strip():
            fields = line.split("\t")
            rows.append(dict(zip(headers, fields)))
    return rows


def write_csv(rows: list[dict], out_path: Path) -> None:
    if not rows:
        out_path.write_text("# No records returned\n", encoding="utf-8")
        return
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = build_parser().parse_args()
    dry_run: bool = args.dry_run

    bbox = aoi_bbox()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_or_init_manifest("usgs_waterdata")
    manifest["query_date"] = datetime.utcnow().strftime("%Y-%m-%d")
    manifest["query_aoi_bbox_wgs84"] = bbox

    service_results: dict[str, dict] = {}

    for site_type, service_key, filename in [
        ("GW", "groundwater_sites", "gw_sites_aoi.csv"),
        ("ST", "streamflow_sites", "streamflow_sites_aoi.csv"),
        ("WQ", "water_quality_sites", "wq_sites_aoi.csv"),
    ]:
        out_path = OUTPUT_DIR / filename
        if dry_run:
            params = {
                "bBox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "siteType": site_type,
                "outputDataTypeCd": "all",
                "format": "rdb",
            }
            url = _nwis_url("site", params)
            print(f"[dry-run] {service_key}: {url}")
            service_results[service_key] = {"url": url, "site_count": None, "output_file": str(out_path)}
            continue

        print(f"Querying NWIS {service_key} …")
        url, text = fetch_nwis_sites(bbox, site_type)
        rows = rdb_to_rows(text)
        write_csv(rows, out_path)
        cksum = sha256(out_path)
        print(f"  {len(rows)} sites → {out_path.name}  SHA-256: {cksum[:12]}…")
        service_results[service_key] = {
            "url": url,
            "site_count": len(rows),
            "output_file": str(out_path.relative_to(PROJECT_ROOT)),
            "checksum_sha256": cksum,
        }

    # Groundwater levels (requires site list from gw_sites query)
    gw_levels_out = OUTPUT_DIR / "gw_levels_aoi.csv"
    if not dry_run and service_results.get("groundwater_sites", {}).get("site_count", 0):
        gw_sites_path = OUTPUT_DIR / "gw_sites_aoi.csv"
        with gw_sites_path.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            site_nos = [row["site_no"] for row in reader if row.get("site_no")]

        if site_nos:
            print(f"Querying groundwater levels for {len(site_nos)} sites …")
            url, text = fetch_nwis_gw_levels(site_nos)
            rows = rdb_to_rows(text)
            write_csv(rows, gw_levels_out)
            cksum = sha256(gw_levels_out)
            print(f"  {len(rows)} level records → {gw_levels_out.name}")
            service_results["groundwater_levels"] = {
                "url": url,
                "record_count": len(rows),
                "output_file": str(gw_levels_out.relative_to(PROJECT_ROOT)),
                "checksum_sha256": cksum,
            }
    elif dry_run:
        print(f"[dry-run] groundwater_levels: would query after site list is available")

    # Update manifest services
    for svc in manifest.get("services", []):
        key = svc.get("service")
        if key in service_results:
            r = service_results[key]
            svc["site_count"] = r.get("site_count")
            svc["output_file"] = r.get("output_file")
            svc.setdefault("query_url", r.get("url"))
            if "checksum_sha256" in r:
                svc["checksum_sha256"] = r["checksum_sha256"]

    record_processing_step(manifest, {
        "step": "nwis_site_and_level_query",
        "script": "src/acquire_usgs_water.py",
        "conda_env": "shadow-ecology",
        "parameters": {
            "nwis_base": NWIS_BASE,
            "site_types": ["GW", "ST", "WQ"],
            "bbox": bbox,
            "dry_run": dry_run,
        },
    })

    if not dry_run:
        save_manifest("usgs_waterdata", manifest)
        print("\nManifest written to data/catalog/manifest_usgs_waterdata.yaml")
        print("\nGOVERNANCE REMINDER: before publishing any map that identifies")
        print("locations on or immediately adjacent to Tribal lands/waters,")
        print("follow the P2 release workflow in governance_boundary_register.md.")
    else:
        print("\n[dry-run] Manifest NOT written.")


if __name__ == "__main__":
    main()
