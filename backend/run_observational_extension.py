import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from app.analysis.observational import observational_sensitivity
from framesignal_metrics import __version__ as metrics_version


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "observational_extension.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    result = observational_sensitivity(
        seed=config["seed"],
        n=config["households_per_run"],
        draws=config["household_bootstrap_draws"],
        scenarios=tuple(config["scenarios"]),
        confounding_grid=tuple(config["unmeasured_confounding_strengths"]),
    )
    output = {
        "study_id": config["study_id"],
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "runtime": {"python": __import__("platform").python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__, "framesignal_metrics": metrics_version},
        "results": result,
        "review_status": "Self-review only; no independent peer review has occurred.",
    }
    report_path = ROOT / "reports" / "observational_extension.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# Observational Extension: Sensitivity Demonstration", "",
        "This is an opt-in synthetic observational extension. It is not randomized ITT, not the primary analysis, and not approval for real-world decisions.", "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Seed: {config['seed']}; N={config['households_per_run']:,} per run; {config['household_bootstrap_draws']} complete-household bootstrap draws.", "",
        "## Estimand and Assumptions", "",
        "The simulated population average effect on fully observed days 29-56 return. Adjustment uses only measured affinity and log viewing opportunity. AIPW relies on consistency, no interference, positivity, no unmeasured confounding given these measured covariates, and correct specification of either the propensity or outcome model. The sensitivity generator deliberately violates conditional exchangeability as hidden loyalty strength increases. AIPW does not remove that bias by declaration.", "",
        "Propensity overlap checks use the predeclared 0.05-0.95 range, common support, clipped-weight frequency, and per-arm effective sample size. Failed overlap is a diagnostic warning; it is not silently repaired or treated as evidence of identification.", "",
        "## Results", "", "| Scenario | Hidden confounding | True population effect | Naive difference (descriptive) | AIPW estimate | Household bootstrap 95% interval | Common-support fraction | Outside 0.05-0.95 | ESS control / treatment | Overlap check |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        estimate = row["observational_estimate"]
        overlap = estimate["overlap"]
        ess = overlap["ipw_effective_sample_size_by_arm"]
        lines.append(
            f"| {row['scenario']} | {row['unmeasured_confounding_strength']:.1f} | {100 * row['known_population_ate']:+.1f} pp | "
            f"{100 * estimate['naive_unadjusted_difference_descriptive_only']:+.2f} pp | {100 * estimate['effect']:+.2f} pp | "
            f"[{100 * estimate['lower']:+.2f}, {100 * estimate['upper']:+.2f}] pp | "
            f"{100 * overlap['fraction_inside_common_support']:.1f}% | "
            f"{100 * overlap['fraction_outside_overlap_range_0_05_0_95']:.1f}% | "
            f"{ess['0']:.0f} / {ess['1']:.0f} | {'pass' if overlap['overlap_check_passed'] else 'flag'} |"
        )
    lines.extend([
        "", "## Interpretation", "",
        "Compare the naive contrast and measured-covariate AIPW estimate with the known synthetic population effect as latent confounding varies. Results are specific to this constructed selection model. The bootstrap resamples complete households but does not account for all nuisance-model uncertainty or eliminate hidden-confounder bias.", "",
        "No observational estimate supersedes the randomized ITT target. Do not use these results to attribute return to a title, claim artistic value, define Netflix retention, or approve any proxy. See the source JSON for propensity quantiles, propensity ranges by assignment arm, clipped fraction, ESS, assumptions, and limitations.", "",
        "Self-review only; no peer feedback is claimed.",
    ])
    (ROOT / "docs" / "observational_extension_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "rows": len(result["rows"]), "status": result["status"]}, indent=2))


if __name__ == "__main__":
    main()