"""SYNTHETIC test fixtures only (not real Elexon data)."""

from datetime import timedelta

import numpy as np
import pandas as pd
import pytest

from app.data.store import Store, set_store


def synthetic_store() -> Store:
    rng = np.random.default_rng(0)
    idx = pd.date_range("2025-12-29", "2026-02-02", freq="30min", tz="UTC", inclusive="left")
    actual = pd.DataFrame(
        {
            "startTime": idx,
            "generation": 4000
            + 2500 * np.sin(np.arange(len(idx)) / 40)
            + rng.normal(0, 100, len(idx)),
        }
    )
    rows = []
    for pt in pd.date_range("2025-12-30", "2026-02-01", freq="6h", tz="UTC"):
        t = idx[(idx > pt) & (idx <= pt + timedelta(hours=72))]
        a = actual.set_index("startTime").generation.reindex(t).values
        rows.append(
            pd.DataFrame(
                {
                    "startTime": t,
                    "publishTime": pt,
                    "generation": a + 200 + rng.normal(0, 300, len(t)),
                }
            )
        )
    return Store(pd.concat(rows, ignore_index=True), actual, {"synthetic": True})


@pytest.fixture(scope="session")
def store():
    s = synthetic_store()
    set_store(s)
    yield s
    set_store(None)
