Shadow Ecology: confirmatory pre-analysis protocol

**Version:** 1.0  
**Date:** 2026-09-24  
**Focal area:** Lower Walker River–Walker Lake terminal-basin cluster, Nevada

## Purpose and primary hypothesis

This protocol fixes the project's confirmatory analysis before land-cover
modeling. Spatially structured land-cover-model residuals are treated as
diagnostic candidates, not direct evidence of shallow groundwater.

The primary hypothesis is supported only when residual clusters are spatially
non-random, recur across model architectures and residual metrics, exceed
spatial null expectations, and associate more strongly with independent
hydrogeologic indicators than with competing explanations or training-data
sparsity.

## Analysis domain and data governance

The study domain includes the lower Walker River from the Wabuska gage through
Weber Reservoir and the Walker River Paiute Reservation to Walker Lake, plus a
valley-floor analysis buffer sufficient to represent groundwater-discharge,
irrigated, playa/saline, shrubland, and upland settings.

Use public data by default. Keep restricted and public data in separate stores.
Do not infer, publish, or expose sensitive locations or non-public Tribal
environmental information without explicit authorization. Monitoring absence is
a data gap, not evidence of the absence of Tribal data or knowledge.

Primary interpretation excludes persistent cloud, cloud shadow, snow, and
quality-flagged imagery; open-water pixels; and sensitive or non-public sites.
Urban cores and active mines are excluded from primary interpretation unless
they are explicitly analyzed as a disturbance stratum. Irrigated land remains
in the domain as a prespecified managed-water confounder.

## Fixed land-cover classes

1. Riparian/phreatophytic vegetation
2. Wet meadow/emergent wetland
3. Irrigated agriculture
4. Shrubland
5. Herbaceous grassland/pasture
6. Barren, playa, saline, or sparsely vegetated surface
7. Woodland/pinyon-juniper
8. Developed, transportation, or disturbed land

Document source labels, class definitions, minimum mapping unit, and known
label limitations before sampling. Do not merge, split, or drop a confirmatory
class after examining residual results without a protocol amendment.

## Inputs and architecture separation

Both architectures use the same study extent, time period, source labels, and
outer spatial folds. Primary predictors are seasonal Sentinel-2 10 m composites
(spring, peak growing season, late season), bands/indices, Landsat temporal
summaries where quality permits, and terrain derivatives.

Do **not** use observed well depth-to-water, groundwater-model outputs,
monitoring density, or Tribal-program presence as primary classifier predictors.
Those variables are reserved for independent attribution.

Train two model families:

- A random forest using spectral, temporal, and terrain predictors.
- A CNN using image patches with comparable Sentinel-2 seasonal inputs.

Hyperparameter tuning occurs only within the outer-fold training areas.

## Spatial cross-validation

Use nested spatial block cross-validation.

- Create a fixed 5 km by 5 km grid over the domain.
- Assign blocks to five spatially balanced outer folds, preserving feasible
  representation of classes and hydrogeomorphic contexts.
- Apply a 1 km buffer between each outer test block and all training blocks.
- Exclude buffered pixels from training for that fold.
- Keep pixels, patches, polygon fragments, and contiguous source-label objects
  within a single outer fold.
- Reserve spatial training blocks for inner validation and tuning.

Report confirmatory performance and misclassification residuals only on outer
held-out predictions.

## Residual fields

Analyze these fields separately:

| Metric | Definition | Primary support |
|---|---|---|
| Misclassification | Predicted class differs from held-out reference label | Held-out labeled pixels |
| Entropy | Shannon entropy of the full predicted class-probability vector | All quality-screened prediction pixels; also summarize on held-out labels |
| Probability margin | Highest minus second-highest predicted probability; lower means more ambiguous | All quality-screened prediction pixels; also summarize on held-out labels |

Convert entropy and probability margin to fold-specific percentile ranks before
mosaicking. Analyze misclassification overall and by true reference class.

## Spatial structure and candidate clusters

Aggregate residual fields to 250 m reporting cells for primary analysis; repeat
at 100 m and 500 m for sensitivity. Use a fixed 1 km distance-band weights
matrix, global Moran's I, 999 spatially constrained permutations, and local
Moran's I/LISA. Control local tests with Benjamini–Hochberg FDR at q = 0.05.
Estimate empirical variograms to document correlation range and guide density
clustering.

A candidate cluster must:

- contain at least 20 contiguous 250 m cells (1.25 km²);
- fall in the high-residual tail: entropy at or above the 90th percentile,
  probability margin at or below the 10th percentile, or class-specific
  misclassification significantly above its matched baseline;
- be LISA-significant after FDR correction;
- persist at 100 m, 250 m, and 500 m; and
- remain detectable in an irrigation-excluded sensitivity run.

HDBSCAN/DBSCAN may help delineate boundaries but cannot alone establish a
cluster. Record parameters before driver attribution.

## Robust-cluster rule

Only clusters satisfying every item below are eligible for confirmatory driver
attribution:

1. Global Moran's I is significant for the residual field (permutation p < 0.05).
2. Local clustering is significant after FDR correction.
3. The cluster occurs in at least two of the three residual metrics.
4. The cluster occurs in both random forest and CNN results.
5. Cross-architecture overlap is Jaccard index >= 0.30 after 250 m rasterization.
6. It persists in at least four of five outer folds where coverage permits.
7. Cluster extent or intensity exceeds the 95th percentile under the applicable
   null model.
8. It is not eliminated after stratifying by training-label density.

## Null models

Use at least 999 realizations per primary comparison.

1. **Spatially constrained label permutation:** permute labels within matched
   broad landform, label-class, and spatial-block strata.
2. **Conditional spatial randomization:** randomize residual values while
   retaining their distribution and broad spatial autocorrelation.
3. **Matched-background null:** sample controls matched on landform, elevation,
   slope, climate zone, and dominant mapped land-cover class.
4. **Training-support null:** compare clusters with locations matched on label
   density, distance to labeled data, and class prevalence.

Report effect sizes and empirical confidence intervals, not just p-values.

## Competing explanations

Test each hydrologic interpretation against irrigation and managed conveyance;
saline/alkaline soils and playa margins; geology and basin-fill setting;
grazing, fire, roads, development, and other disturbance; terrain/compositing
artifacts; label sparsity/class imbalance/extrapolation; and meteorological or
phenological anomalies. A hydrologic interpretation is unsupported where a
competing explanation performs equally well or better.

## March 2027 go/no-go decision

Proceed to full attribution and hydrologic uncertainty propagation only when:

- at least one residual metric from each architecture has global Moran's I
  permutation p < 0.05;
- at least three clusters meet the robust-cluster rule;
- robust clusters exceed spatial-null expectations;
- at least one robust cluster has an independent hydrologic association that
  exceeds matched-background and training-support null expectations; and
- the result persists after excluding irrigated land, or irrigation is shown to
  be the dominant driver and reported as such.

Otherwise pivot to the negative-result pathway: characterize when residuals
reflect label support, class ambiguity, irrigation, or imagery/terrain artifacts
rather than diagnostic hydrologic signals.

## Amendments

After modeling begins, alter this protocol only with a dated amendment stating
what changed, why, whether results had been viewed, and which analyses remain
confirmatory versus exploratory. Exploratory work is welcome but cannot replace
the primary analysis defined here.
