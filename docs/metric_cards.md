# Metric Cards

All windows are relative to randomized assignment on day 0. Household is the assignment and aggregation unit. Treatment-minus-control effects refer to presentation policies, never creative quality.

## Qualified Starts (Primary Candidate)

- Decision: short-term policy screening; not an independent launch criterion.
- Population: every registered assigned household, including no exposure or viewing.
- Aggregation: count qualified events within each household, then average households equally.
- Numerator: events with at least 2 watched minutes; repeated starts count separately.
- Denominator: assigned households per arm.
- Window: days 0-13; predefined days 0-6 sensitivity.
- Missingness: no event is zero, not missing; all synthetic logs are observed.
- Direction: higher intended to be better.
- Limitations: presentation can induce extra starts without return benefit; unequal exposure, repeated starts, and attention capture influence the numerator. Individual prediction does not establish causal surrogacy.
- Inference: household Welch difference, 97.5% candidate-family interval.

## Distinct Viewing Days (Predefined Alternative)

- Decision: alternative short-term policy engagement screen.
- Population: every registered assigned household, including non-viewers.
- Aggregation: household count of distinct days containing a qualified event, then equally weighted household mean.
- Numerator: distinct household-days with at least one 2-minute event.
- Denominator: assigned households per arm.
- Window: days 0-13, bounded 0-14; days 0-6 sensitivity.
- Missingness: no qualified viewing is zero; no log missingness in the simulator.
- Direction: higher intended to be better.
- Limitations: saturation, window boundaries, availability, and repeated short visits; less mechanically runtime-driven than minutes but not necessarily a return surrogate.
- Inference: household Welch difference, 97.5% candidate-family interval.

## Watch Time (Diagnostic)

- Decision: describe policy consumption intensity and challenge runtime/outlier dependence.
- Population: all registered assigned households, including non-viewers.
- Aggregation: sum minutes per household, then household mean.
- Numerator: all watched minutes, including events below the qualification threshold.
- Denominator: assigned households per arm.
- Window: days 0-13; days 0-6 sensitivity.
- Missingness: zero minutes for non-viewers; synthetic events fully observed.
- Direction: higher intended to be better but may indicate inefficient or unwanted consumption.
- Limitations: title runtime, genre mix, heavy-use households, and exposure. No artistic-value or title-retention claim. Capping changes the outcome definition.
- Inference: household Welch difference, descriptive 95% interval; no confirmatory multiplicity claim.

## Completion Among Starters (Descriptive Only)

- Decision: describe viewing depth in the observed starter population, not the clean policy ITT effect.
- Population: households with at least one qualified start within each randomized arm.
- Aggregation: household indicator of any qualified completed event, ratio among starter households. This is not a per-title or event-weighted completion rate.
- Numerator: starter households with any event reaching at least 90% of its title runtime.
- Denominator: qualified starter households, not all registered households.
- Window: days 0-13. Completion is within one simulated event, not reconstructed cumulative title progress.
- Missingness: non-starters have undefined completion, not a completion failure. Empty starter arms are non-estimable. No synthetic outcome missingness.
- Direction: higher intended to be better descriptively.
- Limitations: starting is post-assignment. Policies can change who starts; comparing selected arms can be biased as a statement about all eligible households. Household bootstrap gives uncertainty, not causal identification.
- Inference: 400 stratified complete-household bootstrap draws for the difference of ratios; 95% percentile interval; no p-value or causal label.

## Return During Days 29-56 (Primary Target)

- Decision: advance, reject, or withhold a fictional presentation policy based on its longer-horizon ITT effect.
- Population: all registered assigned households, including no short-term viewing.
- Aggregation: binary household return indicator, equally weighted means by assigned arm.
- Numerator: households with a simulated service return during days 29-56 inclusive.
- Denominator: all assigned households per arm.
- Window: fixed days 29-56; infer only after full observation.
- Missingness: fully observed by construction; a real missingness/censoring process needs a new analysis plan, not dropping non-viewers.
- Direction: higher better; practical threshold +2 percentage points.
- Limitations: illustrative service-return target, not Netflix retention, subscription renewal, creative quality, or proof of a show's causal effect. Synthetic probabilities include latent affinity; oracle fields are audit-only, never model inputs.
- Inference: household Welch difference of proportions with two-sided 95% interval. Advance when the lower bound exceeds +2 pp; reject when upper bound is below zero; otherwise evidence insufficient to advance.