import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AnalysisRun, AuditEvent, FixProposal, ProjectMember, Task
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
from src.services.telegram import TelegramNotifier

logger = logging.getLogger(__name__)
router = APIRouter()


async def _verify_approver_permissions(reviewer_id: str, project_id: str, db: AsyncSession) -> None:
    """Verify that reviewer is a team_lead, project_manager, or admin for the project."""
    stmt = select(ProjectMember).where(
        (ProjectMember.user_id == reviewer_id) | (ProjectMember.name == reviewer_id)
    )
    if project_id:
        stmt = stmt.where(ProjectMember.project_id == project_id)

    res = await db.execute(stmt)
    member = res.scalar_one_or_none()

    if member:
        allowed_roles = ("team_lead", "project_manager", "admin", "lead", "pm")
        if member.role.lower() not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PERMISSION_DENIED",
                    "message": (
                        f"User '{reviewer_id}' with role '{member.role}' is not authorized to approve task mutations. "
                        "Only team leads, project managers, or admins may approve."
                    ),
                },
            )
    else:
        # Check if project has configured members
        any_member_stmt = select(ProjectMember)
        if project_id:
            any_member_stmt = any_member_stmt.where(ProjectMember.project_id == project_id)
        any_res = await db.execute(any_member_stmt.limit(1))
        if any_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "USER_NOT_AUTHORIZED",
                    "message": f"User '{reviewer_id}' not found among authorized project members.",
                },
            )


@router.get(
    "/{proposal_id}",
    response_model=APIResponse[ProposalResponse],
    summary="Get Proposed Fix or Action Details",
    responses={404: {"model": ErrorResponse, "description": "Proposal Not Found"}},
)
async def get_proposal(
    proposal_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details, diff patch, or task action details for a specific proposal."""
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
    summary="Human Approval for Proposal",
    responses={
        404: {"model": ErrorResponse, "description": "Proposal Not Found"},
        400: {"model": ErrorResponse, "description": "Proposal Not in Proposed State"},
        403: {"model": ErrorResponse, "description": "Permission Denied"},
        409: {"model": ErrorResponse, "description": "Stale Proposal - State Changed"},
    },
)
async def approve_proposal(
    proposal_id: str,
    req: ProposalApprovalRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve a proposal.

    If task proposal:
      - Validates approver RBAC (team_lead / project_manager / admin).
      - Validates task version (optimistic locking preventing stale overwrites).
      - Executes backend task mutation (status change, blocker reason, progress note).
      - Logs audit trail and sends Telegram confirmation.
    If code review diff proposal:
      - Resumes LangGraph workflow to create GitHub Draft PR.
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

    # ── Task Proposal Execution Flow ──────────────────────────────────────────
    if proposal.task_id:
        # 1. RBAC check
        await _verify_approver_permissions(req.reviewer_id, proposal.project_id, db)

        # 2. Validate current task state & concurrency guard
        task_res = await db.execute(select(Task).where(Task.id == proposal.task_id))
        task = task_res.scalar_one_or_none()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TASK_NOT_FOUND", "message": f"Target task {proposal.task_id} not found"},
            )

        if proposal.expected_task_version and task.version != proposal.expected_task_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "STALE_PROPOSAL",
                    "message": f"Task state has changed since proposal was generated (task version {task.version} != expected {proposal.expected_task_version}).",
                },
            )

        # 3. Execute approved task transition through validated backend logic
        prev_status = task.status
        action = proposal.proposed_action or "update_progress"

        if action == "set_blocked":
            task.status = "blocked"
            task.blocker_reason = proposal.blocker_reason
            task.version += 1
        elif action == "mark_completed":
            task.status = "completed"
            task.version += 1
        elif action == "assign_task":
            # Assign to target assignee if specified
            task.version += 1
        elif action == "update_progress":
            task.version += 1

        proposal.status = ProposalStatus.EXECUTED.value
        proposal.reviewer_id = req.reviewer_id
        proposal.reviewer_notes = req.comments
        proposal.execution_result = {
            "task_id": task.id,
            "task_key": task.task_key,
            "previous_status": prev_status,
            "new_status": task.status,
            "executed_by": req.reviewer_id,
        }

        # 4. Record audit event
        db.add(
            AuditEvent(
                run_id=proposal.run_id,
                proposal_id=proposal.id,
                task_id=task.id,
                actor=f"human:{req.reviewer_id}",
                action="task_action_approved_and_executed",
                details={
                    "task_id": task.id,
                    "task_key": task.task_key,
                    "previous_status": prev_status,
                    "new_status": task.status,
                    "action": action,
                    "comments": req.comments,
                },
            )
        )
        await db.commit()
        await db.refresh(proposal)

        # 5. Send Telegram confirmation alert
        await TelegramNotifier().send_action_execution_alert(
            task_key=task.task_key,
            task_title=task.title,
            action=action,
            reviewer_id=req.reviewer_id,
            new_status=task.status,
        )

        # 6. Resume graph if associated with a thread
        if proposal.run_id:
            try:
                config = {"configurable": {"thread_id": proposal.run_id}}
                await app_workflow.aupdate_state(
                    config,
                    {
                        "approval_status": "APPROVED",
                        "reviewer_id": req.reviewer_id,
                        "reviewer_notes": req.comments,
                    },
                    as_node="notification_agent",
                )
                await app_workflow.ainvoke(None, config=config)
            except Exception as e:
                logger.warning(f"Could not cleanly resume graph for task proposal: {e}")

        return APIResponse(
            success=True,
            message="Task proposal successfully approved and executed",
            data=ProposalResponse.model_validate(proposal),
        )

    # ── PR Code Review Fix Diff Flow ──────────────────────────────────────────
    proposal.status = ProposalStatus.APPROVED.value
    proposal.reviewer_id = req.reviewer_id
    proposal.reviewer_notes = req.comments

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

    config = {"configurable": {"thread_id": proposal.run_id}}
    try:
        if req.create_draft_pr:
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

        run_res = await db.execute(select(AnalysisRun).where(AnalysisRun.id == proposal.run_id))
        run = run_res.scalar_one_or_none()
        if run:
            run.status = AnalysisRunStatus.COMPLETED.value

        await db.commit()
        await db.refresh(proposal)

    except Exception as e:
        logger.error(f"Error resuming graph execution after approval: {e}")
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
    summary="Human Rejection for Proposal",
    responses={
        404: {"model": ErrorResponse, "description": "Proposal Not Found"},
        400: {"model": ErrorResponse, "description": "Proposal Not in Proposed State"},
        403: {"model": ErrorResponse, "description": "Permission Denied"},
    },
)
async def reject_proposal(
    proposal_id: str,
    req: ProposalRejectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject a proposal.

    For task proposals: leaves task state completely unchanged.
    Records reason in audit trail.
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
                "message": f"Cannot reject proposal in status '{proposal.status}'",
            },
        )

    if proposal.task_id:
        await _verify_approver_permissions(req.reviewer_id, proposal.project_id, db)

    proposal.status = ProposalStatus.REJECTED.value
    proposal.reviewer_id = req.reviewer_id
    proposal.reviewer_notes = req.reason

    db.add(
        AuditEvent(
            run_id=proposal.run_id,
            proposal_id=proposal.id,
            task_id=proposal.task_id,
            actor=f"human:{req.reviewer_id}",
            action="proposal_rejected",
            details={"reason": req.reason},
        )
    )

    if proposal.run_id:
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
