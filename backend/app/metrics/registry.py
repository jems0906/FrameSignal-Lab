import pandas as pd
from framesignal_metrics import METRICS, calculate_household_metrics

from app.simulations.generator import Simulation

__all__ = ["METRICS", "household_metrics"]


def household_metrics(data: Simulation, window: int = 14) -> pd.DataFrame:
    return calculate_household_metrics(data.households, data.events, data.exposures, window)