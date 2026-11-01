# Observational Extension: Fixed-Reference Threshold Audit

This fresh-seed study compares six candidate warning rules against one fixed oracle adequacy reference. Unlike the prior threshold stress study, the oracle label does not change with the candidate rule. The fixed reference is a synthetic convention, not a production recommendation.

Study: `framesignal-observational-overlap-threshold-reference-v1`. Config SHA-256: `5ece708968c4ab3904fe4ea13c9e5a401796b234be4c6ce6ca62aa2ca1e7f4d7`. Source threshold grid: `framesignal-observational-overlap-threshold-stress-v1`. Seed: 30198473; N=2,000; 300 replicates × 8 profiles; 5 cross-fitting folds.

Fixed oracle reference: propensity range 0.05-0.95, per-arm ESS >= 50. Hidden confounding remains zero. Oracle values are diagnostic-only.

## Balanced Profile Summaries

| Candidate rule | Range | ESS floor | Fixed oracle pass | In-sample pass | Cross-fit pass | In-sample false warning | Cross-fit false warning | In-sample missed warning | Cross-fit missed warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| wide_02_98_ess50 | 0.02-0.98 | 50 | 73.8% | 91.0% | 92.2% | 0.0% | 0.1% | 17.2% | 18.5% |
| reference_05_95_ess50 | 0.05-0.95 | 50 | 73.8% | 70.4% | 70.5% | 3.4% | 3.7% | 0.0% | 0.4% |
| tight_10_90_ess50 | 0.10-0.90 | 50 | 73.8% | 49.9% | 49.9% | 24.0% | 23.9% | 0.0% | 0.0% |
| wide_02_98_ess100 | 0.02-0.98 | 100 | 73.8% | 91.0% | 92.2% | 0.0% | 0.1% | 17.2% | 18.5% |
| reference_05_95_ess100 | 0.05-0.95 | 100 | 73.8% | 70.4% | 70.5% | 3.4% | 3.7% | 0.0% | 0.4% |
| tight_10_90_ess100 | 0.10-0.90 | 100 | 73.8% | 49.9% | 49.9% | 24.0% | 23.9% | 0.0% | 0.0% |

## Interpretation

This fixed-reference view makes candidate warning errors comparable within each generator profile. It does not choose a threshold: false-warning and missed-warning costs are unspecified, and the oracle adequacy convention exists only in this simulated study. Detailed familywise intervals for every profile-rule cell are in the JSON report.

Self-review only; no peer feedback is claimed.
