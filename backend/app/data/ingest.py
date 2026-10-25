"""CLI: python -m app.data.ingest  -> parquet snapshot + coverage report."""

import argparse
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from app.config import settings
from app.data.elexon_client import fetch_wind_actuals, fetch_wind_forecasts


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=settings.snapshot_dir)
    p.add_argument("--actual-from", default="2026-01-01")
    p.add_argument("--actual-to", default="2026-02-01")
    p.add_argument("--pub-from", default="2025-12-31")
    p.add_argument("--pub-to", default="2026-02-01")  # exclusive: covers all of 2026-01-31
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO)
    a.out.mkdir(parents=True, exist_ok=True)
    act = fetch_wind_actuals(date.fromisoformat(a.actual_from), date.fromisoformat(a.actual_to))
    fc = fetch_wind_forecasts(
        datetime.fromisoformat(a.pub_from).replace(tzinfo=timezone.utc),
        datetime.fromisoformat(a.pub_to).replace(tzinfo=timezone.utc),
    )
    act.to_parquet(a.out / "wind_actual.parquet", index=False)
    fc.to_parquet(a.out / "wind_forecast.parquet", index=False)
    meta = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "actual_rows": len(act),
        "forecast_rows": len(fc),
        "actual_range": [str(act.startTime.min()), str(act.startTime.max())],
        "publish_range": [str(fc.publishTime.min()), str(fc.publishTime.max())],
        "target_range": [str(fc.startTime.min()), str(fc.startTime.max())],
        "unique_publish_times": int(fc.publishTime.nunique()),
        "duplicate_keys": int(fc.duplicated(["startTime", "publishTime"]).sum()),
        "actual_null_generation": int(act.generation.isna().sum()),
    }
    (a.out / "ingest_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
