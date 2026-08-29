"""Tests for TVDB namespace disambiguation on check-in creation.

TVDB movie and series IDs are separate namespaces, so one number can refer to
two different titles (e.g. 366924 is both Reacher the series and Madame Bovary
the movie). These tests pin the resolution rules: an explicit content_type wins,
an episode_id implies a series, and the legacy movie-first guess only applies
when neither is present.
"""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.core.deps import get_current_user
from app.db.database import get_db
from app.main import app
from app.models.content import Content
from app.schemas.checkin import CheckinCreate

client = TestClient(app)

SERIES_API_DATA = {"name": "Reacher", "year": "2022"}
MOVIE_API_DATA = {"name": "Madame Bovary", "year": "2014"}


def _content_stub(name: str, content_type: str) -> SimpleNamespace:
    """Build a content stub matching ContentSummary."""
    return SimpleNamespace(
        id=10,
        tvdb_id=366924,
        name=name,
        content_type=content_type,
        year=2022,
        poster_url=None,
        image_url=None,
    )


def _checkin_stub(name: str, content_type: str) -> SimpleNamespace:
    """Build a persisted checkin stub matching CheckinResponse."""
    now = datetime(2026, 8, 29, 21, 0, 0)
    return SimpleNamespace(
        id=1,
        user_id=1,
        content_id=366924,
        episode_id=None,
        episode=None,
        watched_at=now,
        location=None,
        watched_with=None,
        notes=None,
        focus=None,
        client_uuid=None,
        created_at=now,
        updated_at=now,
        content=_content_stub(name, content_type),
    )


def _db_for_create(saved_checkin: SimpleNamespace, episode: SimpleNamespace | None = None) -> AsyncMock:
    """Build an AsyncMock session for the create-new-content flow.

    Execute call order in create_checkin (without client_uuid):
    content lookup (miss) -> [episode lookup] -> final checkin reload.
    """
    db = AsyncMock()

    content_miss = MagicMock()
    content_miss.scalars.return_value.first.return_value = None

    reload_hit = MagicMock()
    reload_hit.scalar_one.return_value = saved_checkin

    results = [content_miss]
    if episode is not None:
        episode_hit = MagicMock()
        episode_hit.scalar_one_or_none.return_value = episode
        results.append(episode_hit)
    results.append(reload_hit)

    db.execute = AsyncMock(side_effect=results)
    db.add = MagicMock()
    return db


def _payload(**extra) -> dict:
    """Build a minimal check-in creation payload."""
    return {"content_id": 366924, "watched_at": "2026-08-29T21:00:00", **extra}


class TestCheckinContentTypeSchema:
    """Test content_type on CheckinCreate."""

    def test_accepts_series_and_movie(self):
        """Test that content_type accepts both namespace values."""
        assert CheckinCreate(**_payload(content_type="series")).content_type == "series"
        assert CheckinCreate(**_payload(content_type="movie")).content_type == "movie"

    def test_defaults_to_none(self):
        """Test that content_type is optional for legacy clients."""
        assert CheckinCreate(**_payload()).content_type is None

    def test_rejects_unknown_values(self):
        """Test that content_type rejects values outside the enum."""
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CheckinCreate(**_payload(content_type="documentary"))


class TestContentModelConstraints:
    """Test the composite uniqueness of content identity."""

    def test_tvdb_id_not_globally_unique(self):
        """Test that tvdb_id alone is no longer a unique column."""
        assert Content.__table__.columns["tvdb_id"].unique is not True

    def test_composite_unique_on_tvdb_id_and_type(self):
        """Test that (tvdb_id, content_type) carries the unique constraint."""
        constraint = next(
            c
            for c in Content.__table__.constraints
            if c.name == "uq_content_tvdb_id_content_type"
        )
        assert {col.name for col in constraint.columns} == {"tvdb_id", "content_type"}


