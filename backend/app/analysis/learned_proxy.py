import numpy as np
import pandas as pd

from app.analysis.inference import difference_in_means
from app.analysis.workbench import PLAN, agreement_uncertainty
from app.metrics.registry import household_metrics
from app.simulations.generator import SCENARIOS, simulate


FEATURES = ("qualified_starts", "viewing_days")
EFFECTS = (*FEATURES, "learned_proxy", "returned_d29_56")


def learn_and_validate_proxy(
    seed: int = 20261106,
    n: int = 2000,
    experiments_per_split: int = 9,
    ridge_grid: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0),
    agreement_draws: int = 1000,
) -> dict:
    if n < 100 or n > 20000 or experiments_per_split < 3:
        raise ValueError("Use 100-20000 households and at least three experiments per split.")
    if not ridge_grid or any(alpha < 0 for alpha in ridge_grid):
        raise ValueError("ridge_grid must contain nonnegative penalties.")
    if agreement_draws < 100:
        raise ValueError("Use at least 100 experiment-agreement draws.")

    scenario_names = tuple(SCENARIOS)
    populations = {split: [] for split in PLAN["splits"]}
    seen_households = set()
    experiment_specs = []

    def generate_split(split_index: int, split: str) -> None:
        for index in range(experiments_per_split):
            scenario = scenario_names[index % len(scenario_names)]
            strength = (0.6, 1.0, 1.4)[(index // len(scenario_names)) % 3]
            experiment_seed = int(np.random.SeedSequence([seed, split_index, index, 606]).generate_state(1)[0])
            experiment_id = f"learned-{split}-{index + 1:02d}"
            data = simulate(scenario, n, experiment_seed, experiment_id, split, strength)
            identifiers = set(data.households.household_id)
            if seen_households.intersection(identifiers):
                raise ValueError("Household leakage across learned-proxy splits.")
            seen_households.update(identifiers)
            frame = household_metrics(data)
            populations[split].append({
                "id": experiment_id,
                "seed": experiment_seed,
                "scenario": scenario,
                "strength": strength,
                "truth_return_effect": data.scenario.return_effect * strength,
                "frame": frame,
            })
            experiment_specs.append({"id": experiment_id, "split": split, "scenario": scenario, "strength": strength, "seed": experiment_seed})

    generate_split(0, "train")
    generate_split(1, "validation")

    training = pd.concat([item["frame"] for item in populations["train"]], ignore_index=True)
    validation = pd.concat([item["frame"] for item in populations["validation"]], ignore_index=True)
    training_x = training.loc[:, FEATURES].to_numpy(dtype=float)
    validation_x = validation.loc[:, FEATURES].to_numpy(dtype=float)
    training_y = training.returned_d29_56.to_numpy(dtype=float)
    validation_y = validation.returned_d29_56.to_numpy(dtype=float)
    feature_means = training_x.mean(axis=0)
    feature_scales = training_x.std(axis=0)
    feature_scales[feature_scales == 0] = 1
    train_z = (training_x - feature_means) / feature_scales
    validation_z = (validation_x - feature_means) / feature_scales
    target_mean = float(training_y.mean())
    centered_y = training_y - target_mean
    gram = train_z.T @ train_z / len(training)
    gradient = train_z.T @ centered_y / len(training)

    candidates = []
    for alpha in ridge_grid:
        coefficients = np.linalg.solve(gram + alpha * np.eye(len(FEATURES)), gradient)
        validation_prediction = np.clip(target_mean + validation_z @ coefficients, 0, 1)
        candidates.append({
            "alpha": float(alpha),
            "coefficients_standardized": coefficients,
            "validation_brier": float(np.mean(np.square(validation_prediction - validation_y))),
        })
    selected = min(candidates, key=lambda row: (row["validation_brier"], row["alpha"]))
    coefficients = selected["coefficients_standardized"]

    prediction = {}
    for split in ("train", "validation"):
        split_frame = pd.concat([item["frame"] for item in populations[split]], ignore_index=True)
        split_z = (split_frame.loc[:, FEATURES].to_numpy(dtype=float) - feature_means) / feature_scales
        scores = np.clip(target_mean + split_z @ coefficients, 0, 1)
        outcome = split_frame.returned_d29_56.to_numpy(dtype=float)
        prediction[split] = {
            "brier_score": float(np.mean(np.square(scores - outcome))),
            "pooled_correlation": float(np.corrcoef(scores, outcome)[0, 1]),
            "within_assignment_correlations": {
                str(arm): float(np.corrcoef(scores[split_frame.assignment.to_numpy() == arm], outcome[split_frame.assignment.to_numpy() == arm])[0, 1])
                for arm in (0, 1)
            },
            "n_households": len(split_frame),
        }

    generate_split(2, "heldout")
    heldout_experiments = []
    split = "heldout"
    split_frame = pd.concat([item["frame"] for item in populations[split]], ignore_index=True)
    split_z = (split_frame.loc[:, FEATURES].to_numpy(dtype=float) - feature_means) / feature_scales
    heldout_scores = np.clip(target_mean + split_z @ coefficients, 0, 1)
    heldout_outcome = split_frame.returned_d29_56.to_numpy(dtype=float)
    prediction[split] = {
        "brier_score": float(np.mean(np.square(heldout_scores - heldout_outcome))),
        "pooled_correlation": float(np.corrcoef(heldout_scores, heldout_outcome)[0, 1]),
        "within_assignment_correlations": {
            str(arm): float(np.corrcoef(heldout_scores[split_frame.assignment.to_numpy() == arm], heldout_outcome[split_frame.assignment.to_numpy() == arm])[0, 1])
            for arm in (0, 1)
        },
        "n_households": len(split_frame),
    }
    for item in populations["heldout"]:
        frame = item["frame"].copy()
        z = (frame.loc[:, FEATURES].to_numpy(dtype=float) - feature_means) / feature_scales
        frame["learned_proxy"] = np.clip(target_mean + z @ coefficients, 0, 1)
        arm_frames = [frame[frame.assignment == arm] for arm in (0, 1)]
        effects = {metric: difference_in_means(arm_frames[0][metric], arm_frames[1][metric]) for metric in EFFECTS}
        covariance = sum(np.cov(group[["learned_proxy", "returned_d29_56"]].to_numpy().T, ddof=1) / len(group) for group in arm_frames)
        heldout_experiments.append({
            "id": item["id"],
            "scenario": item["scenario"],
            "strength": item["strength"],
            "truth_return_effect": item["truth_return_effect"],
            "effects": effects,
            "effect_covariance": {"learned_proxy": covariance.tolist()},
        })

    agreement = agreement_uncertainty(heldout_experiments, "learned_proxy", seed + 1000, agreement_draws)
    return {
        "study_id": "framesignal-learned-proxy-v1",
        "seed": seed,
        "n_per_experiment": n,
        "experiments_per_split": experiments_per_split,
        "unique_households": len(seen_households),
        "leakage_check": True,
        "split_households": {split: len(populations[split]) * n for split in PLAN["splits"]},
        "experiment_specs": experiment_specs,
        "feature_names": list(FEATURES),
        "target": "returned_d29_56",
        "weight_training_split": "train",
        "regularization_tuning_split": "validation",
        "weight_freeze_before_heldout": True,
        "forbidden_features": ["assignment", "return_probability", "return_day", "affinity", "assignment_probability_oracle", "latent_loyalty"],
        "training_feature_means": feature_means.tolist(),
        "training_feature_scales": feature_scales.tolist(),
        "model": {
            "type": "ridge linear probability prediction on standardized household metric values",
            "intercept": target_mean,
            "standardized_coefficients": {feature: float(value) for feature, value in zip(FEATURES, coefficients)},
            "selected_alpha": selected["alpha"],
            "validation_brier_scores": [{"alpha": row["alpha"], "brier_score": row["validation_brier"]} for row in candidates],
        },
        "household_prediction": prediction,
        "heldout_experiments": heldout_experiments,
        "heldout_agreement": agreement,
        "interval_scope": "Held-out Welch intervals condition on weights frozen from training and tuning on validation; they do not include training/tuning weight uncertainty.",
        "status": "exploratory_educational_only_not_surrogate_approval",
        "warning": "Household prediction does not establish causal surrogacy. Small constructed experiment families, scenario support, and frozen-weight uncertainty limit inference. No real-world approval is granted.",
    }