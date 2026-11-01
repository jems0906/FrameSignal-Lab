# Scientific Review Record

## Status

Self-review by the project implementation only, 2026-10-31. No external peer review or stakeholder approval has occurred. Automated checks are engineering evidence, not peer feedback.

## Critique

1. The DGP is designed to produce counterexamples. It demonstrates that starts can fail, not how often they fail in any real company. Three scenario families and nine held-out experiments have limited policy support.
2. Target return is directly observed and synthetically simple. Real censoring, subscription changes, calendar shocks, interference, logging loss, heterogeneous treatment effects, and household membership changes are absent.
3. Household correlation is confounded by latent affinity. It is not evidence of mediation, even with a tight interval; assignment can also affect pooled correlations.
4. Completion selects starters after assignment. Resampling complete households fixes the uncertainty unit, not causal selection. No completion estimate is labeled clean ITT.
5. Sign agreement discards magnitude and practical launch thresholds. Target-null signs are unstable. Oracle non-null agreement is reported separately, and null-target positive proxies are counted rather than treated as meaningful directional truth.
6. Experiment-bootstrap intervals are coarse at nine experiments. Correlated Gaussian effect draws are an approximation and sensitivity analysis, not calibrated surrogate inference or a posterior. No definitive regression-on-noisy-effects claim is made.
7. Candidate-family Bonferroni protects two predefined comparisons per experiment; it does not protect a global search across scenarios, all diagnostics, and every experiment. Exploratory results must remain exploratory.
8. Winsorization, runtime/genre event subsets, shorter windows, and per-impression normalization change what is measured. Post-assignment exposure normalization is not the original policy ITT effect.
9. The 2,000-household design is a transparent demonstration size. Power for small effects and the +2 pp confidence-bound decision may be poor; the operating report must reveal that rather than imply adequacy.
10. Target-interval operating checks do not certify candidates or agreement intervals. Future composite metrics require independent train/tune/freeze stages and new held-out experiments. Observational extensions require overlap and confounding sensitivity, not a declaration that a model solves selection.
11. The frozen +4 pp operating run shows 93.1% coverage (Monte Carlo interval 91.4%-94.5%), below nominal. This is an explicit scientific flag, not a passing certification. Across five effect sizes the flags are exploratory and unadjusted; a new prospectively specified study should distinguish sampling variation from approximation error. No seed, effect grid, or estimator was tuned after seeing this result.

## Actual Revision History

| Revision | Change | Reason and evidence |
|---|---|---|
| v0.1 | Established all-household means, explicit late-return DGP, and seeded household assignment | Baseline tests verify retained non-viewers and starts/return reversal. |
| v0.2 | Added complete-household completion bootstrap and descriptive-only labels | Post-assignment starting changes the eligible comparison population. |
| v0.3 | Added frozen candidate family, independent experiment seeds/identities, SQL audits, and runtime/exposure diagnostics | Tests verify denominator counts, config consistency, split disjointness, and multiplicity. |
| v0.4 | Added paired effect covariance to experiment-level noise propagation and separated oracle nulls | Candidate and target effects share households; independent effect draws would discard that covariance. |
| v1.0 | Added known-truth target operating characteristics, generated reports, executable notebooks, UI, CI, and deployment recipes | Verification evidence is recorded in the repository; no peer feedback is invented. |
| v1.0 reporting revision | Explicitly flagged coverage Monte Carlo intervals excluding nominal 95% | Frozen +4 pp run has 93.1% coverage; reporting changed, not the prespecified analysis or seed. |
| v1.0 shared-library handoff | Extracted the same calculator into an installable package; added notebook/export parity, input validation, and educational-only handoff verification | Calculation reuse and checksum tests are engineering safeguards, not surrogate or external-review certification. |
| v1.1 MetricSteward integration | Added a separate SQLite-backed catalog/review application consuming the same package and validated handoff; added cross-app parity tests and Docker/CI wiring | Keeps evidence versions, scientific statuses, review provenance, and calculation outputs consistent. Local tests and container checks do not constitute peer review or real-world metric approval. |
| v1.1 Vite security remediation | Upgraded both frontends from Vite 6.3.5 to 6.4.5, regenerated lockfiles, added npm audit to CI, and configured production cross-app links | Initial advisory scan reported 12 findings including two high; re-scan and both full npm audits are clean. See `docs/cve-fix-summary.md`. |
| v1.2 calibration follow-up | Added a fresh-seed, 10,000-repetition-per-effect follow-up with +4 pp as the only primary calibration point; kept baseline frozen | Fresh +4 pp coverage interval includes 95% (94.31%-95.18%), so the baseline undercoverage signal was not reproduced as a decisive primary finding. Secondary 0 and 10 pp intervals exclude nominal but remain unadjusted exploratory signals. No estimator change is justified by this result alone. |
| v1.3 simultaneous calibration grid | Added a second fresh-seed grid study with 99% Wilson Monte Carlo intervals at five effects (nominal Bonferroni familywise 95%) | All five intervals include nominal 95%; no familywise signal detected under this DGP. Wilson discreteness means this is an approximate interval family, not a strict finite-sample guarantee; it does not prove general calibration or surrogate validity. |
| v1.4 exact Monte Carlo coverage study | Added fresh-seed Clopper-Pearson intervals with Bonferroni familywise control for five Monte Carlo coverage proportions | All exact intervals include nominal 95%. This guarantees the familywise Monte Carlo interval family under independent replications, not validity of the target Welch interval, other DGPs, or surrogate metrics. |
| v1.5 observational and learned extensions | Added isolated synthetic AIPW/overlap/hidden-confounding sensitivity and a household-level learned score with training, validation tuning, frozen held-out evaluation | These meet the optional post-baseline extension scope. They do not alter the randomized ITT baseline, remove unmeasured confounding, quantify learned-weight uncertainty, or approve any proxy. |

## External Review Needs

Request genuine review of estimand relevance, completion definition, practical thresholds, missingness, scenario support, covariance/noise assumptions, and whether a launch-rule rather than sign-agreement validation is preferable. Record reviewer names/comments only after feedback actually occurs, with consent where appropriate. Until then the honest status remains self-reviewed.