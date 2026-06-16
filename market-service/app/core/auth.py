"""Firebase ID token verification service."""

import asyncio

from firebase_admin import auth
from firebase_admin.auth import (
    CertificateFetchError,
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
    UserDisabledError,
)

from app.core.auth_models import FirebaseUser
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.exceptions.auth import UnauthorizedException

logger = get_logger(__name__)


class FirebaseAuthService:
    """Verifies Firebase ID tokens and returns authenticated user context."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def verify_id_token(self, id_token: str) -> FirebaseUser:
        """Verify a Firebase ID token and return the authenticated user."""
        if not self._settings.firebase_auth_enabled:
            raise UnauthorizedException("Firebase authentication is disabled")

        try:
            decoded = await asyncio.to_thread(
                auth.verify_id_token,
                id_token,
                check_revoked=True,
            )
        except ExpiredIdTokenError as exc:
            raise UnauthorizedException(
                "Firebase ID token has expired",
                error_code="TOKEN_EXPIRED",
            ) from exc
        except RevokedIdTokenError as exc:
            raise UnauthorizedException(
                "Firebase ID token has been revoked",
                error_code="TOKEN_REVOKED",
            ) from exc
        except (InvalidIdTokenError, CertificateFetchError, ValueError) as exc:
            raise UnauthorizedException(
                "Invalid Firebase ID token",
                error_code="INVALID_TOKEN",
            ) from exc
        except UserDisabledError as exc:
            raise UnauthorizedException(
                "Firebase user account is disabled",
                error_code="USER_DISABLED",
            ) from exc
        except Exception as exc:
            logger.exception("firebase_token_verification_failed")
            raise UnauthorizedException(
                "Failed to verify Firebase ID token",
                error_code="AUTH_VERIFICATION_FAILED",
            ) from exc

        user = FirebaseUser(
            uid=decoded["uid"],
            email=decoded.get("email"),
            email_verified=decoded.get("email_verified", False),
            name=decoded.get("name"),
            picture=decoded.get("picture"),
        )
        logger.info("firebase_token_verified", uid=user.uid, email=user.email)
        return user


def get_firebase_auth_service() -> FirebaseAuthService:
    """Return Firebase auth service instance."""
    return FirebaseAuthService()
