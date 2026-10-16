import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models import AnalysisRun, AuditEvent, Finding
from src.db.session import get_db
from src.schemas.analysis import (
    AnalysisRunStatus,
    CIStatus,
    FindingResponse,
    PRAnalysisRequest,
    PRAnalysisResponse,
)
from src.schemas.common import APIResponse, ErrorResponse
from src.worker.jobs import enqueue_pr_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/trigger",
    response_model=APIResponse[PRAnalysisResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger PR Analysis",
)
async def trigger_pr_analysis(
    req: PRAnalysisRequest,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger or re-run analysis for a GitHub Pull Request."""
    run_id = str(uuid.uuid4())
    commit_sha = req.commit_sha or "latest"

    run = AnalysisRun(
        id=run_id,
        repo_owner=req.repo_owner,
        repo_name=req.repo_name,
        pr_number=req.pr_number,
        commit_sha=commit_sha,
        status=AnalysisRunStatus.QUEUED.value,
        ci_status=CIStatus.UNKNOWN.value,
    )
    db.add(run)

    db.add(
        AuditEvent(
            run_id=run_id,
            actor="api:manual_trigger",
            action="analysis_manually_triggered",
            details={"req": req.model_dump()},
        )
    )
    await db.commit()
    await db.refresh(run)

    # Dispatch to async worker queue
    await enqueue_pr_analysis(
        run_id=run_id,
        repo_owner=req.repo_owner,
        repo_name=req.repo_name,
        pr_number=req.pr_number,
        commit_sha=commit_sha,
    )

    return APIResponse(
        success=True,
        message="PR analysis queued successfully",
        data=PRAnalysisResponse(
            run_id=run.id,
            repo_full_name=run.repo_full_name,
            pr_number=run.pr_number,
            commit_sha=run.commit_sha,
            status=AnalysisRunStatus(run.status),
            ci_status=CIStatus(run.ci_status),
            total_findings=0,
            highest_severity=run.highest_severity,
            findings=[],
            created_at=run.created_at,
            updated_at=run.updated_at,
        ),
    )


@router.get(
    "/{run_id}",
    response_model=APIResponse[PRAnalysisResponse],
    summary="Get PR Analysis Run Details",
    responses={404: {"model": ErrorResponse, "description": "Run Not Found"}},
)
async def get_analysis_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed status, CI results, and triaged findings for a specific run."""
    stmt = (
        select(AnalysisRun)
        .where(AnalysisRun.id == run_id)
        .options(selectinload(AnalysisRun.findings))
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RUN_NOT_FOUND", "message": f"Analysis run {run_id} does not exist"},
        )

    findings_resp = [
        FindingResponse(
            id=f.id,
            run_id=f.run_id,
            category=f.category,
            severity=f.severity,
            title=f.title,
            file_path=f.file_path,
            line_number=f.line_number,
            description=f.description,
            recommendation=f.recommendation,
            fingerprint=f.fingerprint,
            created_at=f.created_at,
        )
        for f in run.findings
    ]

    return APIResponse(
        success=True,
        data=PRAnalysisResponse(
            run_id=run.id,
            repo_full_name=run.repo_full_name,
            pr_number=run.pr_number,
            commit_sha=run.commit_sha,
            status=AnalysisRunStatus(run.status),
            ci_status=CIStatus(run.ci_status),
            total_findings=len(findings_resp),
            highest_severity=run.highest_severity,
            findings=findings_resp,
            created_at=run.created_at,
            updated_at=run.updated_at,
            error_message=run.error_message,
        ),
    )


@router.get(
    "/{run_id}/audit-trail",
    response_model=APIResponse[List[dict]],
    summary="Get Audit Trail for Run",
)
async def get_run_audit_trail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the full chronological audit trail of agent decisions for a run."""
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.run_id == run_id)
        .order_by(AuditEvent.timestamp.asc())
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    audit_list = [
        {
            "id": e.id,
            "run_id": e.run_id,
            "actor": e.actor,
            "action": e.action,
            "details": e.details,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]

    return APIResponse(success=True, data=audit_list)
