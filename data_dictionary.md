# Shadow Ecology — Data Dictionary

**Status:** Living document updated through Month 6 mid-project documentation sprint

## Imagery Inputs

| Field | Description |
|---|---|
| `sentinel2_composite` | Cloud-free seasonal composite, Sen2Cor atmospheric correction, 10 m, bands stacked and clipped to study region |
| `landsat_stack` | Contemporaneous scenes, atmospheric-corrected, reprojected to match Sentinel-2 grid, 30 m |
| `planetscope_composite` | 3.7 m, opportunistic (CSDA availability dependent) |

## Derived Spectral / Topographic Features

| Field | Formula / Source | Notes |
|---|---|---|
| `NDVI` | (NIR − Red) / (NIR + Red) | Vegetation index |
| `NDWI` | (Green − NIR) / (Green + NIR) | Water index |
| `EVI` | Standard 3-band formula | Enhanced vegetation index |
| `BSI` | Standard formula | Bare soil index |
| `SAVI` | Standard formula, soil-adjustment factor documented at computation | Soil-adjusted vegetation index |
| `slope`, `TWI` | Derived from DEM | Topographic wetness index and slope |
| texture features | [method to be documented at computation, e.g. GLCM] | |

## Land Cover Classes (NLCD-derived training labels)

| Class code | Class name | Aggregation notes |
|---|---|---|
| [to be filled in during Wk 6–7 NLCD reclassification] | | Document any merged/split classes and rationale here |

## Residual Metrics

| Field | Definition | Range |
|---|---|---|
| `misclassification` | Binary: predicted ≠ reference label | {0, 1} |
| `entropy` | Shannon entropy of predicted class-probability distribution | ≥ 0 |
| `probability_margin` | Top-1 probability − top-2 probability | [0, 1] |

## Ancillary / Driver Datasets

| Field | Source | Notes |
|---|---|---|
| `well_density` | USGS groundwater well records | Density surface, spatially joined to study grid |
| `depth_to_water` | Fan et al. 2013 / MODFLOW-derived product | Modeled raster |
| `building_density` | Microsoft/Google building footprints | Computed at 500 m / 1 km / 2 km scales |
| `land_use_change` | Landsat time series change detection | Flags recently converted land |
| `streamgage_density`, `weather_station_density` | USGS, NOAA | Point density surfaces |
| `tribal_monitoring_presence` | Tribal environmental agency records | Documented per data use agreement; not all sources are publicly redistributable |
| `tribal_land_boundary` | [source TBD] | Spatial covariate, flagged not as a "class" but as a monitoring-context indicator |

## Known Limitations / Data Gaps

- NLCD label quality in Tribal and rural areas is expected to be lower. This is treated as a feature of the analysis (part of what the project aims to reveal), not purely a data quality problem to correct away.
- [Additional limitations to be logged here as identified during Month 1–6 QC.]
