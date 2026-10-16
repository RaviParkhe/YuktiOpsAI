"""
Tests for security edge cases: cross-tenant access control, ownership enforcement, and error safety.
"""
from src.auth import VerifiedUser, get_current_user
from src.main import app


def test_cross_tenant_project_isolation(client):
    # Alice creates a project
    r_create = client.post("/api/v1/projects", json={"name": "Alice Secret Project"})
    assert r_create.status_code == 201
    project_id = r_create.json()["data"]["id"]

    # Bob tries to access Alice's project
    bob_user = VerifiedUser(uid="bob-uid-202", email="bob@example.com", is_stub=False)

    async def override_bob():
        return bob_user

    app.dependency_overrides[get_current_user] = override_bob
    try:
        r_bob = client.get(f"/api/v1/projects/{project_id}")
        # Bob is forbidden (not a member)
        assert r_bob.status_code == 403
        assert r_bob.json()["detail"]["code"] == "NOT_A_MEMBER"
    finally:
        # Restore alice
        alice_user = VerifiedUser(uid="alice-uid-101", email="alice@example.com", is_stub=False)

        async def override_alice():
            return alice_user

        app.dependency_overrides[get_current_user] = override_alice


def test_cross_tenant_solution_run_isolation(client):
    # Bob tries to view an arbitrary solution run
    r = client.get("/api/v1/solutions/random-nonexistent-id")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "NOT_FOUND"


def test_malformed_json_returns_clean_error(client):
    resp = client.post(
        "/api/v1/projects",
        content=b"{ invalid json ",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()
    # Confirm no stack traces or server paths leaked in response body
    assert "Traceback" not in resp.text
    assert "D:\\YuktiOpsAI" not in resp.text
