# Contributing to Shadow Ecology

This is a research repository (Shadow Ecology, IRP pilot study, CIRES/CU Boulder). This guide exists primarily to support the Month 6 reproducibility check can someone new run the pipeline from scratch? and to document conventions for future collaborators or Tribal partner review.

## Setup

```bash
git clone <repo-url>
cd shadow-ecology
conda env create -f environment.yml
conda activate shadow-ecology
```

CyVerse Data Store access and an allocation are required to pull raw imagery and run GPU-based CNN training: see `docs/data_management_plan.md` for access details.

## Running the Pipeline

1. **Region and pre-specification lock**: do not proceed past this step until `docs/region_selection_criteria.md` and `docs/pre_specification.md` are both signed off.
2. **Data assembly** notebooks in `notebooks/01_data_assembly/` download and preprocess Sentinel-2, Landsat, NLCD, and ancillary layers.
3. **Classifier training** `notebooks/02_rf_classifier/` and `notebooks/03_cnn_classifier/`, using identical spatial cross-validation splits (do not resample or re-stratify between the two).
4. **Residual generation** `notebooks/04_residuals/` produces the six residual fields (3 metrics × 2 architectures).
5. **Spatial analysis** `notebooks/05_spatial_autocorrelation/` computes Moran's I, LISA, DBSCAN clusters, and null model comparisons.

## Conventions

- All raster outputs are GeoTIFF, CRS and geotransform matched to the Sentinel-2 stack.
- Document any new feature, class, or parameter choice in `docs/data_dictionary.md` at the time you introduce it not retroactively.
- Locked documents (`pre_specification.md`, `region_selection_criteria.md`) may only be changed via a dated amendment, not silent edits.
- Large data files are never committed see `.gitignore`. Use CyVerse Data Store for raw/processed data.

## Working with Tribal-Sourced Data

Any data or context obtained through Tribal environmental agency relationships follows the terms in `docs/data_use_statement.md`. Do not commit, redistribute, or publish such data or derived products without confirming those terms first.
