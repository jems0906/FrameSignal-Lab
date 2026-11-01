# FrameSignal Lab

A statistical workbench for content measurement and proxy validation. Fictional household-level viewing and randomized presentation policies show a short-term metric helping, failing, and reversing a decision. **Synthetic data only. Not affiliated with Netflix; not a definition of Netflix retention or an internal content decision metric.**

## Decision and MVP

The primary estimand is the household-level intention-to-treat effect of a presentation policy on the proportion of assigned households returning during days 29-56. Primary candidate: qualified starts per household. Alternative: distinct viewing days per household. Watch time and completion are diagnostics; completion among starters conditions on post-assignment behavior and is not labeled clean ITT.

Three registered scenarios: helpful (+6 pp true return), unrelated (0), misleading (-6 pp). Policies can increase starts in all three. Every registered household remains in the ITT denominator, including non-viewers and zero-exposure households.

## Run Locally

Requires Python 3.11-3.13 and Node.js 22 (or a Vite-compatible Node 20). These commands assume a terminal at the repository root.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
.venv\Scripts\python -m uvicorn app.api.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open **http://localhost:5173**. API docs: http://127.0.0.1:8000/docs. On Unix, use `.venv/bin/python` in place of `.venv\Scripts\python`. The Vite proxy points to port 8000; if changing backend port update `frontend/vite.config.js` too. For an occupied frontend port, Vite chooses the next available one.

## Reproduce the Evidence

Run with your configured interpreter at the root:

```powershell
python -m ruff check backend packages metricsteward/backend
python -m pip wheel --no-deps ./packages/framesignal-metrics --wheel-dir dist
python backend/run_analysis.py
python backend/run_calibration_followup.py
python backend/run_calibration_grid_followup.py
python backend/run_calibration_exact_followup.py
python backend/run_observational_extension.py
python backend/run_observational_replication.py
python backend/run_observational_robustness_stress.py
python backend/run_observational_overlap_oracle_audit.py
python backend/run_learned_proxy.py
python backend/export_metricsteward.py
python -m pytest -q
python backend/execute_notebooks.py
npm --prefix frontend run build
npm --prefix metricsteward/frontend run build
```

The report command generates 27 independently populated experiments, 54,000 unique households, three detailed scenario runs, and 1,000 target simulations at each of five effect sizes. It writes `reports/latest.json`, `docs/validation_report.md`, and `docs/executive_memo.md`. Defaults and thresholds come from the frozen `configs/analysis_plan.json`; the output records its SHA-256 and runtime versions. Identical seed/config/library versions reproduce the numeric evidence. Notebook execution uses clean kernels, validates notebook JSON, and saves executed outputs; notebook metadata/plot encodings need not be byte-identical.

The separate calibration follow-up is predeclared in `configs/calibration_followup.json`; it uses a fresh seed and 10,000 repetitions per effect without changing the original report or estimator. It writes `reports/calibration_followup.json` and `docs/calibration_followup_report.md`.

A second fresh-seed study in `configs/calibration_grid_followup.json` uses nominal 99% Wilson Monte Carlo intervals at each of five effects to form a nominal Bonferroni familywise 95% interval family. Wilson coverage is approximate for discrete Monte Carlo counts, not a strict finite-sample guarantee. It writes `reports/calibration_grid_followup.json` and `docs/calibration_grid_followup_report.md`. No familywise coverage deviation was detected in this synthetic run; that is not proof of calibration.

A third predeclared study in `configs/calibration_exact_followup.json` uses exact Clopper-Pearson intervals for Monte Carlo coverage proportions, with 99% per-effect intervals and a Bonferroni simultaneous familywise lower bound of 95% across five effects. This guarantee applies only under independent simulation repetitions and only to Monte Carlo coverage proportions, not the Welch intervals themselves. It writes `reports/calibration_exact_followup.json` and `docs/calibration_exact_followup_report.md`.

Two isolated, post-baseline extensions are also predeclared. The observational study reports measured-covariate AIPW estimates, overlap diagnostics, household-bootstrap intervals, and sensitivity to simulated hidden confounding. The learned-score study fits on training households, tunes ridge strength on validation households, freezes the score before held-out households are generated, and reports held-out effect agreement. Both are exploratory: observational identification depends on exchangeability/positivity/model assumptions, and learned-score intervals condition on frozen weights without weight-learning uncertainty. Neither approves a proxy or changes the randomized baseline.

