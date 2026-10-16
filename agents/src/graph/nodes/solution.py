import logging
import uuid
from typing import Any, Dict, List
from src.config import SeverityLevel
from src.graph.state import AgentState
from src.services.llm import LLMService

logger = logging.getLogger(__name__)


async def solution_agent_node(state: AgentState) -> Dict[str, Any]:
    """Solution Agent.

    Generates proposed surgical fix diffs for high-priority/critical findings.
    Leaves changes in PROPOSED state; never performs unilateral writes to GitHub.
    """
    triaged = state.get("triaged_findings", [])
    raw_diff = state.get("raw_diff", "")
    llm_service = LLMService()

    # Target high and critical findings for proposed remediations (limit to top 2 to bound latency & cost)
    candidates = [
        f for f in triaged
        if f.get("severity") in (SeverityLevel.CRITICAL.value, SeverityLevel.HIGH.value)
    ][:2]

    proposals: List[Dict[str, Any]] = []

    for finding in candidates:
        fix_dict = await llm_service.generate_fix_diff(finding, raw_diff)
        if fix_dict and fix_dict.get("diff_patch"):
            proposal_entry = {
                "id": str(uuid.uuid4()),
                "finding_id": finding.get("id"),
                "finding_fingerprint": finding.get("fingerprint"),
                "title": fix_dict.get("title", f"Fix: {finding.get('title')}"),
                "description": fix_dict.get("description", "Proposed remediation patch"),
                "diff_patch": fix_dict.get("diff_patch", ""),
                "target_branch": f"pr-{state.get('pr_number', 0)}-fix",
                "status": "PROPOSED",
            }
            proposals.append(proposal_entry)

    audit_entry = {
        "node": "solution_agent",
        "action": "proposals_generated",
        "count": len(proposals),
    }

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "fix_proposals": proposals,
        "approval_required": len(proposals) > 0,
        "audit_logs": logs,
    }
