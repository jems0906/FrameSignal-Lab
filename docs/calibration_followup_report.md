# Calibration Follow-up Report

A separate, prospectively specified Monte Carlo follow-up to the frozen v1.0 report. The baseline report and analysis plan were not modified.

Study: `framesignal-return-coverage-followup-20261101-v1`. Config SHA-256: `265940393045c7083d764ce22d0339344866f5cc76e51a6ed173462cadcef81f`. Baseline report SHA-256: `a9780837d836eb6f299b8a480fae1e575a4b5ce1707bc438321b2fcb705f8e3b`.

Fresh seed: 20261101; N=2,000 balanced household assignments per repetition; 10,000 repetitions per effect; total 50,000 repetitions.

## Frozen Follow-up Method

Unchanged household Bernoulli return DGP and two-sided Welch household difference-in-means 95% interval. Coverage rates use 95% Wilson Monte Carlo intervals. +4 pp is the predeclared primary calibration point because the earlier independent baseline flag occurred there; other effects are descriptive. No seed, estimator, DGP, sample size, grid, or interval was tuned after seeing these follow-up results.

## Results

| True effect pp | Coverage | 95% Wilson Monte Carlo interval | Null rejection / power | Bias pp ± MC SE | Mean interval width pp |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 94.53% | [94.07%, 94.96%] | 5.47% | -0.025 ± 0.023 | 8.76 pp |
| 2.0 | 95.03% | [94.59%, 95.44%] | 14.33% | -0.008 ± 0.022 | 8.75 pp |
| 4.0 | 94.76% | [94.31%, 95.18%] | 44.52% | +0.010 ± 0.022 | 8.73 pp |
| 6.0 | 94.87% | [94.42%, 95.29%] | 77.26% | +0.021 ± 0.022 | 8.70 pp |
| 10.0 | 95.46% | [95.03%, 95.85%] | 99.54% | +0.053 ± 0.022 | 8.63 pp |

## Primary Interpretation

At +4 pp, baseline coverage was 93.10% [91.36%, 94.51%]; fresh follow-up coverage is 94.76% [94.31%, 95.18%].

Status: **inconclusive**. Monte Carlo interval includes nominal coverage; this is inconclusive, not proof of calibration.

Unadjusted secondary-grid Monte Carlo intervals also exclude nominal at 0 pp, 10 pp. These are exploratory across the grid, not additional confirmatory findings.

These results apply only to this synthetic DGP and this predeclared effect. Coverage checks do not certify proxy validity, real-world retention inference, transportability, or surrogate status. The original 1,000-repetition baseline is preserved for comparison.

Self-review only; no independent peer feedback is claimed.
