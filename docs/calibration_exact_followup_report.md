# Exact Monte Carlo Calibration Follow-up

A separately predeclared fresh-seed check using exact binomial intervals for Monte Carlo coverage proportions. Prior plans and reports remain unchanged.

Study: `framesignal-return-coverage-exact-20261103-v1`. Config SHA-256: `eb0ac2d8e94c160640a3c9cad2cff86a6eac8d622b7ffb511d5639c4ae471209`. Fresh seed: 20261103.
N=2,000 households per repetition; 10,000 repetitions per effect; 50,000 repetitions total.

The target estimator remains the household difference in means with a Welch 95% interval. Only the uncertainty interval for the Monte Carlo proportion of target intervals covering truth changes: two-sided exact Clopper-Pearson intervals at 99% for each of five fixed effects. Exact binomial intervals are conservative, with marginal coverage at least nominal; Bonferroni's union bound gives a simultaneous familywise lower bound of 95% under independent repetitions.

This guarantee concerns uncertainty about the repeated-simulation coverage proportions only. It does **not** make the target Welch interval exact, guarantee its coverage under other DGPs, or validate a proxy.

## Results

| True effect pp | Target-interval coverage | Exact 99% Monte Carlo interval | Target interval rejection / power | Bias pp ± MC SE | Mean target interval width pp |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 94.84% | [94.24%, 95.39%] | 5.16% | +0.021 ± 0.022 | 8.76 pp |
| 2.0 | 94.89% | [94.30%, 95.44%] | 14.60% | -0.009 ± 0.022 | 8.75 pp |
| 4.0 | 94.98% | [94.39%, 95.53%] | 44.32% | +0.035 ± 0.022 | 8.73 pp |
| 6.0 | 94.72% | [94.12%, 95.28%] | 76.87% | -0.004 ± 0.022 | 8.70 pp |
| 10.0 | 95.46% | [94.90%, 95.98%] | 99.66% | -0.013 ± 0.022 | 8.63 pp |

## Interpretation

Status: **no_familywise_signal_detected**. Exact simultaneous intervals excluding nominal 95%: none.

No familywise signal detected; this is not proof of calibration.

Bonferroni familywise lower bound applies to the five Monte Carlo coverage proportions under independent repetitions; it does not make the target Welch intervals exact.

All results apply only to this synthetic DGP, fixed N, estimator, and effect grid. No general calibration or surrogate-validity claim follows. Self-review only; no independent peer feedback is claimed.
