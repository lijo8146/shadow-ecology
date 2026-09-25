# Shadow Ecology Region Selection Report
**PI:** Lilly Jones, PhD · CIRES, CU Boulder
**Decision recorded:** 2026-09-24
**Status:** DECISION LOCKED: changes require a dated amendment

## Purpose
This report compares the three candidate study regions; the Rio Grande Basin,
Colorado Plateau, and Great Basin against the pre-defined selection criteria.
It records the final selection of a bounded Great Basin study area.

## Selection Criteria (locked, Month 1 Week 2)
1. **Subsurface hydrology drives vegetation** vegetation patterns should be plausibly and mechanistically linked to depth-to-water/groundwater dynamics.
2. **Heterogeneous monitoring density** the region should contain a genuine contrast between well-instrumented and sparsely monitored areas, with Tribal lands represented in the monitoring gaps of interest.
3. **Freely accessible imagery** full, reliable Sentinel-2/Landsat coverage with manageable cloud cover and no access barriers.

## Comparative Scoring

| Criterion | Rio Grande Basin | Colorado Plateau | Great Basin |
|---|---|---|---|
| **(a) Hydrology/vegetation link** | Strong riparian galleries and irrigated ag tightly coupled to shallow groundwater/river stage | Moderate vegetation often responds more to bedrock/soil (sandstone, karst) than to depth-to-water; risk of confounding | **Strongest** phreatophyte vegetation is a textbook direct index of depth-to-water |
| **(b) Monitoring heterogeneity** | Strong Pueblo Nations and Navajo Nation portions; sharp contrast between instrumented irrigation districts and sparsely monitored Tribal lands | Strong Navajo, Hopi, Ute Mountain Ute, Southern Ute lands; well-documented monitoring disparities | Good  Western Shoshone, Northern Paiute, Goshute lands; sparse monitoring outside a few basins |
| **(c) Imagery access** | Excellent full coverage, no notable cloud issues | Good full coverage, but canyon/mesa terrain adds shadow/elevation correction complexity | Excellent full coverage, generally clear skies aid cloud-free composites |
| **Risks** | Agricultural signal may confound the "natural" hydrology-vegetation relationship | Geologic/soil signal may be picked up by classifiers as hydrology signal, muddying residual interpretation | Lower vegetation class diversity may reduce textural signal available to CNN |

## Final Decision

**Selected focal area: Lower Walker River–Walker Lake terminal-basin cluster,
Nevada.**

The analysis domain is the lower Walker River from the USGS Wabuska gage,
through Weber Reservoir and the Walker River Paiute Reservation, to Walker Lake,
plus the valley-floor and adjacent-landform contexts needed for comparison. The
authoritative provisional desktop-analysis envelope is maintained in
`config/study_area.yaml`; it is not a Tribal-jurisdiction boundary or fieldwork
authorization.

The Wabuska gage demarcates the upper and lower Walker River basins, and USGS
describes the lower system as a connected surface-water/groundwater system of
losing and gaining reaches from Wabuska to Walker Lake. This creates a strong,
mechanistic setting for testing whether residual patterns persist after known
hydrologic and managed-water explanations are considered. [USGS conceptual
model](https://pubs.usgs.gov/publication/sir20095155)

### Decision rationale

1. **Hydro-vegetation mechanism:** Lower Walker vegetation includes riparian
   and groundwater-discharge settings, while the terminal lake, alluvial aquifer,
   playa/saline surfaces, and river–aquifer exchange offer independent and
   competing hydrologic contexts.
2. **Monitoring and governance relevance:** The selected system includes the
   Walker River Paiute Reservation and established environmental/water programs.
   Public station coverage can be measured, but public-record sparsity will not
   be represented as an absence of Tribal monitoring, data, or knowledge. The
   operating boundaries are in `governance_boundary_register.md`.
3. **Feasible scale:** The bounded Wabuska-to-Walker-Lake system retains
   hydrologic and land-cover contrasts while remaining tractable for 10 m
   seasonal composites, buffered spatial cross-validation, and repeated null
   models.
4. **Falsifiability:** Irrigation, managed conveyance/recharge, salinity/playa
   conditions, geology, disturbance, and sparse training support are explicit
   competing explanations. The project does not assume that vegetation or a
   residual cluster is groundwater-driven.

## Follow-up work

- Validate public-data coverage and licensing in `data_inventory.md`.
- Freeze the precise AOI geometry before downloading data, using the workflow in
  `config/study_area.yaml`.
- Apply `pre_analysis_protocol.md` before any classifier training.
- Treat Snake–Spring Valleys as a future transferability/replication candidate.

Any change to this selection or scope requires a dated amendment documenting
the rationale and whether modeling or residual inspection has already begun.
