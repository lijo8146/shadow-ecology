# Shadow Ecology data inventory and coverage register

**Version:** 1.0  
**Date:** 2026-09-24  
**Study area:** Lower Walker River-Walker Lake terminal-basin cluster, Nevada

This is an acquisition and quality-control register. 

## Status labels                    

- **Core/acquire:** required for the confirmatory workflow.
- **Candidate/validate:** assess coverage, attributes, and terms before use.
- **Context only:** interpretation/control layer, not a classifier input.
- **Restricted by agreement:** do not acquire or use without written terms.

## Source and coverage table

| Theme | Preferred source | Coverage and target dates | Resolution / cadence | Access and license posture | Known gaps and required QC | Governance class | Status |
|---|---|---|---|---|---|---|---|
| Primary imagery | [Copernicus Sentinel-2 L2A](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2) | Whole AOI; seasonal composites for 2022–2026; freeze final target year before sampling | 10 m visible/NIR; 20 m red-edge/SWIR; nominal ~5-day revisit | Free Copernicus access; retain product IDs, processing baseline, and applicable terms | Cloud/shadow/snow, variable dates, terrain shadow, 20-to-10 m resampling; calculate valid-observation count by season/cell | P1 | Core/acquire |
| Long optical and thermal record | [USGS Landsat Collection 2 Level-2](https://www.usgs.gov/landsat-missions/landsat-collection-2) | Whole AOI; archive 1982–present; initial summaries 2000–2026 | 30 m; 16-day per mission | USGS public domain/no-cost policy | Landsat 7 SLC-off, cloud/snow, cross-sensor harmonization, thermal quality, coarser grid | P1 | Core / acquire |
| Reference labels | [NLCD 2021 Products v2.0](https://www.usgs.gov/data/national-land-cover-database-nlcd-2021-products-ver-20-june-2026), with annual products where needed | CONUS; match label year to or before imagery | 30 m; current annual series 1985–2023 | NLCD 2021 release is CC0 1.0; cite USGS/MRLC | Not field truth; likely confusion at riparian, wet meadow, pasture, saline/playa, and irrigation edges | P1 | Core/acquire |
| Wells and water levels | [USGS Water Data for the Nation](https://waterdata.usgs.gov/) and [NGWMN](https://www.usgs.gov/apps/ngwmn/) | Query final AOI; retain all history, then evaluate shared period aligned with imagery | Points; irregular manual/continuous time series; datum varies | USGS public data; preserve final/provisional status | Uneven sites, intermittent records, datum differences, missing depth-to-water, non-USGS providers incompletely represented | P1; P2 for place-specific release | Core/acquire |
| State monitoring | [Nevada DWR Enhanced Hydrologic Monitoring](https://water.nv.gov/programs/nevada-water-initiative/enhanced-hydrologic-monitoring) | Candidate; verify Lower Walker stations, variables, formats, and date span | Point/network-specific, mixed cadence | Public-facing; verify download/API terms and steward metadata | Partial/project-specific coverage; reconcile duplicates, QA, and datums with USGS data | P1 unless source says otherwise | Candidate/validate |
| Springs, streams, canals, waterbodies, basin geometry | [USGS NHDPlus HR / 3D Hydrography](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) and WBD | Whole AOI after boundary freeze | NHDPlus HR built from 1:24,000-scale or more detailed hydrography; vector | Public-domain USGS data | Map absence is not physical absence; inspect intermittent, ditch, spring, and point-feature attribution; legacy NHD is no longer maintained | P1 | Core/acquire |
| Hydrogeologic conceptual context | [USGS Lower Walker conceptual model](https://pubs.usgs.gov/sir/2009/5155/) and [PRMS/MODFLOW study](https://pubs.usgs.gov/publication/sir20145190) | Lower Walker; historical report/model periods | Reports, maps, models where distributed | USGS public-domain publications/data; verify model-file terms | May not represent current conditions; preserve calibration period and assumptions; model output is not observed depth-to-water | P1 | Context only |
| Geology and surficial geology | [NBMG maps and open data](https://nbmg.unr.edu/Maps%26Data/), including [2026 Walker Lake surficial map](https://pubs.nbmg.unr.edu/Surficial_geologic_map_of_the_Walker_Lake_Area_Mi_p/of2026-02.htm) | Candidate coverage over final AOI; terminal-lake map focuses on Walker Lake | Product-specific; Walker Lake map 1:48,000 | Some NBMG open layers are no-cost; product/GIS terms vary and must be verified | Coverage/scale vary; geology may proxy salinity or hydrology—test as a competing explanation | P1, subject to product terms | Candidate/validate |
| Soils, salinity, soil properties | [NRCS SSURGO](https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo) / [gSSURGO](https://www.nrcs.usda.gov/resources/data-and-reports/gridded-soil-survey-geographic-gssurgo-database) | Whole AOI subject to survey coverage; acquire a current, frozen release | SSURGO map scale ~1:12,000–1:63,360; gSSURGO 10 m statewide or 30 m CONUS | Publicly available; cite release/access date and metadata | Remote western survey gaps; map-unit attributes are not point observations; test EC/salinity-attribute completeness | P1 | Core/acquire |
| Salinity/playa proxy | Sentinel-2/Landsat bare-soil, salinity-index, and seasonal-persistence features, corroborated with SSURGO | Whole quality-screened AOI and imagery period | Derived at 10 m/30 m | Derived P1 data; maintain lineage | Not direct salinity measurement; confounded by brightness, moisture, crust, vegetation, and atmosphere | P1 derived; P2 release | Core/derive |
| Evapotranspiration | [OpenET API](https://openet.gitbook.io/docs) ensemble and model-specific products | Whole AOI; monthly 2000–present, daily 2016–present as needed | Landsat-scale products; monthly/daily endpoint dependent | Document model/version, endpoint, query date, and current terms | Modeled ET, not direct measurement; latency/gaps vary; irrigation and open water confound interpretation | P1 public-access; terms verified at acquisition | Candidate/validate |
| Climate | [Daymet V4 R1](https://daymet.ornl.gov/) primary; [gridMET](https://climatetoolbox.org/data/past-weather-data) sensitivity product | Daymet 1980–latest complete year; gridMET 1979–present | Daily 1 km/daily 4 km | Public research products; cite version/access date | Interpolation smooths valley/mountain gradients and station scarcity; retain native scale before aggregation | P1 | Core/acquire |
| Irrigated land | [LANID-US](https://zenodo.org/records/5548555), supplemented by current imagery/change detection and public canal features | LANID annual 1997–2017; validate an update for 2018–2026 | 30 m annual | Cite selected release; verify its terms before redistribution | Ends in 2017; may omit small/intermittent/pasture irrigation; canals and recharge can affect vegetation beyond fields | P1, subject to source terms | Core/acquire/update |
| Monitoring-network density | USGS WDFN, NGWMN, state inventory, and public streamflow/weather/water-quality station metadata | Whole AOI; use period of record and variable availability | Points; mixed periods/cadence | Public data subject to source terms | Presence is not usable record length or variable coverage; public inventories can omit Tribal, local, private, or restricted networks | P1 raw; P2 release | Core/derive |
| Tribal program context/partner data | Only through relevant Tribal government or designated program; see `governance_boundary_register.md` | Defined only by agreement | Varies | Terms determined by partner | Public descriptions do not establish current priorities, design, or data availability | R1/R2 | Do not acquire without agreement |

## Acquisition and acceptance checks

1. Freeze the precise AOI and imagery target years in `pre_analysis_protocol.md`.
2. First acquire Sentinel-2, Landsat, NLCD, NHDPlus HR/WBD, and public
   well/station metadata. For every download, create a manifest with source
   URL/API request, version, product ID, access date, checksum where available,
   CRS, license statement, and processing step.
3. Before modeling, produce AOI coverage reports for valid seasonal imagery,
   label count/area by class, well record length/datum, hydrography completeness,
   soil-attribute completeness, and station years/variables.
4. Acquire each candidate layer only after its coverage report supports the
   planned analysis without undocumented gap filling.
5. Log exclusions, resampling, imputation, datum conversions, and QA flags in
   a dataset-specific processing README.

## Non-negotiable rules

- Public monitoring coverage is a property of the chosen public inventory.
- Wells, modeled depth-to-water, ET, monitoring density, and Tribal-program
  context are independent attribution variables.
- Derived products retain source versions and full processing lineage.
- Recheck availability and licensing before download and release; this register
  is a plan.

## Revision log

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-24 | Initial source, coverage, licensing, gap, and governance register |
