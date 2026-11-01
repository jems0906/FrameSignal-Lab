import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_overlap_threshold_stress


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_overlap_threshold_stress.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    result = observational_overlap_threshold_stress(
        seed=config["seed"],
        n=config["households_per_replicate"],
        replicates=config["replicates_per_profile_cell"],
        folds=config["cross_fitting_folds"],
        scenario=config["scenario"],
        overlap_profiles=tuple(config["overlap_profiles"]),
        nuisance_profiles=tuple(config["nuisance_profiles"]),
        threshold_rules=tuple(config["threshold_rules"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_profile_cells"] != config["profile_cells"]:
        raise ValueError("Configured overlap/nuisance profile count does not match the grid.")
    if result["number_of_familywise_cells"] != config["familywise_cells"]:
        raise ValueError("Configured profile-by-threshold familywise cell count does not match the grid.")
    if result["unmeasured_confounding"] != config["unmeasured_confounding"]:
        raise ValueError("This threshold study must keep hidden confounding fixed at zero.")
    output = {
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
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
    report_path = ROOT / "reports" / "observational_overlap_threshold_stress.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Overlap Threshold Operating Study",
        "",
        "This is a fresh-seed, paired synthetic study of prespecified overlap rules. It does not choose or recommend a production threshold. Oracle diagnostics are audit-only; no oracle value enters a propensity fit or AIPW estimate.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Seed: {config['seed']}; N={config['households_per_replicate']:,}; {config['replicates_per_profile_cell']} replicates per each of eight overlap/nuisance profiles; {config['cross_fitting_folds']} cross-fitting folds.",
        "",
        "The same generated replicate is evaluated under every threshold. Hidden confounding is fixed at zero. Threshold summaries equally weight the eight generator profiles; all profile-level threshold results and Monte Carlo intervals are retained in JSON.",
        "",
        "## Balanced Profile Summaries",
        "",
        "| Threshold rule | Propensity range | ESS floor | Oracle pass | In-sample pass | Cross-fit pass | In-sample false warning | Cross-fit false warning | Crossfit minus in-sample (familywise MC interval) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["threshold_summaries"]:
        difference_lower, difference_upper = row["crossfit_minus_in_sample_false_warning_familywise_mc_interval"]
        lines.append(
            f"| {row['threshold_rule']} | {row['propensity_range'][0]:.2f}-{row['propensity_range'][1]:.2f} | "
            f"{row['minimum_effective_sample_size']} | {100 * row['oracle']['pass_rate']:.1f}% | "
            f"{100 * row['in_sample']['pass_rate']:.1f}% | {100 * row['crossfit']['pass_rate']:.1f}% | "
            f"{100 * row['in_sample']['false_warning_rate']:.1f}% | {100 * row['crossfit']['false_warning_rate']:.1f}% | "
            f"{100 * row['crossfit_minus_in_sample_false_warning_rate']:+.1f} pp [{100 * difference_lower:+.1f}, {100 * difference_upper:+.1f}] pp |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "These summaries describe rule behavior only under the prespecified generator and fresh seed. A looser rule can reduce flags while also allowing poorer support; a stricter rule can flag more cases without proving that the estimate is unusable. The oracle reference is not observable in real observational studies. No rule is selected from this grid.",
        "",
        "Familywise Monte Carlo intervals quantify simulation uncertainty, not external validity. Cross-fitting is diagnostic-only here; the study does not estimate cross-fitted treatment effects.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_overlap_threshold_stress_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "profile_cells": result["number_of_profile_cells"],
        "threshold_rules": result["number_of_threshold_rules"],
        "familywise_cells": result["number_of_familywise_cells"],
        "replicates_per_profile_cell": config["replicates_per_profile_cell"],
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()