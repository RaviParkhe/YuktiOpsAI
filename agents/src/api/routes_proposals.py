import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AnalysisRun, AuditEvent, FixProposal
from src.db.session import get_db
from src.graph.workflow import app_workflow
from src.schemas.analysis import AnalysisRunStatus
from src.schemas.common import APIResponse, ErrorResponse
from src.schemas.proposals import (
    ProposalApprovalRequest,
    ProposalRejectionRequest,
    ProposalResponse,
    ProposalStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/{proposal_id}",
    response_model=APIResponse[ProposalResponse],
    summary="Get Proposed Fix Details",
    responses={404: {"model": ErrorResponse, "description": "Proposal Not Found"}},
)
async def get_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details and diff patch for a specific fix proposal."""
    stmt = select(FixProposal).where(FixProposal.id == proposal_id)
    result = await db.execute(stmt)
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROPOSAL_NOT_FOUND", "message": f"Proposal {proposal_id} not found"},
        )

    return APIResponse(
        success=True,
        data=ProposalResponse.model_validate(proposal),
    )


@router.post(
    "/{proposal_id}/approve",
    response_model=APIResponse[ProposalResponse],
    summary="Human Approval for Fix Proposal",
    responses={
        404: {"model": ErrorResponse, "description": "Proposal Not Found"},
        400: {"model": ErrorResponse, "description": "Proposal Not in Proposed State"},
    },
)
async def approve_proposal(
    proposal_id: str,
    req: ProposalApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve a fix proposal.

    Resumes the LangGraph approval checkpoint and creates a GitHub Draft PR if requested.
    Fix creation strictly requires this explicit human authorization.
    """
    stmt = select(FixProposal).where(FixProposal.id == proposal_id)
    result = await db.execute(stmt)
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROPOSAL_NOT_FOUND", "message": f"Proposal {proposal_id} not found"},
        )

    if proposal.status != ProposalStatus.PROPOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_STATE",
                "message": f"Cannot approve proposal in status '{proposal.status}'",
            },
        )

    # 1. Update database records
    proposal.status = ProposalStatus.APPROVED.value
    proposal.reviewer_id = req.reviewer_id
    proposal.reviewer_notes = req.comments

    # 2. Record audit trail
    db.add(
        AuditEvent(
            run_id=proposal.run_id,
            proposal_id=proposal.id,
            actor=f"human:{req.reviewer_id}",
            action="proposal_approved",
            details={
                "comments": req.comments,
                "create_draft_pr": req.create_draft_pr,
            },
        )
    )
    await db.commit()

    # 3. Resume LangGraph human-in-the-loop workflow
    config = {"configurable": {"thread_id": proposal.run_id}}
    try:
        if req.create_draft_pr:
            # Update graph state with approval signal and resume to execute approval_and_action_node
            await app_workflow.aupdate_state(
                config,
                {
                    "approval_status": "APPROVED",
                    "reviewer_id": req.reviewer_id,
                    "reviewer_notes": req.comments,
                },
                as_node="notification_agent",
            )
            resumed_state = await app_workflow.ainvoke(None, config=config)

            draft_url = resumed_state.get("draft_pr_url")
            if draft_url:
                proposal.github_draft_pr_url = draft_url
                proposal.status = ProposalStatus.EXECUTED.value

        # Update run status to COMPLETED
        run_res = await db.execute(select(AnalysisRun).where(AnalysisRun.id == proposal.run_id))
        run = run_res.scalar_one_or_none()
        if run:
            run.status = AnalysisRunStatus.COMPLETED.value

        await db.commit()
        await db.refresh(proposal)

    except Exception as e:
        logger.error(f"Error resuming graph execution after approval: {e}")
        # Roll proposal back to APPROVED state (not EXECUTED) so it can be retried.
        # Do NOT leave it in an undefined in-between state.
        proposal.status = ProposalStatus.APPROVED.value
        db.add(
            AuditEvent(
                run_id=proposal.run_id,
                proposal_id=proposal.id,
                actor="system:approval_resumption",
                action="resumption_failed",
                details={"error": str(e)},
            )
        )
        await db.commit()

    return APIResponse(
        success=True,
        message="Proposal successfully approved and executed",
        data=ProposalResponse.model_validate(proposal),
    )


@router.post(
    "/{proposal_id}/reject",
    response_model=APIResponse[ProposalResponse],
    summary="Human Rejection for Fix Proposal",
    responses={
        404: {"model": ErrorResponse, "description": "Proposal Not Found"},
        400: {"model": ErrorResponse, "description": "Proposal Not in Proposed State"},
    },
)
async def reject_proposal(
    proposal_id: str,
    req: ProposalRejectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject a proposed fix diff."""
    stmt = select(FixProposal).where(FixProposal.id == proposal_id)
    result = await db.execute(stmt)
    proposal = result.scalar_one_or_none()

    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROPOSAL_NOT_FOUND", "message": f"Proposal {proposal_id} not found"},
        )

    if proposal.status != ProposalStatus.PROPOSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_STATE",
                "message": f"Cannot reject proposal in status '{proposal.status}'",
            },
        )

    proposal.status = ProposalStatus.REJECTED.value
    proposal.reviewer_id = req.reviewer_id
    proposal.reviewer_notes = req.reason

    db.add(
        AuditEvent(
            run_id=proposal.run_id,
            proposal_id=proposal.id,
            actor=f"human:{req.reviewer_id}",
            action="proposal_rejected",
            details={"reason": req.reason},
        )
    )

    # Resume graph to finalize rejected state
    config = {"configurable": {"thread_id": proposal.run_id}}
    try:
        await app_workflow.aupdate_state(
            config,
            {
                "approval_status": "REJECTED",
                "reviewer_id": req.reviewer_id,
                "reviewer_notes": req.reason,
            },
            as_node="notification_agent",
        )
        await app_workflow.ainvoke(None, config=config)

        run_res = await db.execute(select(AnalysisRun).where(AnalysisRun.id == proposal.run_id))
        run = run_res.scalar_one_or_none()
        if run:
            run.status = AnalysisRunStatus.COMPLETED.value

    except Exception as e:
        logger.warning(f"Could not cleanly resume graph for rejection: {e}")

    await db.commit()
    await db.refresh(proposal)

    return APIResponse(
        success=True,
        message="Proposal successfully rejected",
        data=ProposalResponse.model_validate(proposal),
    )
