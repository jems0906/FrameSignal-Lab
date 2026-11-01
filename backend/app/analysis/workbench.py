import copy
import json
import sqlite3
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy import stats

from app.analysis.inference import completion_comparison, difference_in_means
from app.metrics.registry import METRICS, household_metrics
from app.simulations.generator import Simulation, simulate


ROOT = Path(__file__).resolve().parents[3]
PLAN = json.loads((ROOT / "configs" / "analysis_plan.json").read_text())
CANDIDATES = ("qualified_starts", "viewing_days")


def effects(frame, descriptive: bool = True, seed: int = 42) -> dict:
    arms = [frame[frame.assignment == arm] for arm in (0, 1)]
    result = {}
    for metric, card in METRICS.items():
        if metric == "completion":
            if descriptive:
                result[metric] = {**card, **completion_comparison(frame, seed)}
            continue
        alpha = PLAN["candidate_alpha"] if metric in CANDIDATES else 0.05
        result[metric] = {**card, **difference_in_means(arms[0][metric], arms[1][metric], alpha)}
    return result


def sql_audit(data: Simulation) -> dict:
    with sqlite3.connect(":memory:") as database:
        for name in ("households", "titles", "exposures", "events"):
            getattr(data, name).to_sql(name, database, index=False)
        queries = {
            "registered_households": "SELECT COUNT(*) FROM households",
            "households_without_viewing": "SELECT COUNT(*) FROM households h WHERE NOT EXISTS (SELECT 1 FROM events e WHERE e.household_id = h.household_id)",
            "missing_outcomes": "SELECT COUNT(*) FROM households WHERE outcome_observed != 1 OR returned_d29_56 IS NULL",
            "duplicate_households": "SELECT COUNT(*) - COUNT(DISTINCT household_id) FROM households",
            "orphan_events": "SELECT COUNT(*) FROM events e LEFT JOIN households h USING(household_id) WHERE h.household_id IS NULL",
            "invalid_availability": "SELECT COUNT(*) FROM events e JOIN titles t USING(title_id) WHERE e.day < t.available_day",
            "invalid_watch_time": "SELECT COUNT(*) FROM events WHERE minutes < 0 OR minutes > runtime_minutes",
            "invalid_return_window": "SELECT COUNT(*) FROM households WHERE (returned_d29_56 = 1 AND (return_day < 29 OR return_day > 56)) OR (returned_d29_56 = 0 AND return_day != -1)",
            "itt_left_join_count": "SELECT COUNT(*) FROM (SELECT h.household_id FROM households h LEFT JOIN events e USING(household_id) GROUP BY h.household_id)",
        }
        counts = {name: int(database.execute(query).fetchone()[0]) for name, query in queries.items()}
    failures = [name for name, count in counts.items() if name not in ("registered_households", "households_without_viewing", "itt_left_join_count") and count != 0]
    if counts["itt_left_join_count"] != counts["registered_households"]:
        failures.append("itt_left_join_count")
    return {"passed": not failures, "failures": failures, "counts": counts, "queries": queries}


def predictive_association(frame, seed: int, draws: int = 300) -> dict:
    rng = np.random.default_rng(seed)
    result = {}
    target = frame.returned_d29_56.to_numpy()
    for metric in CANDIDATES:
        values = frame[metric].to_numpy()
        coefficient = float(np.corrcoef(values, target)[0, 1])
        boot = []
        for _ in range(draws):
            indices = rng.integers(0, len(frame), len(frame))
            boot.append(float(np.corrcoef(values[indices], target[indices])[0, 1]))
        within = [float(np.corrcoef(frame.loc[frame.assignment == arm, metric], frame.loc[frame.assignment == arm, "returned_d29_56"])[0, 1]) for arm in (0, 1)]
        result[metric] = {"correlation": coefficient, "lower": float(np.quantile(boot, 0.025)), "upper": float(np.quantile(boot, 0.975)), "within_arm": within}
    return {"metrics": result, "warning": "Household prediction is not causal surrogacy. Affinity confounds association; pooled correlation also reflects assignment."}


