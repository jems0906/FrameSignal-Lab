import numpy as np
import pytest

from app.analysis.observational import estimate_observational_effect, observational_sensitivity
from app.metrics.registry import household_metrics
from app.simulations.generator import simulate


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


def test_observational_estimator_requires_both_assignment_groups():
    data = simulate("helpful", n=200, seed=309, assignment_mode="observational")
    frame = household_metrics(data)
    frame["assignment"] = 1
    with pytest.raises(ValueError, match="Both observed assignment groups"):
        estimate_observational_effect(frame, seed=1, draws=20)
