import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from framesignal_metrics.handoff import build_metricsteward_handoff

from metricsteward.store import CatalogStore


@pytest.fixture
def artifacts():
    report = (Path(__file__).resolve().parents[3] / "reports" / "latest.json").read_bytes()
    wheel = b"known-test-artifact"
    handoff = build_metricsteward_handoff(json.loads(report), hashlib.sha256(report).hexdigest())
    handoff["library"].update({"wheel_filename": "framesignal_metrics-1.0.0-py3-none-any.whl", "wheel_sha256": hashlib.sha256(wheel).hexdigest()})
    return handoff, report, wheel


def test_import_is_validated_and_reimport_preserves_reviews(tmp_path, artifacts):
    store = CatalogStore(tmp_path / "catalog.sqlite3")
    imported = store.import_evidence(*artifacts)
    assert imported["created"]
    assert len(store.list_metrics()) == 5
    store.record_review(imported["import_id"], "qualified_starts", "Local reviewer", "self", "educational_accept", "The counterexample is suitable for education, not approval.", attested=True)
    second = CatalogStore(tmp_path / "catalog.sqlite3")
    assert not second.import_evidence(*artifacts)["created"]
    metric = second.get_metric(imported["import_id"], "qualified_starts")
    assert metric["surrogate_status"] == "rejected"
    assert metric["review_status"] == "educational_accept"
    assert len(metric["reviews"]) == 1
    assert not metric["promotion_allowed"]


def test_tampered_handoff_has_no_partial_import(tmp_path, artifacts):
    store = CatalogStore(tmp_path / "catalog.sqlite3")
    handoff, report, wheel = artifacts
    handoff["entries"][0]["promotion_allowed"] = True
    with pytest.raises(ValueError, match="does not match"):
        store.import_evidence(handoff, report, wheel)
    assert store.list_imports() == []


def test_review_cannot_confer_real_world_approval(tmp_path, artifacts):
    store = CatalogStore(tmp_path / "catalog.sqlite3")
    imported = store.import_evidence(*artifacts)
    with pytest.raises(ValueError, match="approval is blocked"):
        store.record_review(imported["import_id"], "qualified_starts", "Reviewer", "self", "approve_real_world", "Approve", attested=True)
    with pytest.raises(ValueError, match="feedback reference"):
        store.record_review(imported["import_id"], "qualified_starts", "Reviewer", "reported_peer", "defer", "Feedback", attested=True)
    assert store.list_reviews(imported["import_id"]) == []


def test_concurrent_identical_imports_create_one_catalog_version(tmp_path, artifacts):
    store = CatalogStore(tmp_path / "catalog.sqlite3")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: store.import_evidence(*artifacts), range(2)))
    assert sum(result["created"] for result in results) == 1
    assert len(store.list_imports()) == 1
    assert len(store.list_metrics()) == 5