import asyncio
import logging
from typing import Any, Dict, Optional
from arq.connections import RedisSettings, create_pool
from sqlalchemy import select
from src.config import get_settings
from src.db.models import AnalysisRun, AuditEvent, Finding, FixProposal
from src.db.session import async_session_factory
from src.graph.state import AgentState
from src.graph.workflow import app_workflow
from src.schemas.analysis import AnalysisRunStatus

logger = logging.getLogger(__name__)


async def execute_pr_analysis_pipeline(
    run_id: str,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    commit_sha: str,
    pr_title: str = "",
    pr_description: str = "",
    auth_token: Optional[str] = None,
) -> None:
    """Execute the full agent workflow pipeline asynchronously and persist outputs."""
    logger.info(f"Starting PR analysis pipeline for run_id={run_id} ({repo_owner}/{repo_name}#{pr_number})")

    async with async_session_factory() as session:
        result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            logger.error(f"AnalysisRun {run_id} not found in database.")
            return

        run.status = AnalysisRunStatus.IN_PROGRESS.value
        await session.commit()

    initial_state: AgentState = {
        "run_id": run_id,
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "pr_number": pr_number,
        "commit_sha": commit_sha,
        "pr_title": pr_title,
        "pr_description": pr_description,
        "auth_token": auth_token,
        "audit_logs": [],
    }

    try:
        config = {"configurable": {"thread_id": run_id}}
        final_state = await app_workflow.ainvoke(initial_state, config=config)

        # Retrieve paused or ended state
        triaged_findings = final_state.get("triaged_findings", [])
        fix_proposals = final_state.get("fix_proposals", [])
        ci_status = final_state.get("ci_status", "UNKNOWN")
        highest_sev = final_state.get("highest_severity", "INFO")
        audit_logs = final_state.get("audit_logs", [])

        # Check if workflow is waiting at approval checkpoint (async-safe call)
        workflow_state = await app_workflow.aget_state(config)
        is_paused_for_approval = bool(workflow_state and workflow_state.next and "approval_and_action" in workflow_state.next)

        async with async_session_factory() as session:
            result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
            run = result.scalar_one_or_none()
            if not run:
                return

            run.ci_status = ci_status
            run.highest_severity = highest_sev
            run.status = (
                AnalysisRunStatus.WAITING_APPROVAL.value
                if is_paused_for_approval
                else AnalysisRunStatus.COMPLETED.value
            )

            # Persist findings
            for item in triaged_findings:
                finding = Finding(
                    id=item.get("id"),
                    run_id=run_id,
                    category=item.get("category", "CODE_QUALITY"),
                    severity=item.get("severity", "INFO"),
                    title=item.get("title", "Detected Finding"),
                    file_path=item.get("file_path"),
                    line_number=item.get("line_number"),
                    description=item.get("description", ""),
                    recommendation=item.get("recommendation"),
                    fingerprint=item.get("fingerprint"),
                )
                session.add(finding)

            # Persist fix proposals
            for p in fix_proposals:
                proposal = FixProposal(
                    id=p.get("id"),
                    run_id=run_id,
                    finding_id=p.get("finding_id"),
                    title=p.get("title", "Fix Proposal"),
                    description=p.get("description", ""),
                    diff_patch=p.get("diff_patch", ""),
                    target_branch=p.get("target_branch", "main"),
                    status=p.get("status", "PROPOSED"),
                )
                session.add(proposal)

            # Persist audit events
            for log_entry in audit_logs:
                audit = AuditEvent(
                    run_id=run_id,
                    actor=f"agent:{log_entry.get('node', 'orchestrator')}",
                    action=log_entry.get("action", "step_executed"),
                    details=log_entry,
                )
                session.add(audit)

            await session.commit()
            logger.info(
                f"PR analysis pipeline finished for {run_id}. "
                f"Status: {run.status}, Findings: {len(triaged_findings)}, Proposals: {len(fix_proposals)}"
            )

    except Exception as e:
        logger.exception(f"Error during PR analysis execution for {run_id}: {e}")
        async with async_session_factory() as session:
            result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == run_id))
            run = result.scalar_one_or_none()
            if run:
                run.status = AnalysisRunStatus.FAILED.value
                run.error_message = str(e)
                session.add(
                    AuditEvent(
                        run_id=run_id,
                        actor="system:orchestrator",
                        action="pipeline_failed",
                        details={"error": str(e)},
                    )
                )
                await session.commit()


