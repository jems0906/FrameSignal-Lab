import numpy as np
import pytest

from app.analysis.observational import (
    estimate_observational_effect,
    _aipw_effect,
    observational_replicated_sensitivity,
    observational_robustness_stress,
    observational_sensitivity,
)
from app.metrics.registry import household_metrics
from app.simulations.generator import SCENARIOS, simulate


def test_observational_aipw_reports_overlap_and_household_uncertainty():
    data = simulate("helpful", n=1200, seed=301, assignment_mode="observational", unmeasured_confounding=0)
    result = estimate_observational_effect(household_metrics(data), seed=302, draws=40)
    assert result["lower"] <= result["effect"] <= result["upper"]
    assert result["bootstrap_draws_used"] >= 36
    assert 0 <= result["overlap"]["fraction_inside_common_support"] <= 1
    assert result["overlap"]["ipw_effective_sample_size"] > 0
    assert "Conditional exchangeability" in result["assumptions"][1]
    assert "not interchangeable with randomized ITT" in result["warning"]


def test_observational_estimator_does_not_use_oracle_or_latent_fields():
    data = simulate("misleading", n=600, seed=303, assignment_mode="observational", unmeasured_confounding=0.75)
    frame = household_metrics(data)
    altered = frame.copy()
    altered["assignment_probability_oracle"] = 1 - altered.assignment_probability_oracle
    altered["unmeasured_confounding_strength_oracle"] = 0
    altered["return_probability"] = altered.return_probability.sample(frac=1, random_state=4).to_numpy()
    altered["latent_loyalty_oracle"] = altered.latent_loyalty_oracle.sample(frac=1, random_state=5).to_numpy()
    baseline = estimate_observational_effect(frame, seed=305, draws=30)
    comparison = estimate_observational_effect(altered, seed=305, draws=30)
    assert baseline["effect"] == comparison["effect"]
    assert baseline["lower"] == comparison["lower"]
    assert baseline["upper"] == comparison["upper"]


def test_hidden_confounding_strength_changes_both_generator_mechanisms():
    unconfounded = simulate("helpful", n=1200, seed=306, assignment_mode="observational", unmeasured_confounding=0)
    confounded = simulate("helpful", n=1200, seed=306, assignment_mode="observational", unmeasured_confounding=1)
    baseline_households = unconfounded.households
    confounded_households = confounded.households
    latent = confounded_households.latent_loyalty_oracle.to_numpy()
    measured_logit = (
        -0.3
        + 2 * (confounded_households.observed_affinity.to_numpy() - 0.5)
        + 0.25 * confounded_households.observed_log_opportunity.to_numpy()
    )
    np.testing.assert_allclose(
        baseline_households.assignment_probability_oracle,
        1 / (1 + np.exp(-measured_logit)),
    )
    np.testing.assert_allclose(
        confounded_households.assignment_probability_oracle,
        1 / (1 + np.exp(-(measured_logit + 0.8 * latent))),
    )
    np.testing.assert_allclose(
        baseline_households.return_probability,
        0.40 + 0.25 * baseline_households.affinity + baseline_households.assignment * unconfounded.scenario.return_effect,
    )
    np.testing.assert_allclose(
        confounded_households.return_probability,
        0.40 + 0.25 * confounded_households.affinity + confounded_households.assignment * confounded.scenario.return_effect + 0.04 * latent,
    )


def test_observational_sensitivity_covers_all_scenarios_and_confounding_levels():
    result = observational_sensitivity(seed=307, n=300, draws=20)
    assert len(result["rows"]) == 9
    assert {row["scenario"] for row in result["rows"]} == {"helpful", "unrelated", "misleading"}
    assert {row["unmeasured_confounding_strength"] for row in result["rows"]} == {0.0, 0.5, 1.0}
    assert result["status"] == "exploratory_not_randomized_itt"
    assert "assignment_probability_oracle" in result["forbidden_estimator_inputs"]


def test_replicated_sensitivity_reports_bias_coverage_and_familywise_mc_intervals():
    result = observational_replicated_sensitivity(
        seed=308, n=300, replicates=30, scenarios=("helpful",), confounding_grid=(0.0, 1.0),
    )
    assert len(result["rows"]) == 2
    assert result["number_of_cells"] == 2
    assert result["status"] == "exploratory_replicated_synthetic_sensitivity_not_randomized_itt"
    for row in result["rows"]:
        bias_interval = row["aipw_bias_familywise_mc_interval"]
        coverage_interval = row["aipw_wald_coverage_familywise_mc_interval"]
        assert bias_interval[0] <= row["mean_aipw_bias"] <= bias_interval[1]
        assert 0 <= coverage_interval[0] <= row["aipw_wald_interval_coverage"] <= coverage_interval[1] <= 1
        assert 0 <= row["overlap_check_pass_rate"] <= 1
        assert row["mean_ipw_effective_sample_size_by_arm"]["0"] > 0


