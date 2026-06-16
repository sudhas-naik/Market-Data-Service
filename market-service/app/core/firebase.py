"""Firebase Admin SDK initialization."""

import firebase_admin

from app.core.config import Settings, get_settings
from app.core.firebase_credentials import resolve_firebase_credentials
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_firebase(settings: Settings | None = None) -> None:
    """Initialize Firebase Admin SDK once at application startup."""
    settings = settings or get_settings()

    if not settings.firebase_auth_enabled:
        logger.info("firebase_auth_disabled")
        return

    if firebase_admin._apps:
        logger.debug("firebase_already_initialized")
        return

    cred, source = resolve_firebase_credentials(settings)

    options: dict[str, str] = {}
    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    firebase_admin.initialize_app(cred, options or None)
    logger.info(
        "firebase_initialized",
        project_id=settings.firebase_project_id,
        credentials_source=source,
    )


def shutdown_firebase() -> None:
    """Delete Firebase app on shutdown."""
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin.get_app())
        logger.info("firebase_shutdown")
