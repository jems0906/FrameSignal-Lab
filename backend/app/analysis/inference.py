import numpy as np
from scipy import stats


def difference_in_means(control, treatment, alpha: float = 0.05) -> dict:
    control = np.asarray(control, dtype=float)
    treatment = np.asarray(treatment, dtype=float)
    if min(len(control), len(treatment)) < 2 or not np.all(np.isfinite(np.concatenate([control, treatment]))):
        raise ValueError("Need at least two finite household outcomes per arm.")
    effect = float(treatment.mean() - control.mean())
    control_variance = float(control.var(ddof=1) / len(control))
    treatment_variance = float(treatment.var(ddof=1) / len(treatment))
    standard_error = float(np.sqrt(control_variance + treatment_variance))
    denominator = control_variance ** 2 / (len(control) - 1) + treatment_variance ** 2 / (len(treatment) - 1)
    degrees = (control_variance + treatment_variance) ** 2 / denominator if denominator else len(control) + len(treatment) - 2
    critical = float(stats.t.ppf(1 - alpha / 2, degrees))
    p_value = float(2 * stats.t.sf(abs(effect / standard_error), degrees)) if standard_error else (1.0 if effect == 0 else 0.0)
    return {
        "control_mean": float(control.mean()), "treatment_mean": float(treatment.mean()),
        "effect": effect, "se": standard_error, "lower": effect - critical * standard_error,
        "upper": effect + critical * standard_error, "p_value": p_value,
        "n_control": len(control), "n_treatment": len(treatment), "alpha": alpha,
    }


def completion_comparison(frame, seed: int, draws: int = 400) -> dict:
    rng = np.random.default_rng(seed)
    arms = [frame[frame.assignment == arm] for arm in (0, 1)]

    def ratio(arm):
        starters = int(arm.starter.sum())
        return float(arm.completed_any.sum() / starters) if starters else None

    means = [ratio(arm) for arm in arms]
    samples = []
    for _ in range(draws):
        ratios = [ratio(arm.iloc[rng.integers(0, len(arm), len(arm))]) for arm in arms]
        if all(value is not None for value in ratios):
            samples.append(ratios[1] - ratios[0])
    valid = all(value is not None for value in means)
    return {
        "control_mean": means[0], "treatment_mean": means[1],
        "effect": means[1] - means[0] if valid else None,
        "lower": float(np.quantile(samples, 0.025)) if samples else None,
        "upper": float(np.quantile(samples, 0.975)) if samples else None,
        "se": float(np.std(samples, ddof=1)) if len(samples) > 1 else None,
        "p_value": None, "n_control": len(arms[0]), "n_treatment": len(arms[1]),
        "starters_control": int(arms[0].starter.sum()), "starters_treatment": int(arms[1].starter.sum()),
        "warning": "Conditions on post-assignment starts; not an ITT causal effect. Complete households resampled.",
        "bootstrap_draws": draws,
    }