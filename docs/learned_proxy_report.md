# Learned Proxy Extension: Exploratory Follow-up

An educational follow-up after the frozen randomized baseline. This learned score is not a validated surrogate, is not approved for decisions, and does not change the frozen baseline or MetricSteward statuses.

Study: `framesignal-learned-proxy-v1`. Config SHA-256: `357e3e80020b6838dea8d9ebe283ae5230c408706563708b774a4f6da1fd0a44`. Seed: 528641.
54,000 disjoint households across 3 splits; 9 experiments per split, N=2,000 each.

## Frozen Learning Protocol

Features are qualified starts and viewing days only. Fit standardized ridge linear-probability weights on training households and their fully observed late-return outcomes. Means, scales, and coefficients are learned on training only. Tune ridge alpha by validation household Brier score (ties choose smaller alpha), then freeze before held-out households are generated. Assignment, late outcome at scoring time, affinity, oracle probabilities, and latent fields are not score features. No held-out labels enter fitting or tuning.

## Learned Model

Ridge alpha: 0.01. Intercept: 0.532611.

| Standardized feature | Frozen coefficient | Training mean | Training SD |
|---|---:|---:|---:|
| qualified_starts | -0.003277 | 2.453778 | 2.908164 |
| viewing_days | +0.020237 | 2.045722 | 1.992812 |

| Candidate alpha | Validation Brier score |
|---:|---:|
| 0.01 | 0.249053 |
| 0.1 | 0.249098 |
| 1.0 | 0.249206 |
| 10.0 | 0.249454 |

## Prediction (Household-Level)

| Split | Households | Brier score | Pooled correlation | Within-control correlation | Within-policy correlation |
|---|---:|---:|---:|---:|---:|
| train | 18,000 | 0.248633 | 0.035 | 0.025 | 0.041 |
| validation | 18,000 | 0.249053 | 0.047 | 0.051 | 0.044 |
| heldout | 18,000 | 0.249266 | 0.031 | 0.041 | 0.029 |

Household association is predictive description, not causal surrogacy; pooled association may reflect policy assignment and shared affinity.

## Held-Out Treatment-Effect Agreement

| Experiment | Scenario | Learned-score effect | Return effect | Known return effect |
|---|---|---:|---:|---:|
| learned-heldout-01 | helpful | +0.0079 [+0.0065, +0.0093] | +2.80 [-1.56, +7.16] pp | +3.60 pp |
| learned-heldout-02 | unrelated | +0.0081 [+0.0067, +0.0095] | -0.50 [-4.88, +3.88] pp | +0.00 pp |
| learned-heldout-03 | misleading | +0.0095 [+0.0081, +0.0109] | -5.60 [-9.98, -1.22] pp | -3.60 pp |
| learned-heldout-04 | helpful | +0.0083 [+0.0069, +0.0097] | +7.20 [+2.84, +11.56] pp | +6.00 pp |
| learned-heldout-05 | unrelated | +0.0115 [+0.0101, +0.0129] | +1.70 [-2.69, +6.09] pp | +0.00 pp |
| learned-heldout-06 | misleading | +0.0108 [+0.0094, +0.0123] | -7.00 [-11.37, -2.63] pp | -6.00 pp |
| learned-heldout-07 | helpful | +0.0108 [+0.0095, +0.0122] | +11.10 [+6.82, +15.38] pp | +8.40 pp |
| learned-heldout-08 | unrelated | +0.0140 [+0.0125, +0.0155] | -0.80 [-5.19, +3.59] pp | +0.00 pp |
| learned-heldout-09 | misleading | +0.0115 [+0.0100, +0.0130] | -13.20 [-17.55, -8.85] pp | -8.40 pp |

Observed held-out sign agreement: 44.4%; experiment-bootstrap interval [11.1%, 77.8%]; effect-noise sensitivity [22.2%, 77.8%].

These are nine constructed held-out experiments. Intervals condition on training/validation-frozen weights and omit weight-learning uncertainty. Experiment resampling and effect-noise sensitivity do not establish causal surrogacy. Results cannot override harmful reversals or directly measured return.

## Status and Limitations

Status: `exploratory_educational_only_not_surrogate_approval`. Weights are fitted from household prediction, not learned from a validated cross-experiment causal-surrogate objective. Latent affinity, limited experiment families, scenario support, and conditional weight uncertainty constrain conclusions. No real-world approval or peer review is claimed.
