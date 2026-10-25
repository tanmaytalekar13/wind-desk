import numpy as np
import pandas as pd

from .timeutils import LONDON

BUCKETS = [0, 6, 12, 24, 48, np.inf]
BUCKET_LABELS = ["0-6h", "6-12h", "12-24h", "24-48h", "48h+"]
REGIMES = ["low", "medium", "high"]


def enrich(df: pd.DataFrame, low: float = 2000.0, high: float = 6000.0) -> pd.DataFrame:
    """Expects startTime, forecast, actual, horizon_hours. Sign: error = forecast - actual."""
    d = df.copy()
    d["error"] = d["forecast"] - d["actual"]
    d["abs_error"] = d["error"].abs()
    d["local_hour"] = d["startTime"].dt.tz_convert(LONDON).dt.hour
    d["horizon_bucket"] = pd.cut(
        d["horizon_hours"], BUCKETS, labels=BUCKET_LABELS, right=False
    ).astype(str)
    d["regime"] = np.where(
        d["actual"] < low, "low", np.where(d["actual"] <= high, "medium", "high")
    )
    return d


def smape(f: pd.Series, a: pd.Series, eps: float = 1.0) -> float | None:
    den = f.abs() + a.abs()
    m = den > eps  # guard actual~0
    return float(100 * np.mean(2 * (f - a).abs()[m] / den[m])) if m.any() else None


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n": 0}
    e, a, f = df["error"], df["actual"], df["forecast"]
    n = len(df)
    sst = float(((a - a.mean()) ** 2).sum())
    corr = float(np.corrcoef(f, a)[0, 1]) if n > 1 and f.std() > 0 and a.std() > 0 else None
    q = e.quantile([0.05, 0.10, 0.50, 0.90, 0.95])
    out = {
        "n": n,
        "mae_mw": float(e.abs().mean()),
        "rmse_mw": float(np.sqrt((e**2).mean())),
        "bias_mw": float(e.mean()),
        "nmae_pct": float(100 * e.abs().mean() / a.mean()) if a.mean() > 0 else None,
        "smape_pct": smape(f, a),
        "correlation": corr,
        "r2": float(1 - (e**2).sum() / sst) if sst > 0 else None,
        "p5": float(q[0.05]),
        "p10": float(q[0.10]),
        "p50": float(q[0.50]),
        "p90": float(q[0.90]),
        "p95": float(q[0.95]),
        "band90_mw": [float(q[0.05]), float(q[0.95])],
        "buffer90_mw": float(max(0.0, q[0.90])),  # one-sided: over-forecast (under-buy) risk
        "mean_actual_mw": float(a.mean()),
    }
    if "baseline" in df:
        b = df.dropna(subset=["baseline"])
        if len(b):
            bm = float((b["baseline"] - b["actual"]).abs().mean())
            out["baseline_mae_mw"] = bm
            out["skill_vs_persistence"] = float(1 - b["abs_error"].mean() / bm) if bm > 0 else None
    return out


def group(df: pd.DataFrame, key: str, order: list[str] | None = None) -> list[dict]:
    rows = []
    for k, g in df.groupby(key, sort=True):
        s = summarize(g)
        rows.append({"key": str(k), **{x: s[x] for x in ("n", "mae_mw", "rmse_mw", "bias_mw")}})
    if order:
        rows.sort(key=lambda r: order.index(r["key"]) if r["key"] in order else 99)
    return rows


def histogram(df: pd.DataFrame, bins: int = 30) -> list[dict]:
    if df.empty:
        return []
    c, edges = np.histogram(df["error"], bins=bins)
    return [
        {"binStart": float(edges[i]), "binEnd": float(edges[i + 1]), "count": int(c[i])}
        for i in range(bins)
    ]


def worst(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    return df.reindex(df["abs_error"].sort_values(ascending=False).index).head(n)


def insight(s: dict) -> str:
    if not s.get("n"):
        return "No data in the selected range."
    side = "over-predicted" if s["bias_mw"] > 0 else "under-predicted"
    txt = (
        f"Forecasts {side} wind by {abs(s['bias_mw']):,.0f} MW on average "
        f"(MAE {s['mae_mw']:,.0f} MW, {s['nmae_pct'] or 0:.1f}% of mean actual). "
        f"In 90% of half-hours the over-forecast stayed below {s['p90']:,.0f} MW, so plan about "
        f"{s['buffer90_mw']:,.0f} MW of buffer for 90% one-sided coverage."
    )
    if s.get("skill_vs_persistence") is not None:
        txt += f" Skill vs 24h persistence: {100 * s['skill_vs_persistence']:.0f}%."
    return txt
