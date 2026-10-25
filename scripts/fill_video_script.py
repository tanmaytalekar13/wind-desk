"""Fill docs/VIDEO_SCRIPT.template.md with numbers computed from the loaded snapshot -> docs/VIDEO_SCRIPT.md."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

c = TestClient(app)
g = lambda p: c.get(p).json()  # noqa: E731
s, hours, hor = g("/api/accuracy/summary"), g("/api/accuracy/by-hour"), g("/api/accuracy/by-horizon")
worst_h = max(hours, key=lambda r: r["mae_mw"])
best_h = min(hours, key=lambda r: r["mae_mw"])
worst_b = max(hor, key=lambda r: r["mae_mw"])
f = lambda x: f"{x:,.0f}"  # noqa: E731
vals = {
    "bias": f(s["bias_mw"]), "mae": f(s["mae_mw"]), "rmse": f(s["rmse_mw"]), "nmae": f"{s['nmae_pct']:.1f}",
    "p5": f(s["p5"]), "p95": f(s["p95"]), "buffer": f(s["buffer90_mw"]),
    "skill": f"{100 * s.get('skill_vs_persistence', float('nan')):.0f}", "n": f(s["n"]),
    "worst_hour": f"{worst_h['key']}:00 (MAE {f(worst_h['mae_mw'])} MW)", "best_hour": f"{best_h['key']}:00 (MAE {f(best_h['mae_mw'])} MW)",
    "worst_bucket": f"{worst_b['key']} (MAE {f(worst_b['mae_mw'])} MW)",
}
t = (ROOT / "docs" / "VIDEO_SCRIPT.template.md").read_text()
for k, v in vals.items():
    t = t.replace("{{" + k + "}}", v)
(ROOT / "docs" / "VIDEO_SCRIPT.md").write_text(t)
print(t)
