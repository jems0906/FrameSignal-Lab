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