"""Tests for refresh-token authentication and Capacitor CORS defaults."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.db.database import get_db
from app.main import app

client = TestClient(app)


class FakeUser:
    """Minimal stand-in for the User model."""

    def __init__(self, user_id: int = 1):
        self.id = user_id
        self.email = "someone@example.com"
        self.username = "someone"
        self.first_name = "Some"
        self.last_name = "One"
        self.created_at = "2026-01-01T00:00:00"
        self.updated_at = "2026-01-01T00:00:00"


def make_db(user: FakeUser | None):
    """
    Build a mock async session whose execute() yields the given user.

    Args:
        user: User to return from scalar_one_or_none(), or None

    Returns:
        Mock async session
    """
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    db = AsyncMock()
    db.execute.return_value = result
    return db


@pytest.fixture
def db_user():
    """Override get_db with a session returning a user, then clean up."""
    user = FakeUser()
    app.dependency_overrides[get_db] = lambda: make_db(user)
    yield user
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def db_no_user():
    """Override get_db with a session returning no user, then clean up."""
    app.dependency_overrides[get_db] = lambda: make_db(None)
    yield
    app.dependency_overrides.pop(get_db, None)


class TestTokenCreation:
    """Test token creation helpers."""

    def test_refresh_token_has_refresh_type(self):
        """Refresh tokens carry a type claim and the given subject."""
        payload = decode_access_token(create_refresh_token({"sub": "1"}))
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["sub"] == "1"

    def test_access_token_has_no_type_claim(self):
        """Access tokens are encoded without a type claim."""
        payload = decode_access_token(create_access_token({"sub": "1"}))
        assert payload is not None
        assert "type" not in payload
        assert payload["sub"] == "1"

    def test_expired_refresh_token_does_not_decode(self):
        """An expired refresh token fails to decode."""
        token = create_refresh_token({"sub": "1"}, expires_delta=timedelta(minutes=-1))
        assert decode_access_token(token) is None


class TestRefreshEndpoint:
    """Test POST /api/auth/refresh."""

    def test_refresh_returns_new_token_pair(self, db_user):
        """A valid refresh token is exchanged for a rotated token pair."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": create_refresh_token({"sub": "1"})},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"]
        assert data["refresh_token"]

        access_payload = decode_access_token(data["access_token"])
        assert access_payload is not None
        assert "type" not in access_payload
        assert access_payload["sub"] == "1"

        refresh_payload = decode_access_token(data["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"

    def test_refresh_rejects_garbage_token(self, db_user):
        """A malformed token is rejected."""
        response = client.post("/api/auth/refresh", json={"refresh_token": "not-a-jwt"})
        assert response.status_code == 401

    def test_refresh_rejects_expired_token(self, db_user):
        """An expired refresh token is rejected."""
        token = create_refresh_token({"sub": "1"}, expires_delta=timedelta(minutes=-1))
        response = client.post("/api/auth/refresh", json={"refresh_token": token})
        assert response.status_code == 401

    def test_refresh_rejects_access_token(self, db_user):
        """An access token cannot be used as a refresh token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": create_access_token({"sub": "1"})},
        )
        assert response.status_code == 401

    def test_refresh_rejects_deleted_user(self, db_no_user):
        """A valid token for a user that no longer exists is rejected."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": create_refresh_token({"sub": "1"})},
        )
        assert response.status_code == 401


class TestAccessTokenAuth:
    """Test which tokens authenticate normal endpoints."""

    def test_refresh_token_rejected_as_bearer(self, db_user):
        """A refresh token cannot authenticate a normal endpoint."""
        token = create_refresh_token({"sub": "1"})
        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_legacy_token_without_type_still_authenticates(self, db_user):
        """Tokens issued before refresh tokens existed keep working."""
        token = create_access_token({"sub": "1"})
        response = client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestSettingsDefaults:
    """Test auth and CORS configuration defaults."""

    def test_capacitor_origins_allowed_by_default(self):
        """Capacitor origins are in the default CORS allow-list."""
        defaults = Settings(_env_file=None)
        assert "capacitor://localhost" in defaults.cors_origins
        assert "https://localhost" in defaults.cors_origins
        assert "http://localhost:5173" in defaults.cors_origins

    def test_token_expiry_defaults(self):
        """Access tokens last 24 hours, refresh tokens ~180 days."""
        assert settings.access_token_expire_minutes == 60 * 24
        assert settings.refresh_token_expire_minutes == 60 * 24 * 180
