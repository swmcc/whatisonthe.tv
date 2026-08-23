"""Tests for idempotent check-in creation via client_uuid."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.checkin import Checkin
from app.schemas.checkin import CheckinCreate, CheckinResponse

client = TestClient(app)

CLIENT_UUID = "6f1d0f1a-6a1e-4b0f-9d4c-2f7e5a1b3c4d"


def _content_stub() -> SimpleNamespace:
    """Build a content stub matching ContentSummary."""
    return SimpleNamespace(
        id=10,
        tvdb_id=12345,
        name="The Bear",
        content_type="series",
        year=2022,
        poster_url=None,
        image_url=None,
    )


def _checkin_stub(user_id: int) -> SimpleNamespace:
    """Build an existing checkin stub matching CheckinResponse."""
    now = datetime(2026, 8, 23, 20, 0, 0)
    return SimpleNamespace(
        id=99,
        user_id=user_id,
        content_id=12345,
        episode_id=None,
        episode=None,
        watched_at=now,
        location=None,
        watched_with=None,
        notes=None,
        focus=None,
        client_uuid=CLIENT_UUID,
        created_at=now,
        updated_at=now,
        content=_content_stub(),
    )


def _db_returning(existing: object) -> AsyncMock:
    """Build an AsyncMock session whose client_uuid lookup returns `existing`."""
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=existing)
    db.execute = AsyncMock(return_value=result)
    return db


def _payload() -> dict:
    """Build a check-in creation payload carrying a client_uuid."""
    return {
        "content_id": 12345,
        "watched_at": "2026-08-23T20:00:00",
        "client_uuid": CLIENT_UUID,
    }


class TestCheckinIdempotencyAuth:
    """Test authentication requirements for check-in creation."""

    def test_create_checkin_requires_auth(self):
        """Test that creating a checkin requires authentication."""
        response = client.post("/api/checkins", json=_payload())
        assert response.status_code in (401, 403)


class TestCheckinClientUuidSchema:
    """Test client_uuid on the check-in schemas."""

    def test_create_accepts_client_uuid(self):
        """Test that CheckinCreate accepts a client_uuid."""
        payload = CheckinCreate(**_payload())
        assert payload.client_uuid == CLIENT_UUID

    def test_create_without_client_uuid_defaults_to_none(self):
        """Test that client_uuid is optional on CheckinCreate."""
        payload = CheckinCreate(content_id=12345, watched_at=datetime(2026, 8, 23))
        assert payload.client_uuid is None

    def test_response_includes_client_uuid(self):
        """Test that CheckinResponse echoes client_uuid."""
        assert "client_uuid" in CheckinResponse.model_fields


class TestCheckinClientUuidModel:
    """Test the client_uuid column on the Checkin model."""

    def test_column_exists_and_is_nullable_unique_string(self):
        """Test that client_uuid is a nullable, unique String(36) column."""
        column = Checkin.__table__.columns["client_uuid"]
        assert column.nullable is True
        assert column.unique is True
        assert column.type.length == 36


class TestCheckinIdempotentCreate:
    """Test replay and conflict behaviour of client_uuid check-ins."""

    def _override(self, user_id: int, existing: object):
        """Override auth and db dependencies for the test client."""
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
        app.dependency_overrides[get_db] = lambda: _db_returning(existing)

    def teardown_method(self):
        """Clear dependency overrides after each test."""
        app.dependency_overrides.clear()

    def test_replay_returns_existing_checkin_with_200(self):
        """Test that replaying a client_uuid returns the existing checkin."""
        self._override(user_id=1, existing=_checkin_stub(user_id=1))

        response = client.post("/api/checkins", json=_payload())

        assert response.status_code == 200
        body = response.json()
        assert body["client_uuid"] == CLIENT_UUID
        assert body["id"] == 99

    def test_client_uuid_owned_by_another_user_conflicts(self):
        """Test that reusing another user's client_uuid returns 409."""
        self._override(user_id=1, existing=_checkin_stub(user_id=2))

        response = client.post("/api/checkins", json=_payload())

        assert response.status_code == 409
        assert response.json()["detail"] == "client_uuid already used by another user"


class TestClientUuidMigration:
    """Test the client_uuid Alembic migration."""

    def test_down_revision_points_at_current_head(self):
        """Test that the migration chains onto the watchlist snapshot revision."""
        import importlib.util
        from pathlib import Path

        path = (
            Path(__file__).resolve().parents[2]
            / "alembic"
            / "versions"
            / "c7d5e1f92a03_add_client_uuid_to_checkins.py"
        )
        spec = importlib.util.spec_from_file_location("client_uuid_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.down_revision == "951a59832cf7"
        assert module.revision == "c7d5e1f92a03"
