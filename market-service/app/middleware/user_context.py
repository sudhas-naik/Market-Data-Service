"""User context middleware for development/testing.

In production, upstream JWT middleware injects request.state.user_id.
This middleware provides a fallback header for local development.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class UserContextMiddleware(BaseHTTPMiddleware):
    """Ensures request.state.user_id is available."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not hasattr(request.state, "user_id") or request.state.user_id is None:
            # Allow X-User-ID header for local dev when JWT middleware is absent
            request.state.user_id = request.headers.get("X-User-ID", "anonymous")
        return await call_next(request)
