# Observational Extension: Overlap Threshold Operating Study

This is a fresh-seed, paired synthetic study of prespecified overlap rules. It does not choose or recommend a production threshold. Oracle diagnostics are audit-only; no oracle value enters a propensity fit or AIPW estimate.

Study: `framesignal-observational-overlap-threshold-stress-v1`. Config SHA-256: `5b38754b32395c8ee2124432878c2ecb78a00cb33152ecaa455532813999690b`. Seed: 9158021; N=2,000; 300 replicates per each of eight overlap/nuisance profiles; 5 cross-fitting folds.

The same generated replicate is evaluated under every threshold. Hidden confounding is fixed at zero. Threshold summaries equally weight the eight generator profiles; all profile-level threshold results and Monte Carlo intervals are retained in JSON.

## Balanced Profile Summaries

| Threshold rule | Propensity range | ESS floor | Oracle pass | In-sample pass | Cross-fit pass | In-sample false warning | Cross-fit false warning | Crossfit minus in-sample (familywise MC interval) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| wide_02_98_ess50 | 0.02-0.98 | 50 | 92.5% | 91.9% | 93.1% | 1.5% | 1.4% | -0.1 pp [-0.6, +0.4] pp |
| reference_05_95_ess50 | 0.05-0.95 | 50 | 74.2% | 70.9% | 70.7% | 3.4% | 3.8% | +0.4 pp [-0.1, +0.9] pp |
| tight_10_90_ess50 | 0.10-0.90 | 50 | 50.0% | 50.0% | 50.0% | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp |
| wide_02_98_ess100 | 0.02-0.98 | 100 | 92.5% | 91.9% | 93.1% | 1.5% | 1.4% | -0.1 pp [-0.6, +0.4] pp |
| reference_05_95_ess100 | 0.05-0.95 | 100 | 74.2% | 70.9% | 70.7% | 3.4% | 3.8% | +0.4 pp [-0.1, +0.9] pp |
| tight_10_90_ess100 | 0.10-0.90 | 100 | 50.0% | 50.0% | 50.0% | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp |

## Interpretation

These summaries describe rule behavior only under the prespecified generator and fresh seed. A looser rule can reduce flags while also allowing poorer support; a stricter rule can flag more cases without proving that the estimate is unusable. The oracle reference is not observable in real observational studies. No rule is selected from this grid.

Familywise Monte Carlo intervals quantify simulation uncertainty, not external validity. Cross-fitting is diagnostic-only here; the study does not estimate cross-fitted treatment effects.

Self-review only; no peer feedback is claimed.
