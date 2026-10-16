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
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    diff_patch = Column(Text, nullable=False)
    target_branch = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default=ProposalStatus.PROPOSED.value)
    reviewer_id = Column(String(100), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    github_draft_pr_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    run = relationship("AnalysisRun", back_populates="proposals")
    finding = relationship("Finding", back_populates="proposals")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=True, index=True)
    proposal_id = Column(String(36), ForeignKey("fix_proposals.id", ondelete="SET NULL"), nullable=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    run = relationship("AnalysisRun", back_populates="audit_events")
