# Requirement Coverage

| Brief requirement | Implementation / evidence |
|---|---|
| Seeded fictional households, titles, runtimes, availability, exposure, viewing, assignment, fully observed outcome | `backend/app/simulations/generator.py`; scenario JSON; reproducibility and availability tests |
| Primary candidate, alternative, target, helpful/unrelated/misleading scenarios | Frozen `configs/analysis_plan.json`; qualified starts, viewing days, late return |
| Four candidate/diagnostic definitions and full metric cards | `docs/metric_cards.md`; UI metric registry dialogs |
| All assigned households, including zero viewing, remain in ITT | Left-aligned household aggregation; SQL left-join count; population tests |
| Completion among starters explicitly limited | Descriptive ratio and complete-household bootstrap; no causal label or p-value |
| Household-matched uncertainty | Welch household inference; household and experiment resampling, not event tests |
| Prediction versus causal surrogacy | Household association, within-arm correlations, held-out effect scatter, experiment agreement |
| Leakage prevention | Independent populations and seeds by split; predefined baseline candidates plus a separate train/validate/freeze learned-score extension |
| Uncertainty in experiment comparisons | Experiment bootstrap and separately labeled correlated effect-noise sensitivity |
| Outliers, sampling, runtime, genre, window, exposure | Nine sensitivity variants, household-bootstrap variability, genre mix, exposure summaries |
| Known-truth coverage, null FPR, power by effect size | 1,000 repeated target simulations per effect with Wilson Monte Carlo intervals, bias/variance/width |
| Follow up baseline coverage flag without tuning | Separate fresh-seed protocol (`configs/calibration_followup.json`), 10,000 repetitions per effect, primary +4 pp Wilson interval and explicit inconclusive rule; original plan/report retained |
| Resolve exploratory grid flags with simultaneous Monte Carlo uncertainty | Fresh seed and 10,000 repetitions per effect; nominal Bonferroni 95% familywise interval using 99% Wilson score intervals across five effects; all include nominal 95%; no familywise signal detected, not proof of calibration; Wilson discreteness means no strict finite-sample guarantee |
| Obtain finite-sample familywise uncertainty for Monte Carlo coverage proportions | Separate fresh-seed study uses exact Clopper-Pearson 99% intervals and Bonferroni across five effects; guarantee applies only to coverage-proportion uncertainty under independent replications, not target Welch interval validity |
| Predefinition, practical threshold, multiplicity, fixed horizon | Frozen v1.0 plan and research document; target at 0.05, two candidates at 0.025; no optional stopping |
| Decision memo with limitations and follow-up | Generated `docs/executive_memo.md`, dynamic UI decision record |
| Research plan and validation report | `docs/research_plan.md`; generated `docs/validation_report.md` and full `reports/latest.json` |
| Honest critique and revisions | `docs/methodology_review.md`; self-review only |
| Seeded reproducible analysis, SQL, tests, end-to-end notebooks | Backend test suite, `backend/run_analysis.py`, both notebooks, clean-kernel execution script |
| FastAPI backend and interactive frontend | API with bounded validated queries, responsive React/TypeScript workbench and downloads |
| Dockerfiles, lockfile, CI, README | Both Dockerfiles, Compose/Nginx, npm lockfile, GitHub Actions, setup/reproduction instructions |
| Research grounding without internal-metric claims | Two verified official publication pages cited in research plan; synthetic disclaimer throughout |
| Learned composite extension | Implemented separately: train-only household prediction weights, validation-only ridge tuning, frozen-before-heldout scoring, held-out treatment-effect agreement and uncertainty; exploratory only |
| Observational causal extensions | Implemented separately: illustrative AIPW/bootstrap, replicated hidden-confounding sensitivity, factorial positivity/nuisance-misspecification stress, and paired in-sample/cross-fit/oracle overlap diagnostics; exploratory, not randomized ITT, with oracle values diagnostic-only |
| Shared calculation library across dashboard and notebooks | Installable `packages/framesignal-metrics`; FrameSignal wrapper delegates; exact-parity notebook cells and independent CSV-export recomputation tests |
| Portable MetricSteward educational handoff | Versioned wheel, report/plan/wheel hashes, fail-closed consumer validator, preserved rejected/descriptive statuses; `docs/metricsteward_handoff.md` |
| Actual integration in MetricSteward | Separate `metricsteward/` app in this monorepo; validated persistent catalog, import history, review log, export and shared calculation endpoint; cross-app parity tests for all scenarios/windows |

Deployment recipes and GitHub Actions are provided. Their actual verification status is recorded separately in `docs/verification.md`; no cloud deployment, executed remote CI, external peer review, or real-data validation is claimed.

Educational calculation availability does not confer surrogate approval. The scientific rejection and calibration flags are valid study outcomes, not failures to implement a promised feature. Genuine peer review and real-world approval cannot be replaced by generated documentation.