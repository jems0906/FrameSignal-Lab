import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from framesignal_metrics import __version__ as metrics_version

from app.analysis.learned_proxy import learn_and_validate_proxy


ROOT = Path(__file__).resolve().parents[1]


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def main():
    config_path = ROOT / "configs" / "learned_proxy_extension.json"
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    result = learn_and_validate_proxy(
        seed=config["seed"],
        n=config["households_per_experiment"],
        experiments_per_split=config["experiments_per_split"],
        ridge_grid=tuple(config["ridge_alpha_grid"]),
        agreement_draws=config["agreement_draws"],
    )
    output = {
        "config": config,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "runtime": {"python": __import__("platform").python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__, "framesignal_metrics": metrics_version},
        "results": result,
    }
    report_path = ROOT / "reports" / "learned_proxy_extension.json"
    report_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    agreement = result["heldout_agreement"]
    lines = [
        "# Learned Proxy Extension: Exploratory Follow-up", "",
        "An educational follow-up after the frozen randomized baseline. This learned score is not a validated surrogate, is not approved for decisions, and does not change the frozen baseline or MetricSteward statuses.", "",
        f"Study: `{config['study_id']}`. Config SHA-256: `{output['config_sha256']}`. Seed: {config['seed']}.",
        f"{result['unique_households']:,} disjoint households across {len(config['splits'])} splits; {config['experiments_per_split']} experiments per split, N={config['households_per_experiment']:,} each.", "",
        "## Frozen Learning Protocol", "",
        "Features are qualified starts and viewing days only. Fit standardized ridge linear-probability weights on training households and their fully observed late-return outcomes. Means, scales, and coefficients are learned on training only. Tune ridge alpha by validation household Brier score (ties choose smaller alpha), then freeze before held-out households are generated. Assignment, late outcome at scoring time, affinity, oracle probabilities, and latent fields are not score features. No held-out labels enter fitting or tuning.", "",
        "## Learned Model", "",
        f"Ridge alpha: {result['model']['selected_alpha']}. Intercept: {result['model']['intercept']:.6f}.", "",
        "| Standardized feature | Frozen coefficient | Training mean | Training SD |",
        "|---|---:|---:|---:|",
    ]
    for index, feature in enumerate(result["feature_names"]):
        lines.append(f"| {feature} | {result['model']['standardized_coefficients'][feature]:+.6f} | {result['training_feature_means'][index]:.6f} | {result['training_feature_scales'][index]:.6f} |")
    lines.extend(["", "| Candidate alpha | Validation Brier score |", "|---:|---:|"])
    for row in result["model"]["validation_brier_scores"]:
        lines.append(f"| {row['alpha']} | {row['brier_score']:.6f} |")
    lines.extend(["", "## Prediction (Household-Level)", "", "| Split | Households | Brier score | Pooled correlation | Within-control correlation | Within-policy correlation |", "|---|---:|---:|---:|---:|---:|"])
    for split in config["splits"]:
        metrics = result["household_prediction"][split]
        lines.append(f"| {split} | {metrics['n_households']:,} | {metrics['brier_score']:.6f} | {metrics['pooled_correlation']:.3f} | {metrics['within_assignment_correlations']['0']:.3f} | {metrics['within_assignment_correlations']['1']:.3f} |")
    lines.extend(["", "Household association is predictive description, not causal surrogacy; pooled association may reflect policy assignment and shared affinity.", "", "## Held-Out Treatment-Effect Agreement", "", "| Experiment | Scenario | Learned-score effect | Return effect | Known return effect |", "|---|---|---:|---:|---:|"])
    for row in result["heldout_experiments"]:
        score = row["effects"]["learned_proxy"]
        target = row["effects"]["returned_d29_56"]
        lines.append(f"| {row['id']} | {row['scenario']} | {score['effect']:+.4f} [{score['lower']:+.4f}, {score['upper']:+.4f}] | {target['effect'] * 100:+.2f} [{target['lower'] * 100:+.2f}, {target['upper'] * 100:+.2f}] pp | {row['truth_return_effect'] * 100:+.2f} pp |")
    lines.extend(["", f"Observed held-out sign agreement: {percent(agreement['observed_agreement'])}; experiment-bootstrap interval [{percent(agreement['lower'])}, {percent(agreement['upper'])}]; effect-noise sensitivity [{percent(agreement['noise_lower'])}, {percent(agreement['noise_upper'])}].", "", "These are nine constructed held-out experiments. Intervals condition on training/validation-frozen weights and omit weight-learning uncertainty. Experiment resampling and effect-noise sensitivity do not establish causal surrogacy. Results cannot override harmful reversals or directly measured return.", "", "## Status and Limitations", "", "Status: `exploratory_educational_only_not_surrogate_approval`. Weights are fitted from household prediction, not learned from a validated cross-experiment causal-surrogate objective. Latent affinity, limited experiment families, scenario support, and conditional weight uncertainty constrain conclusions. No real-world approval or peer review is claimed."])
    (ROOT / "docs" / "learned_proxy_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "split_households": result["split_households"], "selected_alpha": result["model"]["selected_alpha"], "heldout_agreement": agreement["observed_agreement"], "status": result["status"]}, indent=2))


if __name__ == "__main__":
    main()