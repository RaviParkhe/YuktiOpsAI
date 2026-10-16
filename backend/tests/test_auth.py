"""
Tests for authentication dependency, token verification, stub mode, and production security.
"""
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException
from src.auth import _init, get_auth_status, get_current_user
from src.config import Environment, Settings


@pytest.mark.asyncio
async def test_missing_auth_header_rejected_when_firebase_active():
    with patch("src.auth._init", return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_invalid_bearer_token_rejected():
    mock_auth = MagicMock()
    mock_auth.verify_id_token.side_effect = Exception("Signature verification failed")
    with patch("src.auth._init", return_value=True), patch("src.auth._firebase_auth", mock_auth):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer invalid-token-12345")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_dev_tokens_rejected_when_real_firebase_active():
    with patch("src.auth._init", return_value=True):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer dev:fake-user-id")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_dev_token_accepted_in_dev_stub_mode():
    with patch("src.auth._init", return_value=False):
        user = await get_current_user(authorization="Bearer dev:test-developer-99")
        assert user.uid == "test-developer-99"
        assert user.is_stub is True


@pytest.mark.asyncio
async def test_valid_token_extraction():
    mock_auth = MagicMock()
    mock_auth.verify_id_token.return_value = {
        "uid": "verified-uid-777",
        "email": "verified@yuktiops.local",
    }
    with patch("src.auth._init", return_value=True), patch("src.auth._firebase_auth", mock_auth):
        user = await get_current_user(authorization="Bearer good-token-xyz")
        assert user.uid == "verified-uid-777"
        assert user.email == "verified@yuktiops.local"
        assert user.is_stub is False


def test_production_fails_without_credentials():
    prod_settings = Settings(
        ENVIRONMENT=Environment.PRODUCTION,
        FIREBASE_PROJECT_ID=None,
    )
    with patch("src.config.get_settings", return_value=prod_settings), \
         patch("src.auth._firebase_app", None):
        with pytest.raises(RuntimeError) as exc_info:
            _init()
        assert "production" in str(exc_info.value).lower()


def test_get_auth_status_does_not_leak_secrets():
    status = get_auth_status()
    assert "is_stub_mode" in status
    assert "auth_provider" in status
    assert "environment" in status
    assert "private_key" not in status
    assert "secret" not in status