def sensitivity(data: Simulation) -> dict:
    base = household_metrics(data)
    rows = []

    def add(label, frame, note):
        row = {"label": label, "note": note, "effects": {}}
        for metric in ("qualified_starts", "viewing_days", "watch_minutes"):
            row["effects"][metric] = difference_in_means(frame.loc[frame.assignment == 0, metric], frame.loc[frame.assignment == 1, metric])
        rows.append(row)

    add("Days 0-13", base, "Registered household denominator; unadjusted policy ITT.")
    add("Days 0-6", household_metrics(data, 7), "Shorter window; all assigned households retained.")
    capped = base.copy()
    caps = {}
    for metric in ("qualified_starts", "viewing_days", "watch_minutes"):
        caps[metric] = float(base[metric].quantile(0.99))
        capped[metric] = base[metric].clip(upper=caps[metric])
    add("Pooled 99th-percentile cap", capped, "Exploratory winsorization changes the estimand; cap uses both arms.")
    for label, mask in [
        ("Runtime <= 48 minutes", data.events.runtime_minutes <= 48),
        ("Runtime > 48 minutes", data.events.runtime_minutes > 48),
        *[(f"Genre: {genre}", data.events.genre == genre) for genre in ("Drama", "Comedy", "Documentary")],
    ]:
        subset = copy.copy(data)
        subset.events = data.events[mask]
        add(label, household_metrics(subset), "Event subset only; household denominator unchanged. Not a title-quality causal effect.")
    normalized = base.copy()
    for metric in ("qualified_starts", "viewing_days", "watch_minutes"):
        normalized[metric] = base[metric] / base.impressions.clip(lower=1)
    add("Per impression (diagnostic)", normalized, "Post-assignment exposure normalization is NOT the original ITT estimand; zero impressions mapped to zero.")
    runtime = data.events.groupby("genre").agg(events=("event_id", "size"), mean_runtime=("runtime_minutes", "mean"), watch_minutes=("minutes", "sum")).reset_index().to_dict("records")
    rng = np.random.default_rng(data.seed + 900)
    sample_effects = []
    arms = [base[base.assignment == arm] for arm in (0, 1)]
    for _ in range(300):
        samples = [arm.iloc[rng.integers(0, len(arm), len(arm))] for arm in arms]
        sample_effects.append({metric: float(samples[1][metric].mean() - samples[0][metric].mean()) for metric in (*CANDIDATES, "watch_minutes", "returned_d29_56")})
    variation = {metric: {"bootstrap_sd": float(np.std([row[metric] for row in sample_effects], ddof=1)), "lower": float(np.quantile([row[metric] for row in sample_effects], 0.025)), "upper": float(np.quantile([row[metric] for row in sample_effects], 0.975))} for metric in sample_effects[0]}
    exposure = {str(arm): {"mean": float(group.impressions.mean()), "zero_exposure": int((group.impressions == 0).sum())} for arm, group in base.groupby("assignment")}
    return {"rows": rows, "caps": caps, "genre_mix": runtime, "exposure_by_arm": exposure, "sampling_variation": variation, "bootstrap_draws": 300}


def decision_memo(metric_effects: dict) -> dict:
    target = metric_effects["returned_d29_56"]
    starts = metric_effects["qualified_starts"]
    threshold = PLAN["practical_target_effect"]
    if target["lower"] > threshold:
        recommendation = "Advance the fictional policy"
        reason = "The target interval is entirely above the predefined +2 percentage-point practical threshold. This does not validate the proxy generally."
    elif target["upper"] < 0:
        recommendation = "Reject the fictional policy"
        reason = "The longer-horizon target shows harm, regardless of a starts lift."
    else:
        recommendation = "Evidence insufficient to advance"
        reason = "The fixed-horizon target interval does not establish a practically worthwhile benefit. Non-significance is not equivalence."
    return {"recommendation": recommendation, "reason": reason, "starts_target_reversal": starts["effect"] > 0 and target["effect"] < 0, "proxy_recommendation": "Do not replace the return target with qualified starts.", "limitations": ["Synthetic presentation policy, not real-world evidence or Netflix retention.", "No claim about a title's creative quality or artistic value.", "Nine held-out experiments cannot establish transportability across policies.", "Follow up with new preregistered experiments, equivalence margins, and external validation; do not extend this run until significant."]}


