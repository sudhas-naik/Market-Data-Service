"""Firebase authentication middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.auth import FirebaseAuthService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.exceptions.auth import UnauthorizedException

logger = get_logger(__name__)

# Routes that never require authentication
PUBLIC_EXACT_PATHS = frozenset({
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})

# Route prefixes that require a valid Firebase ID token
PROTECTED_PREFIXES = ("/watchlist",)


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_EXACT_PATHS:
        return True
    if path.startswith("/docs") or path.startswith("/redoc"):
        return True
    return False


def _requires_auth(path: str) -> bool:
    if _is_public_path(path):
        return False
    return any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def _extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    return token or None


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    """Verify Firebase ID tokens on protected routes and set request.state.user_id."""

    def __init__(self, app, auth_service: FirebaseAuthService | None = None) -> None:
        super().__init__(app)
        self._auth_service = auth_service or FirebaseAuthService()
        self._settings = get_settings()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user_id = None
        request.state.firebase_user = None

        if not _requires_auth(request.url.path):
            return await call_next(request)

        settings = self._settings

        # Dev bypass when Firebase auth is disabled
        if not settings.firebase_auth_enabled:
            if settings.firebase_auth_dev_bypass:
                request.state.user_id = request.headers.get("X-User-ID", "anonymous")
                return await call_next(request)
            return self._unauthorized_response(
                UnauthorizedException("Firebase authentication is disabled for protected routes")
            )

        token = _extract_bearer_token(request)
        if token is None:
            return self._unauthorized_response(
                UnauthorizedException(
                    "Missing or invalid Authorization header. Use: Bearer <firebase_id_token>",
                    error_code="MISSING_TOKEN",
                )
            )

        try:
            user = await self._auth_service.verify_id_token(token)
        except UnauthorizedException as exc:
            return self._unauthorized_response(exc)

        request.state.user_id = user.uid
        request.state.firebase_user = user
        return await call_next(request)

    @staticmethod
    def _unauthorized_response(exc: UnauthorizedException) -> JSONResponse:
        logger.warning(
            "authentication_failed",
            error_code=exc.error_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )
