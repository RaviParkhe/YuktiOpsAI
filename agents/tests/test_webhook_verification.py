import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient

SECRET = "test_webhook_secret_123"


def compute_signature(payload_bytes: bytes, secret: str = SECRET) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


@pytest.mark.asyncio
async def test_webhook_valid_signature_accepted(client: AsyncClient):
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Add feature X",
            "body": "Implements X",
            "head": {"sha": "abc123def456"},
        },
        "repository": {
            "name": "YuktiOps",
            "owner": {"login": "TechSena"},
        },
    }
    body_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(body_bytes)

    headers = {
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "delivery-uuid-001",
        "Content-Type": "application/json",
    }

    response = await client.post("/api/v1/webhooks/github", content=body_bytes, headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["data"]["event_type"] == "pull_request"
    assert data["data"]["action"] == "opened"
    assert data["data"]["delivery_id"] == "delivery-uuid-001"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(client: AsyncClient):
    payload = {"action": "opened"}
    body_bytes = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Hub-Signature-256": "sha256=invalid_hash_value_here",
        "X-GitHub-Event": "pull_request",
        "Content-Type": "application/json",
    }

    response = await client.post("/api/v1/webhooks/github", content=body_bytes, headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_missing_signature_rejected(client: AsyncClient):
    payload = {"action": "opened"}
    body_bytes = json.dumps(payload).encode("utf-8")

    response = await client.post(
        "/api/v1/webhooks/github",
        content=body_bytes,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_SIGNATURE"
