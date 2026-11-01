# Verification Record

Baseline FrameSignal checks ran locally on 2026-10-31. MetricSteward integration and Vite remediation were verified locally on 2026-11-01. The post-baseline extension checks below were run locally on 2026-11-01. This record reports actual checks, not prospective claims of passing remote CI or peer review.

## Completed Checks

| Check | Observed result |
|---|---|
| Full Python regression suite | 61 passed, including FrameSignal, shared-library, MetricSteward persistence/API, cross-app parity for all scenarios/windows, calibration follow-ups, and both observational/learned extensions |
| Ruff lint | Passed for `backend`, `packages`, and `metricsteward/backend` after removing one unused import surfaced by the first lint run |
| VS Code/Pylance diagnostics | No errors after configuring backend, shared-package, and MetricSteward source roots |
| Frontend production builds | Both apps type-check and build with Vite 6.4.5. FrameSignal retains its non-blocking >500 kB bundle advisory; MetricSteward builds cleanly. |
| npm dependency audit | Both full frontend audits report zero vulnerabilities after remediation; production audit was also clean before the dev-tool fix. |
| GitHub advisory scan | Initial scan found 12 Vite advisories (2 high); follow-up scan for Vite 6.4.5 returned no findings. Details: `docs/cve-fix-summary.md` and `reports/cve-report-*.json`. |
| Frozen full analysis | Executed three scenarios, 27 split experiments, 54,000 unique households, and 5,000 repeated target simulations; JSON and both decision reports generated |
| Calibration follow-up | Fresh seed 20261101; 10,000 repetitions per effect at N=2,000 (50,000 total); original plan/report untouched; report/config hashes recorded |
| Simultaneous calibration grid | Fresh seed 20261102; 10,000 repetitions at each of five effects; nominal Bonferroni familywise 95% using 99% Wilson intervals; no interval excluded 95%; Wilson coverage is approximate for discrete counts; original plan/report untouched |
| Exact Monte Carlo calibration grid | Fresh seed 20261103; 10,000 repetitions at each of five effects; exact Clopper-Pearson 99% intervals with Bonferroni familywise lower bound 95% for the Monte Carlo coverage proportions; all include 95%; this does not guarantee the Welch intervals themselves |
| SQL integrity | All checks passed in all three default scenario runs |
| End-to-end notebooks | Current user-edited notebooks validated and executed in memory from clean Python 3.13 kernels; eight cells each, six code cells each, including shared-library parity; originals were not rewritten |
| Live browser desktop | 1440 x 1000 viewport; default helpful run, misleading switch, complete metric dialogs, nine held-out points with error bars, and no document horizontal overflow |
| Live browser mobile | 390 x 844 viewport; candidate/split selection, diagnostics, scenario controls, and no document horizontal overflow; tables and mobile navigation intentionally scroll within their own containers |
| Exploratory harm example | Misleading n=16,000, seed=23 (the predetermined baseline test example) showed return -5.34 pp, 95% interval -6.88 to -3.79, while starts rose; UI rejected policy. This does not replace or extend the frozen n=2,000 evidence |
| ZIP export | TestClient archive check and live fetch returned HTTP 200, application/zip, and PK signature; local API also served the large example ZIP |
| Compose configuration | `docker compose config --quiet` passed |
| Container images | Frontend and backend images both built successfully; the backend dependency-download blocker was resolved on the resumed build |
| Container integration | Temporary Compose services on port 8081 served the compiled frontend and proxied health, analysis, and ZIP requests through Nginx successfully; backend health status was `healthy` |
| Production-page interaction | Container-served UI switched to misleading: return -3.7 pp, 95% interval -8.1 to +0.7; 452 non-viewers retained; no error banner; ZIP export HTTP 200 with PK signature |
| Extracted metric package | Versioned framesignal-metrics 1.0.0 wheel built and installed; installed calculator and handoff source bytes match the wheel; all registered households retained even with no events |
| Updated container package | Backend image rebuilt with the shared library; a disposable TestClient smoke test confirmed HTTP 200, 200 households, SQL success, and import from installed site-packages |
| MetricSteward handoff consistency | Actual report and wheel checksums validated by the installed consumer; five entries remain educational-only with promotion disabled; mismatched artifacts and edited approval flags fail tests |
| MetricSteward container API | Imported the handoff, listed five definitions, verified two rejected surrogates and zero approvals; shared calculator retained two households with no events, zero starts, and undefined completion |
| MetricSteward approval guard | A live container request to approve synthetic evidence returned HTTP 409 with the expected blocked-approval message |
| Patched frontend images | Both frontends rebuilt; FrameSignal container image matches its tag, and MetricSteward frontend was force-recreated and confirmed to match its patched image tag |
| Vite CVE remediation | Vite 6.3.5 findings fixed by upgrading both apps to 6.4.5; advisory re-scan is empty, both complete npm audits are clean, and clean installs/builds pass |
| MetricSteward browser | Rejected-status filter returns two metrics; evidence inspector reports three harmful reversals and the coverage flag; mobile viewport has no horizontal page overflow |
| Cross-app production navigation | FrameSignal production link resolves to MetricSteward at port 8082; MetricSteward resolves back to FrameSignal at port 8080 |
| MetricSteward application | Separate catalog UI/API builds; persistent SQLite evidence version, search/status filters, review history, export, validated FrameSignal import, and shared `/calculate` endpoint |
| MetricSteward Compose runtime | Both application stacks running locally; all four image builds completed; APIs healthy and frontends return HTTP 200 |
| Container import and approval guard | Imported five educational definitions through Nginx; two remain rejected and zero approved; an approval attempt returned HTTP 409 |
| Container calculator endpoint | Shared-library version 1.0.0; two registered households retained with zero events, zero starts, and undefined completion |
| Live MetricSteward UI | Rejected-status filter returns two rows; inspector shows 44.4% held-out agreement, three known-truth harmful reversals, calibration flag, and approval block; 390px mobile viewport has no horizontal page overflow |
| Notebook source diagnostics | Both current user-edited notebooks are Pylance-clean. Sources were inspected before path configuration; originals were not rewritten for the diagnostic fix. |
| Independent review preparation | Reviewer packet prepared with estimand, methods, results, limitations, and focused questions; no reviewer feedback is claimed |
| Remote GitHub Actions | Run [41321264883](https://github.com/jems0906/FrameSignal-Lab/actions/runs/41321264883) completed successfully on `main` commit `0c763e2a46edbec76824d24a71522406a5d106df`; `scientific-baseline`, `frontend`, and `metricsteward-frontend` all passed |

## Post-Baseline Extension Checks

| Check | Observed result |
|---|---|
| Observational extension runner | Generated nine scenario/confounding cases from `configs/observational_extension.json`; report status is `exploratory_not_randomized_itt` |
| Replicated observational runner | Generated nine cells × 200 independent replicates (1,800 total; N=2,000 each) with outcome-only simulation; report includes familywise Monte Carlo intervals for AIPW mean bias and Wald coverage, plus RMSE, overlap, and ESS |
| Positivity/model-misspecification stress runner | Generated eight factorial cells × 300 independent replicates (2,400 total; N=2,000 each), hidden confounding fixed at zero. Moderate overlap passed all diagnostics; weak-overlap pass rates were 84.7% with both models correct, 79.7% with outcome-only misspecification, and 0% when the propensity model was misspecified. All familywise mean-bias intervals included zero. |
| Paired oracle-overlap audit | Replayed the same 2,400 stress-study seeds. With weak overlap and correct outcome regression, fitted diagnostics falsely warned in 12.0% of `correct_both` and 16.3% of `outcome_misspecified` replicates while oracle diagnostics passed; missed warnings were below 1%. Oracle probabilities were diagnostic-only. |
| Cross-fitted overlap audit | Replayed the same 2,400 seeds with five-fold out-of-fold propensity predictions. False-warning rates remained 12.0% and 15.7% in those weak cells; paired familywise intervals for crossfit-minus-in-sample rates included zero. This compares diagnostics only, not AIPW estimates. |
| Threshold operating study | Fresh seed; 2,400 paired replicates across eight generator profiles and six rules (48 profile-rule cells). Balanced oracle pass rates were 92.5% for 0.02-0.98, 74.2% for 0.05-0.95, and 50.0% for 0.10-0.90. ESS floors 50 vs. 100 did not change balanced pass rates in this run; no rule is selected. |
| Learned-score runner | Generated 54,000 households in disjoint 18,000-household train/validation/held-out splits; validation selected ridge alpha 0.01; held-out experiment sign agreement was 44.4%; status remains educational-only |
| Focused extension tests | Passed for observational estimation, replicated Monte Carlo summaries, independent stress factors, exact-seed in-sample/cross-fit replay, fold exclusion and oracle exclusion, threshold monotonicity/summary contract, learned-score split/freeze behavior, and report endpoint guards |
| Full regression suite | 67 passed; one third-party Starlette/AnyIO deprecation warning |
| Python lint | Ruff passed for `backend`, `packages`, and `metricsteward/backend` |
| Extension report API | TestClient returned the illustrative, replicated, robustness-stress, oracle-overlap, cross-fit-overlap, threshold-stress, and learned-score reports with explicit scope/status fields |
| FrameSignal frontend | TypeScript production build passed with replicated-sensitivity, positivity/model-stress, oracle/cross-fit overlap, and threshold operating panels; Vite reports the existing non-blocking >500 kB chunk advisory |
| MetricSteward frontend | TypeScript production build passed |
| npm audits | Both frontend audits report zero vulnerabilities |
| Compose | `docker compose config --quiet` passed; all four images built, including the FrameSignal backend with the threshold report copied into the image |
| Extensions browser view | Local UI loaded all six threshold summaries and the existing observational panels. At 390px viewport, body width was 375px with no page overflow; evidence tables keep their own horizontal scrolling. |
| Local API port collision | Existing service on port 8000 was left running. Vite now accepts `FRAMESIGNAL_API_TARGET` (default remains `http://127.0.0.1:8000`); browser check used the current backend on port 8002. |
| Remote CI | Run [41353899068](https://github.com/jems0906/FrameSignal-Lab/actions/runs/41353899068) passed on commit `fef1099a41eac74fefed7e5b5c32ac03de7a706f`; all three jobs succeeded, including the threshold runner, 67-test suite, notebook execution, and artifact upload. |

Local execution used Python 3.13.3 with pinned direct scientific dependencies. The notebook environment contains the same pinned packages. Other Python versions are not certified by this local run.

## Scientific Results Are Not All Passing Certifications

- Held-out starts sign agreement: 44.4%, experiment-bootstrap interval 11.1%-77.8%. Positive short-term effects do not establish a safe return surrogate.
- Null target false-positive rate: 5.4%, Monte Carlo interval 4.2%-7.0%.
- True +4 pp target coverage: 93.1%, Monte Carlo interval 91.4%-94.5%, below nominal 95%. The report and UI flag this explicitly. Causes are not established; flags across effect sizes are exploratory and unadjusted. The seed, estimator, and effect grid were not tuned after inspecting it.
- Fresh-seed +4 pp follow-up coverage: 94.76%, 95% Wilson Monte Carlo interval 94.31%-95.18%, which includes nominal coverage. The baseline shortfall was not reproduced as a decisive primary finding; this is inconclusive, not proof of calibration. Secondary unadjusted intervals at 0 pp and 10 pp exclude nominal and are exploratory signals only. See `docs/calibration_followup_report.md`.
- Simultaneous five-effect follow-up: all nominal Bonferroni-adjusted 99% Wilson Monte Carlo intervals include nominal 95%; no familywise signal was detected in this synthetic DGP. Wilson intervals are approximate under discrete counts, so the procedure does not guarantee strict finite-sample coverage. This is not proof of calibration beyond this design. See `docs/calibration_grid_followup_report.md` and `reports/calibration_grid_followup.json`.
- Exact five-effect follow-up: all Bonferroni-adjusted Clopper-Pearson intervals for Monte Carlo coverage proportions include 95%. The familywise lower bound is exact under independent repetitions and applies only to those proportions, not to the underlying Welch intervals or any other DGP. See `docs/calibration_exact_followup_report.md` and `reports/calibration_exact_followup.json`.
- Positivity/model-stress study: with hidden confounding fixed at zero, moderate-overlap cells pass overlap checks in all replicates; weak-overlap cells show diagnostics failing more often, including 100% failure when the propensity model is misspecified. All eight familywise mean-bias intervals include zero, so this run does not precisely establish bias in any cell. These findings are limited to the specified generator and AIPW implementation.
- Oracle-overlap audit: fitted diagnostics false-warned in 12.0% and 16.3% of two weak-overlap cells where oracle diagnostics passed; missed-warning rates were below 1%. In weak cells with propensity misspecification, oracle diagnostics also failed in every replicate. These comparisons are available only because the synthetic generator records true assignment probabilities; they do not establish that oracle information exists in real observational data.
- Cross-fit overlap audit: five-fold predictions left weak-cell false-warning rates essentially unchanged (12.0% and 15.7%); paired familywise intervals for the change include zero. The audit estimates overlap diagnostics, not treatment effects; cross-fitting did not resolve the weak-support signal in this DGP.
- Threshold operating study: wider ranges increased balanced oracle pass rates and strict ranges decreased them; ESS floors 50 and 100 made no difference to the balanced summaries. This describes the frozen synthetic grid only and does not select a production threshold.
- At the default misleading n=2,000, the return interval crosses zero; the correct policy recommendation is insufficient evidence to advance, not certain harm. Non-significance does not establish equivalence.

## Tool and Environment Limitations

The earlier FrameSignal browser pass used explicit forced clicks when ordinary Playwright stability checks stalled. MetricSteward's container UI was also inspected in the integrated browser; filtering, evidence inspection, approval-block labeling, and mobile overflow were checked. Browser checks are local session checks, not a committed remote browser-testing suite.

The Pylance interpreter-update endpoint returned an unsupported-method error; Python conclusions rely on observed tests, notebook execution, and runtime results, not a claimed Pylance environment update. The editor installer also reported package-installation success without making it importable in the explicit runner interpreter. This mismatch was observed in a failing notebook run and an interpreter probe, then repaired by installing the built wheel into that interpreter. Clean notebook kernels now pin their executable to the invoking interpreter. Windows notebook execution emitted a non-fatal ZeroMQ selector-thread warning; all cells completed.

## Deployment and Review Status

The earlier backend download failure (`IncompleteRead`) was resolved when container verification resumed. All four current images build successfully; both frontend images were rebuilt after Vite remediation.

The complete Compose stack is running locally: FrameSignal UI at http://localhost:8080, MetricSteward UI at http://localhost:8082, with APIs on ports 8000 and 8001. Nginx health, import, metric-list, calculation, and export routes were verified. Both backends report healthy. Both frontend images were rebuilt after Vite remediation, and the MetricSteward frontend was force-recreated after image-ID comparison showed its prior container still used the older image.

These are local container checks, not cloud deployment. Native development servers may also still be running on ports 5173/5174 where available.

The initial repository commit has been published to the private GitHub repository, and the linked Actions run completed successfully. No production application security audit, real-data validation, external peer review, or real stakeholder feedback is claimed. CI status applies to the cited commit; later changes require their own workflow result.

## MetricSteward Integration and Dependency Security

MetricSteward is implemented as a separate application in this monorepo. Its local UI, API, persistent import/review flow, evidence checksums, and cross-app calculator parity are verified. No separate repository URL is needed. Educational availability does not promote the rejected proxies or resolve the scientific calibration flag.

Both frontends now pin patched Vite 6.4.5. The initial advisory report (`reports/cve-report-1.json`) found 12 Vite findings, including two high severity; the follow-up report and final report are empty. Both complete npm audits report zero vulnerabilities. See `docs/cve-fix-summary.md`. This is dependency advisory remediation, not a production code security audit.