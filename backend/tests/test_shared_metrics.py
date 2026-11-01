import io
import zipfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from framesignal_metrics import calculate_household_metrics

from app.api.main import app
from app.metrics.registry import household_metrics
from app.simulations.generator import simulate


@pytest.mark.parametrize("scenario", ["helpful", "unrelated", "misleading"])
@pytest.mark.parametrize("window", [7, 14])
def test_shared_calculator_preserves_frame_signal_contract(scenario, window):
    data = simulate(scenario, n=200, seed=21)
    shared = calculate_household_metrics(data.households, data.events, data.exposures, window)
    pd.testing.assert_frame_equal(shared, household_metrics(data, window), check_exact=True)
    assert len(shared) == len(data.households)
    assert shared.loc[~shared.starter, "completion"].isna().all()


def test_dashboard_export_matches_independent_library_consumer():
    response = TestClient(app).get("/api/export?scenario=misleading&n=200&seed=21")
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        frames = {name: pd.read_csv(archive.open(f"{name}.csv")) for name in ("households", "events", "exposures", "household_metrics")}
    calculated = calculate_household_metrics(frames["households"], frames["events"], frames["exposures"])
    pd.testing.assert_frame_equal(calculated, frames["household_metrics"], check_exact=False, rtol=1e-12, atol=1e-12)


@pytest.mark.parametrize("failure", ["duplicate", "orphan", "missing_exposure", "missing_minutes", "negative_day", "string_flag"])
def test_shared_library_rejects_ambiguous_input(failure):
    data = simulate(n=100, seed=21)
    if failure == "duplicate":
        data.households.loc[1, "household_id"] = data.households.loc[0, "household_id"]
    elif failure == "orphan":
        data.events.loc[0, "household_id"] = "unknown"
    elif failure == "missing_exposure":
        data.exposures = data.exposures.iloc[1:]
    elif failure == "missing_minutes":
        data.events.loc[0, "minutes"] = float("nan")
    elif failure == "negative_day":
        data.events.loc[0, "day"] = -1
    else:
        data.events["qualified"] = data.events.qualified.astype(object)
        data.events.loc[0, "qualified"] = "False"
    with pytest.raises(ValueError):
        calculate_household_metrics(data.households, data.events, data.exposures)


def test_shared_library_retains_population_when_event_table_is_empty():
    data = simulate(n=100, seed=21)
    empty_events = pd.DataFrame(columns=data.events.columns)
    result = calculate_household_metrics(data.households, empty_events, data.exposures)
    assert len(result) == 100
    assert result[["qualified_starts", "viewing_days", "watch_minutes"]].to_numpy().sum() == 0
    assert result.completion.isna().all()