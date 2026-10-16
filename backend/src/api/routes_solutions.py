"""
AI Solution Generation API routes.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import VerifiedUser, get_current_user
from src.db.models import SolutionRun
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.solution import solution_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SolutionGenerateRequest(BaseModel):
    problem_statement: str = Field(..., min_length=10, max_length=10000)
    project_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class SolutionRunResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str]
    problem_statement: str
    status: str
    credit_charge: Optional[int]
    idempotency_key: Optional[str]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime


@router.post("/generate", response_model=APIResponse[SolutionRunResponse], status_code=202, tags=["Solutions"])
async def generate_solution(
    req: SolutionGenerateRequest,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a structured AI solution for a problem statement. Enforces credit cost and idempotency."""
    run = await solution_service.generate(
        session=db,
        user_id=current_user.uid,
        problem_statement=req.problem_statement,
        project_id=req.project_id,
        idempotency_key=req.idempotency_key,
    )
    if run.status == "failed" and run.error_message and "Insufficient credits" in run.error_message:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "INSUFFICIENT_CREDITS", "message": run.error_message},
        )

    return APIResponse(
        success=run.status != "failed",
        message="Solution generated" if run.status == "completed" else f"Solution status: {run.status}",
        data=SolutionRunResponse(
            id=run.id,
            user_id=run.user_id,
            project_id=run.project_id,
            problem_statement=run.problem_statement,
            status=run.status,
            credit_charge=run.credit_charge,
            idempotency_key=run.idempotency_key,
            result=run.result,
            error_message=run.error_message,
            created_at=run.created_at,
        ),
    )


@router.get("/{run_id}", response_model=APIResponse[SolutionRunResponse], tags=["Solutions"])
async def get_solution_run(
    run_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve an existing solution run (owner check enforced)."""
    result = await db.execute(
        select(SolutionRun).where(SolutionRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Solution run not found"})
    if run.user_id != current_user.uid:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Access denied"})

    return APIResponse(
        success=True,
        data=SolutionRunResponse(
            id=run.id,
            user_id=run.user_id,
            project_id=run.project_id,
            problem_statement=run.problem_statement,
            status=run.status,
            credit_charge=run.credit_charge,
            idempotency_key=run.idempotency_key,
            result=run.result,
            error_message=run.error_message,
            created_at=run.created_at,
        ),
    )


@router.get("", response_model=APIResponse[List[SolutionRunResponse]], tags=["Solutions"])
async def list_solution_runs(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all solution runs for the authenticated user."""
    result = await db.execute(
        select(SolutionRun).where(SolutionRun.user_id == current_user.uid).order_by(SolutionRun.created_at.desc())
    )
    runs = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            SolutionRunResponse(
                id=r.id,
                user_id=r.user_id,
                project_id=r.project_id,
                problem_statement=r.problem_statement,
                status=r.status,
                credit_charge=r.credit_charge,
                idempotency_key=r.idempotency_key,
                result=r.result,
                error_message=r.error_message,
                created_at=r.created_at,
            )
            for r in runs
        ],
    )
