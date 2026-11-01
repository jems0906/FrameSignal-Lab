# Research Plan

## Business Question

Can a short-term content-use metric safely screen a fictional presentation policy for a longer-horizon household-return decision? When can an attractive signal favor a harmful or ineffective policy?

This portfolio is synthetic, not affiliated with Netflix. Published research motivates the methods, not a claim about internal content decisions. Treatment changes presentation/exposure, not a title's creative quality.

## Estimand First

For the population of all registered households assigned at day 0, estimate the average effect of assignment to the presentation policy rather than control on the indicator of any service return on days 29-56 inclusive:

$$\tau_Y = E[Y_i(1)-Y_i(0)].$$

All assigned households, including zero-exposure households and non-viewers, remain in their randomized arm. Return is a distinct simulated service-return record, not derived from short-term events and not Netflix retention. The binary outcome is fully observed; no right-censoring or attrition is simulated.

## Predefined Protocol

Machine-readable source: `configs/analysis_plan.json`, frozen v1.0 before generating held-out results in this build. This is an internal synthetic protocol, not an externally timestamped preregistration.

- Primary target: household return during days 29-56.
- Primary candidate: qualified starts per assigned household during days 0-13; an event qualifies at 2 minutes.
- Alternative: distinct qualified viewing days per assigned household during days 0-13.
- Diagnostics: minutes per assigned household and any-completion among qualified starter households.
- Sample size: 2,000 households per experiment, balanced 1:1; nine experiments per train, validation, and held-out split (three scenarios at strengths 0.6, 1.0, 1.4).
- Seed: 20261031; independently derived experiment seeds and disjoint household identities across all 27 experiments.
- Practical target threshold: +2 percentage points. Advance only when the lower 95% target interval exceeds +2 pp; reject policy if its upper interval is below zero; otherwise insufficient evidence to advance.
- Primary target: two-sided alpha 0.05. Candidate comparisons: separate two-test Bonferroni family, alpha 0.025 each (97.5% intervals). Candidate statistical significance is never a launch rule.
- Other metrics, correlations, and sensitivity variants are descriptive, not a license for unadjusted confirmatory claims. No global correction across all fictional experiments is claimed.
- Fixed-horizon analysis after day 56. No ordinary p-value peeking, significance-triggered stopping, or outcome-dependent sample extension.

The chosen demonstration size is not adequate for every 2 pp practical decision. Repeated-simulation power and practical-success rates are reported rather than concealed. Future experiments need prospectively justified power, including the confidence-bound launch criterion.

## Generator and Known Truth

Fictional titles have runtime, genre, and availability dates. Household affinity and lognormal viewing opportunity generate heterogeneous exposure and use. Treatment changes impression counts, starts probabilities, and viewed fractions. Independent short-window viewing events are linked to households; multiple events and repeated starts can occur per household.

Return probability is `0.40 + 0.25 * affinity + assignment * scenario_return_effect * strength`, with a separate Bernoulli draw. The return-effect truth is +6 pp (helpful), 0 (unrelated), or -6 pp (misleading), scaled by strength. At allowed strengths probabilities remain in [0,1], so the average return treatment effect equals the configured shift. Positive individual association arises from shared affinity, not an assumed mediation equation. These stylized constructions demonstrate possibility, not frequency in real portfolios.

## Assumptions

Household randomization; consistency; no interference across households; accurate linked logs; no missing assignment or return; stable registration eligibility; no treatment-dependent censoring. Unequal exposure is a consequence of assignment and remains part of the total policy effect. Outcome observation is fixed, not triggered by viewing.

## Inference and Validation

Use treatment-minus-control household means, Welch standard errors and t intervals. Binary return is analyzed as a household proportion difference. Completion is a ratio of any-completed households to starters; stratified complete-household bootstrap intervals preserve starter/non-starter relationships but cannot cure post-assignment selection.

Contrast descriptive household Pearson association (with bootstrap intervals and within-arm association for single runs) against experiment-level sign agreement. Train, validation, and held-out populations are completely separate. No learned composite is fitted in the MVP, so no weights can leak. Later weights must be learned on training experiments, tuning confined to validation, and frozen before fresh held-out assessment.

