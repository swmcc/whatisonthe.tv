"""Tests for main application."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns correct response."""
    response = client.get("/")
    assert response.status_code == 200
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
