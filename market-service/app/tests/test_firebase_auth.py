"""Tests for Firebase authentication."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.auth import FirebaseAuthService
from app.core.auth_models import FirebaseUser
from app.exceptions.auth import UnauthorizedException
from app.middleware.firebase_auth import FirebaseAuthMiddleware, _extract_bearer_token


def test_extract_bearer_token():
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"authorization", b"Bearer my-token-123")],
    }
    request = Request(scope)
    assert _extract_bearer_token(request) == "my-token-123"


@pytest.mark.asyncio
async def test_verify_id_token_success():
    service = FirebaseAuthService()
    decoded = {
        "uid": "firebase-uid-123",
        "email": "user@example.com",
        "email_verified": True,
        "name": "Test User",
    }

    with patch("app.core.auth.asyncio.to_thread", new=AsyncMock(return_value=decoded)):
        with patch.object(service._settings, "firebase_auth_enabled", True):
            user = await service.verify_id_token("valid-token")

    assert user.uid == "firebase-uid-123"
    assert user.email == "user@example.com"


@pytest.mark.asyncio
async def test_verify_id_token_when_disabled():
    service = FirebaseAuthService()
    with patch.object(service._settings, "firebase_auth_enabled", False):
        with pytest.raises(UnauthorizedException):
            await service.verify_id_token("any-token")


@pytest.mark.asyncio
async def test_watchlist_requires_auth_when_enabled(test_app, client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("FIREBASE_AUTH_ENABLED", "true")
    monkeypatch.setenv("FIREBASE_AUTH_DEV_BYPASS", "false")
    get_settings.cache_clear()

    response = await client.get("/watchlist")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"

    get_settings.cache_clear()
