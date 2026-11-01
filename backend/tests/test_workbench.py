import json
from pathlib import Path

import numpy as np
from scipy import stats
from fastapi.testclient import TestClient

from app.analysis.inference import completion_comparison
from app.analysis.workbench import PLAN, agreement_uncertainty, analyze, operating_characteristics, proportion_interval, sql_audit
from app.api.main import app
from app.metrics.registry import household_metrics
from app.simulations.generator import SCENARIOS, simulate


def test_sql_population_and_availability():
    data = simulate("unrelated", n=300, seed=11)
    result = sql_audit(data)
    assert result["passed"]
    assert result["counts"]["registered_households"] == result["counts"]["itt_left_join_count"] == 300
    assert result["counts"]["households_without_viewing"] > 0


def test_configs_match_registered_truth():
    root = Path(__file__).resolve().parents[2]
    for name, scenario in SCENARIOS.items():
        config = json.loads((root / "configs" / "scenarios" / f"{name}.json").read_text())
        assert config == scenario.__dict__
    assert PLAN["candidate_alpha"] * 2 == PLAN["familywise_alpha"]


def test_completion_resamples_households_and_labels_selection():
    frame = household_metrics(simulate(n=300, seed=22))
    result = completion_comparison(frame, 22, draws=100)
    assert result["n_control"] + result["n_treatment"] == 300
    assert "not an ITT" in result["warning"]
    assert result["p_value"] is None
    assert result["lower"] <= result["upper"]


def test_independent_household_populations_and_seeds():
    first = simulate(n=100, seed=1, split="train", experiment_id="train-01")
    second = simulate(n=100, seed=2, split="heldout", experiment_id="heldout-01")
    assert set(first.households.household_id).isdisjoint(second.households.household_id)
    assert not np.array_equal(first.households.affinity, second.households.affinity)


def test_diagnostics_and_api_contract():
    result = analyze("misleading", 300, 33)
    assert result["sql"]["passed"]
    assert len(result["diagnostics"]["rows"]) == 9
    assert result["metrics"]["qualified_starts"]["alpha"] == 0.025
    assert result["metrics"]["completion"]["causal"] is False
    client = TestClient(app)
    assert client.get("/api/health").json()["synthetic_only"]
    assert client.get("/api/analysis?scenario=invalid").status_code == 422
    assert client.get("/api/analysis?n=99").status_code == 422
    assert client.get("/api/analysis?scenario=misleading&n=300&seed=33").status_code == 200
    assert client.get("/api/export?n=100&seed=1").content[:2] == b"PK"


def test_operating_characteristics_known_truth():
    result = operating_characteristics(seed=12, repetitions=300, n=1000)
    null, largest = result["rows"][0], result["rows"][-1]
    assert 0.85 < null["coverage"]["rate"] <= 1
    assert null["rejection_rate"]["rate"] < 0.12
    assert abs(null["bias"]) < 0.01
    assert largest["rejection_rate"]["rate"] > null["rejection_rate"]["rate"] + 0.6
    assert isinstance(result["calibration_flags"], list)
    assert result == operating_characteristics(seed=12, repetitions=300, n=1000)


def test_calibration_followup_is_separate_and_predeclared():
    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "configs" / "analysis_plan.json").read_text())
    followup = json.loads((root / "configs" / "calibration_followup.json").read_text())
    assert followup["seed"] != baseline["seed"]
    assert followup["seed"] != followup["baseline_seed"]
    assert followup["households_per_repetition"] == baseline["households_per_experiment"]
    assert followup["repetitions_per_effect"] > baseline["operating_repetitions"]
    assert followup["effect_grid"] == [0.0, 0.02, 0.04, 0.06, 0.10]
    assert followup["primary_effect"] == 0.04
    assert followup["primary_interval"].startswith("Two-sided Welch household difference-in-means")
    assert followup["decision_rule"]["otherwise"].startswith("Monte Carlo interval includes nominal")
    assert followup["prohibited_changes"][2].startswith("Do not modify")


def test_simultaneous_calibration_grid_protocol_uses_bonferroni():
    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "configs" / "analysis_plan.json").read_text())
    first = json.loads((root / "configs" / "calibration_followup.json").read_text())
    followup = json.loads((root / "configs" / "calibration_grid_followup.json").read_text())
    assert followup["seed"] not in (baseline["seed"], first["seed"])
    assert followup["effect_grid"] == [0.0, 0.02, 0.04, 0.06, 0.10]
    assert followup["per_effect_confidence_level"] == 0.99
    assert followup["familywise_confidence_level"] == 0.95
    assert followup["multiplicity"].startswith("Nominal Bonferroni")
    assert "approximate" in followup["multiplicity"]


def test_monte_carlo_wilson_interval_confidence_level():
    standard = proportion_interval(950, 1000)
    simultaneous = proportion_interval(950, 1000, confidence_level=0.99)
    assert simultaneous["lower"] < standard["lower"]
    assert simultaneous["upper"] > standard["upper"]


def test_exact_monte_carlo_interval_is_conservative_and_method_is_validated():
    exact = proportion_interval(950, 1000, confidence_level=0.99, method="exact")
    expected = stats.binomtest(950, 1000).proportion_ci(confidence_level=0.99, method="exact")
    assert exact["lower"] == expected.low
    assert exact["upper"] == expected.high
    assert exact["lower"] <= 0.95 <= exact["upper"]
    import pytest
    with pytest.raises(ValueError, match="method must be wilson or exact"):
        proportion_interval(950, 1000, method="invalid")


