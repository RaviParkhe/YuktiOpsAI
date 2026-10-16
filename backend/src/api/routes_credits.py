"""
Credits and Referrals API routes.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import VerifiedUser, get_current_user
from src.config import get_settings
from src.db.models import AuditEvent, CreditAccount, CreditLedger, Referral, User
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.credits import apply_credit, get_balance, get_ledger

logger = logging.getLogger(__name__)
router = APIRouter()


class BalanceResponse(BaseModel):
    user_id: str
    credit_balance: int


class LedgerEntryResponse(BaseModel):
    id: str
    amount: int
    balance_after: int
    reason: str
    operation_ref: Optional[str]
    idempotency_key: Optional[str]
    details: Optional[dict]
    created_at: datetime


class ReferralCreateResponse(BaseModel):
    referral_code: str
    referrer_id: str
    created_at: datetime


class ReferralClaimRequest(BaseModel):
    referral_code: str = Field(..., min_length=4, max_length=20)


class ReferralClaimResponse(BaseModel):
    referral_code: str
    status: str
    reward_granted: int


@router.get("/balance", response_model=APIResponse[BalanceResponse], tags=["Credits"])
async def get_user_balance(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current user's credit balance."""
    balance = await get_balance(db, current_user.uid)
    return APIResponse(
        success=True,
        data=BalanceResponse(user_id=current_user.uid, credit_balance=balance),
    )


@router.get("/ledger", response_model=APIResponse[List[LedgerEntryResponse]], tags=["Credits"])
async def get_user_ledger(
    limit: int = 50,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recent credit transactions for the authenticated user."""
    safe_limit = min(max(1, limit), 100)
    entries = await get_ledger(db, current_user.uid, limit=safe_limit)
    return APIResponse(
        success=True,
        data=[
            LedgerEntryResponse(
                id=e.id,
                amount=e.amount,
                balance_after=e.balance_after,
                reason=e.reason,
                operation_ref=e.operation_ref,
                idempotency_key=e.idempotency_key,
                details=e.details,
                created_at=e.created_at,
            )
            for e in entries
        ],
    )


@router.post("/referral/create", response_model=APIResponse[ReferralCreateResponse], tags=["Credits"])
async def create_referral_code(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate or retrieve a unique referral code for the user."""
    existing = await db.execute(
        select(Referral).where(Referral.referrer_id == current_user.uid, Referral.status == "pending")
    )
    ref = existing.scalars().first()
    if not ref:
        code = f"YO-{current_user.uid[:4].upper()}-{uuid.uuid4().hex[:6].upper()}"
        ref = Referral(
            referrer_id=current_user.uid,
            referral_code=code,
            status="pending",
        )
        db.add(ref)
        await db.flush()

    return APIResponse(
        success=True,
        message="Referral code ready",
        data=ReferralCreateResponse(
            referral_code=ref.referral_code,
            referrer_id=ref.referrer_id,
            created_at=ref.created_at,
        ),
    )


@router.post("/referral/claim", response_model=APIResponse[ReferralClaimResponse], tags=["Credits"])
async def claim_referral_code(
    req: ReferralClaimRequest,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Claim a referral code. Enforces eligibility: no self-referral, once per referee."""
    s = get_settings()

    # Look up referral code
    result = await db.execute(
        select(Referral).where(Referral.referral_code == req.referral_code.strip())
    )
    ref = result.scalar_one_or_none()
    if not ref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INVALID_CODE", "message": "Referral code not found"},
        )

    # Self-referral rejection
    if ref.referrer_id == current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_REFERRAL", "message": "You cannot claim your own referral code"},
        )

    # Check if this referee has already claimed a referral
    claimed_result = await db.execute(
        select(Referral).where(Referral.referee_id == current_user.uid)
    )
    if claimed_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "ALREADY_CLAIMED", "message": "You have already claimed a referral reward"},
        )

    now = datetime.now(timezone.utc)
    ref.referee_id = current_user.uid
    ref.status = "rewarded"
    ref.activated_at = now
    ref.rewarded_at = now

    # Reward referrer
    await apply_credit(
        db,
        ref.referrer_id,
        s.CREDIT_REFERRAL_REWARD,
        "referral_reward",
        idempotency_key=f"ref_reward:{ref.id}:{ref.referrer_id}",
        operation_ref=ref.id,
        details={"referee_id": current_user.uid, "code": ref.referral_code},
    )

    # Reward referee (new user bonus)
    await apply_credit(
        db,
        current_user.uid,
        s.CREDIT_REFERRAL_REFEREE_REWARD,
        "referee_bonus",
        idempotency_key=f"ref_bonus:{ref.id}:{current_user.uid}",
        operation_ref=ref.id,
        details={"referrer_id": ref.referrer_id, "code": ref.referral_code},
    )

    db.add(AuditEvent(
        user_id=current_user.uid,
        actor=f"user:{current_user.uid}",
        action="referral_claimed",
        resource_type="referral",
        resource_id=ref.id,
        details={"code": ref.referral_code, "referrer_id": ref.referrer_id},
    ))

    return APIResponse(
        success=True,
        message="Referral reward credited successfully",
        data=ReferralClaimResponse(
            referral_code=ref.referral_code,
            status=ref.status,
            reward_granted=s.CREDIT_REFERRAL_REFEREE_REWARD,
        ),
    )
