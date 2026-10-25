import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("wind-desk")

app = FastAPI(title="Wind Day-Ahead Desk API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(FileNotFoundError)
async def no_snapshot(_: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=503, content={"detail": "Data snapshot missing. Run: python -m app.data.ingest"}
    )


# Locate static directory robustly across local, docker, and serverless environments
candidates = [
    Path(__file__).resolve().parents[1] / "static",
    Path(__file__).resolve().parents[2] / "frontend" / "dist",
    Path(__file__).resolve().parents[2] / "backend" / "static",
]
static_dir = next((c for c in candidates if c.is_dir() and (c / "index.html").exists()), None)
logger.info("Resolved frontend static directory: %s", static_dir)


@app.get("/", include_in_schema=False)
async def serve_root():
    if static_dir and (static_dir / "index.html").exists():
        return FileResponse(static_dir / "index.html")
    return JSONResponse({"status": "ok", "message": "Wind Desk API running"})


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_or_static(full_path: str):
    if (
        full_path.startswith("api/")
        or full_path.startswith("docs")
        or full_path.startswith("openapi")
    ):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if static_dir:
        target = static_dir / full_path
        if target.is_file():
            return FileResponse(target)
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(index)
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
