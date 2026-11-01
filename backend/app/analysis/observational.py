import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import beta, norm, t as student_t

from app.simulations.generator import SCENARIOS, simulate
from app.metrics.registry import household_metrics


OBSERVED_COVARIATES = ("observed_affinity", "observed_log_opportunity")
PROPENSITY_CLIP = (0.01, 0.99)
OVERLAP_RANGE = (0.05, 0.95)


def _fit_propensity_model(
    training_frame: pd.DataFrame,
    prediction_frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    training_covariates = training_frame.loc[:, OBSERVED_COVARIATES].to_numpy(dtype=float)
    prediction_covariates = prediction_frame.loc[:, OBSERVED_COVARIATES].to_numpy(dtype=float)
    means = training_covariates.mean(axis=0)
    scales = training_covariates.std(axis=0)
    scales[scales == 0] = 1
    training_standardized = (training_covariates - means) / scales
    prediction_standardized = (prediction_covariates - means) / scales
    assignment = training_frame.assignment.to_numpy(dtype=float)

    propensity_design = np.column_stack([np.ones(len(training_frame)), training_standardized])

    def objective(coefficients):
        linear = propensity_design @ coefficients
        loss = np.mean(np.logaddexp(0, linear) - assignment * linear) + 0.5e-6 * np.sum(coefficients[1:] ** 2)
        gradient = propensity_design.T @ (expit(linear) - assignment) / len(training_frame)
        gradient[1:] += 1e-6 * coefficients[1:]
        return float(loss), gradient

    fitted = minimize(objective, np.zeros(propensity_design.shape[1]), jac=True, method="L-BFGS-B")
    if not fitted.success and np.linalg.norm(fitted.jac) > 1e-5:
        raise ValueError(f"Propensity model failed to converge: {fitted.message}")
    prediction_design = np.column_stack([np.ones(len(prediction_frame)), prediction_standardized])
    propensity_raw = expit(prediction_design @ fitted.x)
    propensity = np.clip(propensity_raw, *PROPENSITY_CLIP)
    return propensity_raw, propensity


def cross_fitted_propensity_predictions(
    frame: pd.DataFrame,
    folds: int = 5,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    if folds < 2 or folds > len(frame):
        raise ValueError("Cross-fitting requires at least two folds and no more folds than observations.")
    predictions_raw = np.empty(len(frame), dtype=float)
    rng = np.random.default_rng(seed)
    for prediction_indices in np.array_split(rng.permutation(len(frame)), folds):
        training_mask = np.ones(len(frame), dtype=bool)
        training_mask[prediction_indices] = False
        predictions_raw[prediction_indices], _ = _fit_propensity_model(
            frame.iloc[training_mask],
            frame.iloc[prediction_indices],
        )
    return predictions_raw, np.clip(predictions_raw, *PROPENSITY_CLIP)


def _nuisance_predictions(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    propensity_raw, propensity = _fit_propensity_model(frame, frame)
    covariates = frame.loc[:, OBSERVED_COVARIATES].to_numpy(dtype=float)
    means = covariates.mean(axis=0)
    scales = covariates.std(axis=0)
    scales[scales == 0] = 1
    standardized = (covariates - means) / scales
    assignment = frame.assignment.to_numpy(dtype=float)
    outcome = frame.returned_d29_56.to_numpy(dtype=float)

    outcome_design = np.column_stack([np.ones(len(frame)), assignment, standardized])
    coefficients = np.linalg.lstsq(outcome_design, outcome, rcond=None)[0]
    control_design = np.column_stack([np.ones(len(frame)), np.zeros(len(frame)), standardized])
    treatment_design = np.column_stack([np.ones(len(frame)), np.ones(len(frame)), standardized])
    outcome_control = control_design @ coefficients
    outcome_treatment = treatment_design @ coefficients
    return propensity_raw, propensity, outcome_control, outcome_treatment


def _overlap_diagnostics(propensity_raw: np.ndarray, propensity: np.ndarray, assignment: np.ndarray) -> dict:
    weights = np.where(assignment == 1, 1 / propensity, 1 / (1 - propensity))
    by_arm = [propensity_raw[assignment == arm] for arm in (0, 1)]
    common_lower = max(float(values.min()) for values in by_arm)
    common_upper = min(float(values.max()) for values in by_arm)
    common = (propensity_raw >= common_lower) & (propensity_raw <= common_upper)
    effective_sample_size = float(weights.sum() ** 2 / np.square(weights).sum())
    diagnostics = {
        "propensity_quantiles": {str(q): float(np.quantile(propensity_raw, q)) for q in (0.01, 0.05, 0.5, 0.95, 0.99)},
        "propensity_range_by_arm": {str(arm): [float(values.min()), float(values.max())] for arm, values in enumerate(by_arm)},
        "common_support": [common_lower, common_upper],
        "fraction_inside_common_support": float(common.mean()),
        "fraction_outside_overlap_range_0_05_0_95": float(((propensity_raw < OVERLAP_RANGE[0]) | (propensity_raw > OVERLAP_RANGE[1])).mean()),
        "fraction_clipped_for_stability": float((propensity_raw != propensity).mean()),
        "ipw_effective_sample_size": effective_sample_size,
        "ipw_effective_sample_size_by_arm": {
            str(arm): float(weights[assignment == arm].sum() ** 2 / np.square(weights[assignment == arm]).sum())
            for arm in (0, 1)
        },
    }
    diagnostics["overlap_check_passed"] = (
        diagnostics["fraction_inside_common_support"] >= 0.95
        and diagnostics["fraction_outside_overlap_range_0_05_0_95"] <= 0.05
        and min(diagnostics["ipw_effective_sample_size_by_arm"].get(str(arm), 0) for arm in (0, 1)) >= 50
    )
    return diagnostics


def _aipw_effect(frame: pd.DataFrame) -> tuple[float, dict]:
    assignment = frame.assignment.to_numpy(dtype=float)
    outcome = frame.returned_d29_56.to_numpy(dtype=float)
    propensity_raw, propensity, outcome_control, outcome_treatment = _nuisance_predictions(frame)
    pseudo_outcome = (
        outcome_treatment - outcome_control
        + assignment * (outcome - outcome_treatment) / propensity
        - (1 - assignment) * (outcome - outcome_control) / (1 - propensity)
    )
    effect = float(pseudo_outcome.mean())
    influence_se = float(np.std(pseudo_outcome, ddof=1) / np.sqrt(len(pseudo_outcome)))
    diagnostics = _overlap_diagnostics(propensity_raw, propensity, assignment)
    diagnostics["aipw_influence_function_se"] = influence_se
    return effect, diagnostics


def estimate_observational_effect(frame: pd.DataFrame, seed: int, draws: int = 200) -> dict:
    required = {"household_id", "assignment", "returned_d29_56", *OBSERVED_COVARIATES}
    if not required.issubset(frame.columns):
        raise ValueError("Observational analysis requires assignment, observed covariates, and fully observed return.")
    if not frame.returned_d29_56.isin([0, 1]).all() or frame.returned_d29_56.isna().any():
        raise ValueError("The target must be fully observed and binary.")
    if frame.assignment.nunique() != 2 or not frame.assignment.isin([0, 1]).all():
        raise ValueError("Both observed assignment groups are required.")
    if draws < 20:
        raise ValueError("Use at least 20 household-bootstrap draws.")

    aipw, overlap = _aipw_effect(frame)
    groups = [frame[frame.assignment == arm] for arm in (0, 1)]
    naive = float(groups[1].returned_d29_56.mean() - groups[0].returned_d29_56.mean())
    rng = np.random.default_rng(seed)
    bootstrap = []
    for _ in range(draws):
        sample = frame.iloc[rng.integers(0, len(frame), len(frame))]
        if sample.assignment.nunique() < 2:
            continue
        try:
            estimate, _ = _aipw_effect(sample)
        except ValueError:
            continue
        bootstrap.append(estimate)
    if len(bootstrap) < draws * 0.9:
        raise ValueError("Too many household-bootstrap draws lacked both arms or a converged propensity model.")
    return {
        "estimator": "Augmented inverse-probability weighted (AIPW), with household bootstrap uncertainty",
        "effect": aipw,
        "lower": float(np.quantile(bootstrap, 0.025)),
        "upper": float(np.quantile(bootstrap, 0.975)),
        "bootstrap_se": float(np.std(bootstrap, ddof=1)),
        "bootstrap_draws_requested": draws,
        "bootstrap_draws_used": len(bootstrap),
        "naive_unadjusted_difference_descriptive_only": naive,
        "overlap": overlap,
        "assumptions": [
            "Consistency and no interference between households.",
            "Conditional exchangeability given observed affinity and log viewing opportunity; violated when the simulated latent loyalty confounder affects both assignment and return.",
            "Positivity and adequate propensity overlap; inspect the reported common-support and effective-sample-size diagnostics.",
            "Correct specification of either the propensity model or the outcome regression for double robustness; neither model corrects unmeasured confounding.",
            "All registered household outcomes and measured covariates are observed; complete households are resampled for uncertainty.",
        ],
        "warning": "Exploratory synthetic observational estimate; not interchangeable with randomized ITT, not evidence about real content decisions, and not approval of any proxy.",
    }


def observational_sensitivity(
    seed: int = 20261105,
    n: int = 2000,
    draws: int = 200,
    scenarios: tuple[str, ...] = ("helpful", "unrelated", "misleading"),
    confounding_grid: tuple[float, ...] = (0.0, 0.5, 1.0),
) -> dict:
    if any(scenario not in SCENARIOS for scenario in scenarios):
        raise ValueError("Observational sensitivity requires registered scenarios.")
    if any(not 0 <= value <= 1 for value in confounding_grid):
        raise ValueError("Confounding strengths must be between 0 and 1.")
    rows = []
    for scenario_index, scenario in enumerate(scenarios):
        for confounding_index, confounding in enumerate(confounding_grid):
            experiment_seed = int(np.random.SeedSequence([seed, scenario_index, confounding_index]).generate_state(1)[0])
            data = simulate(
                scenario=scenario, n=n, seed=experiment_seed,
                experiment_id=f"obs-{scenario}-{confounding}", split="observational-extension",
                assignment_mode="observational", unmeasured_confounding=confounding,
            )
            frame = household_metrics(data)
            estimate = estimate_observational_effect(frame, experiment_seed + 1, draws)
            rows.append({
                "scenario": scenario,
                "unmeasured_confounding_strength": confounding,
                "n": n,
                "known_population_ate": data.scenario.return_effect,
                "assignment_rate": float(frame.assignment.mean()),
                "observational_estimate": estimate,
            })
    return {
        "seed": seed,
        "n_per_run": n,
        "bootstrap_draws": draws,
        "scenarios": list(scenarios),
        "unmeasured_confounding_grid": list(confounding_grid),
        "assignment_mode": "observational synthetic selection",
        "measured_covariates": list(OBSERVED_COVARIATES),
        "forbidden_estimator_inputs": ["assignment_probability_oracle", "unmeasured_confounding_strength_oracle", "return_probability", "latent_loyalty_oracle"],
        "rows": rows,
        "status": "exploratory_not_randomized_itt",
        "warning": "Observed-covariate adjustment does not remove unmeasured confounding; estimates are synthetic demonstrations with the stated assumptions.",
    }


def observational_replicated_sensitivity(
    seed: int = 8302723,
    n: int = 2000,
    replicates: int = 200,
    scenarios: tuple[str, ...] = ("helpful", "unrelated", "misleading"),
    confounding_grid: tuple[float, ...] = (0.0, 0.5, 1.0),
    confidence_level: float = 0.95,
) -> dict:
    if n < 100 or n > 20000 or replicates < 30:
        raise ValueError("Use 100-20000 households and at least 30 independent replicates per cell.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one.")
    if not scenarios or any(scenario not in SCENARIOS for scenario in scenarios):
        raise ValueError("Replicated sensitivity requires registered scenarios.")
    if not confounding_grid or any(not 0 <= value <= 1 for value in confounding_grid):
        raise ValueError("Confounding strengths must be between 0 and 1.")

    cells = len(scenarios) * len(confounding_grid)
    family_alpha = 1 - confidence_level
    per_cell_alpha = family_alpha / cells
    z_critical = float(norm.ppf(1 - family_alpha / 2))
    rows = []
    for scenario_index, scenario in enumerate(scenarios):
        for confounding_index, confounding in enumerate(confounding_grid):
            effects = []
            biases = []
            naive_biases = []
            covered = 0
            overlap_passed = []
            common_support = []
            outside_overlap = []
            effective_sample_sizes = {"0": [], "1": []}
            true_effect = SCENARIOS[scenario].return_effect

            for replicate in range(replicates):
                replicate_seed = int(np.random.SeedSequence(
                    [seed, scenario_index, confounding_index, replicate]
                ).generate_state(1)[0])
                data = simulate(
                    scenario=scenario,
                    n=n,
                    seed=replicate_seed,
                    experiment_id=f"obs-rep-{scenario}-{confounding}-{replicate:04d}",
                    split="observational-replication",
                    assignment_mode="observational",
                    unmeasured_confounding=confounding,
                    generate_events=False,
                )
                frame = data.households
                effect, overlap = _aipw_effect(frame)
                standard_error = overlap["aipw_influence_function_se"]
                lower = effect - z_critical * standard_error
                upper = effect + z_critical * standard_error
                effects.append(effect)
                biases.append(effect - true_effect)
                naive_difference = float(
                    frame.loc[frame.assignment == 1, "returned_d29_56"].mean()
                    - frame.loc[frame.assignment == 0, "returned_d29_56"].mean()
                )
                naive_biases.append(naive_difference - true_effect)
                covered += int(lower <= true_effect <= upper)
                overlap_passed.append(overlap["overlap_check_passed"])
                common_support.append(overlap["fraction_inside_common_support"])
                outside_overlap.append(overlap["fraction_outside_overlap_range_0_05_0_95"])
                for arm in ("0", "1"):
                    effective_sample_sizes[arm].append(overlap["ipw_effective_sample_size_by_arm"][arm])

            bias_array = np.asarray(biases)
            mean_bias = float(bias_array.mean())
            bias_mc_se = float(bias_array.std(ddof=1) / np.sqrt(replicates))
            bias_critical = float(student_t.ppf(1 - per_cell_alpha / 2, replicates - 1))
            coverage = covered / replicates
            coverage_lower = 0.0 if covered == 0 else float(beta.ppf(per_cell_alpha / 2, covered, replicates - covered + 1))
            coverage_upper = 1.0 if covered == replicates else float(beta.ppf(1 - per_cell_alpha / 2, covered + 1, replicates - covered))
            rows.append({
                "scenario": scenario,
                "unmeasured_confounding_strength": confounding,
                "n": n,
                "replicates": replicates,
                "known_population_ate": true_effect,
                "mean_aipw_effect": float(np.mean(effects)),
                "mean_aipw_bias": mean_bias,
                "aipw_bias_mc_se": bias_mc_se,
                "aipw_bias_familywise_mc_interval": [
                    mean_bias - bias_critical * bias_mc_se,
                    mean_bias + bias_critical * bias_mc_se,
                ],
                "aipw_bias_rmse": float(np.sqrt(np.mean(np.square(bias_array)))),
                "mean_naive_descriptive_bias": float(np.mean(naive_biases)),
                "aipw_wald_interval_coverage": coverage,
                "aipw_wald_covered_replicates": covered,
                "aipw_wald_coverage_familywise_mc_interval": [coverage_lower, coverage_upper],
                "overlap_check_pass_rate": float(np.mean(overlap_passed)),
                "mean_fraction_inside_common_support": float(np.mean(common_support)),
                "mean_fraction_outside_0_05_0_95": float(np.mean(outside_overlap)),
                "mean_ipw_effective_sample_size_by_arm": {
                    arm: float(np.mean(values)) for arm, values in effective_sample_sizes.items()
                },
            })

    return {
        "study_id": "framesignal-observational-replicated-sensitivity-v1",
        "seed": seed,
        "n_per_replicate": n,
        "replicates_per_cell": replicates,
        "scenarios": list(scenarios),
        "unmeasured_confounding_grid": list(confounding_grid),
        "confidence_level": confidence_level,
        "number_of_cells": cells,
        "familywise_mc_interval_scope": "Bonferroni familywise intervals across the fixed scenario-by-confounding cells; exact Clopper-Pearson intervals for coverage proportions and Student-t intervals for mean bias.",
        "aipw_interval_method": "Normal Wald intervals using the empirical variance of the AIPW pseudo-outcome within each replicate; distinct from the household-bootstrap intervals in the illustrative observational report.",
        "assignment_mode": "observational synthetic selection",
        "measured_covariates": list(OBSERVED_COVARIATES),
        "forbidden_estimator_inputs": ["assignment_probability_oracle", "unmeasured_confounding_strength_oracle", "return_probability", "latent_loyalty_oracle"],
        "rows": rows,
        "status": "exploratory_replicated_synthetic_sensitivity_not_randomized_itt",
        "warning": "Monte Carlo results characterize only this constructed selection model. AIPW cannot remove hidden confounding; coverage intervals are not evidence of real-world identification or proxy approval.",
    }


def observational_robustness_stress(
    seed: int = 66752021,
    n: int = 2000,
    replicates: int = 300,
    scenario: str = "helpful",
    overlap_profiles: tuple[dict, ...] = (
        {"name": "moderate", "measured_selection_strength": 1.0},
        {"name": "weak", "measured_selection_strength": 3.0},
    ),
    nuisance_profiles: tuple[dict, ...] = (
        {"name": "correct_both", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.0},
        {"name": "propensity_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.0},
        {"name": "outcome_misspecified", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.3},
        {"name": "both_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.3},
    ),
    confidence_level: float = 0.95,
) -> dict:
    if n < 100 or n > 20000 or replicates < 30:
        raise ValueError("Use 100-20000 households and at least 30 independent replicates per cell.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one.")
    if scenario not in SCENARIOS:
        raise ValueError("Robustness stress requires a registered scenario.")
    if not overlap_profiles or not nuisance_profiles:
        raise ValueError("At least one overlap and nuisance-model profile is required.")
    if any(not 0 <= profile["measured_selection_strength"] <= 5 for profile in overlap_profiles):
        raise ValueError("Measured-selection strengths must be between 0 and 5.")
    if any(
        not 0 <= profile["propensity_nonlinearity"] <= 3
        or not 0 <= profile["outcome_nonlinearity"] <= 0.4
        for profile in nuisance_profiles
    ):
        raise ValueError("Nuisance nonlinearities are outside the supported ranges.")

    cells = len(overlap_profiles) * len(nuisance_profiles)
    family_alpha = 1 - confidence_level
    per_cell_alpha = family_alpha / cells
    z_critical = float(norm.ppf(1 - family_alpha / 2))
    true_effect = SCENARIOS[scenario].return_effect
    rows = []
    for overlap_index, overlap_profile in enumerate(overlap_profiles):
        for nuisance_index, nuisance_profile in enumerate(nuisance_profiles):
            biases = []
            covered = 0
            overlap_passed = []
            common_support = []
            outside_overlap = []
            effective_sample_sizes = {"0": [], "1": []}
            assignment_rates = []

            for replicate in range(replicates):
                replicate_seed = int(np.random.SeedSequence(
                    [seed, overlap_index, nuisance_index, replicate]
                ).generate_state(1)[0])
                data = simulate(
                    scenario=scenario,
                    n=n,
                    seed=replicate_seed,
                    experiment_id=f"robust-{overlap_index}-{nuisance_index}-{replicate:04d}",
                    split="observational-robustness-stress",
                    assignment_mode="observational",
                    unmeasured_confounding=0.0,
                    generate_events=False,
                    measured_selection_strength=overlap_profile["measured_selection_strength"],
                    propensity_nonlinearity=nuisance_profile["propensity_nonlinearity"],
                    outcome_nonlinearity=nuisance_profile["outcome_nonlinearity"],
                )
                frame = data.households
                effect, overlap = _aipw_effect(frame)
                standard_error = overlap["aipw_influence_function_se"]
                covered += int(effect - z_critical * standard_error <= true_effect <= effect + z_critical * standard_error)
                biases.append(effect - true_effect)
                overlap_passed.append(overlap["overlap_check_passed"])
                common_support.append(overlap["fraction_inside_common_support"])
                outside_overlap.append(overlap["fraction_outside_overlap_range_0_05_0_95"])
                assignment_rates.append(float(frame.assignment.mean()))
                for arm in ("0", "1"):
                    effective_sample_sizes[arm].append(overlap["ipw_effective_sample_size_by_arm"][arm])

            bias_array = np.asarray(biases)
            mean_bias = float(bias_array.mean())
            bias_mc_se = float(bias_array.std(ddof=1) / np.sqrt(replicates))
            bias_critical = float(student_t.ppf(1 - per_cell_alpha / 2, replicates - 1))
            coverage = covered / replicates
            coverage_lower = 0.0 if covered == 0 else float(beta.ppf(per_cell_alpha / 2, covered, replicates - covered + 1))
            coverage_upper = 1.0 if covered == replicates else float(beta.ppf(1 - per_cell_alpha / 2, covered + 1, replicates - covered))
            rows.append({
                "overlap_profile": overlap_profile["name"],
                "measured_selection_strength": overlap_profile["measured_selection_strength"],
                "nuisance_profile": nuisance_profile["name"],
                "propensity_nonlinearity": nuisance_profile["propensity_nonlinearity"],
                "outcome_nonlinearity": nuisance_profile["outcome_nonlinearity"],
                "n": n,
                "replicates": replicates,
                "known_population_ate": true_effect,
                "mean_aipw_bias": mean_bias,
                "aipw_bias_mc_se": bias_mc_se,
                "aipw_bias_familywise_mc_interval": [
                    mean_bias - bias_critical * bias_mc_se,
                    mean_bias + bias_critical * bias_mc_se,
                ],
                "aipw_bias_rmse": float(np.sqrt(np.mean(np.square(bias_array)))),
                "aipw_wald_interval_coverage": coverage,
                "aipw_wald_covered_replicates": covered,
                "aipw_wald_coverage_familywise_mc_interval": [coverage_lower, coverage_upper],
                "overlap_check_pass_rate": float(np.mean(overlap_passed)),
                "mean_assignment_rate": float(np.mean(assignment_rates)),
                "mean_fraction_inside_common_support": float(np.mean(common_support)),
                "mean_fraction_outside_0_05_0_95": float(np.mean(outside_overlap)),
                "mean_ipw_effective_sample_size_by_arm": {
                    arm: float(np.mean(values)) for arm, values in effective_sample_sizes.items()
                },
            })

    return {
        "study_id": "framesignal-observational-positivity-misspecification-v1",
        "seed": seed,
        "scenario": scenario,
        "n_per_replicate": n,
        "replicates_per_cell": replicates,
        "unmeasured_confounding": 0.0,
        "overlap_profiles": list(overlap_profiles),
        "nuisance_profiles": list(nuisance_profiles),
        "confidence_level": confidence_level,
        "number_of_cells": cells,
        "forbidden_estimator_inputs": [
            "assignment_probability_oracle", "latent_loyalty_oracle", "return_probability",
            "measured_selection_strength_oracle", "propensity_nonlinearity_oracle", "outcome_nonlinearity_oracle",
        ],
        "familywise_mc_interval_scope": "Bonferroni familywise intervals across the fixed overlap-by-nuisance cells; exact Clopper-Pearson intervals for coverage proportions and Student-t intervals for mean bias.",
        "aipw_interval_method": "Normal Wald intervals using the empirical variance of the AIPW pseudo-outcome within each replicate.",
        "rows": rows,
        "status": "exploratory_synthetic_positivity_and_model_robustness_stress_not_randomized_itt",
        "warning": "The truth and model-correctness labels are exact only under this constructed generator. Monte Carlo summaries do not establish external validity or real-world identification.",
    }


def observational_overlap_oracle_audit(
    seed: int = 66752021,
    n: int = 2000,
    replicates: int = 300,
    scenario: str = "helpful",
    overlap_profiles: tuple[dict, ...] = (
        {"name": "moderate", "measured_selection_strength": 1.0},
        {"name": "weak", "measured_selection_strength": 3.0},
    ),
    nuisance_profiles: tuple[dict, ...] = (
        {"name": "correct_both", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.0},
        {"name": "propensity_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.0},
        {"name": "outcome_misspecified", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.3},
        {"name": "both_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.3},
    ),
    confidence_level: float = 0.95,
) -> dict:
    if n < 100 or n > 20000 or replicates < 30:
        raise ValueError("Use 100-20000 households and at least 30 paired replicates per cell.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one.")
    if scenario not in SCENARIOS or not overlap_profiles or not nuisance_profiles:
        raise ValueError("Oracle audit requires a registered scenario and nonempty stress profiles.")

    cells = len(overlap_profiles) * len(nuisance_profiles)
    family_alpha = 1 - confidence_level
    per_cell_alpha = family_alpha / cells
    difference_critical = float(student_t.ppf(1 - per_cell_alpha / 2, replicates - 1))
    rows = []

    def binomial_interval(successes: int) -> list[float]:
        lower = 0.0 if successes == 0 else float(beta.ppf(per_cell_alpha / 2, successes, replicates - successes + 1))
        upper = 1.0 if successes == replicates else float(beta.ppf(1 - per_cell_alpha / 2, successes + 1, replicates - successes))
        return [lower, upper]

    def mean_interval(values: list[float]) -> list[float]:
        array = np.asarray(values, dtype=float)
        mean = float(array.mean())
        standard_error = float(array.std(ddof=1) / np.sqrt(replicates))
        return [mean - difference_critical * standard_error, mean + difference_critical * standard_error]

    for overlap_index, overlap_profile in enumerate(overlap_profiles):
        for nuisance_index, nuisance_profile in enumerate(nuisance_profiles):
            estimated_pass = []
            oracle_pass = []
            false_warnings = []
            missed_warnings = []
            outside_differences = []
            support_differences = []
            estimated_outside = []
            oracle_outside = []
            estimated_ess = {"0": [], "1": []}
            oracle_ess = {"0": [], "1": []}

            for replicate in range(replicates):
                replicate_seed = int(np.random.SeedSequence(
                    [seed, overlap_index, nuisance_index, replicate]
                ).generate_state(1)[0])
                data = simulate(
                    scenario=scenario,
                    n=n,
                    seed=replicate_seed,
                    experiment_id=f"robust-{overlap_index}-{nuisance_index}-{replicate:04d}",
                    split="observational-robustness-stress",
                    assignment_mode="observational",
                    unmeasured_confounding=0.0,
                    generate_events=False,
                    measured_selection_strength=overlap_profile["measured_selection_strength"],
                    propensity_nonlinearity=nuisance_profile["propensity_nonlinearity"],
                    outcome_nonlinearity=nuisance_profile["outcome_nonlinearity"],
                )
                frame = data.households
                _, fitted_diagnostics = _aipw_effect(frame)
                oracle_propensity = frame.assignment_probability_oracle.to_numpy(dtype=float)
                assignment = frame.assignment.to_numpy(dtype=float)
                oracle_diagnostics = _overlap_diagnostics(
                    oracle_propensity,
                    np.clip(oracle_propensity, *PROPENSITY_CLIP),
                    assignment,
                )
                fitted_ok = fitted_diagnostics["overlap_check_passed"]
                oracle_ok = oracle_diagnostics["overlap_check_passed"]
                estimated_pass.append(fitted_ok)
                oracle_pass.append(oracle_ok)
                false_warnings.append(not fitted_ok and oracle_ok)
                missed_warnings.append(fitted_ok and not oracle_ok)
                fitted_outside = fitted_diagnostics["fraction_outside_overlap_range_0_05_0_95"]
                oracle_outside_value = oracle_diagnostics["fraction_outside_overlap_range_0_05_0_95"]
                estimated_outside.append(fitted_outside)
                oracle_outside.append(oracle_outside_value)
                outside_differences.append(fitted_outside - oracle_outside_value)
                support_differences.append(
                    fitted_diagnostics["fraction_inside_common_support"]
                    - oracle_diagnostics["fraction_inside_common_support"]
                )
                for arm in ("0", "1"):
                    estimated_ess[arm].append(fitted_diagnostics["ipw_effective_sample_size_by_arm"][arm])
                    oracle_ess[arm].append(oracle_diagnostics["ipw_effective_sample_size_by_arm"][arm])

            false_warning_count = int(np.sum(false_warnings))
            missed_warning_count = int(np.sum(missed_warnings))
            rows.append({
                "overlap_profile": overlap_profile["name"],
                "nuisance_profile": nuisance_profile["name"],
                "replicates": replicates,
                "estimated_overlap_pass_rate": float(np.mean(estimated_pass)),
                "oracle_overlap_pass_rate": float(np.mean(oracle_pass)),
                "false_warning_count": false_warning_count,
                "false_warning_rate": false_warning_count / replicates,
                "false_warning_familywise_mc_interval": binomial_interval(false_warning_count),
                "missed_warning_count": missed_warning_count,
                "missed_warning_rate": missed_warning_count / replicates,
                "missed_warning_familywise_mc_interval": binomial_interval(missed_warning_count),
                "mean_estimated_fraction_outside_0_05_0_95": float(np.mean(estimated_outside)),
                "mean_oracle_fraction_outside_0_05_0_95": float(np.mean(oracle_outside)),
                "mean_fitted_minus_oracle_outside_difference": float(np.mean(outside_differences)),
                "fitted_minus_oracle_outside_difference_familywise_mc_interval": mean_interval(outside_differences),
                "mean_fitted_minus_oracle_common_support_difference": float(np.mean(support_differences)),
                "fitted_minus_oracle_common_support_difference_familywise_mc_interval": mean_interval(support_differences),
                "mean_estimated_ess_by_arm": {arm: float(np.mean(values)) for arm, values in estimated_ess.items()},
                "mean_oracle_ess_by_arm": {arm: float(np.mean(values)) for arm, values in oracle_ess.items()},
            })

    return {
        "study_id": "framesignal-observational-oracle-overlap-audit-v1",
        "seed": seed,
        "scenario": scenario,
        "n_per_replicate": n,
        "replicates_per_cell": replicates,
        "number_of_cells": cells,
        "same_seed_replay_of": "framesignal-observational-positivity-misspecification-v1",
        "same_seed_replay": True,
        "unmeasured_confounding": 0.0,
        "oracle_usage": "Diagnostic comparison only; oracle fields are not estimator or AIPW inputs.",
        "forbidden_estimator_inputs": ["assignment_probability_oracle", "return_probability", "latent_loyalty_oracle"],
        "familywise_mc_interval_scope": "Bonferroni familywise intervals across the fixed eight cells; exact Clopper-Pearson intervals for warning rates and Student-t intervals for paired fitted-minus-oracle diagnostic differences.",
        "rows": rows,
        "status": "exploratory_oracle_overlap_diagnostic_audit_not_randomized_itt",
        "warning": "Oracle assignment probabilities are used only to audit overlap diagnostics under this known synthetic generator. Results do not validate real-world identification or proxy approval.",
    }


def observational_crossfit_overlap_audit(
    seed: int = 66752021,
    n: int = 2000,
    replicates: int = 300,
    folds: int = 5,
    scenario: str = "helpful",
    overlap_profiles: tuple[dict, ...] = (
        {"name": "moderate", "measured_selection_strength": 1.0},
        {"name": "weak", "measured_selection_strength": 3.0},
    ),
    nuisance_profiles: tuple[dict, ...] = (
        {"name": "correct_both", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.0},
        {"name": "propensity_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.0},
        {"name": "outcome_misspecified", "propensity_nonlinearity": 0.0, "outcome_nonlinearity": 0.3},
        {"name": "both_misspecified", "propensity_nonlinearity": 2.0, "outcome_nonlinearity": 0.3},
    ),
    confidence_level: float = 0.95,
) -> dict:
    if n < 100 or n > 20000 or replicates < 30:
        raise ValueError("Use 100-20000 households and at least 30 paired replicates per cell.")
    if folds < 2 or folds > n:
        raise ValueError("Use at least two cross-fitting folds and no more folds than households.")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between zero and one.")
    if scenario not in SCENARIOS or not overlap_profiles or not nuisance_profiles:
        raise ValueError("Cross-fit audit requires a registered scenario and nonempty stress profiles.")

    cells = len(overlap_profiles) * len(nuisance_profiles)
    family_alpha = 1 - confidence_level
    per_cell_alpha = family_alpha / cells
    difference_critical = float(student_t.ppf(1 - per_cell_alpha / 2, replicates - 1))
    rows = []

    def binomial_interval(successes: int) -> list[float]:
        lower = 0.0 if successes == 0 else float(beta.ppf(per_cell_alpha / 2, successes, replicates - successes + 1))
        upper = 1.0 if successes == replicates else float(beta.ppf(1 - per_cell_alpha / 2, successes + 1, replicates - successes))
        return [lower, upper]

    def paired_interval(values: list[float]) -> list[float]:
        array = np.asarray(values, dtype=float)
        mean = float(array.mean())
        standard_error = float(array.std(ddof=1) / np.sqrt(replicates))
        return [mean - difference_critical * standard_error, mean + difference_critical * standard_error]

    for overlap_index, overlap_profile in enumerate(overlap_profiles):
        for nuisance_index, nuisance_profile in enumerate(nuisance_profiles):
            in_sample_false = []
            crossfit_false = []
            in_sample_missed = []
            crossfit_missed = []
            paired_false_differences = []
            in_sample_pass = []
            crossfit_pass = []
            oracle_pass = []
            in_sample_outside = []
            crossfit_outside = []
            oracle_outside = []

            for replicate in range(replicates):
                replicate_seed = int(np.random.SeedSequence(
                    [seed, overlap_index, nuisance_index, replicate]
                ).generate_state(1)[0])
                data = simulate(
                    scenario=scenario,
                    n=n,
                    seed=replicate_seed,
                    experiment_id=f"robust-{overlap_index}-{nuisance_index}-{replicate:04d}",
                    split="observational-robustness-stress",
                    assignment_mode="observational",
                    unmeasured_confounding=0.0,
                    generate_events=False,
                    measured_selection_strength=overlap_profile["measured_selection_strength"],
                    propensity_nonlinearity=nuisance_profile["propensity_nonlinearity"],
                    outcome_nonlinearity=nuisance_profile["outcome_nonlinearity"],
                )
                frame = data.households
                _, in_sample_diagnostics = _aipw_effect(frame)
                crossfit_raw, crossfit_clipped = cross_fitted_propensity_predictions(
                    frame,
                    folds=folds,
                    seed=replicate_seed ^ 0x5F3759DF,
                )
                crossfit_diagnostics = _overlap_diagnostics(
                    crossfit_raw,
                    crossfit_clipped,
                    frame.assignment.to_numpy(dtype=float),
                )
                oracle_propensity = frame.assignment_probability_oracle.to_numpy(dtype=float)
                oracle_diagnostics = _overlap_diagnostics(
                    oracle_propensity,
                    np.clip(oracle_propensity, *PROPENSITY_CLIP),
                    frame.assignment.to_numpy(dtype=float),
                )

                in_false = not in_sample_diagnostics["overlap_check_passed"] and oracle_diagnostics["overlap_check_passed"]
                cross_false = not crossfit_diagnostics["overlap_check_passed"] and oracle_diagnostics["overlap_check_passed"]
                in_missed = in_sample_diagnostics["overlap_check_passed"] and not oracle_diagnostics["overlap_check_passed"]
                cross_missed = crossfit_diagnostics["overlap_check_passed"] and not oracle_diagnostics["overlap_check_passed"]
                in_sample_false.append(in_false)
                crossfit_false.append(cross_false)
                in_sample_missed.append(in_missed)
                crossfit_missed.append(cross_missed)
                paired_false_differences.append(float(cross_false) - float(in_false))
                in_sample_pass.append(in_sample_diagnostics["overlap_check_passed"])
                crossfit_pass.append(crossfit_diagnostics["overlap_check_passed"])
                oracle_pass.append(oracle_diagnostics["overlap_check_passed"])
                in_sample_outside.append(in_sample_diagnostics["fraction_outside_overlap_range_0_05_0_95"])
                crossfit_outside.append(crossfit_diagnostics["fraction_outside_overlap_range_0_05_0_95"])
                oracle_outside.append(oracle_diagnostics["fraction_outside_overlap_range_0_05_0_95"])

            in_false_count = int(np.sum(in_sample_false))
            cross_false_count = int(np.sum(crossfit_false))
            in_missed_count = int(np.sum(in_sample_missed))
            cross_missed_count = int(np.sum(crossfit_missed))
            rows.append({
                "overlap_profile": overlap_profile["name"],
                "nuisance_profile": nuisance_profile["name"],
                "folds": folds,
                "replicates": replicates,
                "in_sample_overlap_pass_rate": float(np.mean(in_sample_pass)),
                "crossfit_overlap_pass_rate": float(np.mean(crossfit_pass)),
                "oracle_overlap_pass_rate": float(np.mean(oracle_pass)),
                "in_sample_false_warning_rate": in_false_count / replicates,
                "in_sample_false_warning_familywise_mc_interval": binomial_interval(in_false_count),
                "crossfit_false_warning_rate": cross_false_count / replicates,
                "crossfit_false_warning_familywise_mc_interval": binomial_interval(cross_false_count),
                "in_sample_missed_warning_rate": in_missed_count / replicates,
                "in_sample_missed_warning_familywise_mc_interval": binomial_interval(in_missed_count),
                "crossfit_missed_warning_rate": cross_missed_count / replicates,
                "crossfit_missed_warning_familywise_mc_interval": binomial_interval(cross_missed_count),
                "crossfit_minus_in_sample_false_warning_rate": float(np.mean(paired_false_differences)),
                "crossfit_minus_in_sample_false_warning_familywise_mc_interval": paired_interval(paired_false_differences),
                "mean_in_sample_fraction_outside_0_05_0_95": float(np.mean(in_sample_outside)),
                "mean_crossfit_fraction_outside_0_05_0_95": float(np.mean(crossfit_outside)),
                "mean_oracle_fraction_outside_0_05_0_95": float(np.mean(oracle_outside)),
            })

    return {
        "study_id": "framesignal-observational-crossfit-overlap-audit-v1",
        "seed": seed,
        "scenario": scenario,
        "n_per_replicate": n,
        "replicates_per_cell": replicates,
        "cross_fitting_folds": folds,
        "number_of_cells": cells,
        "same_seed_replay_of": "framesignal-observational-positivity-misspecification-v1",
        "same_seed_replay": True,
        "unmeasured_confounding": 0.0,
        "audit_scope": "Overlap diagnostics only; no cross-fitted AIPW effect is estimated in this report.",
        "oracle_usage": "Diagnostic comparison only; oracle fields are not estimator or AIPW inputs.",
        "forbidden_estimator_inputs": ["assignment_probability_oracle", "return_probability", "latent_loyalty_oracle"],
        "familywise_mc_interval_scope": "Bonferroni familywise intervals across the fixed eight cells; Clopper-Pearson for warning rates and Student-t intervals for paired crossfit-minus-in-sample false-warning differences.",
        "rows": rows,
        "status": "exploratory_crossfit_overlap_diagnostic_audit_not_randomized_itt",
        "warning": "Cross-fitted and oracle propensity diagnostics are compared only under this known synthetic generator. Oracle probabilities are unavailable in real observational data; the audit does not validate real-world identification.",
    }