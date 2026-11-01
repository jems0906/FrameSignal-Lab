import pandas as pd


METRICS = {
    "qualified_starts": {"label": "Qualified starts", "unit": "starts / household", "role": "Primary candidate", "causal": True},
    "viewing_days": {"label": "Distinct viewing days", "unit": "days / household", "role": "Predefined alternative", "causal": True},
    "watch_minutes": {"label": "Watch time", "unit": "minutes / household", "role": "Diagnostic", "causal": True},
    "completion": {"label": "Completion among starters", "unit": "proportion of starters", "role": "Descriptive only", "causal": False},
    "returned_d29_56": {"label": "Return during days 29-56", "unit": "proportion of households", "role": "Primary target", "causal": True},
}


def calculate_household_metrics(
    households: pd.DataFrame,
    events: pd.DataFrame,
    exposures: pd.DataFrame,
    window: int = 14,
) -> pd.DataFrame:
    if window not in (7, 14):
        raise ValueError("Predefined short-term windows are 7 and 14 days.")
    required = [(households, {"household_id"}), (events, {"household_id", "day", "minutes", "qualified", "completed"}), (exposures, {"household_id", "impressions"})]
    if any(not columns.issubset(table.columns) for table, columns in required):
        raise ValueError("Missing required household, event, or exposure columns.")
    if households.household_id.isna().any() or households.household_id.duplicated().any():
        raise ValueError("Registered household IDs must be unique and observed.")
    if exposures.household_id.isna().any() or exposures.household_id.duplicated().any():
        raise ValueError("Exposure rows must have unique, observed household IDs.")
    if set(exposures.household_id) != set(households.household_id) or not events.household_id.isin(households.household_id).all():
        raise ValueError("All registered households need observed exposure rows; event IDs must belong to the registered population.")
    for table, column in [(events, "day"), (events, "minutes"), (exposures, "impressions")]:
        values = table[column]
        if values.empty:
            continue
        if not pd.api.types.is_numeric_dtype(values) or values.isna().any() or (values < 0).any() or values.isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"{column} must contain finite, nonnegative numbers.")
    if not events.qualified.isin([True, False]).all() or not events.completed.isin([True, False]).all():
        raise ValueError("Qualification and completion flags must be observed booleans, not strings.")
    frame = households.copy().set_index("household_id")
    short_events = events[events.day < window]
    qualified = short_events[short_events.qualified.astype(bool)]
    frame["qualified_starts"] = qualified.groupby("household_id").size().reindex(frame.index, fill_value=0)
    frame["viewing_days"] = qualified.groupby("household_id").day.nunique().reindex(frame.index, fill_value=0)
    frame["watch_minutes"] = short_events.groupby("household_id").minutes.sum().reindex(frame.index, fill_value=0)
    frame["starter"] = frame.qualified_starts > 0
    frame["completed_any"] = qualified.groupby("household_id").completed.max().reindex(frame.index, fill_value=False).astype(bool)
    frame["completion"] = frame.completed_any.astype(float).where(frame.starter)
    frame["impressions"] = exposures.set_index("household_id").impressions.reindex(frame.index, fill_value=0)
    return frame.reset_index()