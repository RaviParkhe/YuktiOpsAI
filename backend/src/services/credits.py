"""
Credit service — all balance mutations go through here.

Rules:
- Only server code calls these functions; client-supplied amounts are never trusted.
- Balance is never allowed to go negative (raises InsufficientCreditsError).
- Every mutation is wrapped in a DB transaction.
- Idempotency keys prevent duplicate charges/rewards across retries.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import CreditAccount, CreditLedger

logger = logging.getLogger(__name__)


class InsufficientCreditsError(Exception):
    """Raised when a debit would push the balance below zero."""
    def __init__(self, balance: int, required: int):
        self.balance = balance
        self.required = required
        super().__init__(f"Insufficient credits: has {balance}, needs {required}")


async def _get_or_create_account(session: AsyncSession, user_id: str) -> CreditAccount:
    """Return the user's credit account, creating one if it doesn't exist."""
    result = await session.execute(
        select(CreditAccount).where(CreditAccount.user_id == user_id).with_for_update()
    )
    account = result.scalar_one_or_none()
    if account is None:
        account = CreditAccount(user_id=user_id, balance=0)
        session.add(account)
        await session.flush()  # get ID without committing
    return account


async def get_balance(session: AsyncSession, user_id: str) -> int:
    """Return current credit balance (0 if no account yet)."""
    result = await session.execute(
        select(CreditAccount.balance).where(CreditAccount.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    return row if row is not None else 0


async def apply_credit(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: Optional[str] = None,
    operation_ref: Optional[str] = None,
    details: Optional[dict] = None,
) -> CreditLedger:
    """
    Add `amount` credits to the user's account.

    amount must be positive. Idempotency key prevents double-rewards.
    """
    if amount <= 0:
        raise ValueError(f"Credit amount must be positive, got {amount}")

    if idempotency_key:
        existing = await session.execute(
            select(CreditLedger).where(CreditLedger.idempotency_key == idempotency_key)
        )
        row = existing.scalar_one_or_none()
        if row:
            logger.info(f"[CREDITS] Idempotent: skipping duplicate credit idem={idempotency_key}")
            return row

    account = await _get_or_create_account(session, user_id)
    account.balance += amount
    entry = CreditLedger(
        account_id=account.id,
        user_id=user_id,
        amount=amount,
        balance_after=account.balance,
        reason=reason,
        idempotency_key=idempotency_key or str(uuid.uuid4()),
        operation_ref=operation_ref,
        details=details,
    )
    session.add(entry)
    await session.flush()
    logger.info(f"[CREDITS] +{amount} for {user_id} ({reason}) → balance={account.balance}")
    return entry


async def apply_debit(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: Optional[str] = None,
    operation_ref: Optional[str] = None,
    details: Optional[dict] = None,
) -> CreditLedger:
    """
    Deduct `amount` credits from the user's account.

    Raises InsufficientCreditsError if balance < amount.
    Idempotency key prevents duplicate charges.
    """
    if amount <= 0:
        raise ValueError(f"Debit amount must be positive, got {amount}")

    if idempotency_key:
        existing = await session.execute(
            select(CreditLedger).where(CreditLedger.idempotency_key == idempotency_key)
        )
        row = existing.scalar_one_or_none()
        if row:
            logger.info(f"[CREDITS] Idempotent: skipping duplicate debit idem={idempotency_key}")
            return row

    account = await _get_or_create_account(session, user_id)
    if account.balance < amount:
        raise InsufficientCreditsError(balance=account.balance, required=amount)

    account.balance -= amount
    entry = CreditLedger(
        account_id=account.id,
        user_id=user_id,
        amount=-amount,
        balance_after=account.balance,
        reason=reason,
        idempotency_key=idempotency_key or str(uuid.uuid4()),
        operation_ref=operation_ref,
        details=details,
    )
    session.add(entry)
    await session.flush()
    logger.info(f"[CREDITS] -{amount} for {user_id} ({reason}) → balance={account.balance}")
    return entry


async def get_ledger(session: AsyncSession, user_id: str, limit: int = 50) -> list[CreditLedger]:
    """Return recent credit ledger entries for a user, newest first."""
    result = await session.execute(
        select(CreditLedger)
        .where(CreditLedger.user_id == user_id)
        .order_by(CreditLedger.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
