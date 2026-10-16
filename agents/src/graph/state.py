from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # Context & Target (PR code review)
    run_id: str
    repo_owner: str
    repo_name: str
    pr_number: int
    commit_sha: str
    pr_title: str
    pr_description: str
    auth_token: Optional[str]

    # Task & Message Context (DevOps/Task Management)
    project_id: Optional[str]
    source_platform: Optional[str]  # "telegram", "github", "api"
    source_event_id: Optional[str]
    sender_id: Optional[str]
    message_text: Optional[str]
    task_id: Optional[str]
    task_key: Optional[str]
    intent: Optional[str]
    relevant_context: Optional[Dict[str, Any]]
    github_evidence: Optional[List[Dict[str, Any]]]
    proposed_action: Optional[str]
    blocker_reason: Optional[str]
    next_action: Optional[str]
    confidence: Optional[str]
    expected_task_version: Optional[int]
    clarification_needed: Optional[bool]
    clarification_message: Optional[str]
    execution_result: Optional[Dict[str, Any]]

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
