from datetime import date, time, timedelta

import pandas as pd

from .timeutils import expected_periods, to_utc


def select_decision_forecast(
    df_forecast: pd.DataFrame, delivery_date: date, cutoff_time_local: time = time(9, 0)
) -> pd.DataFrame:
    """Latest forecast per half-hour of `delivery_date` published at/before the cutoff.

    cutoff = (delivery_date - 1 day) at cutoff_time_local (Europe/London) -> UTC.
    Leak-free: rows with publishTime > cutoff are never used. Missing half-hours are kept as rows
    with missing=True (never filled).
    Input columns: startTime, publishTime (tz-aware UTC), generation.
    """
    cutoff = to_utc(delivery_date - timedelta(days=1), cutoff_time_local)
    exp = expected_periods(delivery_date)
    c = df_forecast[
        df_forecast["startTime"].isin(exp)
        & (df_forecast["publishTime"] <= cutoff)
        & df_forecast["generation"].notna()
    ]
    if len(c):
        c = c.loc[c.groupby("startTime")["publishTime"].idxmax()]
    out = pd.DataFrame({"startTime": exp}).merge(
        c[["startTime", "publishTime", "generation"]], on="startTime", how="left"
    )
    out["missing"] = out["generation"].isna()
    out["horizon_hours"] = (out["startTime"] - out["publishTime"]).dt.total_seconds() / 3600
    out["delivery_date"] = delivery_date
    out["cutoff_utc"] = cutoff
    return out
