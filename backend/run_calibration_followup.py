import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from app.analysis.workbench import operating_characteristics
from framesignal_metrics import __version__ as metrics_version


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "calibration_followup.json"
    baseline_path = ROOT / "reports" / "latest.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    baseline_bytes = baseline_path.read_bytes()
    baseline = json.loads(baseline_bytes)
    if config["seed"] == config["baseline_seed"] or config["seed"] == baseline["provenance"]["seed"]:
        raise ValueError("Calibration follow-up must use a fresh seed distinct from the frozen baseline.")
    if config["effect_grid"] != [row["true_effect"] for row in baseline["operating"]["rows"]]:
        raise ValueError("Follow-up effect grid must match the preregistered baseline grid.")

    results = operating_characteristics(
        seed=config["seed"],
        repetitions=config["repetitions_per_effect"],
        n=config["households_per_repetition"],
    )
    primary = next(row for row in results["rows"] if row["true_effect"] == config["primary_effect"])
    secondary_flags = [
        row for row in results["rows"]
        if row["true_effect"] != config["primary_effect"]
        and (row["coverage"]["upper"] < 0.95 or row["coverage"]["lower"] > 0.95)
    ]
    lower = primary["coverage"]["lower"]
    upper = primary["coverage"]["upper"]
    if upper < 0.95:
        interpretation = config["decision_rule"]["upper_below_0.95"]
        status = "undercoverage_signal"
    elif lower > 0.95:
        interpretation = config["decision_rule"]["lower_above_0.95"]
        status = "overcoverage_signal"
    else:
        interpretation = config["decision_rule"]["otherwise"]
        status = "inconclusive"

    output = {
        "study_id": config["study_id"],
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "baseline_report_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "framesignal_metrics": metrics_version,
        },
        "baseline_primary_coverage": next(row for row in baseline["operating"]["rows"] if row["true_effect"] == config["primary_effect"])["coverage"],
        "primary_followup_coverage": primary["coverage"],
        "primary_status": status,
        "interpretation": interpretation,
        "results": results,
        "review_status": "Self-review only; no independent peer review has occurred.",
    }
    report_path = ROOT / "reports" / "calibration_followup.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Calibration Follow-up Report", "",
        "A separate, prospectively specified Monte Carlo follow-up to the frozen v1.0 report. The baseline report and analysis plan were not modified.", "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Baseline report SHA-256: `{output['baseline_report_sha256']}`.", "",
        f"Fresh seed: {config['seed']}; N={config['households_per_repetition']:,} balanced household assignments per repetition; {config['repetitions_per_effect']:,} repetitions per effect; total {config['repetitions_per_effect'] * len(config['effect_grid']):,} repetitions.", "",
        "## Frozen Follow-up Method", "",
        "Unchanged household Bernoulli return DGP and two-sided Welch household difference-in-means 95% interval. Coverage rates use 95% Wilson Monte Carlo intervals. +4 pp is the predeclared primary calibration point because the earlier independent baseline flag occurred there; other effects are descriptive. No seed, estimator, DGP, sample size, grid, or interval was tuned after seeing these follow-up results.", "",
        "## Results", "", "| True effect pp | Coverage | 95% Wilson Monte Carlo interval | Null rejection / power | Bias pp ± MC SE | Mean interval width pp |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in results["rows"]:
        coverage = row["coverage"]
        lines.append(
            f"| {100 * row['true_effect']:.1f} | {100 * coverage['rate']:.2f}% | "
            f"[{100 * coverage['lower']:.2f}%, {100 * coverage['upper']:.2f}%] | "
            f"{100 * row['rejection_rate']['rate']:.2f}% | "
            f"{100 * row['bias']:+.3f} ± {100 * row['bias_mc_se']:.3f} | "
            f"{100 * row['mean_interval_width']:.2f} pp |"
        )
    lines.extend([
        "", "## Primary Interpretation", "",
        f"At +4 pp, baseline coverage was {100 * output['baseline_primary_coverage']['rate']:.2f}% "
        f"[{100 * output['baseline_primary_coverage']['lower']:.2f}%, {100 * output['baseline_primary_coverage']['upper']:.2f}%]; "
        f"fresh follow-up coverage is {100 * primary['coverage']['rate']:.2f}% "
        f"[{100 * lower:.2f}%, {100 * upper:.2f}%].",
        "", f"Status: **{status}**. {interpretation}", "",
        ("Unadjusted secondary-grid Monte Carlo intervals also exclude nominal at "
         + ", ".join(f"{100 * row['true_effect']:.0f} pp" for row in secondary_flags)
         + ". These are exploratory across the grid, not additional confirmatory findings."
         if secondary_flags else "No secondary-grid Wilson interval excludes nominal 95%; secondary effects remain descriptive."), "",
        "These results apply only to this synthetic DGP and this predeclared effect. Coverage checks do not certify proxy validity, real-world retention inference, transportability, or surrogate status. The original 1,000-repetition baseline is preserved for comparison.", "",
        "Self-review only; no independent peer feedback is claimed.",
    ])
    (ROOT / "docs" / "calibration_followup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "primary_effect": config["primary_effect"], "status": status,
                      "coverage": primary["coverage"], "interpretation": interpretation}, indent=2))


if __name__ == "__main__":
    main()