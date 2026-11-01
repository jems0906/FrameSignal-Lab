# Independent Statistical Review Request

**Status: prepared for review; no peer review has occurred.** This packet is not a review record or approval. Add reviewer identity, feedback, and response only after an independent reviewer actually provides them.

## Review Scope

FrameSignal Lab is a synthetic educational study of randomized presentation policies. It is not Netflix data, a definition of Netflix retention, a claim about internal content metrics, or a claim that a title caused return.

Primary estimand: intention-to-treat effect of household assignment to a fictional presentation policy on the indicator of any service return during days 29-56. All assigned households, including non-viewers and zero-exposure households, remain in the population. Household is the assignment and inference unit.

The frozen baseline uses 2,000 households per randomized experiment, a household difference in means with a Welch interval, qualified starts as the primary short-term candidate, and viewing days as the predefined alternative. Completion among starters is descriptive because starting is post-assignment. Three synthetic scenarios target helpful (+6 pp), unrelated (0 pp), and misleading (-6 pp) return effects. Training, validation, and held-out experiments use distinct household populations. No proxy weights are learned.

## Findings to Review

- Baseline target coverage at +4 pp was 93.10%, with 95% Wilson Monte Carlo interval [91.36%, 94.51%], after 1,000 repetitions per effect.
- Fresh-seed +4 pp follow-up coverage was 94.76%, interval [94.31%, 95.18%], after 10,000 repetitions. This interval includes nominal 95%; the baseline shortfall was not reproduced as a decisive primary finding.
- A separately predeclared simultaneous grid study used seed 20261102, 10,000 repetitions per effect, and nominal 99% Wilson intervals at five effects to form a nominal Bonferroni familywise 95% interval family. Wilson intervals are approximate for discrete Monte Carlo counts. None excluded 95%; this is no detected familywise signal for this DGP, not proof of calibration.
- A third fresh-seed study used exact Clopper-Pearson 99% intervals with Bonferroni across five effect sizes. All intervals included 95%. Its finite-sample simultaneous guarantee concerns Monte Carlo coverage proportions under independent repetitions only; it does not guarantee validity of the target Welch intervals or general calibration.
- Held-out candidate sign agreement was 44.4% across nine experiments, with experiment-bootstrap interval [11.1%, 77.8%]. The simulated harmful-proxy counterexample includes three held-out experiments where starts rose while oracle return effects were negative.
- A separate 80% interval launch/agreement screen is not met. The study does not authorize either short-term candidate as a general real-world surrogate.

Full artifacts: [research plan](research_plan.md), [frozen protocol](../configs/analysis_plan.json), [baseline validation report](validation_report.md), [first calibration follow-up](calibration_followup_report.md), [simultaneous grid follow-up](calibration_grid_followup_report.md), [scientific review and revision history](methodology_review.md), and [metric cards](metric_cards.md).

## Questions for the Reviewer

1. Is the stated estimand and household-level randomization/inference aligned with the simulated data-generating process?
2. Are the Welch target intervals, Wilson Monte Carlo intervals, and the fresh-seed/simultaneous follow-up interpretation appropriate for these claims?
3. Does the simultaneous five-effect procedure support only the limited “no familywise signal detected” statement, and are any conclusions overstated?
4. Are the practical +2 pp threshold, sample size, multiplicity family, and target-based advance/reject/insufficient-evidence rule defensible for this educational example?
5. Is experiment-level sign agreement a useful illustrative failure diagnostic at nine experiments, and what limitations must accompany it?
6. Are the completion-among-starters, exposure, runtime, genre, window, and outlier diagnostics described without implying causal effects they do not identify?
7. What additional simulations or design changes would be required before making any real-world calibration or surrogate-validity claim?

Please distinguish major validity concerns from optional improvements. Review should be independent of the implementation; self-review, automated checks, and user-entered review logs do not substitute for peer feedback.

## Feedback Record

Pending. No reviewer has been contacted through this packet, and no response is claimed.