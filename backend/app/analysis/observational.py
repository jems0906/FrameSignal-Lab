import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

from app.simulations.generator import SCENARIOS, simulate
from app.metrics.registry import household_metrics


OBSERVED_COVARIATES = ("observed_affinity", "observed_log_opportunity")
PROPENSITY_CLIP = (0.01, 0.99)
OVERLAP_RANGE = (0.05, 0.95)


def _nuisance_predictions(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    covariates = frame.loc[:, OBSERVED_COVARIATES].to_numpy(dtype=float)
    means = covariates.mean(axis=0)
    scales = covariates.std(axis=0)
    scales[scales == 0] = 1
    standardized = (covariates - means) / scales
    assignment = frame.assignment.to_numpy(dtype=float)
    outcome = frame.returned_d29_56.to_numpy(dtype=float)

    propensity_design = np.column_stack([np.ones(len(frame)), standardized])

    def objective(coefficients):
        linear = propensity_design @ coefficients
        loss = np.mean(np.logaddexp(0, linear) - assignment * linear) + 0.5e-6 * np.sum(coefficients[1:] ** 2)
        gradient = propensity_design.T @ (expit(linear) - assignment) / len(frame)
        gradient[1:] += 1e-6 * coefficients[1:]
        return float(loss), gradient

    fitted = minimize(objective, np.zeros(propensity_design.shape[1]), jac=True, method="L-BFGS-B")
    if not fitted.success and np.linalg.norm(fitted.jac) > 1e-5:
        raise ValueError(f"Propensity model failed to converge: {fitted.message}")
    propensity_raw = expit(propensity_design @ fitted.x)
    propensity = np.clip(propensity_raw, *PROPENSITY_CLIP)

    outcome_design = np.column_stack([np.ones(len(frame)), assignment, standardized])
    coefficients = np.linalg.lstsq(outcome_design, outcome, rcond=None)[0]
    control_design = np.column_stack([np.ones(len(frame)), np.zeros(len(frame)), standardized])
    treatment_design = np.column_stack([np.ones(len(frame)), np.ones(len(frame)), standardized])
    outcome_control = control_design @ coefficients
    outcome_treatment = treatment_design @ coefficients
    return propensity_raw, propensity, outcome_control, outcome_treatment


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
    weights = np.where(assignment == 1, 1 / propensity, 1 / (1 - propensity))
    effective_sample_size = float(weights.sum() ** 2 / np.square(weights).sum())
    by_arm = [propensity_raw[assignment == arm] for arm in (0, 1)]
    common_lower = max(float(values.min()) for values in by_arm)
    common_upper = min(float(values.max()) for values in by_arm)
    common = (propensity_raw >= common_lower) & (propensity_raw <= common_upper)
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