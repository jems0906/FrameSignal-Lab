from dataclasses import dataclass

import numpy as np
import pandas as pd


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


def simulate(
    scenario: str = "helpful",
    n: int = 2000,
    seed: int = 20261031,
    experiment_id: str = "interactive",
    split: str = "exploratory",
    strength: float = 1.0,
) -> Simulation:
    if scenario not in SCENARIOS or n < 100 or n > 20000:
        raise ValueError("Use a registered scenario and 100-20000 households.")
    if not 0 <= strength <= 1.5:
        raise ValueError("strength must be between 0 and 1.5")
    spec = SCENARIOS[scenario]
    rng = np.random.default_rng(seed)
    assignment = rng.permutation(np.arange(n) % 2)
    affinity = rng.beta(2, 2, n)
    opportunity = rng.lognormal(-0.15, 0.65, n)
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
    genres = ["Drama", "Comedy", "Documentary"]
    titles = pd.DataFrame([
        {"title_id": f"t{index:02d}", "title": f"Fictional {genres[index % 3]} {index + 1}",
         "genre": genres[index % 3], "runtime_minutes": [24, 48, 96, 140][index % 4],
         "available_day": index % 8}
        for index in range(18)
    ])
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
    return Simulation(households, titles, pd.DataFrame(exposure_rows), events, spec, seed, experiment_id, split)