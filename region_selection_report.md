# Shadow Ecology Region Selection Report (Draft)
**PI:** Lilly Jones, PhD · CIRES, CU Boulder
**Prepared:** Month 1, Week 4
**Status:** DRAFT: for internal review; final decision due Month 2, Week 1 (locked, no revisiting)

## Purpose
This report compares the three candidate study regions — Rio Grande Basin, Colorado Plateau, and Great Basin against the pre-defined selection criteria established in Month 1, Week 2. It is intended to provide the comparative evidence needed to lock the study region decision by end of Month 2.

## Selection Criteria (locked, Month 1 Week 2)
1. **Subsurface hydrology drives vegetation** vegetation patterns should be plausibly and mechanistically linked to depth-to-water / groundwater dynamics, not primarily to geology, soils, or irrigation.
2. **Heterogeneous monitoring density, including Tribal lands** the region should contain a genuine contrast between well-instrumented and sparsely monitored areas, with Tribal lands represented in the monitoring gaps of interest.
3. **Freely accessible imagery** full, reliable Sentinel-2 / Landsat coverage with manageable cloud cover and no access barriers.

## Comparative Scoring

| Criterion | Rio Grande Basin | Colorado Plateau | Great Basin |
|---|---|---|---|
| **(a) Hydrology/vegetation link** | Strong riparian galleries and irrigated ag tightly coupled to shallow groundwater/river stage | Moderate vegetation often responds more to bedrock/soil (sandstone, karst) than to depth-to-water; risk of confounding | **Strongest** phreatophyte vegetation is a textbook direct index of depth-to-water |
| **(b) Monitoring heterogeneity / Tribal lands** | Strong Pueblo Nations and Navajo Nation portions; sharp contrast between instrumented irrigation districts and sparsely monitored Tribal lands | Strong Navajo, Hopi, Ute Mountain Ute, Southern Ute lands; well-documented monitoring disparities | Good  Western Shoshone, Northern Paiute, Goshute lands; sparse monitoring outside a few basins |
| **(c) Imagery access** | Excellent full coverage, no notable cloud issues | Good — full coverage, but canyon/mesa terrain adds shadow/elevation correction complexity | Excellent full coverage, generally clear skies aid cloud-free composites |
| **Key risk** | Agricultural signal may confound the "natural" hydrology-vegetation relationship | Geologic/soil signal may be picked up by classifiers as hydrology signal, muddying residual interpretation | Lower vegetation class diversity may reduce textural signal available to CNN |

## Open Items Before Final Decision
- [ ] Confirm depth-to-water product coverage and resolution (Fan et al. 2013 / MODFLOW outputs) for each region availability could break a tie
- [ ] Confirm USGS groundwater well density by region (Week 3 inventory)
- [ ] Confirm monitoring network density memo findings (streamgages, NOAA stations, Tribal environmental monitoring programs)
- [ ] Confirm Sentinel-2 seasonal cloud-free composite availability by region (Week 2–3 imagery memo)

## Preliminary Recommendation
*Pending confirmation of the open items above.* Based on criteria (a) and (c) alone, **Great Basin** presents the cleanest hydrology-driven vegetation signal with minimal confounding. **Rio Grande Basin** offers a starker monitoring-density contrast and richer land cover class diversity, at the cost of agricultural confounding. **Colorado Plateau** is viable but carries the highest risk of conflating geologic and hydrologic drivers.

## Decision Rationale (to be completed Month 2, Week 5)
*[Fill in after Month 1 data inventories are complete: see Region Selection Decision deliverable, locked no later than Month 2 Week 1.]*

*This report feeds directly into the locked Region Selection Decision (Month 2, Week 5) per the Shadow Ecology pre-specification framework. Do not begin classifier training or image download until the region is locked.*
