"""Vercel serverless entry: exposes the FastAPI ASGI app."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.main import app as base_app  # noqa: E402


class VercelPathMiddleware:
    """Normalize Vercel incoming paths.

    If Vercel rewrites to /api/index.py, restore original path from x-matched-path
    or Vercel routing headers so FastAPI routes are matched correctly.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            matched = headers.get(b"x-matched-path") or headers.get(
                b"x-vercel-matched-path"
            )
            raw_path = scope.get("path", "")
            if matched:
                matched_str = matched.decode("utf-8", errors="ignore")
                if matched_str and not matched_str.startswith("/api/index"):
                    path_part, *q_part = matched_str.split("?", 1)
                    scope["path"] = path_part
                    if q_part and not scope.get("query_string"):
                        scope["query_string"] = q_part[0].encode("utf-8")
            elif raw_path.startswith("/api/index.py/"):
                scope["path"] = raw_path[len("/api/index.py") :]
            elif raw_path.startswith("/api/index/"):
                scope["path"] = raw_path[len("/api/index") :]
            elif raw_path in ("/api/index.py", "/api/index"):
                scope["path"] = "/"

        await self.inner(scope, receive, send)


app = VercelPathMiddleware(base_app)