The single-run observational table is illustrative, not evidence of an average sensitivity trend. A separate `configs/observational_replication.json` study runs 200 independent replicates in each of nine scenario/confounding cells. It reports mean AIPW bias, RMSE, influence-function Wald interval coverage, overlap, and ESS with Bonferroni familywise Monte Carlo intervals. Its Wald intervals are distinct from the household-bootstrap intervals in the illustrative report; all results remain specific to the synthetic generator.

`configs/observational_robustness_stress.json` separately crosses moderate/weak measured overlap with four nuisance-model profiles across 300 replicates per cell. Hidden confounding remains zero to isolate positivity from propensity/outcome misspecification. The report is exploratory and does not establish performance beyond this constructed generator.

`configs/observational_overlap_oracle_audit.json` replays the exact stress-study seeds and compares fitted-propensity overlap diagnostics with known assignment-probability diagnostics. Oracle probabilities are audit-only and never enter AIPW; they are unavailable in real observational data. This replay does not alter or replace the source stress report.

For interactive notebooks, select the same environment as the installed dependencies. Both notebooks locate the root from their current working directory and run without pre-existing report files. Full execution can take a few minutes on slower systems; the UI caches bounded analysis results in the local process.

## Shared Library and MetricSteward

Metric calculations live in the installable [framesignal-metrics package](packages/framesignal-metrics/README.md). Installing backend requirements from the root installs this package too. FrameSignal's API and both notebooks use it; exact DataFrame parity and independent dashboard-export recomputation tests prevent a second set of formulas from silently drifting. The clean notebook runner pins its kernel to the invoking interpreter.

MetricSteward is now a separate application under [metricsteward/README.md](metricsteward/README.md) in this repository. It imports the wheel/report handoff through a validated consumer, persists evidence versions and append-only reviews in SQLite, and exposes `/api/steward/calculate` using the same shared library. Cross-app tests cover all three scenarios and both windows. **Import and educational acceptance never approve a retention proxy.** Starts/viewing days remain rejected as general surrogates; completion stays descriptive, and calibration flags are retained.

After preparing the evidence, start the MetricSteward backend in another terminal:

```powershell
python -m uvicorn metricsteward.api:app --app-dir metricsteward/backend --host 127.0.0.1 --port 8001
```

Start its frontend separately:

```powershell
npm --prefix metricsteward/frontend ci
npm --prefix metricsteward/frontend run dev
```

Open http://localhost:5174. FrameSignal remains at http://localhost:5173. See [handoff and promotion boundaries](docs/metricsteward_handoff.md). MetricSteward records actual self-review or explicitly user-reported peer feedback; it does not authenticate reviewers or provide production authorization.

## Scientific Safeguards

- Household outcomes and complete-household resampling match random assignment; event rows are not independent inference units.
- Fixed day-56 horizon, no repeated ordinary p-value peeking or optional stopping.
- Target inference at alpha 0.05; two predefined candidate comparisons at Bonferroni alpha 0.025 each. Diagnostics and cross-experiment exploratory results do not acquire blanket multiplicity protection.
- Disjoint training, validation, and held-out household populations and seeds. The optional learned score is fit/tuned/frozen before held-out assessment; its intervals omit weight-learning uncertainty and do not establish surrogacy.
- Separate individual correlation from experiment-effect agreement. Experiment bootstrap and correlated Gaussian effect-noise sensitivity are descriptive, not definitive surrogacy validation.
- Known-truth coverage, null false-positive rate, power, variance, bias, and practical-success rates include Monte Carlo uncertainty. These check target inference, not all proxy assumptions.
- Runtime, genre, time-window, outlier, sampling, and exposure diagnostics preserve household denominators and label changed estimands.
- Oracle affinity and return probabilities are audit-only. No proxy uses late outcomes, oracle fields, or held-out learned weights.

## Portfolio Deliverables

