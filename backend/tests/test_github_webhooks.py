"""
Tests for GitHub webhook HMAC-SHA256 signature verification, deduplication, and agent forwarding.
"""
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch
from src.config import get_settings


def test_github_webhook_signature_rejections(client):
    body = json.dumps({"action": "opened"}).encode()

    # Missing signature -> 401
    r_missing = client.post(
        "/api/v1/github/webhook",
        content=body,
        headers={"X-GitHub-Event": "pull_request"},
    )
    assert r_missing.status_code == 401
    assert r_missing.json()["detail"]["code"] == "INVALID_SIGNATURE"

    # Invalid signature -> 401
    r_invalid = client.post(
        "/api/v1/github/webhook",
        content=body,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=badbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbadbad",
        },
    )
    assert r_invalid.status_code == 401


def test_github_webhook_valid_delivery_and_forwarding(client):
    s = get_settings()
    secret = s.GITHUB_WEBHOOK_SECRET

    payload = {
        "action": "opened",
        "pull_request": {"number": 42, "title": "Add essential integrations"},
        "repository": {"full_name": "RaviParkhe/YuktiOpsAI"},
    }
    body = json.dumps(payload).encode()
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    sig = f"sha256={mac}"

    with patch("src.api.routes_github._forward_to_agents", new_callable=AsyncMock) as mock_fwd:
        # First delivery -> 202
        resp = client.post(
            "/api/v1/github/webhook",
            content=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "delivery-uuid-001",
                "X-Hub-Signature-256": sig,
            },
        )
        assert resp.status_code == 202
        assert resp.json()["data"]["event_type"] == "pull_request"
        assert mock_fwd.called

        # In-memory duplicate delivery -> deduplicated
        resp_dup = client.post(
            "/api/v1/github/webhook",
            content=body,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "delivery-uuid-001",
                "X-Hub-Signature-256": sig,
            },
        )
        assert resp_dup.status_code == 202
        assert resp_dup.json().get("status") == "deduplicated"
