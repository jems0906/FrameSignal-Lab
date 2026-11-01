import hashlib
import json
from pathlib import Path

from app.analysis.workbench import operating_characteristics


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "calibration_grid_followup.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    previous_reports = [ROOT / "reports" / "latest.json", ROOT / "reports" / "calibration_followup.json"]
    previous = [json.loads(path.read_bytes()) for path in previous_reports]
    if config["seed"] in {report["provenance"]["seed"] if "provenance" in report else report["config"]["seed"] for report in previous}:
        raise ValueError("Grid follow-up seed must differ from baseline and first follow-up seeds.")
    if config["effect_grid"] != [row["true_effect"] for row in previous[0]["operating"]["rows"]]:
        raise ValueError("Grid follow-up must retain the frozen baseline effect grid.")

    results = operating_characteristics(
        seed=config["seed"],
        repetitions=config["repetitions_per_effect"],
        n=config["households_per_repetition"],
        rate_confidence_level=config["per_effect_confidence_level"],
    )
    off_nominal = [
        row["true_effect"] for row in results["rows"]
        if row["coverage"]["upper"] < 0.95 or row["coverage"]["lower"] > 0.95
    ]
    status = "simultaneous_off_nominal_signal" if off_nominal else "no_familywise_signal_detected"
    interpretation = config["decision_rule"]["any_simultaneous_interval_excludes_0.95"] if off_nominal else config["decision_rule"]["all_simultaneous_intervals_include_0.95"]
    output = {
        "study_id": config["study_id"], "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "source_report_hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in previous_reports},
        "results": results, "off_nominal_effects": off_nominal,
        "status": status, "interpretation": interpretation,
        "review_status": "Self-review only; no independent peer review has occurred.",
    }
    report_path = ROOT / "reports" / "calibration_grid_followup.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Simultaneous Calibration Grid Follow-up", "",
        "A separately predeclared Monte Carlo check following the inconclusive +4 pp follow-up. Neither prior report nor the frozen analysis plan was changed.", "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Fresh seed: {config['seed']}.",
        f"N={config['households_per_repetition']:,} households per repetition; {config['repetitions_per_effect']:,} repetitions per effect; {config['repetitions_per_effect'] * len(config['effect_grid']):,} repetitions total.", "",
        "Each of the five effect-specific Wilson intervals uses 99% confidence, giving Bonferroni simultaneous familywise confidence of at least 95%. This adjusts Monte Carlo uncertainty across the five grid points; it does not change the target's Welch interval or alter the household DGP.", "",
        "## Results", "", "| True effect pp | Coverage | Simultaneous Wilson interval | Target interval rejection / power | Bias pp ± MC SE | Mean target interval width pp |",
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
        "", "## Interpretation", "", f"Status: **{status}**. Coverage intervals excluding nominal 95%: {effects}.", "",
        interpretation, "",
        "All outcomes are conditional on this synthetic DGP and this predeclared design. A no-signal result is not proof of universal calibration; an off-nominal point would motivate a separately planned method investigation, not post-hoc correction of this run.", "",
        "Self-review only; no independent peer feedback is claimed.",
    ])
    (ROOT / "docs" / "calibration_grid_followup_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "status": status, "off_nominal_effects": off_nominal,
                      "results": {str(row["true_effect"]): row["coverage"] for row in results["rows"]}}, indent=2))


if __name__ == "__main__":
    main()