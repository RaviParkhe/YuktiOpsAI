import logging
import uuid
from typing import Any, Dict, List
from src.config import SeverityLevel
from src.graph.state import AgentState
from src.services.llm import LLMService

logger = logging.getLogger(__name__)


async def solution_agent_node(state: AgentState) -> Dict[str, Any]:
    """Solution Agent.

    Handles either:
    1. Task Message: Produces a structured proposed task action with blocker reason, next action, and approval requirement.
    2. PR Code Review: Generates proposed surgical fix diffs for high-priority/critical findings.
    """
    logs = list(state.get("audit_logs", []))

    if state.get("message_text"):
        clarification_needed = state.get("clarification_needed", False)
        task_id = state.get("task_id")

        if clarification_needed or not task_id:
            audit_entry = {
                "node": "solution_agent",
                "action": "proposals_skipped_for_clarification",
            }
            logs.append(audit_entry)
            return {
                "fix_proposals": [],
                "approval_required": False,
                "audit_logs": logs,
            }

        task_key = state.get("task_key", "TASK")
        proposed_action = state.get("proposed_action", "update_progress")
        intent = state.get("intent", "progress_update")
        blocker_reason = state.get("blocker_reason")
        next_action = state.get("next_action")
        confidence = state.get("confidence", "HIGH")
        approval_required = state.get("approval_required", True)

        proposal_id = str(uuid.uuid4())
        desc_parts = [f"Classified intent: {intent}."]
        if blocker_reason:
            desc_parts.append(f"Blocker: {blocker_reason}.")
        if next_action:
            desc_parts.append(f"Next action: {next_action}.")

        proposal_entry = {
            "id": proposal_id,
            "task_id": task_id,
            "project_id": state.get("project_id"),
            "title": f"Task Mutation: {proposed_action} on {task_key}",
            "description": " ".join(desc_parts),
            "intent": intent,
            "proposed_action": proposed_action,
            "blocker_reason": blocker_reason,
            "next_action": next_action,
            "confidence": confidence,
            "expected_task_version": state.get("expected_task_version", 1),
            "source_platform": state.get("source_platform", "telegram"),
            "source_event_id": state.get("source_event_id"),
            "sender_id": state.get("sender_id"),
            "diff_patch": "",
            "target_branch": "main",
            "status": "PROPOSED",
        }

        audit_entry = {
            "node": "solution_agent",
            "action": "task_proposal_generated",
            "proposal_id": proposal_id,
            "proposed_action": proposed_action,
            "approval_required": approval_required,
        }
        logs.append(audit_entry)

        return {
            "fix_proposals": [proposal_entry],
            "approval_required": approval_required,
            "audit_logs": logs,
        }

    # PR Code Review Patch Generation
    triaged = state.get("triaged_findings", [])
    raw_diff = state.get("raw_diff", "")
    llm_service = LLMService()

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
    logs.append(audit_entry)

    return {
        "fix_proposals": proposals,
        "approval_required": len(proposals) > 0,
        "audit_logs": logs,
    }
