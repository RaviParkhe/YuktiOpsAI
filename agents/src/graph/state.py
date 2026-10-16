from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # Context & Target
    run_id: str
    repo_owner: str
    repo_name: str
    pr_number: int
    commit_sha: str
    pr_title: str
    pr_description: str
    auth_token: Optional[str]

    # Deterministic Context Ingestion
    raw_diff: str
    diff_truncated: bool
    ci_status: str

    # Logical Analysis & Triage
    raw_findings: List[Dict[str, Any]]
    triaged_findings: List[Dict[str, Any]]
    highest_severity: str

    # Solution Generation
    fix_proposals: List[Dict[str, Any]]

    # Notifications
    notification_sent: bool

    # Approval & Human-in-the-Loop Action
    approval_required: bool
    approval_status: str  # PENDING, APPROVED, REJECTED
    reviewer_id: Optional[str]
    reviewer_notes: Optional[str]
    draft_pr_url: Optional[str]

    # Audit & Status
    audit_logs: List[Dict[str, Any]]
    status: str
    error: Optional[str]
