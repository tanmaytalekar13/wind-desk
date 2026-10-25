from datetime import date, time

import pandas as pd

from app.core.selection import select_decision_forecast
from app.core.timeutils import expected_periods, to_utc


def _fc(rows):
    return pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"]).astype(
        {"startTime": "datetime64[ns, UTC]", "publishTime": "datetime64[ns, UTC]"}
    )


def test_no_lookahead_and_latest_wins(store):
    d = date(2026, 1, 15)
    sel = select_decision_forecast(store.forecasts, d, time(9, 0))
    cutoff = to_utc(date(2026, 1, 14), time(9, 0))
    assert len(sel) == 48 and not sel.missing.any()
    assert (sel.publishTime <= cutoff).all()
    # latest vintage <= cutoff is selected
    pool = store.forecasts[store.forecasts.publishTime <= cutoff]
    assert sel.publishTime.max() == pool.publishTime.max()


def test_future_forecast_never_used():
    t = pd.Timestamp("2026-01-02 12:00", tz="UTC")
    df = _fc(
        [
            [t, pd.Timestamp("2026-01-01 08:00", tz="UTC"), 100.0],
            [t, pd.Timestamp("2026-01-01 09:30", tz="UTC"), 999.0],
        ]
    )
    sel = select_decision_forecast(df, date(2026, 1, 2), time(9, 0))
    assert sel.loc[sel.startTime == t, "generation"].iloc[0] == 100.0


def test_cutoff_timezone_bst_vs_gmt():
    assert to_utc(date(2026, 7, 1), time(9, 0)).hour == 8  # BST
    assert to_utc(date(2026, 1, 1), time(9, 0)).hour == 9  # GMT


def test_dst_period_counts():
    assert len(expected_periods(date(2026, 3, 29))) == 46
    assert len(expected_periods(date(2026, 10, 25))) == 50
    assert len(expected_periods(date(2026, 1, 15))) == 48


def test_missing_flagged_not_filled():
    t = pd.Timestamp("2026-01-02 00:00", tz="UTC")
    sel = select_decision_forecast(
        _fc([[t, pd.Timestamp("2026-01-01 08:00", tz="UTC"), 50.0]]), date(2026, 1, 2)
    )
    assert sel.missing.sum() == 47 and sel.generation.isna().sum() == 47
