"""Tests for watchlist API endpoints."""

from fastapi.testclient import TestClient

from app.main import app
from app.models.watchlist import WatchlistItemType, PersonRoleFilter

client = TestClient(app)


class TestWatchlistEndpoints:
    """Test watchlist API endpoints."""

    def test_list_watchlist_requires_auth(self):
        """Test that listing watchlist requires authentication."""
        response = client.get("/watchlist")
        # FastAPI returns 403 when no credentials provided with OAuth2
        assert response.status_code in (401, 403)

    def test_add_content_requires_auth(self):
        """Test that adding content to watchlist requires authentication."""
        response = client.post("/watchlist/content", json={"tvdb_id": 123})
        assert response.status_code in (401, 403)

    def test_add_person_requires_auth(self):
        """Test that adding person to watchlist requires authentication."""
        response = client.post(
            "/watchlist/person",
            json={"person_id": 456, "person_role_filter": "any"}
        )
        assert response.status_code in (401, 403)

    def test_remove_content_requires_auth(self):
        """Test that removing content from watchlist requires authentication."""
        response = client.delete("/watchlist/content/123")
        assert response.status_code in (401, 403)

    def test_remove_person_requires_auth(self):
        """Test that removing person from watchlist requires authentication."""
        response = client.delete("/watchlist/person/456")
        assert response.status_code in (401, 403)

    def test_check_content_requires_auth(self):
        """Test that checking content in watchlist requires authentication."""
        response = client.get("/watchlist/check/content/123")
        assert response.status_code in (401, 403)

    def test_check_person_requires_auth(self):
        """Test that checking person in watchlist requires authentication."""
        response = client.get("/watchlist/check/person/456")
        assert response.status_code in (401, 403)

    def test_update_content_requires_auth(self):
        """Test that updating content watchlist entry requires authentication."""
        response = client.patch(
            "/watchlist/content/123",
            json={"notes": "Updated notes"}
        )
        assert response.status_code in (401, 403)

    def test_update_person_requires_auth(self):
        """Test that updating person watchlist entry requires authentication."""
        response = client.patch(
            "/watchlist/person/456",
            json={"person_role_filter": "actor"}
        )
        assert response.status_code in (401, 403)


class TestWatchlistItemType:
    """Test WatchlistItemType enum."""

    def test_content_value(self):
        """Test content item type value."""
        assert WatchlistItemType.CONTENT.value == "content"

    def test_person_value(self):
        """Test person item type value."""
        assert WatchlistItemType.PERSON.value == "person"


class TestPersonRoleFilter:
    """Test PersonRoleFilter enum."""

    def test_any_value(self):
        """Test any role filter value."""
        assert PersonRoleFilter.ANY.value == "any"

    def test_actor_value(self):
        """Test actor role filter value."""
        assert PersonRoleFilter.ACTOR.value == "actor"

    def test_director_value(self):
        """Test director role filter value."""
        assert PersonRoleFilter.DIRECTOR.value == "director"
