# Observational Extension: Replicated Sensitivity Study

This predeclared repeated-simulation study is separate from the single-run illustrative bootstrap report. It is synthetic, exploratory, not randomized ITT, and not approval for real-world decisions.

Study: `framesignal-observational-replicated-sensitivity-v1`. Config SHA-256: `5c0ca995bf56e8e12e5b56ba231c5acf4bf5d9305bb146cd72cb08a755883dfc`. Seed: 8302723; N=2,000 per replicate; 200 independent replicates per cell.

AIPW uses observed affinity and log opportunity only. Each replicate's 95% Wald interval uses the empirical variance of its AIPW pseudo-outcome; it is not the household-bootstrap interval used in the illustrative report. The reported Monte Carlo intervals use Bonferroni familywise control across the fixed nine cells: Student-t intervals for mean bias and exact Clopper-Pearson intervals for coverage proportions.

## Results

| Scenario | Hidden confounding | True ATE | Mean AIPW bias (familywise MC interval) | Bias RMSE | Wald coverage (familywise MC interval) | Overlap pass rate | Mean ESS control / treatment |
|---|---:|---:|---:|---:|---:|---:|---:|
| helpful | 0.0 | +6.0 pp | -0.29 [-0.73, +0.14] pp | 2.21 pp | 96.5% [91.2, 99.1]% | 100.0% | 1109 / 780 |
| helpful | 0.5 | +6.0 pp | +0.13 [-0.34, +0.59] pp | 2.34 pp | 95.0% [89.1, 98.3]% | 100.0% | 1115 / 778 |
| helpful | 1.0 | +6.0 pp | +1.05 [+0.61, +1.48] pp | 2.43 pp | 92.5% [85.9, 96.7]% | 100.0% | 1108 / 790 |
| unrelated | 0.0 | +0.0 pp | -0.10 [-0.56, +0.36] pp | 2.32 pp | 95.5% [89.8, 98.6]% | 100.0% | 1109 / 778 |
| unrelated | 0.5 | +0.0 pp | -0.05 [-0.53, +0.43] pp | 2.40 pp | 94.5% [88.5, 98.0]% | 100.0% | 1111 / 779 |
| unrelated | 1.0 | +0.0 pp | +1.07 [+0.61, +1.52] pp | 2.52 pp | 93.5% [87.1, 97.4]% | 100.0% | 1108 / 790 |
| misleading | 0.0 | -6.0 pp | -0.05 [-0.55, +0.46] pp | 2.53 pp | 93.5% [87.1, 97.4]% | 100.0% | 1112 / 779 |
| misleading | 0.5 | -6.0 pp | +0.33 [-0.15, +0.81] pp | 2.46 pp | 93.5% [87.1, 97.4]% | 100.0% | 1110 / 782 |
| misleading | 1.0 | -6.0 pp | +0.92 [+0.48, +1.37] pp | 2.44 pp | 95.5% [89.8, 98.6]% | 100.0% | 1106 / 790 |

## Interpretation

These results estimate average behavior of the AIPW estimator under this specific generator. Monte Carlo intervals quantify simulation uncertainty, not uncertainty about whether the generator or identification assumptions match a real application. Coverage of the replicate-level Wald intervals does not validate real-world identification or the original household-bootstrap interval.

AIPW does not remove hidden confounding. Overlap and effective sample size are diagnostics, not proof of identification. Do not combine this repeated study with the single-run illustrative report, replace randomized ITT, or approve any proxy.

Self-review only; no peer feedback is claimed.