| Deliverable | Location |
|---|---|
| Business question, estimand, assumptions, splits, frozen criteria, research citations | [Research plan](docs/research_plan.md), [machine-readable protocol](configs/analysis_plan.json) |
| Full measurement definitions | [Metric cards](docs/metric_cards.md) |
| Variance, bias, agreement, uncertainty, failure modes | [Validation report](docs/validation_report.md), [numeric evidence](reports/latest.json) |
| Fresh-seed interval-coverage follow-up | [Predeclared config](configs/calibration_followup.json), [follow-up report](docs/calibration_followup_report.md) |
| Simultaneous grid-coverage follow-up | [Predeclared config](configs/calibration_grid_followup.json), [follow-up report](docs/calibration_grid_followup_report.md) |
| Exact Monte Carlo coverage follow-up | [Predeclared config](configs/calibration_exact_followup.json), [follow-up report](docs/calibration_exact_followup_report.md) |
| Observational sensitivity extension | [Predeclared config](configs/observational_extension.json), [report](docs/observational_extension_report.md) |
| Replicated observational sensitivity | [Predeclared config](configs/observational_replication.json), [report](docs/observational_replication_report.md) |
| Positivity and nuisance-model stress | [Predeclared config](configs/observational_robustness_stress.json), [report](docs/observational_robustness_stress_report.md) |
| Paired oracle-overlap diagnostic audit | [Predeclared config](configs/observational_overlap_oracle_audit.json), [report](docs/observational_overlap_oracle_audit_report.md) |
| Train/validate/frozen-heldout learned score | [Predeclared config](configs/learned_proxy_extension.json), [report](docs/learned_proxy_report.md) |
| Honest self-review and revision history | [Scientific review](docs/methodology_review.md) |
| Independent statistician review request | [Invitation draft](docs/peer_review_invitation.md), [review packet](docs/peer_review_packet.md); feedback status remains pending until received |
| Fictional stakeholder recommendation and non-conclusions | [Executive memo](docs/executive_memo.md) |
| End-to-end reproducible analysis | [Proxy notebook](notebooks/proxy_validation.ipynb), [diagnostics notebook](notebooks/simulation_diagnostics.ipynb), tests and fixture |
| Brief coverage and actual check status | [Coverage](docs/requirements_checklist.md), [verification](docs/verification.md) |
| Shared metric package and tested educational handoff | [Package](packages/framesignal-metrics/README.md), [MetricSteward contract](docs/metricsteward_handoff.md) |
| Persistent MetricSteward catalog, evidence and review history | [MetricSteward app](metricsteward/README.md) |
| Frontend dependency advisory and remediation record | [Vite CVE fix summary](docs/cve-fix-summary.md) |

## API and Exports

`GET /api/analysis?scenario=misleading&n=2000&seed=20261031` returns metric effects, intervals, predictive association, sensitivity, SQL checks, known truth, and memo. `/api/validation` runs the frozen split design; `/api/operating` reports target operating characteristics. `/api/export` downloads all synthetic source tables, household aggregates, run analysis, and provenance as a ZIP. Inputs are bounded and validated. This is a local research app, not a multi-user authenticated production service.

`/api/observational`, `/api/observational-replication`, `/api/observational-robustness`, `/api/observational-overlap-audit`, and `/api/learned-proxy` serve separately generated exploratory reports; the Extensions view exposes overlap/sensitivity diagnostics, paired oracle comparisons, replicated AIPW summaries, and held-out score agreement. Oracle values are diagnostic-only; none of these reports replaces randomized ITT or authorizes real-world use.

## Containers and CI

```powershell
docker compose up --build
```

Prepare the wheel and matching evidence before building containers. FrameSignal UI: http://localhost:8080; MetricSteward UI: http://localhost:8082. All Docker builds use the **repository root** as context; MetricSteward uses a named volume for its catalog. Stop native servers on ports 8000/8001 before running the default Compose stack. GitHub Actions generates evidence before cross-app integration tests, runs both frontend builds and notebooks, and uploads evidence artifacts. Remote CI is not claimed until it actually runs; local container integration passed. Both frontends use patched Vite 6.4.5; see [the remediation record](docs/cve-fix-summary.md).

## Boundaries

The presentation policy is not a randomized manipulation of artistic quality. Do not infer that a specific title caused return or that creative value has an objective scalar score. Netflix's published proxy and surrogate-index research is a methodological starting point only; the research plan links verified official publication pages. No Netflix data, models, internal metrics, production validation, external peer review, or real stakeholder feedback are claimed. Optional observational and learned-score studies are separate, synthetic, exploratory extensions; the randomized MVP remains primary and unchanged.