import json
from datetime import date, time, timedelta
from pathlib import Path

import pandas as pd

from app.config import settings
from app.core.metrics import enrich
from app.core.selection import select_decision_forecast
from app.core.timeutils import expected_periods


class Store:
    def __init__(self, forecasts: pd.DataFrame, actuals: pd.DataFrame, meta: dict | None = None):
        self.forecasts, self.actuals, self.meta = forecasts, actuals, meta or {}
        self._actual = actuals.set_index("startTime")["generation"]
        self._cache: dict = {}

    @classmethod
    def load(cls, d: Path) -> "Store":
        mp = d / "ingest_meta.json"
        return cls(
            pd.read_parquet(d / "wind_forecast.parquet"),
            pd.read_parquet(d / "wind_actual.parquet"),
            json.loads(mp.read_text()) if mp.exists() else {},
        )

    def decision(self, delivery: date, cutoff: time) -> pd.DataFrame:
        sel = select_decision_forecast(self.forecasts, delivery, cutoff)
        sel["actual"] = sel["startTime"].map(self._actual)
        return sel

    def aligned(self, d_from: date, d_to: date, cutoff: time) -> pd.DataFrame:
        """Decision-time-aligned forecast vs actual; decision dates d_from..d_to (delivery = D+1)."""
        key = (d_from, d_to, cutoff)
        if key not in self._cache:
            parts, d = [], d_from
            while d <= d_to:
                s = self.decision(d + timedelta(days=1), cutoff)
                parts.append(s[~s["missing"]])
                d += timedelta(days=1)
            df = pd.concat(parts, ignore_index=True)
            df = df.rename(columns={"generation": "forecast"}).dropna(subset=["actual"])
            if len(df):
                df["baseline"] = self._actual.reindex(
                    df["startTime"] - pd.Timedelta(hours=24)
                ).values
                df = enrich(df, settings.low_wind_mw, settings.high_wind_mw)
            self._cache[key] = df
        return self._cache[key]

    def vintages(self, target: date) -> pd.DataFrame:
        v = self.forecasts[self.forecasts["startTime"].isin(expected_periods(target))].copy()
        v["actual"] = v["startTime"].map(self._actual)
        return v.sort_values(["publishTime", "startTime"])


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store.load(settings.snapshot_dir)
    return _store


def set_store(s: Store | None) -> None:
    global _store
    _store = s
