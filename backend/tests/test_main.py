"""Tests for main application."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Check if frontend build exists (affects routing behavior)
frontend_build_path = Path(__file__).parent.parent.parent / "frontend" / "build"
frontend_built = frontend_build_path.exists()


def test_root_endpoint():
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
    if frontend_built:
        # When frontend is built, root serves HTML
        assert "text/html" in response.headers["content-type"]
    else:
        data = response.json()
        assert data["app"] == "WatchLog"
        assert data["status"] == "running"
        assert "version" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
