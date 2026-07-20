# Shadow Ecology

**Mining Land Cover Model Residuals to Reveal Unmapped Hydrologic Drivers and Data Gaps in Sensor-Poor Landscapes**

PI: Lilly Jones, PhD · CIRES, CU Boulder
IRP Pilot Study

## Overview

Machine learning models in Earth observation routinely produce spatially structured residuals, systematic mismatches between predictions and observed ecosystem states, that are typically treated as error to be minimized. This project tests whether such residuals can instead serve as **diagnostic indicators of unmodeled environmental processes or data limitations**, particularly in sensor-poor regions.

We target landscapes where monitoring infrastructure is chronically sparse, including Tribal lands in the western U.S., where model residuals may be the only available signal of real ecosystem processes. This project is explicitly framed as a feasibility test: a positive result demonstrates that residual patterns can help prioritize locations for additional data collection or model refinement; a negative result provides equally valuable guidance by discouraging over-interpretation of model error.

## Research Questions

- **RQ1:** Are residuals spatially structured, and does that structure persist across model architectures, residual metrics, and null comparisons?
- **RQ2:** Are residual patterns more strongly associated than expected under null models with independent indicators of subsurface hydrologic conditions, informal land use, and monitoring network density?
- **RQ3:** Do residual-informed perturbations produce meaningful differences in downstream hydrologic model outputs, and are effects concentrated in data-sparse landscape contexts?

## Approach

1. Train land cover classifiers (Random Forest and CNN) on Sentinel-2 imagery and generate spatially explicit residual fields using three metrics: misclassification, entropy, and probability margin.
2. Quantify spatial structure in residuals using Moran's I and LISA statistics; identify robust clusters using density-based methods (DBSCAN) validated against spatial null models.
3. Evaluate whether residual clusters are more strongly associated than expected under null models with independent indicators of subsurface hydrology, informal land use, and monitoring network sparsity.
4. Assess whether residual-informed perturbations produce meaningful differences in downstream hydrologic estimates, focusing on data-sparse regions.

## Study Region

A single semi-arid western U.S. landscape, selected to satisfy:

- **(a)** Subsurface hydrology exerts strong control on vegetation patterns
- **(b)** Monitoring network density is heterogeneous, including areas of chronic data sparsity such as Tribal lands
- **(c)** Multi-resolution satellite imagery is freely accessible

Primary candidate: **Rio Grande Basin**, with **Colorado Plateau** and **Great Basin** as pre-validated alternatives. Final selection locked at end of Month 2 (see `docs/region_selection_report.md`).

## Data Sources

| Dataset | Source | Resolution | Use |
|---|---|---|---|
| Sentinel-2 | ESA Copernicus | 10 m | Primary classifier input |
| Landsat | NASA Earthdata | 30 m | Temporal depth, cross-sensor validation |
| PlanetScope | NASA CSDA Program | 3.7 m | Resolution sensitivity (where available) |
| NLCD | USGS | 30 m | Land cover training labels |
| Groundwater well records | USGS | - | Depth-to-water / subsurface hydrology driver |
| Building footprints | Microsoft/Google | - | Informal land use indicator |
| Monitoring network records | USGS, NOAA, Tribal environmental agencies | - | Monitoring density covariate |

## Project Phases

| Phase | Months | Focus |
|---|---|---|
| **1 Data Assembly and Land Cover Modeling** | 1–6 | Region selection, RF/CNN training, residual field generation |
| **2 Residual Structure and Clustering** | 5–9 | Moran's I, LISA, DBSCAN, null-model validation |
| **Go/No-Go Decision** | End of Month 9 | Requires significant spatial structure (Moran's I p < 0.05), consistency across ≥2 metrics, robustness against null models |
| **3 Driver Attribution & Monitoring Gap Analysis** | 8–14 | Spatial regression against groundwater, land use, and monitoring density covariates; results shared with Tribal environmental programs |
| **4 Targeted Uncertainty Propagation** | 12–16 | Water balance / Sobol sensitivity analysis; manuscript and toolkit development |

## Repository Structure

```
data/        raw and processed input datasets
notebooks/   analysis and modeling notebooks
results/     residual fields, statistical outputs, figures
docs/        pre-specification, region selection, and review documents
```

## Status

Active Phase 1, Month 1 (project setup and region scoping).

## References

Anselin, L. (1995). Local Indicators of Spatial Association—LISA. *Geographical Analysis*.  
Beven, K., & Binley, A. (1992). The future of distributed models. *Hydrological Processes*.  
Eamus, D. et al. (2015). Groundwater-dependent ecosystems: recent insights. *Hydrogeology Journal*.  
Fan, Y. et al. (2013). Global patterns of groundwater table depth. *Science*.  
Meyer, H., & Pebesma, E. (2021). Predicting into unknown space? *Methods in Ecology and Evolution*.  
Saltelli, A. et al. (2010). Variance based sensitivity analysis of model output. *Computer Physics Communications*.  
Schubert, E. et al. (2017). DBSCAN revisited. *ACM Transactions on Database Systems*.  
Wadoux, A. et al. (2021). Spatial cross-validation is not the right way to evaluate map accuracy. *Ecological Modelling*.  