from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    snapshot_dir: Path = ROOT / "data" / "snapshot"
    default_cutoff: str = "09:00"  # Europe/London, on D-1
    cors_origins: str = "*"
    low_wind_mw: float = 2000.0
    high_wind_mw: float = 6000.0
    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    scope_from: str = "2026-01-01"  # first decision date
    scope_to: str = "2026-01-31"  # last decision date


settings = Settings()
