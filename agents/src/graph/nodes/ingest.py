import logging
import re
from typing import Any, Dict, List
from sqlalchemy import select
from src.config import get_settings
from src.db.models import GitHubEvidence, Project, Task, TaskMessage
from src.db.session import async_session_factory
from src.graph.state import AgentState
from src.services.github import GitHubService

logger = logging.getLogger(__name__)


async def ingest_context_node(state: AgentState) -> Dict[str, Any]:
    """Deterministic context ingestion node.

    Handles either:
    1. Task Message (Telegram/Chat input): loads verified task context, dependencies, recent history, GitHub evidence.
    2. GitHub PR code review: fetches bounded PR diff and CI status.
    """
    if state.get("message_text"):
        return await _ingest_task_message_context(state)
    return await _ingest_pr_diff_context(state)


async def _ingest_task_message_context(state: AgentState) -> Dict[str, Any]:
    """Identify project, sender, and strictly match the relevant task from DB state."""
    message_text = state.get("message_text", "")
    project_id = state.get("project_id")
    task_id = state.get("task_id")
    sender_id = state.get("sender_id")

    matched_task = None
    clarification_needed = False
    clarification_message = None
    evidence_records: List[Dict[str, Any]] = []
    relevant_context: Dict[str, Any] = {}

    async with async_session_factory() as session:
        # 1. Resolve project
        project = None
        if project_id:
            res = await session.execute(select(Project).where((Project.id == project_id) | (Project.key == project_id)))
            project = res.scalar_one_or_none()
        if not project:
            res = await session.execute(select(Project))
            project = res.scalars().first()

        proj_id = project.id if project else None

        # 2. Strict Task Matching:
        # Check explicit task_id / task_key provided in state
        if task_id:
            res = await session.execute(
                select(Task).where((Task.id == task_id) | (Task.task_key == task_id))
            )
            matched_task = res.scalar_one_or_none()

        # If not explicit, extract from message text via regex (e.g. YUK-101, PROJ-42)
        if not matched_task and message_text:
            m = re.search(r"\b([A-Za-z]{2,10}-\d+)\b", message_text)
            if m:
                key = m.group(1).upper()
                res = await session.execute(select(Task).where(Task.task_key == key))
                matched_task = res.scalar_one_or_none()

        # If still not matched, check keywords in title or sender active task
        if not matched_task and proj_id:
            # Query candidate tasks for this project
            stmt = select(Task).where(Task.project_id == proj_id, Task.status != "completed")
            res = await session.execute(stmt)
            open_tasks = res.scalars().all()

            # Check keyword match in message against task title
            candidate_matches = []
            msg_lower = message_text.lower()
            for t in open_tasks:
                title_words = [w.lower() for w in re.split(r"\W+", t.title) if len(w) > 2]
                if any(w in msg_lower for w in title_words) or (t.task_key.lower() in msg_lower):
                    candidate_matches.append(t)

            # If sender has exactly one active task in progress, consider it as candidate
            if not candidate_matches and sender_id:
                sender_tasks = [t for t in open_tasks if t.assignee_id == sender_id]
                if len(sender_tasks) == 1:
                    candidate_matches = sender_tasks

            # Strict matching: act ONLY if exactly one verified task is matched. Never guess.
            if len(candidate_matches) == 1:
                matched_task = candidate_matches[0]
            elif len(candidate_matches) > 1:
                keys = ", ".join([t.task_key for t in candidate_matches])
                clarification_needed = True
                clarification_message = (
                    f"Your message could apply to multiple tasks ({keys}). "
                    f"Please specify the exact task key."
                )
            else:
                clarification_needed = True
                clarification_message = (
                    "Could not link this message to an open task. "
                    "Please specify the task key (e.g., YUK-101)."
                )

        if matched_task:
            # Retrieve relevant history: task details, dependencies, recent evidence
            relevant_context = {
                "task_id": matched_task.id,
                "task_key": matched_task.task_key,
                "title": matched_task.title,
                "description": matched_task.description,
                "status": matched_task.status,
                "assignee_id": matched_task.assignee_id,
                "blocker_reason": matched_task.blocker_reason,
                "dependencies": matched_task.dependencies or [],
                "acceptance_criteria": matched_task.acceptance_criteria,
                "version": matched_task.version,
                "project_id": matched_task.project_id,
            }

            # Retrieve recent GitHub evidence attached to this task
            ev_stmt = select(GitHubEvidence).where(GitHubEvidence.task_id == matched_task.id).order_by(GitHubEvidence.created_at.desc()).limit(5)
            ev_res = await session.execute(ev_stmt)
            for ev in ev_res.scalars().all():
                evidence_records.append({
                    "event_type": ev.event_type,
                    "commit_sha": ev.commit_sha,
                    "pr_number": ev.pr_number,
                    "branch": ev.branch,
                    "details": ev.details,
                })

            # Retrieve recent task messages for conversation context
            msg_stmt = select(TaskMessage).where(TaskMessage.task_id == matched_task.id).order_by(TaskMessage.created_at.desc()).limit(5)
            msg_res = await session.execute(msg_stmt)
            recent_msgs = [{"sender": m.sender_id, "text": m.message_text} for m in msg_res.scalars().all()]
            relevant_context["recent_messages"] = recent_msgs

    audit_entry = {
        "node": "ingest_context",
        "action": "task_context_ingested",
        "task_matched": bool(matched_task),
        "task_key": matched_task.task_key if matched_task else None,
        "clarification_needed": clarification_needed,
        "evidence_count": len(evidence_records),
    }

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "project_id": proj_id,
        "task_id": matched_task.id if matched_task else None,
        "task_key": matched_task.task_key if matched_task else None,
        "relevant_context": relevant_context,
        "github_evidence": evidence_records,
        "expected_task_version": matched_task.version if matched_task else 1,
        "clarification_needed": clarification_needed,
        "clarification_message": clarification_message,
        "audit_logs": logs,
    }


async def _ingest_pr_diff_context(state: AgentState) -> Dict[str, Any]:
    """Fetch bounded PR diff and CI status for PR code review."""
    settings = get_settings()
    github = GitHubService()

    raw_diff = state.get("raw_diff")
    if not raw_diff:
        raw_diff = await github.fetch_pr_diff(
            owner=state["repo_owner"],
            repo=state["repo_name"],
            pr_number=state["pr_number"],
            auth_token=state.get("auth_token"),
        )

    lines = raw_diff.splitlines()
    truncated = False
    if len(lines) > settings.MAX_DIFF_LINES:
        raw_diff = "\n".join(lines[: settings.MAX_DIFF_LINES]) + "\n[TRUNCATED: Exceeded max allowed diff lines]"
        truncated = True

    ci_status = state.get("ci_status")
    if not ci_status or ci_status == "UNKNOWN":
        ci_status_enum = await github.fetch_ci_status(
            owner=state["repo_owner"],
            repo=state["repo_name"],
            commit_sha=state["commit_sha"],
            auth_token=state.get("auth_token"),
        )
        ci_status = ci_status_enum.value

    audit_entry = {
        "node": "ingest_context",
        "action": "context_ingested",
        "diff_lines": len(raw_diff.splitlines()),
        "truncated": truncated,
        "ci_status": ci_status,
    }

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "raw_diff": raw_diff,
        "diff_truncated": truncated,
        "ci_status": ci_status,
        "audit_logs": logs,
    }