async def arq_analyze_pr_job(
    ctx: Dict[str, Any],
    run_id: str,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    commit_sha: str,
    pr_title: str = "",
    pr_description: str = "",
    auth_token: Optional[str] = None,
) -> None:
    """ARQ Worker entrypoint."""
    await execute_pr_analysis_pipeline(
        run_id=run_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=pr_number,
        commit_sha=commit_sha,
        pr_title=pr_title,
        pr_description=pr_description,
        auth_token=auth_token,
    )


class WorkerSettings:
    """ARQ Worker configuration."""
    functions = [arq_analyze_pr_job]
    redis_settings = RedisSettings.from_dsn(get_settings().REDIS_URL)


async def execute_task_message_pipeline(
    run_id: str,
    sender_id: str,
    message_text: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    source_event_id: Optional[str] = None,
    source_platform: str = "telegram",
) -> Optional[Dict[str, Any]]:
    """Execute the agent workflow pipeline for a task message."""
    logger.info(f"Starting task message pipeline for run_id={run_id} sender={sender_id}")

    initial_state: AgentState = {
        "run_id": run_id,
        "project_id": project_id,
        "source_platform": source_platform,
        "source_event_id": source_event_id,
        "sender_id": sender_id,
        "message_text": message_text,
        "task_id": task_id,
        "audit_logs": [],
    }

    try:
        config = {"configurable": {"thread_id": run_id}}
        final_state = await app_workflow.ainvoke(initial_state, config=config)

        proposals = final_state.get("fix_proposals", [])
        audit_logs = final_state.get("audit_logs", [])

        # Persist generated proposals into database
        async with async_session_factory() as session:
            for p in proposals:
                # Check duplicate active proposal
                dup_stmt = select(FixProposal).where(
                    FixProposal.task_id == p.get("task_id"),
                    FixProposal.proposed_action == p.get("proposed_action"),
                    FixProposal.status == "PROPOSED",
                )
                res = await session.execute(dup_stmt)
                if res.scalar_one_or_none():
                    logger.info(f"Identical active proposal already exists for task {p.get('task_id')}, skipping duplicate.")
                    continue

                proposal_record = FixProposal(
                    id=p.get("id"),
                    run_id=run_id,
                    task_id=p.get("task_id"),
                    project_id=p.get("project_id"),
                    title=p.get("title", "Task Proposal"),
                    description=p.get("description", ""),
                    diff_patch="",
                    target_branch="main",
                    status=p.get("status", "PROPOSED"),
                    intent=p.get("intent"),
                    proposed_action=p.get("proposed_action"),
                    blocker_reason=p.get("blocker_reason"),
                    next_action=p.get("next_action"),
                    confidence=p.get("confidence"),
                    expected_task_version=p.get("expected_task_version"),
                    source_platform=p.get("source_platform", "telegram"),
                    source_event_id=p.get("source_event_id"),
                    sender_id=p.get("sender_id"),
                )
                session.add(proposal_record)

            # Persist audit entries
            for log_entry in audit_logs:
                session.add(
                    AuditEvent(
                        run_id=run_id,
                        task_id=final_state.get("task_id"),
                        actor=f"agent:{log_entry.get('node', 'orchestrator')}",
                        action=log_entry.get("action", "step_executed"),
                        details=log_entry,
                    )
                )

            await session.commit()
            return final_state

    except Exception as e:
        logger.exception(f"Error during task message pipeline execution for {run_id}: {e}")
        async with async_session_factory() as session:
            session.add(
                AuditEvent(
                    run_id=run_id,
                    task_id=task_id,
                    actor="system:orchestrator",
                    action="task_pipeline_failed",
                    details={"error": str(e), "message_text": message_text},
                )
            )
            await session.commit()
        return None


