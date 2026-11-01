# Observational Extension: Sensitivity Demonstration

This is an opt-in synthetic observational extension. It is not randomized ITT, not the primary analysis, and not approval for real-world decisions.

Study: `framesignal-observational-sensitivity-v1`. Config SHA-256: `fdf6838436f71d3fce02758c009f888f19945d32753d659a1bcb42296e0f6476`. Seed: 7483829; N=2,000 per run; 200 complete-household bootstrap draws.

## Estimand and Assumptions

The simulated population average effect on fully observed days 29-56 return. Adjustment uses only measured affinity and log viewing opportunity. AIPW relies on consistency, no interference, positivity, no unmeasured confounding given these measured covariates, and correct specification of either the propensity or outcome model. The sensitivity generator deliberately violates conditional exchangeability as hidden loyalty strength increases. AIPW does not remove that bias by declaration.

Propensity overlap checks use the predeclared 0.05-0.95 range, common support, clipped-weight frequency, and per-arm effective sample size. Failed overlap is a diagnostic warning; it is not silently repaired or treated as evidence of identification.

## Results

| Scenario | Hidden confounding | True population effect | Naive difference (descriptive) | AIPW estimate | Household bootstrap 95% interval | Common-support fraction | Outside 0.05-0.95 | ESS control / treatment | Overlap check |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| helpful | 0.0 | +6.0 pp | +7.47 pp | +5.05 pp | [+0.66, +9.07] pp | 99.9% | 0.0% | 1053 / 825 | pass |
| helpful | 0.5 | +6.0 pp | +8.68 pp | +6.06 pp | [+1.90, +11.75] pp | 99.9% | 0.0% | 1082 / 831 | pass |
| helpful | 1.0 | +6.0 pp | +7.12 pp | +5.17 pp | [+0.24, +9.62] pp | 99.9% | 0.0% | 1099 / 828 | pass |
| unrelated | 0.0 | +0.0 pp | +1.38 pp | -0.74 pp | [-5.99, +4.44] pp | 99.8% | 0.0% | 1108 / 761 | pass |
| unrelated | 0.5 | +0.0 pp | +2.66 pp | +0.21 pp | [-4.20, +4.90] pp | 99.1% | 0.0% | 1111 / 788 | pass |
| unrelated | 1.0 | +0.0 pp | +3.27 pp | +2.27 pp | [-1.60, +6.46] pp | 99.7% | 0.0% | 1091 / 817 | pass |
| misleading | 0.0 | -6.0 pp | -2.93 pp | -5.68 pp | [-10.47, -1.16] pp | 99.2% | 0.0% | 1108 / 773 | pass |
| misleading | 0.5 | -6.0 pp | -2.42 pp | -5.46 pp | [-9.79, -1.61] pp | 99.7% | 0.0% | 1092 / 778 | pass |
| misleading | 1.0 | -6.0 pp | -3.02 pp | -4.34 pp | [-8.54, +0.12] pp | 99.9% | 0.0% | 1059 / 837 | pass |

## Interpretation

Compare the naive contrast and measured-covariate AIPW estimate with the known synthetic population effect as latent confounding varies. Results are specific to this constructed selection model. The bootstrap resamples complete households but does not account for all nuisance-model uncertainty or eliminate hidden-confounder bias.

No observational estimate supersedes the randomized ITT target. Do not use these results to attribute return to a title, claim artistic value, define Netflix retention, or approve any proxy. See the source JSON for propensity quantiles, propensity ranges by assignment arm, clipped fraction, ESS, assumptions, and limitations.

Self-review only; no peer feedback is claimed.
