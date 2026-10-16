"""
User and Auth route — upserts Firebase-verified user on first sign-in,
grants initial credits, returns profile.
"""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.auth import VerifiedUser, get_current_user
from src.config import get_settings
from src.db.models import AuditEvent, CreditAccount, User
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.credits import apply_credit

logger = logging.getLogger(__name__)
router = APIRouter()


class UserProfile(BaseModel):
    id: str
    email: Optional[str]
    display_name: Optional[str]
    photo_url: Optional[str]
    role: str
    credit_balance: int
    is_stub_auth: bool = False


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    photo_url: Optional[str] = Field(None, max_length=512)


@router.post("/me", response_model=APIResponse[UserProfile], tags=["Auth"])
async def upsert_user(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Called on sign-in. Creates user + credit account if first time.
    Awards CREDIT_NEW_USER_GRANT credits once.
    Returns the current profile.
    """
    s = get_settings()

    result = await db.execute(select(User).where(User.id == current_user.uid))
    user = result.scalar_one_or_none()
    is_new = user is None

    if is_new:
        user = User(
            id=current_user.uid,
            email=current_user.email,
            display_name=current_user.email,
            role="member",
        )
        db.add(user)
        await db.flush()

        # Grant initial credits
        await apply_credit(
            db, current_user.uid, s.CREDIT_NEW_USER_GRANT, "new_user_grant",
            idempotency_key=f"new_user:{current_user.uid}",
            details={"reason": "First sign-in welcome credits"},
        )
        db.add(AuditEvent(
            user_id=current_user.uid,
            actor=f"system:auth",
            action="user_created",
            resource_type="user",
            resource_id=current_user.uid,
        ))
        logger.info(f"[AUTH] New user created: {current_user.uid}")
    else:
        # Update email if changed
        if current_user.email and user.email != current_user.email:
            user.email = current_user.email

    balance_result = await db.execute(
        select(CreditAccount.balance).where(CreditAccount.user_id == current_user.uid)
    )
    balance = balance_result.scalar_one_or_none() or 0

    return APIResponse(
        success=True,
        message="Welcome back" if not is_new else "Account created",
        data=UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            role=user.role,
            credit_balance=balance,
            is_stub_auth=current_user.is_stub,
        ),
    )


@router.get("/me", response_model=APIResponse[UserProfile], tags=["Auth"])
async def get_profile(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile and credit balance."""
    result = await db.execute(select(User).where(User.id == current_user.uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Call POST /me to create your profile first"},
        )
    balance_result = await db.execute(
        select(CreditAccount.balance).where(CreditAccount.user_id == current_user.uid)
    )
    balance = balance_result.scalar_one_or_none() or 0
    return APIResponse(
        success=True,
        data=UserProfile(
            id=user.id, email=user.email, display_name=user.display_name,
            photo_url=user.photo_url, role=user.role, credit_balance=balance,
            is_stub_auth=current_user.is_stub,
        ),
    )


@router.patch("/me", response_model=APIResponse[UserProfile], tags=["Auth"])
async def update_profile(
    req: UpdateProfileRequest,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update display name or photo URL."""
    result = await db.execute(select(User).where(User.id == current_user.uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "Profile not found"})
    if req.display_name is not None:
        user.display_name = req.display_name
    if req.photo_url is not None:
        user.photo_url = req.photo_url
    balance_result = await db.execute(
        select(CreditAccount.balance).where(CreditAccount.user_id == current_user.uid)
    )
    balance = balance_result.scalar_one_or_none() or 0
    return APIResponse(
        success=True, message="Profile updated",
        data=UserProfile(
            id=user.id, email=user.email, display_name=user.display_name,
            photo_url=user.photo_url, role=user.role, credit_balance=balance,
            is_stub_auth=current_user.is_stub,
        ),
    )
