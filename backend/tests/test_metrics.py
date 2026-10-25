import math

import pandas as pd

from app.core import metrics as M


def _df():
    t = pd.date_range("2026-01-02", periods=3, freq="30min", tz="UTC")
    return M.enrich(
        pd.DataFrame(
            {
                "startTime": t,
                "forecast": [110.0, 90.0, 100.0],
                "actual": [100.0, 100.0, 100.0],
                "horizon_hours": [10.0, 20.0, 30.0],
                "baseline": [120.0, 100.0, 100.0],
            }
        )
    )


def test_hand_computed():
    s = M.summarize(_df())
    assert math.isclose(s["mae_mw"], 20 / 3) and math.isclose(s["rmse_mw"], math.sqrt(200 / 3))
    assert abs(s["bias_mw"]) < 1e-9 and math.isclose(s["nmae_pct"], 100 * (20 / 3) / 100)
    assert math.isclose(
        s["skill_vs_persistence"], 1 - (20 / 3) / (20 / 3)
    )  # baseline MAE = 20/3 too


def test_sign_and_buckets():
    d = _df()
    assert d.error.tolist() == [10.0, -10.0, 0.0]
    assert d.horizon_bucket.tolist() == ["6-12h", "12-24h", "24-48h"]


def test_smape_guard():
    assert M.smape(pd.Series([0.0]), pd.Series([0.0])) is None
