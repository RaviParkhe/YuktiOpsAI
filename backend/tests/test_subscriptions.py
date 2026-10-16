"""
Tests verifying subscription and entitlement boundaries:
Ensures client-side claims like `is_subscribed=true` cannot bypass credit costs or feature entitlements.
"""
import pytest
from src.services.ads import rewarded_ad_service


@pytest.mark.asyncio
async def test_client_cannot_claim_entitlement_without_server_grant(db_session):
    uid = "attacker-user-009"
    # User attempts to claim entitlement
    has_ent = await rewarded_ad_service.has_entitlement(db_session, uid, "full_solution")
    assert has_ent is False


def test_no_arbitrary_subscription_bypass(client):
    """
    Submitting requests with spoofed subscription flags must not grant
    unauthorized credits or skip payment.
    """
    resp = client.post(
        "/api/v1/auth/me",
        headers={"X-Spoofed-Subscription": "active"},
    )
    assert resp.status_code == 200
    # Role remains member, not paid tier
    assert resp.json()["data"]["role"] == "member"
