import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_replicated_sensitivity


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_replication.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    result = observational_replicated_sensitivity(
        seed=config["seed"],
        n=config["households_per_replicate"],
        replicates=config["replicates_per_cell"],
        scenarios=tuple(config["scenarios"]),
        confounding_grid=tuple(config["unmeasured_confounding_strengths"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_cells"] != config["familywise_cells"]:
        raise ValueError("Configured familywise cell count does not match the scenario grid.")
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
    report_path = ROOT / "reports" / "observational_replication.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Replicated Sensitivity Study",
        "",
        "This predeclared repeated-simulation study is separate from the single-run illustrative bootstrap report. It is synthetic, exploratory, not randomized ITT, and not approval for real-world decisions.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Seed: {config['seed']}; N={config['households_per_replicate']:,} per replicate; {config['replicates_per_cell']} independent replicates per cell.",
        "",
        "AIPW uses observed affinity and log opportunity only. Each replicate's 95% Wald interval uses the empirical variance of its AIPW pseudo-outcome; it is not the household-bootstrap interval used in the illustrative report. The reported Monte Carlo intervals use Bonferroni familywise control across the fixed nine cells: Student-t intervals for mean bias and exact Clopper-Pearson intervals for coverage proportions.",
        "",
        "## Results",
        "",
        "| Scenario | Hidden confounding | True ATE | Mean AIPW bias (familywise MC interval) | Bias RMSE | Wald coverage (familywise MC interval) | Overlap pass rate | Mean ESS control / treatment |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        bias_lower, bias_upper = row["aipw_bias_familywise_mc_interval"]
        coverage_lower, coverage_upper = row["aipw_wald_coverage_familywise_mc_interval"]
        ess = row["mean_ipw_effective_sample_size_by_arm"]
        lines.append(
            f"| {row['scenario']} | {row['unmeasured_confounding_strength']:.1f} | {100 * row['known_population_ate']:+.1f} pp | "
            f"{100 * row['mean_aipw_bias']:+.2f} [{100 * bias_lower:+.2f}, {100 * bias_upper:+.2f}] pp | "
            f"{100 * row['aipw_bias_rmse']:.2f} pp | "
            f"{100 * row['aipw_wald_interval_coverage']:.1f}% [{100 * coverage_lower:.1f}, {100 * coverage_upper:.1f}]% | "
            f"{100 * row['overlap_check_pass_rate']:.1f}% | {ess['0']:.0f} / {ess['1']:.0f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "These results estimate average behavior of the AIPW estimator under this specific generator. Monte Carlo intervals quantify simulation uncertainty, not uncertainty about whether the generator or identification assumptions match a real application. Coverage of the replicate-level Wald intervals does not validate real-world identification or the original household-bootstrap interval.",
        "",
        "AIPW does not remove hidden confounding. Overlap and effective sample size are diagnostics, not proof of identification. Do not combine this repeated study with the single-run illustrative report, replace randomized ITT, or approve any proxy.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_replication_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "cells": len(result["rows"]),
        "replicates": config["replicates_per_cell"],
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()