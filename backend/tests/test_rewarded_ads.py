"""
Tests for rewarded ads, AdMob SSV verification, test mode, and temporary feature entitlements.
"""
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import Settings
from src.services.ads import rewarded_ad_service


@pytest.mark.asyncio
async def test_rewarded_ad_lifecycle(db_session: AsyncSession):
    user_id = "test-ad-user-001"

    # 1. Create session for eligible feature
    session = await rewarded_ad_service.create_session(db_session, user_id, "full_solution")
    assert session.status == "pending"
    assert session.feature_key == "full_solution"

    # Ineligible feature rejection
    with pytest.raises(ValueError) as exc_info:
        await rewarded_ad_service.create_session(db_session, user_id, "unsupported_secret_feature")
    assert "not eligible" in str(exc_info.value)

    # 2. Complete session
    entitlement = await rewarded_ad_service.complete_session(
        db_session,
        ad_session_id=session.id,
        user_id=user_id,
        provider_transaction_id="tx_admob_12345",
    )
    assert entitlement.feature_key == "full_solution"
    assert entitlement.is_active is True
    assert entitlement.expires_at > datetime.now(timezone.utc)

    # 3. Check active entitlement
    has_access = await rewarded_ad_service.has_entitlement(db_session, user_id, "full_solution")
    assert has_access is True

    # Check ungranted feature
    has_research = await rewarded_ad_service.has_entitlement(db_session, user_id, "social_research")
    assert has_research is False


def test_admob_ssv_hmac_verification():
    secret = "test_admob_secret_key"
    mock_settings = Settings(
        REWARDED_ADS_TEST_MODE=False,
        ADMOB_SERVER_SIDE_VERIFICATION_SECRET=secret,
    )

    params = {"ad_unit": "ca-app-pub-123", "user_id": "u456", "reward_amount": "10"}
    sorted_query = urllib.parse.urlencode(sorted(params.items()))
    mac = hmac.new(secret.encode(), sorted_query.encode(), hashlib.sha256).hexdigest()

    valid_query = f"{sorted_query}&signature={mac}&key_id=1234"
    tampered_query = f"{sorted_query}&signature=invalid_mac&key_id=1234"

    # Valid signature accepted
    assert rewarded_ad_service.verify_admob_ssv(valid_query, settings=mock_settings) is True
    # Tampered signature rejected
    assert rewarded_ad_service.verify_admob_ssv(tampered_query, settings=mock_settings) is False


def test_ads_api_flow(client):
    # Start session
    resp = client.post("/api/v1/ads/session", json={"feature_key": "full_solution"})
    assert resp.status_code == 201
    session_id = resp.json()["data"]["session_id"]

    # Complete session
    resp_comp = client.post(
        "/api/v1/ads/complete",
        json={"session_id": session_id, "provider_transaction_id": "tx_mock_777"},
    )
    assert resp_comp.status_code == 200
    assert resp_comp.json()["data"]["feature_key"] == "full_solution"

    # List entitlements
    resp_ent = client.get("/api/v1/ads/entitlements")
    assert resp_ent.status_code == 200
    entitlements = resp_ent.json()["data"]
    assert any(e["feature_key"] == "full_solution" for e in entitlements)
