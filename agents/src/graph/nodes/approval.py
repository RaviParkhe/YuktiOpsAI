import logging
from typing import Any, Dict
from src.config import get_settings
from src.graph.state import AgentState
from src.services.github import GitHubService

logger = logging.getLogger(__name__)


async def approval_and_action_node(state: AgentState) -> Dict[str, Any]:
    """Approval & Action Node.

    Executes state changes or external draft PR creations ONLY after human approval.
    Note: Only the first proposal in fix_proposals is actioned per approval cycle.
    """
    approval_status = state.get("approval_status", "PENDING")
    proposals = list(state.get("fix_proposals", []))
    draft_pr_url = state.get("draft_pr_url")

    audit_entry = {
        "node": "approval_and_action",
        "approval_status": approval_status,
        "reviewer_id": state.get("reviewer_id"),
    }

    if proposals and proposals[0].get("task_id"):
        # Task proposal workflow
        proposal = proposals[0]
        audit_entry["task_id"] = proposal.get("task_id")

        if approval_status == "APPROVED":
            proposal["status"] = "EXECUTED"
            audit_entry["action"] = "task_action_executed"
            audit_entry["proposed_action"] = proposal.get("proposed_action")
        elif approval_status == "REJECTED":
            proposal["status"] = "REJECTED"
            audit_entry["action"] = "task_action_rejected"
        elif approval_status == "PENDING":
            audit_entry["action"] = "awaiting_human_approval"
        else:
            logger.warning(f"approval_and_action_node: unrecognised approval_status='{approval_status}'")
            audit_entry["action"] = f"unknown_status:{approval_status}"

        logs = list(state.get("audit_logs", []))
        logs.append(audit_entry)
        return {
            "fix_proposals": proposals,
            "audit_logs": logs,
        }

    # PR Code Review Draft PR Workflow
    if approval_status == "APPROVED" and proposals:
        repo_owner = state.get("repo_owner", "")
        repo_name = state.get("repo_name", "")
        if not repo_owner or not repo_name:
            logger.error("approval_and_action_node: repo_owner or repo_name missing from state.")
            audit_entry["action"] = "action_execution_failed"
            audit_entry["error"] = "Missing repo_owner or repo_name in workflow state."
            logs = list(state.get("audit_logs", []))
            logs.append(audit_entry)
            return {"fix_proposals": proposals, "draft_pr_url": draft_pr_url, "audit_logs": logs}

        auth_token = state.get("auth_token")
        settings = get_settings()
        if not auth_token and settings.ENVIRONMENT.value == "production":
            logger.error("approval_and_action_node: auth_token is required in production.")
            audit_entry["action"] = "action_execution_failed"
            audit_entry["error"] = "auth_token is required in production to create a Draft PR."
            logs = list(state.get("audit_logs", []))
            logs.append(audit_entry)
            return {"fix_proposals": proposals, "draft_pr_url": draft_pr_url, "audit_logs": logs}

        github = GitHubService()
        proposal = proposals[0]

        try:
            draft_pr_url = await github.create_draft_pr_for_proposal(
                owner=repo_owner,
                repo=repo_name,
                target_branch=proposal.get("target_branch", "main"),
                proposal_title=proposal.get("title", "Fix PR"),
                proposal_body=proposal.get("description", ""),
                diff_patch=proposal.get("diff_patch", ""),
                auth_token=auth_token,
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

    elif approval_status == "PENDING":
        audit_entry["action"] = "awaiting_human_approval"

    else:
        logger.warning(f"approval_and_action_node: unrecognised approval_status='{approval_status}'")
        audit_entry["action"] = f"unknown_status:{approval_status}"

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "fix_proposals": proposals,
        "draft_pr_url": draft_pr_url,
        "audit_logs": logs,
    }
