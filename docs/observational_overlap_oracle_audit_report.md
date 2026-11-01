# Observational Extension: Oracle Overlap Diagnostic Audit

This is a paired, same-seed replay of the positivity/model-misspecification stress study. Oracle assignment probabilities are used only to audit fitted overlap diagnostics; they are never passed to AIPW. Oracle probabilities are unavailable in real observational data.

Study: `framesignal-observational-oracle-overlap-audit-v1`. Config SHA-256: `8b785f2820525a90fdec0c5d8222a8f1a12683820a3a5aa669ca4a67c60d09e1`. Source study: `framesignal-observational-positivity-misspecification-v1`; source config SHA-256: `e43970a71de45826c56b4ca33318afa4c1ed76a8e1caf38562bfc40cb9f3ea63`. Seed: 66752021; N=2,000; 300 paired replicates per cell.

A false warning means the fitted-propensity overlap rule fails while the oracle-propensity rule passes. A missed warning means the fitted rule passes while the oracle rule fails. The paired fitted-minus-oracle intervals use Student-t Monte Carlo intervals; warning-rate intervals use exact Clopper-Pearson intervals. Both use Bonferroni familywise control across eight cells.

## Results

| Overlap | Nuisance profile | Fitted pass | Oracle pass | False warning (familywise MC interval) | Missed warning (familywise MC interval) | Outside-range difference, fitted - oracle (familywise MC interval) | Mean ESS fitted/oracle, control / treatment |
|---|---|---:|---:|---:|---:|---:|---|
| moderate | correct_both | 100.0% | 100.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.0 pp [+0.0, +0.0] pp | 1111/1111 / 780/780 |
| moderate | propensity_misspecified | 100.0% | 100.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.0 pp [-0.0, +0.0] pp | 987/950 / 623/664 |
| moderate | outcome_misspecified | 100.0% | 100.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.0 pp [+0.0, +0.0] pp | 1112/1113 / 778/779 |
| moderate | both_misspecified | 100.0% | 100.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.0 pp [+0.0, +0.0] pp | 987/950 / 624/665 |
| weak | correct_both | 84.7% | 96.0% | 12.0% [7.4, 18.0]% | 0.7% [0.0, 3.2]% | +0.2 pp [+0.0, +0.4] pp | 748/754 / 425/427 |
| weak | propensity_misspecified | 0.0% | 0.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.8 pp [+0.5, +1.2] pp | 567/493 / 258/313 |
| weak | outcome_misspecified | 79.7% | 95.7% | 16.3% [11.0, 22.9]% | 0.3% [0.0, 2.6]% | +0.2 pp [-0.0, +0.4] pp | 746/754 / 424/426 |
| weak | both_misspecified | 0.0% | 0.0% | 0.0% [0.0, 1.9]% | 0.0% [0.0, 1.9]% | +0.8 pp [+0.5, +1.2] pp | 573/497 / 249/305 |

## Interpretation

This audit identifies disagreement between fitted and oracle overlap diagnostics for this known synthetic generator. It does not show that the oracle quantities are observable in practice, that the fitted diagnostic is generally calibrated, or that AIPW is identified. Estimator inputs and the source stress estimates are unchanged.

Self-review only; no peer feedback is claimed.
