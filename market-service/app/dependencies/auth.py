"""Authentication dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.auth_models import FirebaseUser
from app.exceptions.auth import UnauthorizedException


def get_current_user_id(request: Request) -> str:
    """Return authenticated Firebase UID from request state."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise UnauthorizedException(
            "Authentication required. Send Firebase ID token as: Authorization: Bearer <token>",
            error_code="UNAUTHORIZED",
        )
    return str(user_id)


def get_current_firebase_user(request: Request) -> FirebaseUser:
    """Return full Firebase user context from request state."""
    user = getattr(request.state, "firebase_user", None)
    if user is None:
        raise UnauthorizedException(
            "Authentication required. Send Firebase ID token as: Authorization: Bearer <token>",
            error_code="UNAUTHORIZED",
        )
    return user


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
CurrentFirebaseUser = Annotated[FirebaseUser, Depends(get_current_firebase_user)]
