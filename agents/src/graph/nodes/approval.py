import logging
from typing import Any, Dict
from src.graph.state import AgentState
from src.services.github import GitHubService

logger = logging.getLogger(__name__)


async def approval_and_action_node(state: AgentState) -> Dict[str, Any]:
    """Approval & Action Node.

    Executes state changes or external draft PR creations ONLY after human approval.
    """
    approval_status = state.get("approval_status", "PENDING")
    proposals = list(state.get("fix_proposals", []))
    draft_pr_url = state.get("draft_pr_url")

    audit_entry = {
        "node": "approval_and_action",
        "approval_status": approval_status,
        "reviewer_id": state.get("reviewer_id"),
    }

    if approval_status == "APPROVED" and proposals:
        github = GitHubService()
        proposal = proposals[0]

        try:
            draft_pr_url = await github.create_draft_pr_for_proposal(
                owner=state["repo_owner"],
                repo=state["repo_name"],
                target_branch=proposal.get("target_branch", "main"),
                proposal_title=proposal.get("title", "Fix PR"),
                proposal_body=proposal.get("description", ""),
                diff_patch=proposal.get("diff_patch", ""),
                auth_token=state.get("auth_token"),
            )
            proposal["status"] = "EXECUTED"
            proposal["github_draft_pr_url"] = draft_pr_url
            audit_entry["action"] = "draft_pr_created"
            audit_entry["draft_pr_url"] = draft_pr_url
        except Exception as e:
            logger.error(f"Failed to execute draft PR action: {e}")
            proposal["status"] = "FAILED"
            audit_entry["action"] = "action_execution_failed"
            audit_entry["error"] = str(e)

    elif approval_status == "REJECTED" and proposals:
        for p in proposals:
            p["status"] = "REJECTED"
        audit_entry["action"] = "proposals_rejected"

    else:
        audit_entry["action"] = "awaiting_human_approval"

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "fix_proposals": proposals,
        "draft_pr_url": draft_pr_url,
        "audit_logs": logs,
    }
