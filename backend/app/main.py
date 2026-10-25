import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=logging.INFO)
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
