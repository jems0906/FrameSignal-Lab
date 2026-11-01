# framesignal-metrics

An installable, simulation-independent Python library for shared household-level educational metric calculations. FrameSignal's API and notebooks use this implementation; MetricSteward can consume the same versioned wheel rather than duplicating formulas.

## API

```python
from framesignal_metrics import calculate_household_metrics

outcomes = calculate_household_metrics(households, events, exposures, window=14)
```

Inputs are pandas DataFrames. `households` contains unique, observed `household_id` values for the complete registered population; other household fields, including assignment and the fully observed target, are preserved. `events` contains `household_id`, `day`, `minutes`, `qualified`, and `completed`. `exposures` contains one observed `household_id` / `impressions` row per registered household, including explicit zeros.

Producer contract: `qualified` means at least 2 watched minutes; `completed` means at least 90% of the title runtime within one event. These upstream event flags must be observed booleans, not strings. The library validates IDs, linkage, missingness, finite nonnegative numeric values, and boolean flags; title availability/runtime consistency is additionally audited by FrameSignal's SQL checks. A consumer must not replace absent logs with fabricated zeros or invent completion flags.

Outputs count qualified starts, distinct qualified days, all watched minutes, and any-completion among starter households. Every registered household is retained. No viewing is zero for ITT viewing metrics, but completion is undefined for non-starters. Supported short windows are days 0-6 or 0-13. An empty event table is valid; missing exposure records are not silently treated as observed zero exposure.

## Educational Handoff

`framesignal_metrics.handoff.build_metricsteward_handoff` constructs an educational-only catalog from the frozen research evidence. `validate_educational_handoff` verifies that entries, evidence checksums, and wheel checksum match the supplied artifacts; tampered approval flags are rejected.

This is consistency checking, not cryptographic authorship authentication or causal validation. All imported entries retain `promotion_allowed=false`. Starts/viewing-day counterexamples remain rejected as universal surrogates; completion remains descriptive, and calibration flags remain visible. No internal Netflix metric, real retention, title-quality, or artistic-value claim is authorized.