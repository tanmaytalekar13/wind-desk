from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc


def parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def to_utc(d: date, t: time) -> datetime:
    """Local Europe/London wall-clock -> aware UTC datetime (DST-correct)."""
    return datetime.combine(d, t, tzinfo=LONDON).astimezone(UTC)


def expected_periods(d: date) -> pd.DatetimeIndex:
    """All 30-min settlement period start times (UTC) of local day d: 48, or 46/50 on clock changes."""
    start = to_utc(d, time(0, 0))
    end = to_utc(d + timedelta(days=1), time(0, 0))
    return pd.date_range(start, end, freq="30min", inclusive="left")