Agreement uncertainty includes a complete-experiment bootstrap and a separately labeled correlated Gaussian effect-noise sensitivity calculation using within-household candidate/target covariance. No naive regression of estimated effects is presented as definitive validation. Known-zero target experiments are distinguished from non-null oracle agreement; an estimated null sign is unstable. Nine experiments and repeated scenario families limit generalization.

Proxy success requires the held-out agreement lower bound to exceed 80% and no demonstrated harmful reversal. This is a stringent illustrative screen, not a validated causal-surrogacy criterion. Reject on reversal; otherwise declare insufficient evidence if the uncertainty or policy coverage is inadequate.

## Failure Analysis and Operating Checks

Compare raw and pooled 99th-percentile-capped outcomes, 7 versus 14 days, short/long title runtimes, genre-specific event subsets, and per-impression diagnostics. Preserve all households when subsetting events. Exposure-normalized and capped analyses have different estimands; runtime/genre subsets are not causal title-quality comparisons.

Repeat the target return DGP 1,000 times per true effect (0, 2, 4, 6, 10 pp). Report interval coverage, null false-positive rate, two-sided non-null power, bias with Monte Carlo SE, sampling variance, width, and confidence-bound practical success. Wilson intervals quantify Monte Carlo uncertainty of rates. These operating checks concern target inference, not surrogate certification.

The 2026-11-01 calibration follow-up is separately predeclared in `configs/calibration_followup.json` after the original +4 pp coverage interval fell below nominal. It uses fresh seed 20261101, the same N=2,000, Welch estimator and interval, and 10,000 repetitions per unchanged effect grid. The +4 pp point is its sole primary calibration question; other grid points are explicitly descriptive. The decision rule distinguishes interval below, above, or containing 95%; an interval containing 95% is inconclusive, not proof of calibration. This follow-up does not alter the frozen baseline plan or its report.

A subsequent simultaneous grid follow-up is separately specified in `configs/calibration_grid_followup.json`: fresh seed 20261102; unchanged N, DGP, Welch estimator, target interval, and five-effect grid; 10,000 repetitions per effect. Five two-sided nominal 99% Wilson Monte Carlo intervals form a nominal Bonferroni familywise 95% interval family. Wilson intervals are approximate because the Monte Carlo count is discrete, so the procedure does not provide a strict finite-sample 95% guarantee. Any off-nominal interval is a signal for a separately planned method investigation; if all include 95%, the result is no detected familywise deviation, not certification. This adjusts the interpretation across the secondary grid rather than treating several unadjusted intervals as independent confirmatory evidence.

## Extensions and Review

Learned composites and observational causal analyses are deliberately deferred until the baseline is reproducible. An observational extension must specify identification assumptions, overlap/positivity diagnostics, and sensitivity to unmeasured confounding; predictive models cannot declare away selection bias.

Review status: self-review only. The scientific critique and actual revisions are in `methodology_review.md`; no peer feedback is claimed.

## Research Starting Points

Verified against Netflix's official publication pages during this build on 2026-10-31:

1. Kallus, Ejdemyr, Chou, and Bibaut. *Improve Your Next Experiment by Learning Better Proxy Metrics From Past Experiments*, Netflix Research, August 26, 2024. [Official publication](https://research.netflix.com/publication/improve-your-next-experiment-by-learning-better-proxy-metrics-from-past). Motivates learning cross-experiment treatment-effect covariance. This MVP does not reproduce their estimator or learn weights.
2. Zhang, Zhao, Le, and Kallus. *Evaluating the Surrogate Index as a Decision-Making Tool Using 200 A/B Tests at Netflix*, Netflix Research, November 9, 2023. [Official publication](https://research.netflix.com/publication/evaluating-the-surrogate-index-as-a-decision-making-tool-using-200-a-b-tests); [paper](https://arxiv.org/abs/2311.11922). Motivates experiment-level decision agreement. Their outcomes, data, index, and findings are not this project's simulated target or metrics.

Neither citation proves that any proposed portfolio metric is used internally for content decisions.