class TestNamespaceResolution:
    """Test which TVDB namespace create_checkin queries."""

    def _override(self, db: AsyncMock):
        """Override auth and db dependencies for the test client."""
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
        app.dependency_overrides[get_db] = lambda: db

    def teardown_method(self):
        """Clear dependency overrides after each test."""
        app.dependency_overrides.clear()

    def _post(self, payload: dict, series_data: dict | None, movie_data: dict | None, episode=None, saved=None):
        """POST a check-in with the TVDB service and background tasks mocked."""
        saved = saved or _checkin_stub("Reacher", "series")
        self._override(_db_for_create(saved, episode=episode))
        with (
            patch("app.services.tvdb.tvdb_service.get_series_details", return_value=series_data) as series_mock,
            patch("app.services.tvdb.tvdb_service.get_movie_details", return_value=movie_data) as movie_mock,
            patch("app.tasks.content.save_series_full") as series_task,
            patch("app.tasks.content.save_movie_full") as movie_task,
        ):
            response = client.post("/api/checkins", json=payload)
        return response, series_mock, movie_mock, series_task, movie_task

    def test_explicit_series_never_queries_movie_namespace(self):
        """Test that content_type=series skips the movie lookup entirely."""
        response, series_mock, movie_mock, series_task, movie_task = self._post(
            _payload(content_type="series"), SERIES_API_DATA, MOVIE_API_DATA
        )

        assert response.status_code == 201
        assert response.json()["content"]["name"] == "Reacher"
        series_mock.assert_called_once_with(366924)
        movie_mock.assert_not_called()
        series_task.delay.assert_called_once()
        movie_task.delay.assert_not_called()

    def test_explicit_movie_never_queries_series_namespace(self):
        """Test that content_type=movie skips the series lookup entirely."""
        response, series_mock, movie_mock, _, movie_task = self._post(
            _payload(content_type="movie"),
            SERIES_API_DATA,
            MOVIE_API_DATA,
            saved=_checkin_stub("Madame Bovary", "movie"),
        )

        assert response.status_code == 201
        assert response.json()["content"]["name"] == "Madame Bovary"
        movie_mock.assert_called_once_with(366924)
        series_mock.assert_not_called()
        movie_task.delay.assert_called_once()

    def test_episode_id_implies_series(self):
        """Test that an episode check-in resolves as a series without content_type."""
        episode = SimpleNamespace(id=7, content_id=None)
        response, series_mock, movie_mock, _, _ = self._post(
            _payload(episode_id=4242), SERIES_API_DATA, MOVIE_API_DATA, episode=episode
        )

        assert response.status_code == 201
        series_mock.assert_called_once_with(366924)
        movie_mock.assert_not_called()

    def test_legacy_payload_still_guesses_movie_first(self):
        """Test that omitting content_type preserves the movie-first fallback."""
        response, series_mock, movie_mock, _, _ = self._post(
            _payload(),
            SERIES_API_DATA,
            MOVIE_API_DATA,
            saved=_checkin_stub("Madame Bovary", "movie"),
        )

        assert response.status_code == 201
        movie_mock.assert_called_once_with(366924)
        series_mock.assert_not_called()

    def test_explicit_series_404s_when_series_missing(self):
        """Test that a series check-in doesn't silently fall back to a movie."""
        response, _, movie_mock, _, _ = self._post(
            _payload(content_type="series"), None, MOVIE_API_DATA
        )

        assert response.status_code == 404
        movie_mock.assert_not_called()


class TestNamespaceMigration:
    """Test the composite-unique Alembic migration."""

    def test_revision_chains_onto_client_uuid(self):
        """Test that the migration chains onto the client_uuid revision."""
        import importlib.util
        from pathlib import Path

        path = (
            Path(__file__).resolve().parents[2]
            / "alembic"
            / "versions"
            / "d1d6d54fa743_content_tvdb_id_unique_per_content_type.py"
        )
        spec = importlib.util.spec_from_file_location("namespace_migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.down_revision == "c7d5e1f92a03"
        assert module.revision == "d1d6d54fa743"
