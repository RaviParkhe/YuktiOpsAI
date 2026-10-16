import logging
from typing import Any, Dict
from src.config import get_settings
from src.graph.state import AgentState
from src.services.github import GitHubService

logger = logging.getLogger(__name__)


async def ingest_context_node(state: AgentState) -> Dict[str, Any]:
    """Deterministic context ingestion node.

    Fetches bounded PR diff and CI status. Avoids LLM calls for work deterministic code can do.
    """
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

    # Check truncation
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
