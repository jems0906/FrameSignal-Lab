import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_overlap_oracle_audit


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_overlap_oracle_audit.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    source_path = ROOT / "configs" / config["source_config"]
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    if source["study_id"] != config["source_study_id"]:
        raise ValueError("Oracle audit source study ID does not match the predeclared source config.")
    if not config["reuse_source_seed_grid"] or source["unmeasured_confounding"] != 0:
        raise ValueError("Oracle audit must replay the source seed grid with hidden confounding fixed at zero.")

    result = observational_overlap_oracle_audit(
        seed=source["seed"],
        n=source["households_per_replicate"],
        replicates=source["replicates_per_cell"],
        scenario=source["scenario"],
        overlap_profiles=tuple(source["overlap_profiles"]),
        nuisance_profiles=tuple(source["nuisance_profiles"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_cells"] != config["familywise_cells"] or not result["same_seed_replay"]:
        raise ValueError("Oracle audit did not reproduce the configured paired design.")
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
    report_path = ROOT / "reports" / "observational_overlap_oracle_audit.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Oracle Overlap Diagnostic Audit",
        "",
        "This is a paired, same-seed replay of the positivity/model-misspecification stress study. Oracle assignment probabilities are used only to audit fitted overlap diagnostics; they are never passed to AIPW. Oracle probabilities are unavailable in real observational data.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Source study: `{source['study_id']}`; source config SHA-256: `{output['source_config_sha256']}`. Seed: {source['seed']}; N={source['households_per_replicate']:,}; {source['replicates_per_cell']} paired replicates per cell.",
        "",
        "A false warning means the fitted-propensity overlap rule fails while the oracle-propensity rule passes. A missed warning means the fitted rule passes while the oracle rule fails. The paired fitted-minus-oracle intervals use Student-t Monte Carlo intervals; warning-rate intervals use exact Clopper-Pearson intervals. Both use Bonferroni familywise control across eight cells.",
        "",
        "## Results",
        "",
        "| Overlap | Nuisance profile | Fitted pass | Oracle pass | False warning (familywise MC interval) | Missed warning (familywise MC interval) | Outside-range difference, fitted - oracle (familywise MC interval) | Mean ESS fitted/oracle, control / treatment |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        false_lower, false_upper = row["false_warning_familywise_mc_interval"]
        missed_lower, missed_upper = row["missed_warning_familywise_mc_interval"]
        outside_lower, outside_upper = row["fitted_minus_oracle_outside_difference_familywise_mc_interval"]
        fitted_ess = row["mean_estimated_ess_by_arm"]
        oracle_ess = row["mean_oracle_ess_by_arm"]
        lines.append(
            f"| {row['overlap_profile']} | {row['nuisance_profile']} | "
            f"{100 * row['estimated_overlap_pass_rate']:.1f}% | {100 * row['oracle_overlap_pass_rate']:.1f}% | "
            f"{100 * row['false_warning_rate']:.1f}% [{100 * false_lower:.1f}, {100 * false_upper:.1f}]% | "
            f"{100 * row['missed_warning_rate']:.1f}% [{100 * missed_lower:.1f}, {100 * missed_upper:.1f}]% | "
            f"{100 * row['mean_fitted_minus_oracle_outside_difference']:+.1f} pp [{100 * outside_lower:+.1f}, {100 * outside_upper:+.1f}] pp | "
            f"{fitted_ess['0']:.0f}/{oracle_ess['0']:.0f} / {fitted_ess['1']:.0f}/{oracle_ess['1']:.0f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "This audit identifies disagreement between fitted and oracle overlap diagnostics for this known synthetic generator. It does not show that the oracle quantities are observable in practice, that the fitted diagnostic is generally calibrated, or that AIPW is identified. Estimator inputs and the source stress estimates are unchanged.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_overlap_oracle_audit_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "cells": len(result["rows"]),
        "replicates": source["replicates_per_cell"],
        "same_seed_replay": result["same_seed_replay"],
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()