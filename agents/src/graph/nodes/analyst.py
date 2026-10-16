import logging
from typing import Any, Dict
from src.graph.state import AgentState
from src.services.llm import LLMService

logger = logging.getLogger(__name__)


async def code_and_security_analysis_node(state: AgentState) -> Dict[str, Any]:
    """Specialized logical agent pass: Code Analyst + Quality & Security Analyst.

    Batches analysis per PR and isolates untrusted repository text from instructions.
    """
    llm_service = LLMService()

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

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "raw_findings": raw_findings,
        "audit_logs": logs,
    }