@lru_cache(maxsize=12)
def analyze(scenario: str = "helpful", n: int = 2000, seed: int = 20261031) -> dict:
    data = simulate(scenario, n, seed)
    frame = household_metrics(data)
    metric_effects = effects(frame, seed=seed)
    return {
        "scenario": scenario, "description": data.scenario.description, "seed": seed,
        "n": n, "events": len(data.events), "non_viewers": int((~frame.starter).sum()),
        "estimand": "ITT effect of randomized presentation on assigned households returning during days 29-56.",
        "truth": {"return_effect": data.scenario.return_effect, "label": "Synthetic oracle, not an estimated result"},
        "plan": PLAN, "metrics": metric_effects, "prediction": predictive_association(frame, seed + 1),
        "diagnostics": sensitivity(data), "sql": sql_audit(data), "memo": decision_memo(metric_effects),
    }


def direction(effect: float, threshold: float = 0) -> int:
    return 1 if effect > threshold else (-1 if effect < -threshold else 0)


def agreement_uncertainty(experiments: list, metric: str, seed: int, draws: int = 1000) -> dict:
    rng = np.random.default_rng(seed)
    observed = [direction(row["effects"][metric]["effect"]) == direction(row["effects"]["returned_d29_56"]["effect"]) for row in experiments]
    empirical = []
    noise_sensitive = []
    for _ in range(draws):
        sampled = rng.integers(0, len(experiments), len(experiments))
        empirical.append(float(np.mean([observed[index] for index in sampled])))
        indicators = []
        for index in sampled:
            row = experiments[index]
            covariance = np.array(row["effect_covariance"][metric])
            means = [row["effects"][metric]["effect"], row["effects"]["returned_d29_56"]["effect"]]
            candidate, target = rng.multivariate_normal(means, covariance, check_valid="raise")
            indicators.append(direction(candidate) == direction(target))
        noise_sensitive.append(float(np.mean(indicators)))
    resolved = [row for row in experiments if row["effects"]["returned_d29_56"]["lower"] > 0 or row["effects"]["returned_d29_56"]["upper"] < 0]
    oracle_nonnull = [row for row in experiments if row["truth_return_effect"] != 0]
    oracle_agreement = [direction(row["effects"][metric]["effect"]) == direction(row["truth_return_effect"]) for row in oracle_nonnull]
    nulls = [row for row in experiments if row["truth_return_effect"] == 0]
    return {
        "observed_agreement": float(np.mean(observed)), "lower": float(np.quantile(empirical, 0.025)), "upper": float(np.quantile(empirical, 0.975)),
        "noise_lower": float(np.quantile(noise_sensitive, 0.025)), "noise_upper": float(np.quantile(noise_sensitive, 0.975)),
        "n_experiments": len(experiments), "resolved_target_experiments": len(resolved),
        "oracle_nonnull_agreement": float(np.mean(oracle_agreement)) if oracle_agreement else None,
        "oracle_null_proxy_positive": sum(row["effects"][metric]["lower"] > 0 for row in nulls),
        "oracle_null_experiments": len(nulls), "draws": draws,
        "warning": "Experiment bootstrap interval is descriptive with only nine experiments. Correlated Gaussian effect draws propagate household covariance, but are a measurement-error sensitivity analysis, not a definitive surrogate test. Null-target signs are unstable; oracle non-null agreement is reported separately.",
    }


