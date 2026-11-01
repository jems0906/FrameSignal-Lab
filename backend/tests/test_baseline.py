import numpy as np
import pandas as pd

from app.analysis.inference import difference_in_means
from app.metrics.registry import household_metrics
from app.simulations.generator import simulate


def test_seed_reproducibility_and_population():
    first = simulate(n=400, seed=12)
    second = simulate(n=400, seed=12)
    pd.testing.assert_frame_equal(first.events, second.events)
    frame = household_metrics(first)
    assert len(frame) == 400
    assert (frame.qualified_starts == 0).any()
    assert frame.returned_d29_56.notna().all()
    assert frame.groupby("assignment").size().tolist() == [200, 200]
    assert frame.loc[~frame.starter, "completion"].isna().all()


def test_observational_simulation_is_explicit_and_retains_complete_population():
    data = simulate("misleading", n=1000, seed=51, assignment_mode="observational", unmeasured_confounding=0.5)
    frame = household_metrics(data)
    assert data.assignment_mode == "observational"
    assert len(frame) == 1000
    assert frame.returned_d29_56.notna().all()
    assert frame.assignment_probability_oracle.between(0, 1).all()
    assert {"observed_affinity", "observed_log_opportunity"}.issubset(frame.columns)
    assert "latent_loyalty" not in frame.columns
    assert frame.loc[~frame.starter, "completion"].isna().all()


def test_randomized_simulation_rejects_observational_sensitivity_argument():
    import pytest

    with pytest.raises(ValueError, match="applies only to observational"):
        simulate(n=100, seed=3, unmeasured_confounding=0.2)


def test_outcome_only_simulation_preserves_households_without_building_events():
    full = simulate("helpful", n=300, seed=401, assignment_mode="observational", unmeasured_confounding=0.5)
    outcome_only = simulate(
        "helpful", n=300, seed=401, assignment_mode="observational",
        unmeasured_confounding=0.5, generate_events=False,
    )
    pd.testing.assert_frame_equal(full.households, outcome_only.households)
    assert outcome_only.exposures.empty
    assert outcome_only.events.empty


def test_misleading_scenario_reverses_starts_decision():
    data = simulate("misleading", n=16000, seed=23)
    frame = household_metrics(data)
    control = frame[frame.assignment == 0]
    treatment = frame[frame.assignment == 1]
    starts = difference_in_means(control.qualified_starts, treatment.qualified_starts)
    target = difference_in_means(control.returned_d29_56, treatment.returned_d29_56)
    assert starts["lower"] > 0
    assert target["upper"] < 0
    assert target["lower"] < data.scenario.return_effect < target["upper"]


def test_difference_in_means_matches_manual_standard_error():
    control = np.array([0, 1, 0, 1, 0, 0])
    treatment = np.array([1, 1, 1, 0, 1, 0])
    result = difference_in_means(control, treatment)
    assert np.isclose(result["effect"], treatment.mean() - control.mean())
    assert np.isclose(result["se"], np.sqrt(control.var(ddof=1) / 6 + treatment.var(ddof=1) / 6))