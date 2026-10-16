"""
Tests for service startup, liveness, and readiness endpoints.
"""
from fastapi.testclient import TestClient
from src.main import app


def test_health_liveness():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "YuktiOps" in data["service"]
        assert "version" in data


def test_readiness_probe(client):
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "database" in data
    assert "auth" in data
    assert "is_stub_mode" in data["auth"]


def test_cors_headers():
    with TestClient(app) as client:
        resp = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers
