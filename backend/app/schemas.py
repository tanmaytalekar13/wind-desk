from pydantic import BaseModel


class Health(BaseModel):
    status: str


class DecisionRow(BaseModel):
    startTime: str
    localTime: str
    forecastMW: float | None
    publishTime: str | None
    horizonHours: float | None
    actualMW: float | None
    missing: bool


class DecisionResponse(BaseModel):
    decision_date: str
    delivery_date: str
    cutoff_local: str
    cutoff_utc: str
    rows: list[DecisionRow]
    summary: dict


class Meta(BaseModel):
    scope: dict
    default_cutoff: str
    timezone: str
    sign_convention: str
    regimes_mw: dict
    ingest: dict
    attribution: str
    assumptions: list[str]


class GroupRow(BaseModel):
    key: str
    n: int
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
