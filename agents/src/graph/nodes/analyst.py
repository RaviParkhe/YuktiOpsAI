import logging
from typing import Any, Dict
from src.graph.state import AgentState
from src.services.llm import LLMService

logger = logging.getLogger(__name__)


async def code_and_security_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Specialized logical agent pass:
    1. If message_text is present: DevOps Task Intent & Action classification pass.
    2. If raw_diff is present: Code Analyst + Quality & Security Analyst pass.
    """
    llm_service = LLMService()
    logs = list(state.get("audit_logs", []))

    if state.get("message_text"):
        classification = await llm_service.classify_intent_and_action(
            message_text=state.get("message_text", ""),
            task_context=state.get("relevant_context"),
            sender_id=state.get("sender_id"),
            evidence_summary=state.get("github_evidence"),
        )

        audit_entry = {
            "node": "code_and_security_analysis",
            "action": "intent_classified",
            "intent": classification.get("intent"),
            "proposed_action": classification.get("proposed_action"),
            "confidence": classification.get("confidence"),
        }
        logs.append(audit_entry)

        return {
            "intent": classification.get("intent"),
            "proposed_action": classification.get("proposed_action"),
            "blocker_reason": classification.get("blocker_reason"),
            "next_action": classification.get("next_action"),
            "confidence": classification.get("confidence", "HIGH"),
            "approval_required": classification.get("approval_required", True),
            "audit_logs": logs,
        }

    # PR Code Review Analysis
    raw_findings = await llm_service.analyze_pr_changes(
        pr_diff=state.get("raw_diff", ""),
        pr_title=state.get("pr_title", ""),
        pr_description=state.get("pr_description", ""),
        ci_status=state.get("ci_status", "UNKNOWN"),
    )

    audit_entry = {
        "node": "code_and_security_analysis",
        "action": "logical_analysis_completed",
        "findings_detected": len(raw_findings),
    }
    logs.append(audit_entry)

    return {
        "raw_findings": raw_findings,
        "audit_logs": logs,
    }
