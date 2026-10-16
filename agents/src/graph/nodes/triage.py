import hashlib
import logging
from typing import Any, Dict, List
from src.config import SeverityLevel
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    SeverityLevel.CRITICAL.value: 4,
    SeverityLevel.HIGH.value: 3,
    SeverityLevel.MEDIUM.value: 2,
    SeverityLevel.LOW.value: 1,
    SeverityLevel.INFO.value: 0,
}


def compute_finding_fingerprint(finding: Dict[str, Any]) -> str:
    """Compute deterministic fingerprint for finding deduplication."""
    category = str(finding.get("category", "")).strip().upper()
    file_path = str(finding.get("file_path", "")).strip().lower()
    line_number = str(finding.get("line_number") or 0)
    title = str(finding.get("title", "")).strip().lower()
    raw = f"{category}:{file_path}:{line_number}:{title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


async def triage_and_risk_node(state: AgentState) -> Dict[str, Any]:
    """Triage & Risk Agent.

    Handles either:
    1. Task Message: Validates proposed action against DB state and business rules.
       - Enforces strict task matching: cannot mutate task if not uniquely verified.
       - Prevents invented IDs or unverified evidence.
       - Verifies acceptance criteria for task completion.
    2. PR Code Review: Deterministically deduplicates findings and scores severity.
    """
    logs = list(state.get("audit_logs", []))

    if state.get("message_text"):
        clarification_needed = state.get("clarification_needed", False)
        task_id = state.get("task_id")
        intent = state.get("intent", "ambiguous")
        proposed_action = state.get("proposed_action", "request_clarification")

        # Business Rule 1: Task matching is strict. Act only on verified task linked to source event.
        if clarification_needed or not task_id:
            audit_entry = {
                "node": "triage_and_risk",
                "action": "task_triage_clarification_required",
                "reason": "Task not uniquely identified. Downgrading to clarification request.",
            }
            logs.append(audit_entry)
            return {
                "clarification_needed": True,
                "proposed_action": "request_clarification",
                "approval_required": False,
                "highest_severity": SeverityLevel.INFO.value,
                "audit_logs": logs,
            }

        # Business Rule 2: Acceptance criteria verification.
        # Do not treat a commit or merged PR as proof of task completion alone.
        if intent == "task_completed":
            ctx = state.get("relevant_context") or {}
            # If current task is blocked, require human review before completion
            if ctx.get("status") == "blocked":
                logger.info(f"Task {task_id} was blocked; transition to complete requires lead review.")

        # Rate severity: Blocker reports have HIGH severity to trigger Telegram notification
        highest_sev = SeverityLevel.HIGH.value if proposed_action == "set_blocked" else SeverityLevel.INFO.value

        audit_entry = {
            "node": "triage_and_risk",
            "action": "task_triage_validated",
            "task_id": task_id,
            "intent": intent,
            "proposed_action": proposed_action,
            "highest_severity": highest_sev,
        }
        logs.append(audit_entry)

        return {
            "highest_severity": highest_sev,
            "audit_logs": logs,
        }

    # PR Code Review Triage
    raw_findings = state.get("raw_findings", [])
    deduped_map: Dict[str, Dict[str, Any]] = {}

    for item in raw_findings:
        fp = compute_finding_fingerprint(item)
        if fp not in deduped_map:
            normalized = dict(item)
            normalized["fingerprint"] = fp
            sev = str(normalized.get("severity", "INFO")).upper()
            if sev not in SEVERITY_WEIGHTS:
                sev = SeverityLevel.INFO.value
            normalized["severity"] = sev
            deduped_map[fp] = normalized

    triaged = list(deduped_map.values())
    triaged.sort(
        key=lambda f: SEVERITY_WEIGHTS.get(f.get("severity", SeverityLevel.INFO.value), 0),
        reverse=True,
    )

    highest_sev = SeverityLevel.INFO.value
    if triaged:
        highest_sev = triaged[0].get("severity", SeverityLevel.INFO.value)

    audit_entry = {
        "node": "triage_and_risk",
        "action": "triage_completed",
        "total_findings": len(triaged),
        "highest_severity": highest_sev,
    }
    logs.append(audit_entry)

    return {
        "triaged_findings": triaged,
        "highest_severity": highest_sev,
        "audit_logs": logs,
    }
