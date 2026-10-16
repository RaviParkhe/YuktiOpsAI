"""
Tests for Telegram bot service, webhook secret validation, deduplication, and classifier.
"""
from unittest.mock import AsyncMock, patch
import pytest
from src.services.classifier import message_classifier
from src.services.telegram import telegram_service


def test_telegram_secret_token_verification():
    with patch.object(telegram_service, "webhook_secret", "my-secret-key-999"):
        assert telegram_service.verify_secret_token("my-secret-key-999") is True
        assert telegram_service.verify_secret_token("wrong-secret") is False
        assert telegram_service.verify_secret_token(None) is False


@pytest.mark.asyncio
async def test_message_classifier_heuristics():
    # Blocker keyword check (English & Hinglish)
    r1 = await message_classifier.classify("I am stuck on the database connection, error keeps failing")
    assert r1["category"] == "blocker"

    r2 = await message_classifier.classify("Yahan pe atka hoon, task complete nahi ho raha")
    assert r2["category"] == "blocker"

    # Done keyword check
    r3 = await message_classifier.classify("The backend models are done and merged")
    assert r3["category"] == "task_update"

    # Question check
    r4 = await message_classifier.classify("How do we configure the webhook endpoint?")
    assert r4["category"] == "question"


def test_telegram_webhook_deduplication(client):
    payload = {
        "update_id": 99001122,
        "message": {
            "chat": {"id": 123456},
            "from": {"id": 789},
            "text": "Task progress update",
        },
    }

    with patch.object(telegram_service, "send_message", new_callable=AsyncMock) as mock_send, \
         patch.object(telegram_service, "verify_secret_token", return_value=True):
        # 1. First delivery
        resp1 = client.post(
            "/api/v1/telegram/webhook",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["ok"] is True

        # 2. Duplicate delivery (same update_id)
        resp2 = client.post(
            "/api/v1/telegram/webhook",
            json=payload,
            headers={"X-Telegram-Bot-Api-Secret-Token": "test"},
        )
        assert resp2.status_code == 200
        assert resp2.json().get("deduplicated") is True
