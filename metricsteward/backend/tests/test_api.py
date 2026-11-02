import json
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.metrics.registry import household_metrics
from app.simulations.generator import simulate
from metricsteward.api import create_app


ROOT = Path(__file__).resolve().parents[3]


def client(tmp_path):
    return TestClient(create_app(tmp_path / "catalog.sqlite3", ROOT))


def test_real_artifact_import_and_review(tmp_path):
    api = client(tmp_path)
    assert api.get("/api/steward/metrics").json() == []
    imported = api.post("/api/steward/imports/framesignal")
    assert imported.status_code == 200
    import_id = imported.json()["import_id"]
    assert len(api.get("/api/steward/metrics").json()) == 5
    review = {"import_id": import_id, "reviewer": "Test self-reviewer", "review_kind": "self", "decision": "educational_accept", "notes": "Educational calculation parity is verified; no retention approval.", "attested": True}
    assert api.post("/api/steward/metrics/qualified_starts/reviews", json=review).status_code == 200
    detail = api.get(f"/api/steward/metrics/qualified_starts?import_id={import_id}").json()
    assert detail["surrogate_status"] == "rejected"
    assert not detail["promotion_allowed"]
    assert detail["reviews"][0]["review_kind"] == "self"
    assert api.post("/api/steward/metrics/qualified_starts/reviews", json={**review, "decision": "approve_real_world"}).status_code == 409
    export = api.get(f"/api/steward/exports/{import_id}")
    assert export.status_code == 200
    assert not export.json()["promotion_allowed"]
    assert not api.post("/api/steward/imports/framesignal").json()["created"]


@pytest.mark.parametrize("scenario", ["helpful", "unrelated", "misleading"])
@pytest.mark.parametrize("window", [7, 14])
def test_metricsteward_and_framesignal_calculation_parity(tmp_path, scenario, window):
    data = simulate(scenario, n=100, seed=31)
    payload = {name: json.loads(getattr(data, name).to_json(orient="records", double_precision=15)) for name in ("households", "events", "exposures")}
    response = client(tmp_path).post("/api/steward/calculate", json={**payload, "window": window})
    assert response.status_code == 200
    result = response.json()
    assert result["household_count"] == 100
    expected = household_metrics(data, window).set_index("household_id")
    for row in result["outcomes"]:
        household = expected.loc[row["household_id"]]
        for metric in ("qualified_starts", "viewing_days", "watch_minutes", "returned_d29_56", "impressions"):
            assert np.isclose(row[metric], household[metric], rtol=1e-12, atol=1e-12)
        assert row["completion"] == (float(household.completion) if household.starter else None)


def test_bad_evidence_and_missingness_fail_closed(tmp_path):
    api = TestClient(create_app(tmp_path / "catalog.sqlite3", tmp_path))
    assert api.post("/api/steward/imports/framesignal").status_code == 422
    assert api.get("/api/steward/imports").json() == []
    assert api.post("/api/steward/calculate", json={"households": [], "events": [], "exposures": []}).status_code == 422


def test_read_only_mode_preserves_catalog_and_rejects_writes(tmp_path):
    database_path = tmp_path / "catalog.sqlite3"
    writable = TestClient(create_app(database_path, ROOT))
    import_id = writable.post("/api/steward/imports/framesignal").json()["import_id"]
    review = {"import_id": import_id, "reviewer": "Private reviewer name", "review_kind": "self", "decision": "defer", "notes": "Private review notes remain preserved.", "evidence_reference": "private-reference", "attested": True}
    assert writable.post("/api/steward/metrics/qualified_starts/reviews", json=review).status_code == 200

    read_only = TestClient(create_app(database_path, ROOT, read_only=True))
    assert read_only.get("/api/steward/health").json()["read_only"] is True
    assert len(read_only.get(f"/api/steward/metrics?import_id={import_id}").json()) == 5
    reviews = read_only.get(f"/api/steward/reviews?import_id={import_id}").json()
    assert len(reviews) == 1
    assert reviews[0]["reviewer"] == "Withheld"
    assert "Private" not in reviews[0]["notes"]
    assert reviews[0]["evidence_reference"] == ""
    detail = read_only.get(f"/api/steward/metrics/qualified_starts?import_id={import_id}").json()
    assert detail["reviews"] == reviews
    assert read_only.get(f"/api/steward/exports/{import_id}").status_code == 403
    assert read_only.post("/api/steward/imports/framesignal").status_code == 403
    assert read_only.post("/api/steward/metrics/qualified_starts/reviews", json=review).status_code == 403
    assert len(read_only.get(f"/api/steward/reviews?import_id={import_id}").json()) == 1