@lru_cache(maxsize=2)
def validation_suite(seed: int = 20261031) -> dict:
    experiments = []
    identities = set()
    for split_index, split in enumerate(PLAN["splits"]):
        for index in range(PLAN["experiments_per_split"]):
            scenario = ("helpful", "unrelated", "misleading")[index % 3]
            strength = (0.6, 1.0, 1.4)[index // 3]
            experiment_id = f"{split}-{index + 1:02d}"
            experiment_seed = int(np.random.SeedSequence([seed, split_index, index]).generate_state(1)[0])
            data = simulate(scenario, PLAN["households_per_experiment"], experiment_seed, experiment_id, split, strength)
            ids = set(data.households.household_id)
            if identities.intersection(ids):
                raise ValueError("Household leakage across experiment splits")
            identities.update(ids)
            frame = household_metrics(data)
            covariance = {}
            for metric in CANDIDATES:
                covariance[metric] = sum(np.cov(group[[metric, "returned_d29_56"]].to_numpy().T, ddof=1) / len(group) for _, group in frame.groupby("assignment")).tolist()
            experiments.append({"id": experiment_id, "split": split, "scenario": scenario, "strength": strength, "seed": experiment_seed,
                                "n": len(frame), "truth_return_effect": data.scenario.return_effect * strength,
                                "effects": effects(frame, descriptive=False), "effect_covariance": covariance,
                                "prediction": {metric: float(np.corrcoef(frame[metric], frame.returned_d29_56)[0, 1]) for metric in CANDIDATES}})
    summaries = {}
    for split_index, split in enumerate(PLAN["splits"]):
        rows = [row for row in experiments if row["split"] == split]
        summaries[split] = {metric: agreement_uncertainty(rows, metric, seed + split_index, PLAN["agreement_draws"]) for metric in CANDIDATES}
    return {"plan": PLAN, "experiments": experiments, "agreement": summaries, "unique_households": len(identities),
            "leakage_check": True, "learned_weights": None, "frozen_candidates": list(CANDIDATES),
            "decision": "Reject qualified starts as a universal surrogate; viewing days also requires independent validation. No candidate is authorized to replace the target."}


def proportion_interval(successes: int, total: int, confidence_level: float = 0.95) -> dict:
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be strictly between 0 and 1.")
    interval = stats.binomtest(successes, total).proportion_ci(confidence_level=confidence_level, method="wilson")
    return {"rate": successes / total, "lower": float(interval.low), "upper": float(interval.high)}


@lru_cache(maxsize=4)
def operating_characteristics(seed: int = 20261031, repetitions: int = 1000, n: int = 2000, rate_confidence_level: float = 0.95) -> dict:
    if not 50 <= repetitions <= 10000 or not 100 <= n <= 20000:
        raise ValueError("Use 50-10000 repetitions and 100-20000 households.")
    if not 0 < rate_confidence_level < 1:
        raise ValueError("rate_confidence_level must be strictly between 0 and 1.")
    rows = []
    for effect_index, true_effect in enumerate((0.0, 0.02, 0.04, 0.06, 0.10)):
        rng = np.random.default_rng(np.random.SeedSequence([seed, effect_index, 800]))
        covered, rejected, practical = 0, 0, 0
        estimates, widths = [], []
        for _ in range(repetitions):
            assignment = rng.permutation(np.arange(n) % 2)
            affinity = rng.beta(2, 2, n)
            target = rng.binomial(1, 0.40 + 0.25 * affinity + assignment * true_effect)
            estimate = difference_in_means(target[assignment == 0], target[assignment == 1])
            covered += estimate["lower"] <= true_effect <= estimate["upper"]
            rejected += estimate["p_value"] < 0.05
            practical += estimate["lower"] > PLAN["practical_target_effect"]
            estimates.append(estimate["effect"])
            widths.append(estimate["upper"] - estimate["lower"])
        rows.append({"true_effect": true_effect, "coverage": proportion_interval(covered, repetitions, rate_confidence_level),
                 "rejection_rate": proportion_interval(rejected, repetitions, rate_confidence_level), "practical_success": proportion_interval(practical, repetitions, rate_confidence_level),
                     "bias": float(np.mean(estimates) - true_effect), "bias_mc_se": float(np.std(estimates, ddof=1) / np.sqrt(repetitions)),
                     "sampling_variance": float(np.var(estimates, ddof=1)), "mean_interval_width": float(np.mean(widths))})
    calibration_flags = [
        f"At true effect {100 * row['true_effect']:.0f} pp, the Monte Carlo coverage interval excludes nominal 95% coverage. Investigate in a new, prospectively specified simulation study; do not tune this run to pass."
        for row in rows if row["coverage"]["upper"] < 0.95 or row["coverage"]["lower"] > 0.95
    ]
    return {"seed": seed, "repetitions": repetitions, "n": n, "rate_confidence_level": rate_confidence_level,
            "rows": rows, "calibration_flags": calibration_flags,
            "scope": "Target inference only, using the same household return DGP. Null rejection is false-positive rate; non-null rejection is two-sided power. Wilson intervals quantify Monte Carlo uncertainty. Candidate-surrogacy certification is not implied."}