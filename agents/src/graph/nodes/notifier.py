import logging
from typing import Any, Dict
from src.config import SeverityLevel, get_settings
from src.graph.state import AgentState
from src.services.telegram import TelegramNotifier

logger = logging.getLogger(__name__)

SEVERITY_RANKS = {
    SeverityLevel.INFO.value: 0,
    SeverityLevel.LOW.value: 1,
    SeverityLevel.MEDIUM.value: 2,
    SeverityLevel.HIGH.value: 3,
    SeverityLevel.CRITICAL.value: 4,
}


async def notification_node(state: AgentState) -> Dict[str, Any]:
    """Notification & Escalation Agent.

    Handles either:
    1. Task Message: Dispatches concise Telegram proposal alerts or clarification messages.
    2. PR Code Review: Evaluates severity thresholds and routes actionable summaries to Telegram.
    """
    settings = get_settings()
    notifier = TelegramNotifier()
    logs = list(state.get("audit_logs", []))
    sent = False

    if state.get("message_text"):
        clarification_needed = state.get("clarification_needed", False)

        if clarification_needed:
            msg = state.get("clarification_message") or "Which task does this update relate to? Please specify the task key (e.g. YUK-101)."
            sent = await notifier.send_clarification_message(msg)
            action_name = "clarification_dispatched"
        elif state.get("fix_proposals"):
            p = state["fix_proposals"][0]
            task_key = state.get("task_key", "Task")
            ctx = state.get("relevant_context") or {}
            task_title = ctx.get("title", "Task Update")

            sent = await notifier.send_task_proposal_alert(
                task_key=task_key,
                task_title=task_title,
                proposal_id=p["id"],
                proposed_action=p.get("proposed_action", "mutate_task"),
                blocker_reason=p.get("blocker_reason"),
                next_action=p.get("next_action"),
                sender_id=state.get("sender_id"),
            )
            action_name = "task_proposal_alert_dispatched"
        else:
            action_name = "no_notification_needed"

        audit_entry = {
            "node": "notification_agent",
            "action": action_name,
            "sent": sent,
        }
        logs.append(audit_entry)

        return {
            "notification_sent": sent,
            "audit_logs": logs,
        }

    # PR Code Review Notification
    highest_sev = state.get("highest_severity", SeverityLevel.INFO.value)
    threshold = settings.SEVERITY_NOTIFICATION_THRESHOLD.value

    current_rank = SEVERITY_RANKS.get(highest_sev, 0)
    threshold_rank = SEVERITY_RANKS.get(threshold, 3)

    if current_rank >= threshold_rank:
        proposals = state.get("fix_proposals", [])
        proposal_id = proposals[0]["id"] if proposals else None
        repo_full = f"{state.get('repo_owner')}/{state.get('repo_name')}"

        sent = await notifier.send_finding_alert(
            repo_full_name=repo_full,
            pr_number=state.get("pr_number", 0),
            run_id=state.get("run_id", ""),
            highest_severity=highest_sev,
            findings=state.get("triaged_findings", []),
            proposal_id=proposal_id,
        )

    audit_entry = {
        "node": "notification_agent",
        "action": "notification_dispatched",
        "sent": sent,
        "highest_severity": highest_sev,
    }
    logs.append(audit_entry)

    return {
        "notification_sent": sent,
        "audit_logs": logs,
    }
