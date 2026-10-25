from datetime import date, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.core import metrics as M
from app.core.timeutils import LONDON, parse_hhmm
from app.data.store import get_store
from app.schemas import DecisionResponse, GroupRow, Health, Meta

router = APIRouter(prefix="/api")
S_FROM, S_TO = date.fromisoformat(settings.scope_from), date.fromisoformat(settings.scope_to)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    return o


def _date(s: str, name: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(422, f"{name} must be YYYY-MM-DD")


def _decision_date(s: str, name: str = "decision_date") -> date:
    d = _date(s, name)
    if not (S_FROM <= d <= S_TO):
        raise HTTPException(422, f"{name} must be within {S_FROM}..{S_TO} (January 2026 scope)")
    return d


def _cutoff(s: str | None):
    try:
        return parse_hhmm(s or settings.default_cutoff)
    except Exception:
        raise HTTPException(422, "cutoff must be HH:MM (Europe/London, on D-1)")


def _filtered(from_: str, to: str, cutoff: str | None, horizon_max: float | None) -> pd.DataFrame:
    a, b = _decision_date(from_, "from"), _decision_date(to, "to")
    if a > b:
        raise HTTPException(422, "from must be <= to")
    df = get_store().aligned(a, b, _cutoff(cutoff))
    if horizon_max is not None and len(df):
        df = df[df["horizon_hours"] <= horizon_max]
    return df


def _iso(ts) -> str | None:
    return None if pd.isna(ts) else pd.Timestamp(ts).isoformat()


@router.get("/health", response_model=Health)
def health():
    return {"status": "ok"}


@router.get("/meta", response_model=Meta)
def meta():
    return {
        "scope": {
            "decision_from": settings.scope_from,
            "decision_to": settings.scope_to,
            "delivery_from": str(S_FROM + timedelta(days=1)),
            "delivery_to": str(S_TO + timedelta(days=1)),
        },
        "default_cutoff": settings.default_cutoff,
        "timezone": "Europe/London (display); UTC (storage)",
        "sign_convention": "error = forecast - actual; positive = over-forecast = under-buy risk",
        "regimes_mw": {"low_below": settings.low_wind_mw, "high_above": settings.high_wind_mw},
        "ingest": get_store().meta,
        "attribution": "Contains BMRS data © Elexon",
        "assumptions": [
            "Decisions on Jan 1..31 2026 -> delivery days Jan 2..Feb 1",
            "See docs/ASSUMPTIONS.md",
        ],
    }


@router.get("/decision-forecast", response_model=DecisionResponse)
def decision_forecast(decision_date: str, cutoff: str | None = None):
    d, c = _decision_date(decision_date), _cutoff(cutoff)
    sel = get_store().decision(d + timedelta(days=1), c)
    ok = sel[~sel["missing"]]
    rows = [
        {
            "startTime": _iso(r.startTime),
            "localTime": r.startTime.tz_convert(LONDON).strftime("%Y-%m-%d %H:%M"),
            "forecastMW": None if r.missing else r.generation,
            "publishTime": _iso(r.publishTime),
            "horizonHours": None if r.missing else r.horizon_hours,
            "actualMW": None if pd.isna(r.actual) else r.actual,
            "missing": bool(r.missing),
        }
        for r in sel.itertuples()
    ]
    g = ok["generation"]
    summ = {
        "periods": len(sel),
        "missing_periods": int(sel["missing"].sum()),
        "peak_mw": g.max() if len(g) else None,
        "mean_mw": g.mean() if len(g) else None,
        "min_mw": g.min() if len(g) else None,
        "low_wind_periods": int((g < settings.low_wind_mw).sum()),
        "low_wind_threshold_mw": settings.low_wind_mw,
        "horizon_min_h": ok["horizon_hours"].min() if len(ok) else None,
        "horizon_max_h": ok["horizon_hours"].max() if len(ok) else None,
        "latest_publish_time": _iso(ok["publishTime"].max()) if len(ok) else None,
        "oldest_publish_time": _iso(ok["publishTime"].min()) if len(ok) else None,
        "actuals_available": int(sel["actual"].notna().sum()),
    }
    return clean(
        {
            "decision_date": str(d),
            "delivery_date": str(d + timedelta(days=1)),
            "cutoff_local": (cutoff or settings.default_cutoff),
            "cutoff_utc": sel["cutoff_utc"].iloc[0].isoformat(),
            "rows": rows,
            "summary": summ,
        }
    )


@router.get("/forecast-vintages")
def forecast_vintages(target_date: str):
    t = _date(target_date, "target_date")
    v = get_store().vintages(t)
    vint = [
        {
            "publishTime": _iso(pt),
            "points": [
                {"startTime": _iso(r.startTime), "forecastMW": r.generation} for r in g.itertuples()
            ],
        }
        for pt, g in v.groupby("publishTime")
    ]
    act = v.drop_duplicates("startTime")[["startTime", "actual"]]
    return clean(
        {
            "target_date": str(t),
            "vintages": vint,
            "actual": [
                {"startTime": _iso(r.startTime), "actualMW": r.actual} for r in act.itertuples()
            ],
        }
    )


Q = dict(from_=Query(settings.scope_from, alias="from"), to=Query(settings.scope_to))


@router.get("/accuracy/summary")
def acc_summary(
    from_: str = Q["from_"],
    to: str = Q["to"],
    cutoff: str | None = None,
    horizon_max: float | None = None,
):
    s = M.summarize(_filtered(from_, to, cutoff, horizon_max))
    return clean({**s, "insight": M.insight(s)})


def _grp(key: str, order=None):
    def h(
        from_: str = Q["from_"],
        to: str = Q["to"],
        cutoff: str | None = None,
        horizon_max: float | None = None,
    ):
        df = _filtered(from_, to, cutoff, horizon_max)
        return clean(M.group(df, key, order) if len(df) else [])

    return h


for path, key, order in [
    ("by-hour", "local_hour", None),
    ("by-horizon", "horizon_bucket", M.BUCKET_LABELS),
    ("by-day", "delivery_date", None),
    ("by-regime", "regime", M.REGIMES),
]:
    router.add_api_route(
        f"/accuracy/{path}", _grp(key, order), methods=["GET"], response_model=list[GroupRow]
    )


@router.get("/accuracy/error-distribution")
def error_dist(
    from_: str = Q["from_"],
    to: str = Q["to"],
    cutoff: str | None = None,
    horizon_max: float | None = None,
):
    return clean(M.histogram(_filtered(from_, to, cutoff, horizon_max)))


@router.get("/accuracy/scatter")
def scatter(
    from_: str = Q["from_"],
    to: str = Q["to"],
    cutoff: str | None = None,
    horizon_max: float | None = None,
):
    df = _filtered(from_, to, cutoff, horizon_max)
    if len(df) > 1500:
        df = df.iloc[:: len(df) // 1500 + 1]
    return clean([{"forecast": r.forecast, "actual": r.actual} for r in df.itertuples()])


@router.get("/accuracy/worst-errors")
def worst_errors(
    from_: str = Q["from_"],
    to: str = Q["to"],
    cutoff: str | None = None,
    horizon_max: float | None = None,
    n: int = Query(15, ge=1, le=100),
):
    w = M.worst(_filtered(from_, to, cutoff, horizon_max), n)
    return clean(
        [
            {
                "localTime": r.startTime.tz_convert(LONDON).strftime("%Y-%m-%d %H:%M"),
                "forecastMW": r.forecast,
                "actualMW": r.actual,
                "errorMW": r.error,
                "horizonHours": r.horizon_hours,
            }
            for r in w.itertuples()
        ]
    )