def test_stress_generator_varies_overlap_and_nuisance_models_independently():
    baseline = simulate(
        "helpful", n=1000, seed=313, assignment_mode="observational", generate_events=False,
    ).households
    weak_overlap = simulate(
        "helpful", n=1000, seed=313, assignment_mode="observational", generate_events=False,
        measured_selection_strength=3,
    ).households
    propensity_misspecified = simulate(
        "helpful", n=1000, seed=313, assignment_mode="observational", generate_events=False,
        propensity_nonlinearity=2,
    ).households
    outcome_misspecified = simulate(
        "helpful", n=1000, seed=313, assignment_mode="observational", generate_events=False,
        outcome_nonlinearity=0.3,
    ).households

    assert baseline.unmeasured_confounding_strength_oracle.eq(0).all()
    assert weak_overlap.assignment_probability_oracle.min() < baseline.assignment_probability_oracle.min()
    assert weak_overlap.assignment_probability_oracle.max() > baseline.assignment_probability_oracle.max()
    assert not np.allclose(propensity_misspecified.assignment_probability_oracle, baseline.assignment_probability_oracle)
    np.testing.assert_allclose(
        propensity_misspecified.return_probability
        - propensity_misspecified.assignment * SCENARIOS["helpful"].return_effect,
        baseline.return_probability - baseline.assignment * SCENARIOS["helpful"].return_effect,
    )
    np.testing.assert_allclose(outcome_misspecified.assignment_probability_oracle, baseline.assignment_probability_oracle)
    outcome_shift = outcome_misspecified.return_probability - baseline.return_probability
    np.testing.assert_allclose(
        outcome_shift,
        0.3 * (np.square(baseline.affinity - 0.5) - 0.05),
    )
    for data, nonlinearity in (
        (baseline, 0.0),
        (weak_overlap, 0.0),
        (propensity_misspecified, 0.0),
        (outcome_misspecified, 0.3),
    ):
        expected = (
            0.40 + 0.25 * data.affinity
            + data.assignment * SCENARIOS["helpful"].return_effect
            + nonlinearity * (np.square(data.affinity - 0.5) - 0.05)
        )
        np.testing.assert_allclose(data.return_probability, expected)

    altered_oracles = baseline.copy()
    for column in (
        "assignment_probability_oracle", "latent_loyalty_oracle",
        "measured_selection_strength_oracle", "propensity_nonlinearity_oracle",
        "outcome_nonlinearity_oracle", "return_probability",
    ):
        altered_oracles[column] = np.random.default_rng(314).permutation(altered_oracles[column].to_numpy())
    assert _aipw_effect(baseline) == _aipw_effect(altered_oracles)


def test_robustness_stress_emits_all_eight_factorial_cells():
    result = observational_robustness_stress(seed=711, n=300, replicates=30)
    assert result["number_of_cells"] == 8
    assert result["unmeasured_confounding"] == 0
    assert "propensity_nonlinearity_oracle" in result["forbidden_estimator_inputs"]
    assert result["status"] == "exploratory_synthetic_positivity_and_model_robustness_stress_not_randomized_itt"
    assert {row["overlap_profile"] for row in result["rows"]} == {"moderate", "weak"}
    assert {row["nuisance_profile"] for row in result["rows"]} == {
        "correct_both", "propensity_misspecified", "outcome_misspecified", "both_misspecified",
    }
    for row in result["rows"]:
        lower, upper = row["aipw_bias_familywise_mc_interval"]
        assert lower <= row["mean_aipw_bias"] <= upper
        coverage_lower, coverage_upper = row["aipw_wald_coverage_familywise_mc_interval"]
        assert 0 <= coverage_lower <= row["aipw_wald_interval_coverage"] <= coverage_upper <= 1
        assert row["overlap_check_pass_rate"] in (0, 1) or 0 < row["overlap_check_pass_rate"] < 1


def test_observational_estimator_requires_both_assignment_groups():
    data = simulate("helpful", n=200, seed=309, assignment_mode="observational")
    frame = household_metrics(data)
    frame["assignment"] = 1
    with pytest.raises(ValueError, match="Both observed assignment groups"):
        estimate_observational_effect(frame, seed=1, draws=20)
