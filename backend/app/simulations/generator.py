from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import expit


@dataclass(frozen=True)
class Scenario:
    name: str
    starts_lift: float
    engagement_shift: float
    return_effect: float
    description: str


SCENARIOS = {
    "helpful": Scenario("helpful", 0.45, 0.16, 0.06, "Relevant presentation increases use and later return."),
    "unrelated": Scenario("unrelated", 0.65, -0.08, 0.0, "Attention-grabbing presentation increases starts without changing return."),
    "misleading": Scenario("misleading", 0.85, -0.30, -0.06, "Aggressive presentation increases starts but reduces later return."),
}


@dataclass
class Simulation:
    households: pd.DataFrame
    titles: pd.DataFrame
    exposures: pd.DataFrame
    events: pd.DataFrame
    scenario: Scenario
    seed: int
    experiment_id: str
    split: str
    assignment_mode: str = "randomized"


def simulate(
    scenario: str = "helpful",
    n: int = 2000,
    seed: int = 20261031,
    experiment_id: str = "interactive",
    split: str = "exploratory",
    strength: float = 1.0,
    assignment_mode: str = "randomized",
    unmeasured_confounding: float = 0.0,
    generate_events: bool = True,
    measured_selection_strength: float = 1.0,
    propensity_nonlinearity: float = 0.0,
    outcome_nonlinearity: float = 0.0,
) -> Simulation:
    if scenario not in SCENARIOS or n < 100 or n > 20000:
        raise ValueError("Use a registered scenario and 100-20000 households.")
    if not 0 <= strength <= 1.5:
        raise ValueError("strength must be between 0 and 1.5")
    if assignment_mode not in ("randomized", "observational"):
        raise ValueError("assignment_mode must be randomized or observational")
    if not 0 <= unmeasured_confounding <= 1:
        raise ValueError("unmeasured_confounding must be between 0 and 1")
    if not 0 <= measured_selection_strength <= 5:
        raise ValueError("measured_selection_strength must be between 0 and 5")
    if not 0 <= propensity_nonlinearity <= 3:
        raise ValueError("propensity_nonlinearity must be between 0 and 3")
    if not 0 <= outcome_nonlinearity <= 0.4:
        raise ValueError("outcome_nonlinearity must be between 0 and 0.4")
    if assignment_mode == "randomized" and (
        unmeasured_confounding != 0
        or measured_selection_strength != 1
        or propensity_nonlinearity != 0
        or outcome_nonlinearity != 0
    ):
        raise ValueError("unmeasured_confounding applies only to observational assignment; stress parameters are observational-only")
    spec = SCENARIOS[scenario]
    rng = np.random.default_rng(seed)
    assignment = rng.permutation(np.arange(n) % 2) if assignment_mode == "randomized" else None
    affinity = rng.beta(2, 2, n)
    opportunity = rng.lognormal(-0.15, 0.65, n)
    observed_log_opportunity = np.log(opportunity)
    if assignment_mode == "observational":
        latent_loyalty = rng.uniform(-1, 1, n)
        assignment_logit = (
            -0.3
            + measured_selection_strength * (2 * (affinity - 0.5) + 0.25 * observed_log_opportunity)
            + propensity_nonlinearity * (np.square(affinity) - 0.3)
            + 0.8 * unmeasured_confounding * latent_loyalty
        )
        assignment_probability = expit(assignment_logit)
        assignment = rng.binomial(1, assignment_probability)
        outcome_shift = outcome_nonlinearity * (np.square(affinity - 0.5) - 0.05)
        return_probability = (
            0.40 + 0.25 * affinity + assignment * spec.return_effect * strength
            + outcome_shift + 0.04 * unmeasured_confounding * latent_loyalty
        )
    else:
        assignment_probability = np.full(n, 0.5)
        return_probability = 0.40 + 0.25 * affinity + assignment * spec.return_effect * strength
    returned = rng.binomial(1, return_probability)
    household_ids = [f"{split}:{experiment_id}:h{index:05d}" for index in range(n)]
    households = pd.DataFrame({
        "household_id": household_ids,
        "experiment_id": experiment_id,
        "split": split,
        "assignment": assignment,
        "registered_day": 0,
        "eligible": True,
        "affinity": affinity,
        "return_probability": return_probability,
        "returned_d29_56": returned,
        "return_day": np.where(returned, rng.integers(29, 57, n), -1),
        "outcome_observed": True,
    })
    if assignment_mode == "observational":
        households["observed_affinity"] = affinity
        households["observed_log_opportunity"] = observed_log_opportunity
        households["assignment_probability_oracle"] = assignment_probability
        households["latent_loyalty_oracle"] = latent_loyalty
        households["unmeasured_confounding_strength_oracle"] = unmeasured_confounding
        households["measured_selection_strength_oracle"] = measured_selection_strength
        households["propensity_nonlinearity_oracle"] = propensity_nonlinearity
        households["outcome_nonlinearity_oracle"] = outcome_nonlinearity
    genres = ["Drama", "Comedy", "Documentary"]
    titles = pd.DataFrame([
        {"title_id": f"t{index:02d}", "title": f"Fictional {genres[index % 3]} {index + 1}",
         "genre": genres[index % 3], "runtime_minutes": [24, 48, 96, 140][index % 4],
         "available_day": index % 8}
        for index in range(18)
    ])
    if not generate_events:
        return Simulation(
            households,
            titles,
            pd.DataFrame(columns=["household_id", "impressions", "window_end"]),
            pd.DataFrame(columns=["event_id", "household_id", "title_id", "day", "minutes", "runtime_minutes", "genre", "qualified", "completed"]),
            spec,
            seed,
            experiment_id,
            split,
            assignment_mode,
        )
    exposure_rows = []
    event_rows = []
    for index, household_id in enumerate(household_ids):
        treatment = int(assignment[index])
        exposure_count = int(rng.poisson((3 + 4 * affinity[index]) * opportunity[index] * (1 + 0.25 * treatment)))
        exposure_rows.append({"household_id": household_id, "impressions": exposure_count, "window_end": 14})
        start_probability = min(0.85, (0.16 + 0.28 * affinity[index]) * (1 + treatment * spec.starts_lift * strength))
        starts = int(rng.binomial(exposure_count, start_probability))
        for start_index in range(starts):
            title_index = int(rng.integers(0, len(titles)))
            title = titles.iloc[title_index]
            start_day = int(rng.integers(int(title.available_day), 14))
            fraction = float(np.clip(rng.beta(2 + 3 * affinity[index], 2) + treatment * spec.engagement_shift * strength, 0.01, 1))
            minutes = float(title.runtime_minutes * fraction)
            event_rows.append({
                "event_id": f"{household_id}:e{start_index}", "household_id": household_id,
                "title_id": title.title_id, "day": start_day, "minutes": minutes,
                "runtime_minutes": int(title.runtime_minutes), "genre": title.genre,
                "qualified": minutes >= 2, "completed": fraction >= 0.9,
            })
    events = pd.DataFrame(event_rows, columns=[
        "event_id", "household_id", "title_id", "day", "minutes", "runtime_minutes", "genre", "qualified", "completed",
    ])
    return Simulation(households, titles, pd.DataFrame(exposure_rows), events, spec, seed, experiment_id, split, assignment_mode)