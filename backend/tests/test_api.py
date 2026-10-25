from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def test_health(store):
    assert c.get("/api/health").json() == {"status": "ok"}


def test_meta(store):
    j = c.get("/api/meta").json()
    assert "Elexon" in j["attribution"] and j["default_cutoff"] == "09:00"


def test_decision(store):
    j = c.get("/api/decision-forecast", params={"decision_date": "2026-01-10"}).json()
    assert (
        j["delivery_date"] == "2026-01-11"
        and len(j["rows"]) == 48
        and j["summary"]["missing_periods"] == 0
    )


def test_decision_out_of_scope(store):
    assert (
        c.get("/api/decision-forecast", params={"decision_date": "2026-02-10"}).status_code == 422
    )
    assert c.get("/api/decision-forecast", params={"decision_date": "nope"}).status_code == 422


def test_accuracy_endpoints(store):
    s = c.get("/api/accuracy/summary").json()
    assert s["n"] > 1000 and "insight" in s and s["bias_mw"] > 0
    for p in [
        "by-hour",
        "by-horizon",
        "by-day",
        "by-regime",
        "error-distribution",
        "worst-errors",
        "scatter",
    ]:
        r = c.get(f"/api/accuracy/{p}")
        assert r.status_code == 200 and len(r.json()) > 0, p
    assert len(c.get("/api/accuracy/by-hour").json()) == 24


def test_vintages(store):
    j = c.get("/api/forecast-vintages", params={"target_date": "2026-01-10"}).json()
    assert len(j["vintages"]) > 1 and len(j["actual"]) == 48
