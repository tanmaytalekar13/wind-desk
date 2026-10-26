# Wind Day-Ahead Desk

Web app for a GB utility's day-ahead power-buying team. Using only Elexon national wind data it (1) shows the **latest wind forecast available at the day-ahead decision cut-off** and (2) quantifies **forecast accuracy** so traders can size a buffer. Scope: decisions made in January 2026 (delivery Jan 2 - Feb 1).

- Deployed app: https://wind-desk.vercel.app/
- Video:(https://youtu.be/VE0jBo9xOaI)

## Layout
```
backend/app/core/      pure functions: selection.py (leak-free decision forecast), metrics.py, timeutils.py
backend/app/data/      elexon_client.py (retrying client), ingest.py (CLI), store.py (in-memory data access)
backend/app/api/       routes.py (validation + JSON shaping only)
backend/tests/         pytest: no-lookahead, timezone, DST 46/50, hand-computed metrics, API contract (synthetic fixtures)
backend/data/snapshot/ parquet snapshot written by ingest
frontend/src/          Vite + React + TS: pages (4 tabs), components, hooks, api client
api/index.py           Vercel serverless entry
scripts/               probe_elexon.py (recon), fill_video_script.py
```

## Start
1. Get data (needs internet): `cd backend && pip install -r requirements.txt && python -m app.data.ingest`
2. **Docker:** `docker compose up --build` then open http://localhost:8080 (health: `/api/health`)
3. **No Docker:** `cd backend && uvicorn app.main:app --reload` and `cd frontend && npm install && npm run dev` (http://localhost:5173)

## Tests
`cd backend && pip install -r requirements-dev.txt && pytest` · `cd frontend && npm test && npm run build`

## Refresh data
`cd backend && python -m app.data.ingest` (commit the parquet files under `backend/data/snapshot/` for deployment).

## Env vars
`SNAPSHOT_DIR`, `DEFAULT_CUTOFF` (09:00), `CORS_ORIGINS`, `LOW_WIND_MW` (2000), `HIGH_WIND_MW` (6000); frontend: `VITE_API_BASE`. See `.env.example`.

## API
| Endpoint | Purpose |
|---|---|
| GET /api/health | liveness |
| GET /api/meta | scope, cut-off, ingest info, attribution |
| GET /api/decision-forecast?decision_date=&cutoff= | latest forecast per half-hour at cut-off + KPIs |
| GET /api/forecast-vintages?target_date= | all forecast vintages vs actual |
| GET /api/accuracy/summary?from=&to=&cutoff=&horizon_max= | MAE, RMSE, bias, bands, skill, insight text |
| GET /api/accuracy/{by-hour,by-horizon,by-day,by-regime,error-distribution,scatter,worst-errors} | breakdowns |

## Methodology and assumptions
Cut-off default 09:00 Europe/London on D-1 (configurable). For each half-hour of delivery day D the forecast with the greatest `publishTime <= cut-off` is used (never later). Timestamps stored in UTC, displayed in Europe/London; DST days have 46/50 periods. January interpretation: decisions Jan 1..31 -> delivery Jan 2..Feb 1. Error = forecast - actual (positive = over-forecast = under-buy risk).

## Deploy
**Vercel:** `npm i -g vercel && vercel login && vercel --prod` (uses `vercel.json`; root `requirements.txt`). Bundle includes `backend/` and the snapshot.
**Heroku (fallback, paid):** `heroku create <name> --stack container && git push heroku main` (uses `heroku.yml`; serves the API only).

Contains BMRS data © Elexon. Subject to the BMRS Data Licence and API Terms of Use.
