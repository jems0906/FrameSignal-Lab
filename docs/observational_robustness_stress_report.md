# Observational Extension: Positivity and Model-Robustness Stress

This predeclared synthetic study varies measured-covariate overlap and nuisance-model specification independently. Hidden confounding is fixed at zero to isolate these mechanisms. Results are exploratory, not randomized ITT, and not approval for real-world decisions.

Study: `framesignal-observational-positivity-misspecification-v1`. Config SHA-256: `e43970a71de45826c56b4ca33318afa4c1ed76a8e1caf38562bfc40cb9f3ea63`. Seed: 66752021; N=2,000 per replicate; 300 independent replicates per cell; 8 cells.

The correct-both profile matches the fitted logistic propensity and linear outcome models. Propensity-only misspecification adds a centered quadratic affinity term to assignment while retaining a correct outcome regression. Outcome-only misspecification adds a centered, assignment-invariant quadratic affinity term to outcomes while retaining a correct propensity model. The both-misspecified profile includes both terms. Because each outcome nonlinearity is assignment-invariant, the known treatment effect stays fixed.

Each replicate's interval is a normal Wald interval using the empirical variance of its AIPW pseudo-outcome. Monte Carlo intervals use Bonferroni familywise control across the fixed eight cells: Student-t intervals for mean bias and exact Clopper-Pearson intervals for coverage proportions. These are not the earlier household-bootstrap intervals.

## Results

| Overlap | Nuisance model profile | Mean AIPW bias (familywise MC interval) | Bias RMSE | Wald coverage (familywise MC interval) | Overlap pass rate | Mean ESS control / treatment |
|---|---|---:|---:|---:|---:|---:|
| moderate | correct_both | -0.07 [-0.43, +0.29] pp | 2.26 pp | 95.3% [91.0, 98.0]% | 100.0% | 1111 / 780 |
| moderate | propensity_misspecified | +0.05 [-0.36, +0.46] pp | 2.58 pp | 95.3% [91.0, 98.0]% | 100.0% | 987 / 623 |
| moderate | outcome_misspecified | -0.03 [-0.39, +0.32] pp | 2.21 pp | 96.7% [92.7, 98.8]% | 100.0% | 1112 / 778 |
| moderate | both_misspecified | +0.20 [-0.18, +0.59] pp | 2.45 pp | 96.7% [92.7, 98.8]% | 100.0% | 987 / 624 |
| weak | correct_both | +0.08 [-0.41, +0.56] pp | 3.06 pp | 94.7% [90.1, 97.6]% | 84.7% | 748 / 425 |
| weak | propensity_misspecified | -0.02 [-0.65, +0.62] pp | 3.99 pp | 93.0% [88.0, 96.4]% | 0.0% | 567 / 258 |
| weak | outcome_misspecified | -0.26 [-0.73, +0.21] pp | 2.96 pp | 95.0% [90.5, 97.8]% | 79.7% | 746 / 424 |
| weak | both_misspecified | +0.61 [-0.01, +1.23] pp | 3.96 pp | 93.3% [88.4, 96.6]% | 0.0% | 573 / 249 |

## Interpretation

The factorial cells distinguish measured-overlap stress from nuisance-model misspecification under this specific generator. Double robustness is an asymptotic property under identification and regularity conditions, not a guarantee of finite-sample unbiasedness or nominal coverage. Poor overlap can destabilize estimation even when the nuisance models are correctly specified.

Monte Carlo intervals quantify simulation uncertainty within this design only. They do not establish external validity, real-world identification, or proxy approval. Hidden confounding is not studied here; see the separately predeclared observational confounding sensitivity reports.

Self-review only; no peer feedback is claimed.
