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

A third follow-up, `configs/calibration_exact_followup.json`, uses Clopper-Pearson exact binomial intervals for each repeated-simulation coverage proportion. With nominal 99% two-sided marginal intervals at each of five fixed effects, Bonferroni's union bound gives simultaneous familywise coverage of at least 95% for the five Monte Carlo proportions, assuming independent simulation repetitions at each effect. This finite-sample guarantee is about Monte Carlo uncertainty in coverage estimates only. It does not make the target Welch confidence interval exact, guarantee its coverage under other DGPs, or validate a proxy. The seed is 20261103, with the same N, DGP, target estimator, and effect grid. Results are in `docs/calibration_exact_followup_report.md`; all five simultaneous intervals contain 95%, so no familywise deviation was detected, not proved absent.

## Post-Baseline Extensions

The randomized baseline remains primary and unchanged. Two isolated exploratory extensions were added after the baseline became reproducible; the observational extension has an illustrative single-run report and a separate replicated sensitivity study. Neither extension changes the frozen v1.0 analysis plan, primary UI decision rule, or MetricSteward approval states.

The observational demonstration is preregistered in `configs/observational_extension.json`. It simulates selected treatment assignment as a function of measured affinity/opportunity and a hidden loyalty factor; later return also depends on the hidden factor. It reports the naive descriptive contrast and a cross-sectional AIPW estimate using only measured affinity and log opportunity, with complete-household bootstrap intervals, propensity quantiles, common support, overlap-range violations, clipping, and effective sample sizes. Identification assumes consistency, no interference, positivity, complete data, conditional exchangeability given measured covariates, and correct specification of either the propensity or outcome model. The sensitivity grid varies hidden-confounding strength (0, 0.5, 1). AIPW does not fix unmeasured confounding; poor overlap is surfaced rather than silently trimmed. These synthetic estimates are not randomized ITT and are not evidence about real populations.

The single-run table is illustrative only and cannot establish how average bias changes with confounding strength. A separate repeated study, `configs/observational_replication.json`, runs 200 independent outcome-only simulations per scenario/strength cell (1,800 total), avoiding event generation because it is irrelevant to this estimator. It reports mean AIPW bias and RMSE, replicate-level Wald interval coverage, overlap pass rate, and ESS. Each replicate's normal Wald interval uses the empirical AIPW pseudo-outcome variance; this is distinct from the household-bootstrap interval above. Student-t Monte Carlo intervals for mean bias and exact Clopper-Pearson intervals for coverage proportions use Bonferroni familywise control across the fixed nine cells. The Monte Carlo intervals quantify simulation uncertainty under this constructed generator, not uncertainty about real-world identification. AIPW remains biased under hidden confounding; overlap diagnostics do not prove identification.

A third observational study, `configs/observational_robustness_stress.json`, uses a two-by-four factorial design: moderate/weak measured-overlap profiles crossed with both nuisance models correct, propensity-only misspecification, outcome-only misspecification, and both misspecified. It runs 300 independent outcome-only simulations per cell (2,400 total) with hidden confounding fixed at zero. The assignment model's centered quadratic affinity term isolates propensity misspecification; an assignment-invariant centered quadratic outcome term isolates outcome-regression misspecification while preserving the treatment effect. It reports AIPW bias/RMSE, Wald interval coverage, overlap pass rates, and ESS with familywise Monte Carlo intervals across the eight cells. This is a finite-sample stress test of this specified generator; it is not external validation of double robustness or real-world identification.

A paired diagnostic-only replay, `configs/observational_overlap_oracle_audit.json`, regenerates the exact same eight-cell seed grid as the stress study and compares fitted-propensity overlap diagnostics with the known assignment probabilities. It reports fitted/oracle pass rates, false and missed warning rates, outside-range/common-support differences, and ESS differences with familywise Monte Carlo intervals. Oracle values are not inputs to AIPW and are available only because the data are simulated. The source stress report and AIPW estimates are not changed by this audit.

A second paired diagnostic replay, `configs/observational_crossfit_overlap_audit.json`, uses the exact same seed grid and five-fold cross-fitted logistic propensity predictions. Each household is scored by nuisance coefficients and standardization learned without that household. The report compares in-sample and cross-fitted overlap warning rates against the same oracle diagnostics with familywise Monte Carlo intervals. This audit estimates neither cross-fitted AIPW treatment effects nor a new causal estimand; it leaves the source stress estimates unchanged. It can reveal whether overlap-warning disagreement changes when propensity-fitting reuse is removed, but cannot establish better calibration beyond this generator.

A fresh-seed threshold operating study, `configs/observational_overlap_threshold_stress.json`, compares six preregistered combinations of propensity range (0.02-0.98, 0.05-0.95, 0.10-0.90) and minimum per-arm ESS (50, 100). It reuses each of 2,400 generated datasets across all six rules and evaluates in-sample, five-fold cross-fitted, and oracle diagnostics across the eight overlap/nuisance profiles. It reports pass rates, false/missed warnings, and familywise Monte Carlo intervals. This study does not select or recommend a threshold; any future threshold decision requires a separately justified operational loss function and external evidence.

The learned household prediction score is preregistered in `configs/learned_proxy_extension.json`. It uses qualified starts and viewing days to predict days 29-56 return in training households, standardizing features on training data only. Ridge penalty is tuned by household Brier score in a separate validation population. Weights and transforms are frozen before held-out households are generated and evaluated. The held-out treatment effect of the frozen score is compared with return effects across experiments, separately from household prediction. Experiment-bootstrap and correlated effect-noise intervals are reported. These intervals condition on fitted weights and omit training/tuning weight uncertainty; nine experiments per split and the constructed scenarios limit generalization. This is an exploratory demonstration, not a definitive surrogate method or approval.

All observational estimators prohibit hidden/oracle fields as inputs; stress audits fix hidden-confounding strength at zero, and oracle fields are diagnostic-only. Self-review only. No external peer review or real-world identification validation has occurred.

## Review

Learned proxies and observational analyses remain optional extensions, not replacements for the randomized baseline. Real observational use would additionally require domain-specific identification arguments, overlap assessment, and sensitivity to unmeasured confounding. Predictive models cannot declare away selection bias.

Review status: self-review only. The scientific critique and actual revisions are in `methodology_review.md`; no peer feedback is claimed.

## Research Starting Points

Verified against Netflix's official publication pages during this build on 2026-10-31:

1. Kallus, Ejdemyr, Chou, and Bibaut. *Improve Your Next Experiment by Learning Better Proxy Metrics From Past Experiments*, Netflix Research, August 26, 2024. [Official publication](https://research.netflix.com/publication/improve-your-next-experiment-by-learning-better-proxy-metrics-from-past). Motivates learning cross-experiment treatment-effect covariance. This MVP does not reproduce their estimator or learn weights.
2. Zhang, Zhao, Le, and Kallus. *Evaluating the Surrogate Index as a Decision-Making Tool Using 200 A/B Tests at Netflix*, Netflix Research, November 9, 2023. [Official publication](https://research.netflix.com/publication/evaluating-the-surrogate-index-as-a-decision-making-tool-using-200-a-b-tests); [paper](https://arxiv.org/abs/2311.11922). Motivates experiment-level decision agreement. Their outcomes, data, index, and findings are not this project's simulated target or metrics.

Neither citation proves that any proposed portfolio metric is used internally for content decisions.