"""Vercel serverless entry: exposes the FastAPI ASGI app."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.main import app as base_app  # noqa: E402


class VercelPathMiddleware:
    """Strip Vercel entrypoint prefix if present, preserving the actual sub-path."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            raw_path = scope.get("path", "")
            if raw_path.startswith("/api/index.py"):
                scope["path"] = raw_path[len("/api/index.py"):] or "/"
            elif raw_path.startswith("/api/index"):
                scope["path"] = raw_path[len("/api/index"):] or "/"

        await self.inner(scope, receive, send)


app = VercelPathMiddleware(base_app)
