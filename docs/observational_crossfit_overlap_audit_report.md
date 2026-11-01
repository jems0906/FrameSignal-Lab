# Observational Extension: Cross-Fitted Overlap Diagnostic Audit

This is a paired, same-seed replay of the positivity/model-misspecification stress study. Cross-fitted propensity predictions are used only for overlap diagnostics; this report does not estimate a cross-fitted AIPW effect. Oracle assignment probabilities are diagnostic-only and never enter propensity fitting.

Study: `framesignal-observational-crossfit-overlap-audit-v1`. Config SHA-256: `3e13f3d935e14dcdd8a25ad8f2db33801bf9e6b0b38478767bc05bad9c39b1ca`. Source study: `framesignal-observational-positivity-misspecification-v1`; source config SHA-256: `e43970a71de45826c56b4ca33318afa4c1ed76a8e1caf38562bfc40cb9f3ea63`. Seed: 66752021; N=2,000; 300 paired replicates per cell; 5 folds.

False warning means the fitted or cross-fitted overlap rule fails while the oracle rule passes. Missed warning means that rule passes while the oracle rule fails. The paired crossfit-minus-in-sample false-warning interval uses Student-t Monte Carlo uncertainty; warning-rate intervals use exact Clopper-Pearson intervals. Bonferroni familywise control covers the fixed eight cells.

## Results

| Overlap | Nuisance profile | In-sample false warning | Cross-fit false warning | Cross-fit minus in-sample (familywise MC interval) | In-sample missed warning | Cross-fit missed warning | Oracle pass rate |
|---|---|---:|---:|---:|---:|---:|---:|
| moderate | correct_both | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 100.0% |
| moderate | propensity_misspecified | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 100.0% |
| moderate | outcome_misspecified | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 100.0% |
| moderate | both_misspecified | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 100.0% |
| weak | correct_both | 12.0% | 12.0% | +0.0 pp [-1.8, +1.8] pp | 0.7% | 1.0% | 96.0% |
| weak | propensity_misspecified | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 0.0% |
| weak | outcome_misspecified | 16.3% | 15.7% | -0.7 pp [-2.5, +1.2] pp | 0.3% | 1.7% | 95.7% |
| weak | both_misspecified | 0.0% | 0.0% | +0.0 pp [+0.0, +0.0] pp | 0.0% | 0.0% | 0.0% |

## Interpretation

The paired comparison estimates whether out-of-fold propensity predictions change overlap warning behavior relative to the source study's in-sample diagnostics for this synthetic generator. Cross-fitting can reduce reuse of observations in nuisance fitting, but it does not guarantee better overlap calibration, fix propensity misspecification, or address positivity violations.

Oracle values are available only in this simulated audit; they are not real-world inputs. No AIPW effect estimate or proxy status is changed by this follow-up.

Self-review only; no peer feedback is claimed.