async def arq_task_message_job(
    ctx: Dict[str, Any],
    run_id: str,
    sender_id: str,
    message_text: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    source_event_id: Optional[str] = None,
    source_platform: str = "telegram",
) -> None:
    """ARQ Worker entrypoint for task message pipeline."""
    await execute_task_message_pipeline(
        run_id=run_id,
        sender_id=sender_id,
        message_text=message_text,
        project_id=project_id,
        task_id=task_id,
        source_event_id=source_event_id,
        source_platform=source_platform,
    )


async def enqueue_task_message(
    run_id: str,
    sender_id: str,
    message_text: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    source_event_id: Optional[str] = None,
    source_platform: str = "telegram",
) -> None:
    """Enqueue task message either to Redis (ARQ) or fallback to asyncio task if Redis is offline."""
    # Deduplication check
    if source_event_id:
        async with async_session_factory() as session:
            res = await session.execute(
                select(FixProposal).where(FixProposal.source_event_id == source_event_id)
            )
            if res.scalar_one_or_none():
                logger.info(f"Duplicate event {source_event_id} already processed. Skipping.")
                return

    settings = get_settings()
    enqueued_to_redis = False
    if settings.ENVIRONMENT.value != "testing":
        try:
            redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
            await redis_pool.enqueue_job(
                "arq_task_message_job",
                run_id=run_id,
                sender_id=sender_id,
                message_text=message_text,
                project_id=project_id,
                task_id=task_id,
                source_event_id=source_event_id,
                source_platform=source_platform,
            )
            await redis_pool.close()
            enqueued_to_redis = True
            logger.info(f"Enqueued task message job to Redis ARQ for run_id={run_id}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis ({e}). Falling back to local asyncio background task.")

    if not enqueued_to_redis:
        def _handle_task_error(task: asyncio.Task) -> None:
            if task.cancelled():
                return
            exc = task.exception()
            if exc:
                logger.error(f"Background task pipeline failed for run_id={run_id}: {exc}", exc_info=exc)

        task = asyncio.create_task(
            execute_task_message_pipeline(
                run_id=run_id,
                sender_id=sender_id,
                message_text=message_text,
                project_id=project_id,
                task_id=task_id,
                source_event_id=source_event_id,
                source_platform=source_platform,
            )
        )
        task.add_done_callback(_handle_task_error)


async def enqueue_pr_analysis(
    run_id: str,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    commit_sha: str,
    pr_title: str = "",
    pr_description: str = "",
    auth_token: Optional[str] = None,
) -> None:
    """Enqueue PR analysis either to Redis (ARQ) or fallback to asyncio task if Redis is offline."""
    settings = get_settings()
    enqueued_to_redis = False

    if settings.ENVIRONMENT.value != "testing":
        try:
            redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
            await redis_pool.enqueue_job(
                "arq_analyze_pr_job",
                run_id=run_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pr_number=pr_number,
                commit_sha=commit_sha,
                pr_title=pr_title,
                pr_description=pr_description,
                auth_token=auth_token,
            )
            await redis_pool.close()
            enqueued_to_redis = True
            logger.info(f"Enqueued job to Redis ARQ for run_id={run_id}")
        except Exception as e:
            logger.warning(f"Could not connect to Redis ({e}). Falling back to local asyncio background task.")

    if not enqueued_to_redis:
        # Standalone local development fallback — runs in the current event loop.
        # Store the task reference so unhandled exceptions are surfaced via the callback.
        def _handle_task_error(task: asyncio.Task) -> None:
            if task.cancelled():
                return
            exc = task.exception()
            if exc:
                logger.error(f"Background pipeline task failed for run_id={run_id}: {exc}", exc_info=exc)

        task = asyncio.create_task(
            execute_pr_analysis_pipeline(
                run_id=run_id,
                repo_owner=repo_owner,
                repo_name=repo_name,
                pr_number=pr_number,
                commit_sha=commit_sha,
                pr_title=pr_title,
                pr_description=pr_description,
                auth_token=auth_token,
            )
        )
        task.add_done_callback(_handle_task_error)
