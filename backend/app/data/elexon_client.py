"""Elexon Insights (BMRS) client. Response shape handled defensively (bare list or {"data": [...]})."""

import logging
import time
from datetime import date, datetime, timedelta

import httpx
import pandas as pd

from app.config import settings

log = logging.getLogger(__name__)


def _rows(payload) -> list[dict]:
    if isinstance(payload, dict):
        payload = payload.get("data", [])
    return payload or []


def _get(client: httpx.Client, path: str, params: dict, retries: int = 5) -> list[dict]:
    for attempt in range(retries):
        try:
            r = client.get(f"{settings.elexon_base_url}{path}", params=params, timeout=60)
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError("retryable", request=r.request, response=r)
            r.raise_for_status()
            return _rows(r.json())
        except (httpx.TransportError, httpx.HTTPStatusError) as exc:
            wait = 2**attempt
            log.warning("GET %s failed (%s); retry in %ss", path, exc, wait)
            if attempt == retries - 1:
                raise
            time.sleep(wait)
    return []


def _frame(rows: list[dict], cols: list[str]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    for c in cols:
        if c not in df:
            df[c] = pd.NA
    for c in ("startTime", "publishTime"):
        if c in df:
            df[c] = pd.to_datetime(df[c], utc=True)
    if "generation" in df:
        df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    return df


def fetch_wind_actuals(start: date, end: date, chunk_days: int = 7) -> pd.DataFrame:
    parts, d = [], start
    with httpx.Client(headers={"Accept": "application/json"}) as c:
        while d <= end:
            e = min(d + timedelta(days=chunk_days - 1), end)
            rows = _get(
                c,
                "/datasets/FUELHH/stream",
                {
                    "settlementDateFrom": d.isoformat(),
                    "settlementDateTo": e.isoformat(),
                    "fuelType": "WIND",
                },
            )
            parts.append(_frame(rows, ["startTime", "generation", "fuelType"]))
            d = e + timedelta(days=1)
    df = pd.concat(parts, ignore_index=True)
    df = df[df["fuelType"].astype(str).str.upper() == "WIND"]  # client-side safety filter
    return df[["startTime", "generation"]].drop_duplicates("startTime", keep="last")


def fetch_wind_forecasts(start: datetime, end: datetime, chunk_days: int = 3) -> pd.DataFrame:
    parts, d = [], start
    with httpx.Client(headers={"Accept": "application/json"}) as c:
        while d < end:
            e = min(d + timedelta(days=chunk_days), end)
            rows = _get(
                c,
                "/datasets/WINDFOR/stream",
                {
                    "publishDateTimeFrom": d.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "publishDateTimeTo": e.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            )
            parts.append(_frame(rows, ["startTime", "publishTime", "generation"]))
            d = e
    df = pd.concat(parts, ignore_index=True)
    return df[["startTime", "publishTime", "generation"]].drop_duplicates(
        ["startTime", "publishTime"], keep="last"
    )
