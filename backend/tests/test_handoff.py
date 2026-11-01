import copy
import hashlib
import json
from pathlib import Path

import pytest
from framesignal_metrics.handoff import build_metricsteward_handoff, validate_educational_handoff


def evidence():
    raw = (Path(__file__).resolve().parents[2] / "reports" / "latest.json").read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def test_handoff_preserves_rejection_and_provenance():
    report, digest = evidence()
    handoff = build_metricsteward_handoff(report, digest)
    assert handoff["source_report_sha256"] == digest
    assert handoff["library"]["version"] == "1.0.0"
    assert handoff["integration_status"] == "handoff_prepared_not_imported"
    entries = {entry["metric_id"]: entry for entry in handoff["entries"]}
    for metric in ("qualified_starts", "viewing_days"):
        assert entries[metric]["surrogate_status"] == "rejected"
        assert not entries[metric]["agreement_screen_passed"]
        assert entries[metric]["harmful_oracle_reversals"]
    assert entries["completion"]["surrogate_status"] == "descriptive_only"
    assert all(entry["education_use_only"] and not entry["promotion_allowed"] for entry in entries.values())


@pytest.mark.parametrize("failure", ["leakage", "sql"])
def test_handoff_fails_closed_on_integrity(failure):
    report, digest = evidence()
    report = copy.deepcopy(report)
    if failure == "leakage":
        report["validation"]["leakage_check"] = False
    else:
        report["scenarios"]["helpful"]["sql"]["passed"] = False
    with pytest.raises(ValueError, match="failed split or data-integrity"):
        build_metricsteward_handoff(report, digest)


@pytest.mark.parametrize("tamper", [None, "approval", "wheel", "report"])
def test_consumer_verifies_handoff_and_never_promotes(tamper):
    report, _ = evidence()
    raw = json.dumps(report).encode()
    wheel = b"test-wheel-bytes"
    handoff = build_metricsteward_handoff(report, hashlib.sha256(raw).hexdigest())
    handoff["library"].update({"wheel_filename": "framesignal_metrics-1.0.0-py3-none-any.whl", "wheel_sha256": hashlib.sha256(wheel).hexdigest()})
    if tamper == "approval":
        handoff["entries"][0]["promotion_allowed"] = True
    elif tamper == "wheel":
        wheel = b"altered-wheel"
    elif tamper == "report":
        raw = json.dumps({**report, "altered": True}).encode()
    if tamper:
        with pytest.raises(ValueError, match="does not match"):
            validate_educational_handoff(handoff, raw, wheel)
    else:
        entries = validate_educational_handoff(handoff, raw, wheel)
        assert len(entries) == 5
        assert all(not entry["promotion_allowed"] for entry in entries)