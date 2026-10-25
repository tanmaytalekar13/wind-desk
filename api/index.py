"""Vercel serverless entry: exposes the FastAPI ASGI app."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.main import app as base_app  # noqa: E402


class VercelPathMiddleware:
    """Normalize Vercel incoming paths.

    When Vercel rewrites / or any route to /api/index.py or /api/index,
    scope['path'] gets set to /api/index.py or /api/index.
    This middleware restores the original path from x-matched-path or normalizes it.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            # x-matched-path header is set by Vercel to the original URL requested
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            raw_path = scope.get("path", "")

            # If x-matched-path is provided, use it!
            if matched_path:
                scope["path"] = matched_path
            elif raw_path.startswith("/api/index.py"):
                scope["path"] = raw_path[len("/api/index.py"):] or "/"
            elif raw_path.startswith("/api/index"):
                scope["path"] = raw_path[len("/api/index"):] or "/"

        await self.inner(scope, receive, send)


app = VercelPathMiddleware(base_app)
