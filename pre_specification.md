# Shadow Ecology Pre-Specification Document

**Status:** DRAFT must be reviewed and signed off by PI before any classifier training begins
**Locked:** [date to be filled in at sign-off, Month 2 Week 5–6]

> This document exists to prevent post-hoc adjustment of the analysis plan. If methodological decisions are made after seeing residual patterns, the core claim that residual structure reveals real processes — is compromised. Nothing below may be changed after lock without a documented, dated amendment.

## 1. Residual Metrics (exact definitions)

All three metrics are computed identically for both the RF and CNN classifiers, using each model's predicted class-probability distribution per pixel.

1. **Misclassification map** binary indicator per pixel: `1` if predicted class ≠ reference/held-out label, `0` otherwise. Aggregated to spatial units for visualization.
2. **Entropy surface** Shannon entropy of the predicted class-probability distribution at each pixel: `H = -Σ p_i * log(p_i)` over all classes `i`. Higher entropy = more uncertain prediction.
3. **Probability margin map** difference between the top-1 and top-2 predicted class probabilities at each pixel: `margin = p_(1) - p_(2)`. Lower margin = more uncertain prediction.

Each metric is analyzed **separately**, not combined into a composite index, per architecture, yielding 6 residual fields total (3 metrics × 2 architectures).

## 2. Spatial Autocorrelation Statistics

- **Global Moran's I** computed per residual field, with permutation-based significance (999 permutations), reporting statistic, p-value, and z-score.
- **Local Indicators of Spatial Association (LISA)** HH/HL/LH/LL cluster classification and outliers per residual field, with Benjamini-Hochberg FDR correction applied to control for multiple testing across spatial units. Uncorrected LISA maps will not be used for cluster claims.
- **Spatial weights matrix** queen contiguity or distance-band threshold, selected based on variogram range; choice and sensitivity to alternatives documented in `docs/spatial_weights_decision.md`.

## 3. Clustering (DBSCAN)

- Run on residual field values aggregated to a coarser grid (500 m or 1 km), not pixel-level.
- Epsilon and `min_samples` tuned via k-distance plot and variogram analysis; final parameter choices documented before use, not adjusted post-hoc based on cluster appearance.

## 4. Null Model Procedures

1. **Spatial randomization** residual field values randomly permuted across spatial units (999 iterations); observed Moran's I must exceed the 95th percentile of the null distribution.
2. **Label permutation** training labels randomly permuted before classification (999 iterations); residuals and Moran's I recomputed for each permuted run, confirming observed structure exceeds what arbitrary label assignment produces.

## 5. Cross-Metric / Cross-Architecture Robustness Rule

A cluster is considered **robust** and advances to Phase 3 driver attribution, only if it is present across:
- at least 2 of the 3 residual metrics, **and**
- both model architectures (RF and CNN)

## 6. Go/No-Go Criteria (End of Month 9)

All of the following must hold:
- Statistically significant spatial structure: Moran's I p < 0.05
- Consistency across at least 2 of 3 residual metrics
- Robustness confirmed against both null model types

**If not met:** Phase 3 is abbreviated. The project pivots to characterizing when/why residuals are not informative, and that finding is prepared for publication rather than treated as project failure.

## 7. Sign-Off

| Role | Name | Date | Signature |
|---|---|---|---|
| PI | Lilly Jones, PhD | | |

*No classifier training may begin until this section is completed.*
