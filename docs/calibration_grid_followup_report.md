# Simultaneous Calibration Grid Follow-up

A separately predeclared Monte Carlo check following the inconclusive +4 pp follow-up. Neither prior report nor the frozen analysis plan was changed.

Study: `framesignal-return-coverage-grid-20261102-v1`. Config SHA-256: `45ca4b74aa924c0074699f3c75f84bf54a9f00fbb3739a540f66cc2681f19abb`. Fresh seed: 20261102.
N=2,000 households per repetition; 10,000 repetitions per effect; 50,000 repetitions total.

Each effect-specific Wilson score interval uses nominal 99% confidence, forming a nominal Bonferroni familywise 95% interval family across the five grid points. Wilson intervals are approximate and may not attain nominal marginal coverage exactly because the Monte Carlo count is discrete. This adjusts Monte Carlo uncertainty across the grid; it does not change the target's Welch interval or alter the household DGP.

## Results

| True effect pp | Coverage | Simultaneous Wilson interval | Target interval rejection / power | Bias pp ± MC SE | Mean target interval width pp |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 94.63% | [94.02%, 95.18%] | 5.37% | -0.030 ± 0.023 | 8.76 pp |
| 2.0 | 94.66% | [94.05%, 95.21%] | 15.58% | +0.053 ± 0.023 | 8.75 pp |
| 4.0 | 95.37% | [94.80%, 95.88%] | 42.41% | -0.063 ± 0.022 | 8.73 pp |
| 6.0 | 94.89% | [94.29%, 95.43%] | 77.39% | -0.012 ± 0.022 | 8.70 pp |
| 10.0 | 94.86% | [94.26%, 95.40%] | 99.36% | -0.045 ± 0.022 | 8.63 pp |

## Interpretation

Status: **no_familywise_signal_detected**. Coverage intervals excluding nominal 95%: none.

No familywise signal detected; this is not proof of calibration.

All outcomes are conditional on this synthetic DGP and this predeclared design. A no-signal result is not proof of universal calibration; an off-nominal point would motivate a separately planned method investigation, not post-hoc correction of this run.

Self-review only; no independent peer feedback is claimed.
