import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.observational import observational_robustness_stress


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_robustness_stress.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    result = observational_robustness_stress(
        seed=config["seed"],
        n=config["households_per_replicate"],
        replicates=config["replicates_per_cell"],
        scenario=config["scenario"],
        overlap_profiles=tuple(config["overlap_profiles"]),
        nuisance_profiles=tuple(config["nuisance_profiles"]),
        confidence_level=config["confidence_level"],
    )
    if result["number_of_cells"] != config["familywise_cells"]:
        raise ValueError("Configured familywise cell count does not match the factorial design.")
    if result["unmeasured_confounding"] != config["unmeasured_confounding"]:
        raise ValueError("This design must keep hidden confounding fixed at zero.")
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
    report_path = ROOT / "reports" / "observational_robustness_stress.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Positivity and Model-Robustness Stress",
        "",
        "This predeclared synthetic study varies measured-covariate overlap and nuisance-model specification independently. Hidden confounding is fixed at zero to isolate these mechanisms. Results are exploratory, not randomized ITT, and not approval for real-world decisions.",
        "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Seed: {config['seed']}; N={config['households_per_replicate']:,} per replicate; {config['replicates_per_cell']} independent replicates per cell; {result['number_of_cells']} cells.",
        "",
        "The correct-both profile matches the fitted logistic propensity and linear outcome models. Propensity-only misspecification adds a centered quadratic affinity term to assignment while retaining a correct outcome regression. Outcome-only misspecification adds a centered, assignment-invariant quadratic affinity term to outcomes while retaining a correct propensity model. The both-misspecified profile includes both terms. Because each outcome nonlinearity is assignment-invariant, the known treatment effect stays fixed.",
        "",
        "Each replicate's interval is a normal Wald interval using the empirical variance of its AIPW pseudo-outcome. Monte Carlo intervals use Bonferroni familywise control across the fixed eight cells: Student-t intervals for mean bias and exact Clopper-Pearson intervals for coverage proportions. These are not the earlier household-bootstrap intervals.",
        "",
        "## Results",
        "",
        "| Overlap | Nuisance model profile | Mean AIPW bias (familywise MC interval) | Bias RMSE | Wald coverage (familywise MC interval) | Overlap pass rate | Mean ESS control / treatment |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        bias_lower, bias_upper = row["aipw_bias_familywise_mc_interval"]
        coverage_lower, coverage_upper = row["aipw_wald_coverage_familywise_mc_interval"]
        ess = row["mean_ipw_effective_sample_size_by_arm"]
        lines.append(
            f"| {row['overlap_profile']} | {row['nuisance_profile']} | "
            f"{100 * row['mean_aipw_bias']:+.2f} [{100 * bias_lower:+.2f}, {100 * bias_upper:+.2f}] pp | "
            f"{100 * row['aipw_bias_rmse']:.2f} pp | "
            f"{100 * row['aipw_wald_interval_coverage']:.1f}% [{100 * coverage_lower:.1f}, {100 * coverage_upper:.1f}]% | "
            f"{100 * row['overlap_check_pass_rate']:.1f}% | {ess['0']:.0f} / {ess['1']:.0f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The factorial cells distinguish measured-overlap stress from nuisance-model misspecification under this specific generator. Double robustness is an asymptotic property under identification and regularity conditions, not a guarantee of finite-sample unbiasedness or nominal coverage. Poor overlap can destabilize estimation even when the nuisance models are correctly specified.",
        "",
        "Monte Carlo intervals quantify simulation uncertainty within this design only. They do not establish external validity, real-world identification, or proxy approval. Hidden confounding is not studied here; see the separately predeclared observational confounding sensitivity reports.",
        "",
        "Self-review only; no peer feedback is claimed.",
    ])
    markdown_path = ROOT / "docs" / "observational_robustness_stress_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(report_path),
        "cells": len(result["rows"]),
        "replicates": config["replicates_per_cell"],
        "status": result["status"],
    }, indent=2))


if __name__ == "__main__":
    main()