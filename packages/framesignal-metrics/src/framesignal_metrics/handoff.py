import hashlib
import json

from . import METRICS, __version__


def build_metricsteward_handoff(report: dict, report_sha256: str) -> dict:
    validation = report["validation"]
    if not validation["leakage_check"] or not all(row["sql"]["passed"] for row in report["scenarios"].values()):
        raise ValueError("Do not publish a handoff with failed split or data-integrity checks.")
    entries = []
    heldout = [row for row in validation["experiments"] if row["split"] == "heldout"]
    for metric, definition in METRICS.items():
        entry = {
            "metric_id": metric, "definition": dict(definition),
            "implementation_status": "educational_calculation_available",
            "approval_status": "not_approved_for_real_world_decisions",
            "education_use_only": True,
            "limitations": ["Synthetic household-randomized presentation-policy evidence only.",
                            "Not Netflix retention, an internal content metric, or an artistic-value score.",
                            "Self-review only; no external peer review or real-world validation."],
        }
        if metric in validation["frozen_candidates"]:
            agreement = validation["agreement"]["heldout"][metric]
            reversals = [row["id"] for row in heldout if row["truth_return_effect"] < 0 and row["effects"][metric]["effect"] > 0]
            lower = agreement["lower"]
            threshold = validation["plan"]["minimum_agreement_lower_bound"]
            entry.update({
                "surrogate_status": "rejected" if reversals else "insufficient_evidence",
                "heldout_agreement": agreement,
                "harmful_oracle_reversals": reversals,
                "agreement_screen_passed": lower > threshold,
                "required_agreement_lower_bound": threshold,
                "calibration_flags": report["operating"]["calibration_flags"],
                "promotion_allowed": False,
            })
        else:
            entry.update({"surrogate_status": "descriptive_only" if metric == "completion" else "primary_target" if metric == "returned_d29_56" else "not_evaluated_as_surrogate", "promotion_allowed": False})
        if metric == "completion":
            entry["limitations"].append("Conditions on post-assignment starters; not a clean all-household ITT causal comparison.")
        entries.append(entry)
    return {
        "schema_version": "1.0.0", "destination": "MetricSteward", "integration_status": "handoff_prepared_not_imported",
        "library": {"name": "framesignal-metrics", "version": __version__, "entrypoint": "framesignal_metrics.calculate_household_metrics"},
        "source_report_sha256": report_sha256, "source_plan_sha256": report["provenance"]["plan_sha256"],
        "source_seed": report["provenance"]["seed"], "entries": entries,
        "promotion_policy": "Import as educational definitions/evidence only. Real-world approval requires new scoped validation and actual review; importing this handoff cannot confer approval.",
    }


def validate_educational_handoff(handoff: dict, report_bytes: bytes, wheel_bytes: bytes) -> list:
    expected = build_metricsteward_handoff(json.loads(report_bytes), hashlib.sha256(report_bytes).hexdigest())
    expected["library"].update({
        "wheel_filename": f"framesignal_metrics-{__version__}-py3-none-any.whl",
        "wheel_sha256": hashlib.sha256(wheel_bytes).hexdigest(),
    })
    if handoff != expected:
        raise ValueError("Handoff evidence, library checksum, or educational approval status does not match.")
    return expected["entries"]