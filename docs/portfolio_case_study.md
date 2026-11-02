# FrameSignal Lab: Portfolio Case Study

## Question and Decision

Can a short-term content-use metric safely screen a fictional randomized presentation policy for longer-horizon household return?

The target is the effect of assignment on the proportion of all assigned households returning during days 29-56. It is an illustrative outcome, not Netflix retention. The treatment is presentation/exposure, not creative quality or the causal effect of a specific title.

## Design and Implementation

- Simulated households, titles, availability, impressions, viewing events, and fully observed return.
- Qualified starts as the primary candidate; distinct viewing days as the predefined alternative; watch time and completion as diagnostics.
- Household-level difference-in-means inference, retaining non-viewers and zero-exposure households. Completion among starters is descriptive because starting is post-assignment.
- A frozen fixed-horizon protocol: 2,000 households per experiment, nine experiments in each of independent training, validation, and held-out populations; a +2 percentage-point practical target threshold; separate candidate-family multiplicity handling.
- Household prediction is separated from experiment-effect agreement. Experiment bootstrap and correlated effect-noise sensitivity describe uncertainty without claiming definitive causal surrogacy.
- A shared installable calculation library serves FrameSignal, both research notebooks, and MetricSteward. Parity and export-recomputation tests guard against formula drift.

## Findings

Default scenario estimates from the frozen baseline (N=2,000):

| Scenario | Starts per household, policy minus control | Return effect and 95% interval | Policy recommendation |
|---|---:|---|---|
| Helpful | +1.50 | +6.00 pp [+1.64, +10.36] | Insufficient evidence to advance: lower bound does not clear +2 pp |
| Unrelated | +1.92 | -1.00 pp [-5.39, +3.39] | Insufficient evidence; not proof of no effect |
| Misleading | +1.96 | -3.70 pp [-8.08, +0.68] | Insufficient evidence; estimated reversal is not certain harm |

The generator's known return effects are +6, 0, and -6 pp respectively. The observed default estimates must not be confused with that known synthetic truth.

Held-out starts sign agreement was 44.4% across nine experiments, with an experiment-bootstrap interval of 11.1%-77.8%. The conclusion is to retain directly measured return as the target and reject starts as a universal surrogate, not to manufacture a passing proxy.

The original operating check flagged 93.1% target-interval coverage at +4 pp. Separate fresh-seed calibration studies preserved that baseline and documented Monte Carlo uncertainty. Exact Clopper-Pearson/Bonferroni guarantees concern simulation coverage proportions, not the underlying Welch intervals or general proxy validity.

Optional learned-score and observational follow-ups remain separate, exploratory evidence. Oracle quantities are diagnostic-only; adjustment does not remove hidden confounding by declaration. Threshold comparisons recommend no production rule.

## MetricSteward Handoff

MetricSteward consumes the shared calculation package and a versioned educational evidence handoff. Evidence hashes, persistent versions, review provenance, and promotion guards preserve rejected/descriptive statuses. Educational catalog availability is not approval to replace the return target.

## Demo (About Two Minutes)

The [31-second silent screen recording](portfolio/framesignal-metricsteward-demo.webm) shows the default scenarios, held-out view, and MetricSteward safeguards. The following script provides a longer narrated walkthrough; the recording itself has no narration.

1. Open FrameSignal's Experiment view with N=2,000 and seed 20261031. Show Helpful, then Unrelated, then Misleading; compare starts with return and its interval.
2. Show that non-viewers remain in the population and that completion is descriptive. Explain that the default misleading interval crosses zero, despite the generator's negative true effect.
3. Open Proxy validation, select held-out evidence, and distinguish household association from treatment-effect agreement and uncertainty.
4. Open MetricSteward, filter rejected metrics, and inspect evidence plus educational-only/promotion-blocked status. Do not record invented peer feedback or change approval state.
5. Close with the shared library, reproducible notebooks, and the conclusion: a failed surrogate is a valid research outcome.

## Screenshots

Captured from the running local Compose apps on 2026-11-02. Scenario screenshots use the frozen baseline controls, not stronger post-hoc examples. MetricSteward captures show the existing imported evidence; no reviews or approvals were created during capture.

| View | Capture |
|---|---|
| Helpful policy and uncertainty | [Screenshot](portfolio/framesignal-helpful.png) |
| Unrelated policy and uncertainty | [Screenshot](portfolio/framesignal-unrelated.png) |
| Misleading policy, retained non-viewers, and estimated reversal | [Screenshot](portfolio/framesignal-misleading.png) |
| Held-out proxy validation | [Screenshot](portfolio/framesignal-heldout-validation.png) |
| Rejected surrogate catalog | [Screenshot](portfolio/metricsteward-rejected-catalog.png) |
| Educational-only evidence and blocked real-world approval | [Screenshot](portfolio/metricsteward-promotion-blocked.png) |
| MetricSteward mobile layout | [Screenshot](portfolio/metricsteward-mobile.png) |

[Capture evidence](portfolio/capture-evidence.json) records scenario verdicts, the screenshot inventory, mobile dimensions, and zero browser runtime errors. The 390px mobile capture had no document horizontal overflow. The complete video decoded successfully (771 frames, 30.84 seconds).

## Reproduce the Captures

Start the applications with `docker compose up -d --wait`. MetricSteward must already contain a valid educational handoff import; the capture script does not mutate evidence or submit reviews.

The [capture script](../scripts/capture_portfolio.cjs) uses a temporary Playwright 1.56.1 installation and local Microsoft Edge; neither application dependency manifest is modified. From the repository root in PowerShell:

```powershell
npm install --prefix "$env:TEMP/framesignal-portfolio-capture" --no-save --package-lock=false playwright@1.56.1
node "$env:TEMP/framesignal-portfolio-capture/node_modules/playwright/cli.js" install ffmpeg
$env:PLAYWRIGHT_MODULE = "$env:TEMP/framesignal-portfolio-capture/node_modules/playwright"
node scripts/capture_portfolio.cjs
```

Screenshots and video are written to `docs/portfolio/`. This script is an optional local capture tool, not a required CI dependency. It checks scenario controls, promotion-blocked labeling, self-review boundaries, browser runtime errors, and mobile overflow. Timing and video bytes can vary between runs.

## Evidence and Reproduction

- [Research plan](research_plan.md) and [frozen protocol](../configs/analysis_plan.json).
- [Metric definitions](metric_cards.md), [validation report](validation_report.md), and [executive memo](executive_memo.md).
- [Shared calculator](../packages/framesignal-metrics/README.md) and [MetricSteward handoff](metricsteward_handoff.md).
- [Proxy notebook](../notebooks/proxy_validation.ipynb) and [diagnostics notebook](../notebooks/simulation_diagnostics.ipynb).
- [Setup and reproduction commands](../README.md) and [verification record](verification.md).

## Limitations and Review

Synthetic data, limited constructed policies, nine held-out experiments, a demonstration-sized sample, and conditional uncertainty limit generalization. No Netflix data, internal metric claims, real-data validation, cloud deployment, or production authorization is claimed.

Review status: **self-review only**. No independent peer feedback has occurred. This portfolio is an educational engineering/research deliverable, not scientific certification.