def test_exact_followup_protocol_is_fresh_and_uses_exact_intervals():
    root = Path(__file__).resolve().parents[2]
    baseline = json.loads((root / "configs" / "analysis_plan.json").read_text())
    followup = json.loads((root / "configs" / "calibration_followup.json").read_text())
    grid = json.loads((root / "configs" / "calibration_grid_followup.json").read_text())
    exact = json.loads((root / "configs" / "calibration_exact_followup.json").read_text())
    assert exact["seed"] not in (baseline["seed"], followup["seed"], grid["seed"])
    assert exact["effect_grid"] == grid["effect_grid"]
    assert exact["repetitions_per_effect"] == 10000
    assert exact["per_effect_confidence_level"] == 0.99
    assert "Clopper-Pearson exact" in exact["monte_carlo_interval_method"]
    assert exact["prohibited_changes"][2].startswith("Do not describe these exact Monte Carlo intervals")


def test_noisy_agreement_includes_experiment_uncertainty():
    rows = [{"effects": {"qualified_starts": {"effect": 0.2, "se": 0.1, "lower": 0.01}, "returned_d29_56": {"effect": -0.03, "se": 0.04, "lower": -0.11, "upper": 0.05}}, "effect_covariance": {"qualified_starts": [[0.01, 0], [0, 0.0016]]}, "truth_return_effect": -0.03} for _ in range(9)]
    result = agreement_uncertainty(rows, "qualified_starts", seed=2, draws=100)
    assert result["observed_agreement"] == 0
    assert result["noise_upper"] > 0
    assert result["oracle_nonnull_agreement"] == 0


def test_extension_report_endpoints_are_explicitly_exploratory():
    client = TestClient(app)
    observational = client.get("/api/observational")
    replication = client.get("/api/observational-replication")
    robustness = client.get("/api/observational-robustness")
    oracle_audit = client.get("/api/observational-overlap-audit")
    crossfit_audit = client.get("/api/observational-crossfit-audit")
    threshold_stress = client.get("/api/observational-threshold-stress")
    threshold_reference = client.get("/api/observational-threshold-reference-audit")
    learned = client.get("/api/learned-proxy")
    assert observational.status_code == 200
    assert replication.status_code == 200
    assert robustness.status_code == 200
    assert oracle_audit.status_code == 200
    assert crossfit_audit.status_code == 200
    assert threshold_stress.status_code == 200
    assert threshold_reference.status_code == 200
    assert learned.status_code == 200
    assert observational.json()["results"]["status"] == "exploratory_not_randomized_itt"
    assert replication.json()["results"]["status"] == "exploratory_replicated_synthetic_sensitivity_not_randomized_itt"
    assert replication.json()["results"]["replicates_per_cell"] == 200
    assert robustness.json()["results"]["status"] == "exploratory_synthetic_positivity_and_model_robustness_stress_not_randomized_itt"
    assert robustness.json()["results"]["unmeasured_confounding"] == 0
    assert robustness.json()["results"]["number_of_cells"] == 8
    assert "propensity_nonlinearity_oracle" in robustness.json()["results"]["forbidden_estimator_inputs"]
    assert oracle_audit.json()["results"]["same_seed_replay"]
    assert oracle_audit.json()["results"]["oracle_usage"].startswith("Diagnostic comparison only")
    assert oracle_audit.json()["results"]["status"] == "exploratory_oracle_overlap_diagnostic_audit_not_randomized_itt"
    assert crossfit_audit.json()["results"]["same_seed_replay"]
    assert crossfit_audit.json()["results"]["cross_fitting_folds"] == 5
    assert "no cross-fitted AIPW effect" in crossfit_audit.json()["results"]["audit_scope"]
    assert threshold_stress.json()["results"]["number_of_threshold_rules"] == 6
    assert threshold_stress.json()["results"]["number_of_familywise_cells"] == 48
    assert len(threshold_stress.json()["results"]["threshold_summaries"]) == 6
    assert threshold_stress.json()["results"]["unmeasured_confounding"] == 0
    assert threshold_stress.json()["results"]["status"] == "exploratory_synthetic_overlap_threshold_operating_study_not_randomized_itt"
    assert threshold_reference.json()["results"]["status"] == "exploratory_synthetic_overlap_threshold_fixed_reference_audit_not_randomized_itt"
    assert threshold_reference.json()["results"]["oracle_reference_rule"]["name"] == "fixed_reference_05_95_ess50"
    assert threshold_reference.json()["results"]["status"] == "exploratory_synthetic_overlap_threshold_fixed_reference_audit_not_randomized_itt"
    assert threshold_reference.json()["results"]["oracle_reference_rule"]["name"] == "fixed_reference_05_95_ess50"
    assert len(threshold_reference.json()["results"]["threshold_summaries"]) == 6
    assert crossfit_audit.json()["results"]["same_seed_replay"]
    assert crossfit_audit.json()["results"]["cross_fitting_folds"] == 5
    assert "no cross-fitted AIPW effect" in crossfit_audit.json()["results"]["audit_scope"]
    assert learned.json()["results"]["status"] == "exploratory_educational_only_not_surrogate_approval"
    assert learned.json()["results"]["weight_freeze_before_heldout"]