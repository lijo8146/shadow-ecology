# AOI Decision Note — Lower Walker River–Walker Lake Terminal-Basin Cluster

**Status:** FROZEN — changes require a dated amendment in this file and in
`pre_analysis_protocol.md`.  
**Decision date:** 2026-10-01  
**Prepared by:** Shadow Ecology project team  
**Supersedes:** provisional bbox in `config/study_area.yaml` v1.0 (2026-09-24)

---

## 1. Geometry method

The computational AOI is derived from the USGS NHDPlus High Resolution (HR)
Watershed Boundary Dataset (WBD), HUC-8 unit **16050302**
(Walker Lake / Lower Walker River), intersected with the corridor defined by
the two authoritative study anchors (see §3). A 2 km valley-floor buffer is
applied to the river/lake edge of the WBD polygon to capture groundwater-
discharge, irrigated-field, playa/saline, and upland transitional contexts
required by `pre_analysis_protocol.md`. The buffer was selected to retain
the dominant landform-contrast settings while avoiding overlap with
hydrologically unrelated basins to the west (Smith Valley) and east.

Desktop derivation used the NHDPlus HR/WBD GPKG file at the HUC-4 level
(1605), dissolved to HUC-8 subbasin 16050302, then clipped to the anchor
latitude bounds (§3) and buffered in EPSG:32611 (UTM Zone 11N).

No field work, drone overflight, or Tribal data were used to define this
boundary. It is a desktop-analysis polygon, not a determination of
sovereignty, jurisdiction, or land ownership.

---

## 2. Source dataset and version

| Item | Value |
|---|---|
| Source | USGS NHDPlus HR / Watershed Boundary Dataset (WBD) |
| Product access | https://www.usgs.gov/national-hydrography/access-national-hydrography-products |
| HUC-8 subbasin | 16050302 — Walker Lake / Lower Walker River |
| NHDPlus HR version | To be recorded at download (enter version/publication date here) |
| WBD version | To be recorded at download |
| Extraction / download date | To be recorded at download |
| Processing CRS | EPSG:32611 (UTM Zone 11N) — all area and buffer calculations |
| Delivery CRS (stored file) | EPSG:4326 (WGS 84 geographic) for GeoJSON; EPSG:32611 for analysis rasters |
| Output file | `data/catalog/aoi_final.geojson` |
| Checksum (SHA-256) | To be recorded after file is written |

---

## 3. Study anchors retained

| Anchor | Name | Longitude (WGS 84) | Latitude (WGS 84) | Authority |
|---|---|---|---|---|
| Upstream | USGS 10301500 Walker River near Wabuska | −119.0988889 | 39.1524611 | USGS NWIS gage |
| Downstream | Walker Lake near Hawthorne (centroid) | −118.7720849 | 38.6765864 | `config/study_area.yaml` |

The frozen AOI polygon must contain both anchor points. If the WBD/NHDPlus
extraction does not encompass a point, expand the clip bounds to include it
and record the adjustment here.

---

## 4. Approximate area

| Quantity | Approximate value | Notes |
|---|---|---|
| Bounding box (WGS 84) | W −119.20, S 38.50, E −118.55, N 39.22 | From provisional config; refine after NHDPlus extraction |
| Expected polygon area | ~2 200–2 800 km² (valley-floor + 2 km buffer) | Refine to two significant figures after extraction |
| Dominant land covers (expected) | Riparian corridor, irrigated agriculture, shrubland, barren/playa, Walker Lake open water | Per NLCD 2021 preview |

Refine the area figure and update this table after writing `aoi_final.geojson`.

---

## 5. Buffer rationale

A 2 km lateral buffer beyond the NHDPlus HR channel/lake boundary was chosen
because:

- The `pre_analysis_protocol.md` requires representation of
  groundwater-discharge, irrigated, playa/saline, shrubland, and upland
  settings within the domain.
- Alluvial aquifer extents in the lower Walker system (USGS SIR 2009-5155)
  extend 1–3 km from the main channel in valley segments.
- A 2 km radius fits within the valley floor for most of the corridor without
  capturing unrelated mountain slopes.
- Sensitivity runs at 1 km and 3 km buffers will be evaluated before modeling.

---

## 6. CRS summary

| Use | CRS |
|---|---|
| Storage / exchange | EPSG:4326 (WGS 84) |
| All area, distance, and raster analyses | EPSG:32611 (UTM Zone 11N) |
| `config/study_area.yaml` `crs_analysis` field | EPSG:32611 (already set) |

---

## 7. Amendment log

| Date | Change | Made before or after viewing model results? |
|---|---|---|
| 2026-10-01 | Initial AOI decision note created; NHDPlus extraction and checksum pending download | Before any model training |
