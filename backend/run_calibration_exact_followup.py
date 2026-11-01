import hashlib
import json
from pathlib import Path

from app.analysis.workbench import operating_characteristics


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "calibration_exact_followup.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    prior_paths = [
        ROOT / "reports" / "latest.json",
        ROOT / "reports" / "calibration_followup.json",
        ROOT / "reports" / "calibration_grid_followup.json",
    ]
    prior_reports = [json.loads(path.read_bytes()) for path in prior_paths]
    prior_seeds = {
        report["provenance"]["seed"] if "provenance" in report else report["config"]["seed"]
        for report in prior_reports
    }
    if config["seed"] in prior_seeds or set(config["prior_seeds"]) != prior_seeds:
        raise ValueError("Exact follow-up must use a fresh seed and identify every prior study seed.")
    baseline_grid = [row["true_effect"] for row in prior_reports[0]["operating"]["rows"]]
    if config["effect_grid"] != baseline_grid:
        raise ValueError("Exact follow-up must retain the frozen baseline effect grid.")

    results = operating_characteristics(
        seed=config["seed"],
        repetitions=config["repetitions_per_effect"],
        n=config["households_per_repetition"],
        rate_confidence_level=config["per_effect_confidence_level"],
        rate_interval_method="exact",
    )
    off_nominal = [
        row["true_effect"] for row in results["rows"]
        if row["coverage"]["upper"] < 0.95 or row["coverage"]["lower"] > 0.95
    ]
    status = "familywise_off_nominal_signal" if off_nominal else "no_familywise_signal_detected"
    interpretation = config["decision_rule"]["any_exact_simultaneous_interval_excludes_0.95"] if off_nominal else config["decision_rule"]["all_exact_simultaneous_intervals_include_0.95"]
    output = {
        "study_id": config["study_id"], "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_report_hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in prior_paths},
        "results": results, "off_nominal_effects": off_nominal,
        "status": status, "interpretation": interpretation,
        "coverage_guarantee_scope": "Bonferroni familywise lower bound applies to the five Monte Carlo coverage proportions under independent repetitions; it does not make the target Welch intervals exact.",
        "review_status": "Self-review only; no independent peer review has occurred.",
    }
    report_path = ROOT / "reports" / "calibration_exact_followup.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Exact Monte Carlo Calibration Follow-up", "",
        "A separately predeclared fresh-seed check using exact binomial intervals for Monte Carlo coverage proportions. Prior plans and reports remain unchanged.", "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Fresh seed: {config['seed']}.",
        f"N={config['households_per_repetition']:,} households per repetition; {config['repetitions_per_effect']:,} repetitions per effect; {config['repetitions_per_effect'] * len(config['effect_grid']):,} repetitions total.", "",
        "The target estimator remains the household difference in means with a Welch 95% interval. Only the uncertainty interval for the Monte Carlo proportion of target intervals covering truth changes: two-sided exact Clopper-Pearson intervals at 99% for each of five fixed effects. Exact binomial intervals are conservative, with marginal coverage at least nominal; Bonferroni's union bound gives a simultaneous familywise lower bound of 95% under independent repetitions.", "",
        "This guarantee concerns uncertainty about the repeated-simulation coverage proportions only. It does **not** make the target Welch interval exact, guarantee its coverage under other DGPs, or validate a proxy.", "",
        "## Results", "", "| True effect pp | Target-interval coverage | Exact 99% Monte Carlo interval | Target interval rejection / power | Bias pp ± MC SE | Mean target interval width pp |",
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
    effects = ", ".join(f"{100 * effect:.0f} pp" for effect in off_nominal) or "none"
    lines.extend([
        "", "## Interpretation", "", f"Status: **{status}**. Exact simultaneous intervals excluding nominal 95%: {effects}.", "",
        interpretation, "", output["coverage_guarantee_scope"], "",
        "All results apply only to this synthetic DGP, fixed N, estimator, and effect grid. No general calibration or surrogate-validity claim follows. Self-review only; no independent peer feedback is claimed.",
    ])
    (ROOT / "docs" / "calibration_exact_followup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "status": status, "off_nominal_effects": off_nominal,
                      "results": {str(row["true_effect"]): row["coverage"] for row in results["rows"]}}, indent=2))


if __name__ == "__main__":
    main()