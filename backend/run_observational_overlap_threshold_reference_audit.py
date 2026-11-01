import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_overlap_threshold_reference_audit


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_overlap_threshold_reference_audit.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    source_path = ROOT / "configs" / config["source_config"]
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    if source["study_id"] != config["source_study_id"]:
        raise ValueError("Threshold audit source study ID does not match the predeclared source config.")
    if source["unmeasured_confounding"] != config["unmeasured_confounding"]:
        raise ValueError("The fixed-reference threshold audit must keep hidden confounding at zero.")

    result = observational_overlap_threshold_reference_audit(
        seed=config["seed"],
        n=config["households_per_replicate"],
        replicates=config["replicates_per_profile_cell"],
        folds=config["cross_fitting_folds"],
        scenario=source["scenario"],
        overlap_profiles=tuple(source["overlap_profiles"]),
        nuisance_profiles=tuple(source["nuisance_profiles"]),
        threshold_rules=tuple(source["threshold_rules"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_profile_cells"] != config["profile_cells"]:
        raise ValueError("Threshold audit profile count does not match the frozen source grid.")
    if result["number_of_threshold_rules"] != config["threshold_rules"]:
        raise ValueError("Threshold audit candidate count does not match the frozen source grid.")
    if result["number_of_familywise_cells"] != config["familywise_cells"]:
        raise ValueError("Threshold audit familywise cell count does not match the frozen design.")
    if result["oracle_reference_rule"] != config["oracle_reference_rule"]:
        raise ValueError("Oracle reference rule does not match the predeclared criterion.")
    oracle_rates_by_profile = {}
    for row in result["rows"]:
        profile = (row["overlap_profile"], row["nuisance_profile"])
        oracle_rates_by_profile.setdefault(profile, set()).add(row["oracle_pass_rate"])
    if len(oracle_rates_by_profile) != config["profile_cells"] or any(
        len(rates) != 1 for rates in oracle_rates_by_profile.values()
    ):
        raise ValueError("Oracle reference pass rate should be constant across candidate rules within each profile.")

    output = {
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_config_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "runtime": {
            "python": __import__("platform").python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "framesignal_metrics": metrics_version,
        },
        "results": result,
        "review_status": "Self-review only; no independent peer review has occurred.",
    }
    report_path = ROOT / "reports" / "observational_overlap_threshold_reference_audit.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Fixed-Reference Threshold Audit",
        "",
        "This fresh-seed study compares six candidate warning rules against one fixed oracle adequacy reference. Unlike the prior threshold stress study, the oracle label does not change with the candidate rule. The fixed reference is a synthetic convention, not a production recommendation.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Source threshold grid: `{source['study_id']}`. Seed: {config['seed']}; N={config['households_per_replicate']:,}; {config['replicates_per_profile_cell']} replicates × {config['profile_cells']} profiles; {config['cross_fitting_folds']} cross-fitting folds.",
        "",
        f"Fixed oracle reference: propensity range {config['oracle_reference_rule']['propensity_range'][0]:.2f}-{config['oracle_reference_rule']['propensity_range'][1]:.2f}, per-arm ESS >= {config['oracle_reference_rule']['minimum_effective_sample_size']}. Hidden confounding remains zero. Oracle values are diagnostic-only.",
        "",
        "## Balanced Profile Summaries",
        "",
        "| Candidate rule | Range | ESS floor | Fixed oracle pass | In-sample pass | Cross-fit pass | In-sample false warning | Cross-fit false warning | In-sample missed warning | Cross-fit missed warning |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["threshold_summaries"]:
        lines.append(
            f"| {row['threshold_rule']} | {row['propensity_range'][0]:.2f}-{row['propensity_range'][1]:.2f} | "
            f"{row['minimum_effective_sample_size']} | {100 * row['oracle']['pass_rate']:.1f}% | "
            f"{100 * row['in_sample']['pass_rate']:.1f}% | {100 * row['crossfit']['pass_rate']:.1f}% | "
            f"{100 * row['in_sample']['false_warning_rate']:.1f}% | {100 * row['crossfit']['false_warning_rate']:.1f}% | "
            f"{100 * row['in_sample']['missed_warning_rate']:.1f}% | {100 * row['crossfit']['missed_warning_rate']:.1f}% |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "This fixed-reference view makes candidate warning errors comparable within each generator profile. It does not choose a threshold: false-warning and missed-warning costs are unspecified, and the oracle adequacy convention exists only in this simulated study. Detailed familywise intervals for every profile-rule cell are in the JSON report.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_overlap_threshold_reference_audit_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "profile_cells": result["number_of_profile_cells"],
        "threshold_rules": result["number_of_threshold_rules"],
        "familywise_cells": result["number_of_familywise_cells"],
        "same_threshold_grid": True,
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()