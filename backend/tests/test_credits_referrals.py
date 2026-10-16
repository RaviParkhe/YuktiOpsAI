"""
Tests for credits lifecycle, balances, debit rejection, ledger logging, and referrals.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import User
from src.services.credits import (
    InsufficientCreditsError,
    apply_credit,
    apply_debit,
    get_balance,
    get_ledger,
)


@pytest.mark.asyncio
async def test_initial_credit_and_balance(db_session: AsyncSession):
    uid = "test-user-credit-001"
    balance = await get_balance(db_session, uid)
    assert balance == 0

    entry = await apply_credit(db_session, uid, 50, "new_user_grant")
    assert entry.amount == 50
    assert entry.balance_after == 50

    balance = await get_balance(db_session, uid)
    assert balance == 50


@pytest.mark.asyncio
async def test_debit_and_insufficient_credits_rejection(db_session: AsyncSession):
    uid = "test-user-credit-002"
    await apply_credit(db_session, uid, 30, "admin_grant")

    # Valid debit
    debit_entry = await apply_debit(db_session, uid, 10, "solution_charge")
    assert debit_entry.amount == -10
    assert debit_entry.balance_after == 20

    # Insufficient credits rejection (prevents negative balance)
    with pytest.raises(InsufficientCreditsError) as exc_info:
        await apply_debit(db_session, uid, 25, "solution_charge")
    assert exc_info.value.balance == 20
    assert exc_info.value.required == 25

    # Balance remains intact at 20
    current_balance = await get_balance(db_session, uid)
    assert current_balance == 20


@pytest.mark.asyncio
async def test_apply_credit_idempotency_bug_regression(db_session: AsyncSession):
    """
    REGRESSION TEST:
    Verifies that calling apply_credit with the same idempotency_key returns
    the existing ledger entry rather than None or a duplicate charge.
    """
    uid = "test-user-credit-003"
    idem_key = "reward-idem-999"

    entry1 = await apply_credit(db_session, uid, 40, "task_reward", idempotency_key=idem_key)
    assert entry1 is not None
    assert entry1.amount == 40
    assert entry1.balance_after == 40

    # Repeat with identical idempotency key
    entry2 = await apply_credit(db_session, uid, 40, "task_reward", idempotency_key=idem_key)
    assert entry2 is not None, "Regression: duplicate idempotency key must return the existing record, not None"
    assert entry2.id == entry1.id

    # Balance should NOT have doubled
    balance = await get_balance(db_session, uid)
    assert balance == 40


@pytest.mark.asyncio
async def test_apply_debit_idempotency(db_session: AsyncSession):
    uid = "test-user-credit-004"
    await apply_credit(db_session, uid, 50, "grant")

    idem_key = "debit-idem-888"
    entry1 = await apply_debit(db_session, uid, 10, "solution_charge", idempotency_key=idem_key)
    assert entry1.balance_after == 40

    # Repeat debit with same key
    entry2 = await apply_debit(db_session, uid, 10, "solution_charge", idempotency_key=idem_key)
    assert entry2.id == entry1.id

    # Balance remains 40 (not 30)
    balance = await get_balance(db_session, uid)
    assert balance == 40


def test_credits_api_endpoints(client):
    # Check balance endpoint
    resp = client.get("/api/v1/credits/balance")
    assert resp.status_code == 200
    assert "credit_balance" in resp.json()["data"]

    # Check ledger endpoint
    resp_ledger = client.get("/api/v1/credits/ledger")
    assert resp_ledger.status_code == 200
    assert isinstance(resp_ledger.json()["data"], list)

    # Check referral creation endpoint
    resp_ref = client.post("/api/v1/credits/referral/create")
    assert resp_ref.status_code == 200
    ref_code = resp_ref.json()["data"]["referral_code"]
    assert ref_code.startswith("YO-")


def test_referral_self_claim_rejected(client):
    resp_ref = client.post("/api/v1/credits/referral/create")
    ref_code = resp_ref.json()["data"]["referral_code"]

    # Alice tries to claim her own code
    resp_claim = client.post("/api/v1/credits/referral/claim", json={"referral_code": ref_code})
    assert resp_claim.status_code == 400
    assert resp_claim.json()["detail"]["code"] == "SELF_REFERRAL"
