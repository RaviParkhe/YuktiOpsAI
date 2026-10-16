"""
Rewarded Ads and Temporary Entitlements API routes.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import VerifiedUser, get_current_user
from src.config import get_settings
from src.db.models import AdSession, FeatureEntitlement
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.ads import AdVerificationError, rewarded_ad_service

logger = logging.getLogger(__name__)
router = APIRouter()


class AdSessionCreate(BaseModel):
    feature_key: str = Field(..., description="Eligible feature to unlock, e.g. full_solution, social_research")


class AdSessionResponse(BaseModel):
    session_id: str
    feature_key: str
    status: str
    test_mode: bool
    created_at: datetime


class AdCompleteRequest(BaseModel):
    session_id: str
    provider_transaction_id: Optional[str] = None
    verification_payload: Optional[dict] = None


class EntitlementResponse(BaseModel):
    id: str
    feature_key: str
    grant_source: str
    starts_at: datetime
    expires_at: datetime
    is_active: bool


@router.post("/session", response_model=APIResponse[AdSessionResponse], status_code=201, tags=["Ads"])
async def start_ad_session(
    req: AdSessionCreate,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate a server-tracked rewarded ad session for a specific feature unlock."""
    try:
        session = await rewarded_ad_service.create_session(db, current_user.uid, req.feature_key)
        return APIResponse(
            success=True,
            message="Ad session created",
            data=AdSessionResponse(
                session_id=session.id,
                feature_key=session.feature_key,
                status=session.status,
                test_mode=session.test_mode,
                created_at=session.created_at,
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INELIGIBLE_FEATURE", "message": str(e)},
        )


@router.post("/complete", response_model=APIResponse[EntitlementResponse], tags=["Ads"])
async def complete_ad_session(
    req: AdCompleteRequest,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete a rewarded ad session and grant feature entitlement."""
    try:
        entitlement = await rewarded_ad_service.complete_session(
            db,
            ad_session_id=req.session_id,
            user_id=current_user.uid,
            provider_transaction_id=req.provider_transaction_id,
            verification_payload=req.verification_payload,
        )
        return APIResponse(
            success=True,
            message="Feature entitlement unlocked",
            data=EntitlementResponse(
                id=entitlement.id,
                feature_key=entitlement.feature_key,
                grant_source=entitlement.grant_source,
                starts_at=entitlement.starts_at,
                expires_at=entitlement.expires_at,
                is_active=entitlement.is_active,
            ),
        )
    except AdVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "AD_VERIFICATION_FAILED", "message": str(e)},
        )


@router.get("/entitlements", response_model=APIResponse[List[EntitlementResponse]], tags=["Ads"])
async def list_user_entitlements(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active feature entitlements for the authenticated user."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(FeatureEntitlement).where(
            FeatureEntitlement.user_id == current_user.uid,
            FeatureEntitlement.is_active == True,
            FeatureEntitlement.expires_at > now,
        )
    )
    entitlements = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            EntitlementResponse(
                id=ent.id,
                feature_key=ent.feature_key,
                grant_source=ent.grant_source,
                starts_at=ent.starts_at,
                expires_at=ent.expires_at,
                is_active=ent.is_active,
            )
            for ent in entitlements
        ],
    )
