import json
from pathlib import Path

import pandas as pd

from app.metrics.registry import household_metrics
from app.simulations.generator import SCENARIOS, Simulation


def test_hand_computable_metric_fixture():
    fixture = json.loads((Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "households.json").read_text())
    data = Simulation(pd.DataFrame(fixture["households"]), pd.DataFrame(), pd.DataFrame(fixture["exposures"]), pd.DataFrame(fixture["events"]), SCENARIOS["helpful"], 1, "fixture", "test")
    frame = household_metrics(data)
    assert frame.qualified_starts.tolist() == [0, 0, 2, 0]
    assert frame.viewing_days.tolist() == [0, 0, 1, 0]
    assert frame.watch_minutes.tolist() == [0, 1, 47, 0]
    assert frame.completion.isna().tolist() == [True, True, False, True]
    assert frame.completion.iloc[2] == 1
    assert frame.returned_d29_56.tolist() == [0, 1, 1, 0]