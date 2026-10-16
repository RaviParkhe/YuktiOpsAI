import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from src.config import SeverityLevel
from src.schemas.analysis import AnalysisRunStatus, CIStatus
from src.schemas.proposals import ProposalStatus
from .session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    key = Column(String(20), nullable=False, unique=True, index=True)  # e.g. YUK
    repo_name = Column(String(100), nullable=True)  # e.g. TechSena/YuktiOps
    created_at = Column(DateTime, default=utc_now, nullable=False)

    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default="developer")  # team_lead, project_manager, admin, developer
    telegram_user_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    project = relationship("Project", back_populates="members")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_key = Column(String(50), nullable=False, index=True)  # e.g. YUK-101
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="todo")  # todo, in_progress, blocked, in_review, completed
    assignee_id = Column(String(100), nullable=True, index=True)
    blocker_reason = Column(Text, nullable=True)
    progress_notes = Column(Text, nullable=True)
    dependencies = Column(JSON, nullable=True)  # e.g. ["YUK-100"]
    acceptance_criteria = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)  # optimistic concurrency guard
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="tasks")
    messages = relationship("TaskMessage", back_populates="task", cascade="all, delete-orphan")
    evidence = relationship("GitHubEvidence", back_populates="task", cascade="all, delete-orphan")
    proposals = relationship("FixProposal", back_populates="task", cascade="all, delete-orphan")


class TaskMessage(Base):
    __tablename__ = "task_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    sender_id = Column(String(100), nullable=False, index=True)
    source_platform = Column(String(30), nullable=False, default="telegram")
    source_event_id = Column(String(100), nullable=True, index=True)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("Task", back_populates="messages")


class GitHubEvidence(Base):
    __tablename__ = "github_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)  # commit, pull_request, review
    delivery_id = Column(String(100), nullable=True, index=True)
    commit_sha = Column(String(40), nullable=True)
    pr_number = Column(Integer, nullable=True)
    branch = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    task = relationship("Task", back_populates="evidence")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    delivery_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(30), nullable=False, default="queued")
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    repo_owner = Column(String(100), nullable=False, index=True)
    repo_name = Column(String(100), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    commit_sha = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False, default=AnalysisRunStatus.QUEUED.value)
    ci_status = Column(String(30), nullable=False, default=CIStatus.UNKNOWN.value)
    highest_severity = Column(String(30), nullable=False, default=SeverityLevel.INFO.value)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    findings = relationship("Finding", back_populates="run", cascade="all, delete-orphan")
    proposals = relationship("FixProposal", back_populates="run", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="run", cascade="all, delete-orphan")

    @property
    def repo_full_name(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    severity = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=True)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    fingerprint = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AnalysisRun", back_populates="findings")
    proposals = relationship("FixProposal", back_populates="finding")


class FixProposal(Base):
    __tablename__ = "fix_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    diff_patch = Column(Text, nullable=True, default="")
    target_branch = Column(String(100), nullable=True, default="main")
    status = Column(String(30), nullable=False, default=ProposalStatus.PROPOSED.value)
    intent = Column(String(50), nullable=True)
    proposed_action = Column(String(100), nullable=True)  # set_blocked, mark_completed, assign_task, update_progress, request_clarification
    blocker_reason = Column(Text, nullable=True)
    next_action = Column(Text, nullable=True)
    confidence = Column(String(20), nullable=True)
    expected_task_version = Column(Integer, nullable=True)
    source_platform = Column(String(30), nullable=True, default="telegram")
    source_event_id = Column(String(100), nullable=True, index=True)
    sender_id = Column(String(100), nullable=True)
    clarification_prompt = Column(Text, nullable=True)
    execution_result = Column(JSON, nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    github_draft_pr_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    run = relationship("AnalysisRun", back_populates="proposals")
    finding = relationship("Finding", back_populates="proposals")
    task = relationship("Task", back_populates="proposals")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    proposal_id = Column(String(36), ForeignKey("fix_proposals.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AnalysisRun", back_populates="audit_events")
