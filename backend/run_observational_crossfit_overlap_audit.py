import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_crossfit_overlap_audit


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_crossfit_overlap_audit.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    source_path = ROOT / "configs" / config["source_config"]
    source_bytes = source_path.read_bytes()
    source = json.loads(source_bytes)
    if source["study_id"] != config["source_study_id"]:
        raise ValueError("Cross-fit audit source study ID does not match the predeclared source config.")
    if not config["reuse_source_seed_grid"] or source["unmeasured_confounding"] != 0:
        raise ValueError("Cross-fit audit must replay the source seed grid with hidden confounding fixed at zero.")

    result = observational_crossfit_overlap_audit(
        seed=source["seed"],
        n=source["households_per_replicate"],
        replicates=source["replicates_per_cell"],
        folds=config["cross_fitting_folds"],
        scenario=source["scenario"],
        overlap_profiles=tuple(source["overlap_profiles"]),
        nuisance_profiles=tuple(source["nuisance_profiles"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_cells"] != config["familywise_cells"] or not result["same_seed_replay"]:
        raise ValueError("Cross-fit audit did not reproduce the configured paired design.")
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
    report_path = ROOT / "reports" / "observational_crossfit_overlap_audit.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Cross-Fitted Overlap Diagnostic Audit",
        "",
        "This is a paired, same-seed replay of the positivity/model-misspecification stress study. Cross-fitted propensity predictions are used only for overlap diagnostics; this report does not estimate a cross-fitted AIPW effect. Oracle assignment probabilities are diagnostic-only and never enter propensity fitting.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Source study: `{source['study_id']}`; source config SHA-256: `{output['source_config_sha256']}`. Seed: {source['seed']}; N={source['households_per_replicate']:,}; {source['replicates_per_cell']} paired replicates per cell; {config['cross_fitting_folds']} folds.",
        "",
        "False warning means the fitted or cross-fitted overlap rule fails while the oracle rule passes. Missed warning means that rule passes while the oracle rule fails. The paired crossfit-minus-in-sample false-warning interval uses Student-t Monte Carlo uncertainty; warning-rate intervals use exact Clopper-Pearson intervals. Bonferroni familywise control covers the fixed eight cells.",
        "",
        "## Results",
        "",
        "| Overlap | Nuisance profile | In-sample false warning | Cross-fit false warning | Cross-fit minus in-sample (familywise MC interval) | In-sample missed warning | Cross-fit missed warning | Oracle pass rate |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        difference_lower, difference_upper = row["crossfit_minus_in_sample_false_warning_familywise_mc_interval"]
        lines.append(
            f"| {row['overlap_profile']} | {row['nuisance_profile']} | "
            f"{100 * row['in_sample_false_warning_rate']:.1f}% | "
            f"{100 * row['crossfit_false_warning_rate']:.1f}% | "
            f"{100 * row['crossfit_minus_in_sample_false_warning_rate']:+.1f} pp [{100 * difference_lower:+.1f}, {100 * difference_upper:+.1f}] pp | "
            f"{100 * row['in_sample_missed_warning_rate']:.1f}% | "
            f"{100 * row['crossfit_missed_warning_rate']:.1f}% | "
            f"{100 * row['oracle_overlap_pass_rate']:.1f}% |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The paired comparison estimates whether out-of-fold propensity predictions change overlap warning behavior relative to the source study's in-sample diagnostics for this synthetic generator. Cross-fitting can reduce reuse of observations in nuisance fitting, but it does not guarantee better overlap calibration, fix propensity misspecification, or address positivity violations.",
        "",
        "Oracle values are available only in this simulated audit; they are not real-world inputs. No AIPW effect estimate or proxy status is changed by this follow-up.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_crossfit_overlap_audit_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "cells": len(result["rows"]),
        "replicates": source["replicates_per_cell"],
        "folds": config["cross_fitting_folds"],
        "same_seed_replay": result["same_seed_replay"],
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()