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

    Evaluates severity thresholds and routes actionable summaries to Telegram.
    """
    settings = get_settings()
    notifier = TelegramNotifier()

    highest_sev = state.get("highest_severity", SeverityLevel.INFO.value)
    threshold = settings.SEVERITY_NOTIFICATION_THRESHOLD.value

    current_rank = SEVERITY_RANKS.get(highest_sev, 0)
    threshold_rank = SEVERITY_RANKS.get(threshold, 3)

    sent = False
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

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "notification_sent": sent,
        "audit_logs": logs,
    }
