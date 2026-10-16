"""
Social Research (Reddit + LinkedIn) API routes.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import VerifiedUser, get_current_user
from src.db.models import ResearchRun
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.research import research_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    idempotency_key: Optional[str] = None


class ResearchRunResponse(BaseModel):
    id: str
    user_id: str
    query: str
    status: str
    credit_charge: Optional[int]
    idempotency_key: Optional[str]
    reddit_status: Optional[str]
    linkedin_status: Optional[str]
    results: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]
    created_at: datetime


@router.post("", response_model=APIResponse[ResearchRunResponse], status_code=202, tags=["Research"])
async def run_social_research(
    req: ResearchRequest,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute concurrent Reddit and LinkedIn research. Enforces credits and partial failure safety."""
    run = await research_service.run(
        session=db,
        user_id=current_user.uid,
        query=req.query,
        idempotency_key=req.idempotency_key,
    )
    if run.status == "failed" and run.error_message and "Insufficient credits" in run.error_message:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "INSUFFICIENT_CREDITS", "message": run.error_message},
        )

    return APIResponse(
        success=run.status not in ("failed", "error"),
        message=f"Research {run.status}",
        data=ResearchRunResponse(
            id=run.id,
            user_id=run.user_id,
            query=run.query,
            status=run.status,
            credit_charge=run.credit_charge,
            idempotency_key=run.idempotency_key,
            reddit_status=run.reddit_status,
            linkedin_status=run.linkedin_status,
            results=run.results,
            error_message=run.error_message,
            created_at=run.created_at,
        ),
    )


@router.get("/{run_id}", response_model=APIResponse[ResearchRunResponse], tags=["Research"])
async def get_research_run(
    run_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve an existing research run."""
    result = await db.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Research run not found"})
    if run.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    return APIResponse(
        success=True,
        data=ResearchRunResponse(
            id=run.id,
            user_id=run.user_id,
            query=run.query,
            status=run.status,
            credit_charge=run.credit_charge,
            idempotency_key=run.idempotency_key,
            reddit_status=run.reddit_status,
            linkedin_status=run.linkedin_status,
            results=run.results,
            error_message=run.error_message,
            created_at=run.created_at,
        ),
    )


@router.get("", response_model=APIResponse[List[ResearchRunResponse]], tags=["Research"])
async def list_research_runs(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all research runs for authenticated user."""
    result = await db.execute(
        select(ResearchRun).where(ResearchRun.user_id == current_user.uid).order_by(ResearchRun.created_at.desc())
    )
    runs = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            ResearchRunResponse(
                id=r.id,
                user_id=r.user_id,
                query=r.query,
                status=r.status,
                credit_charge=r.credit_charge,
                idempotency_key=r.idempotency_key,
                reddit_status=r.reddit_status,
                linkedin_status=r.linkedin_status,
                results=r.results,
                error_message=r.error_message,
                created_at=r.created_at,
            )
            for r in runs
        ],
    )
