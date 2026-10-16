"""
YuktiOpsAI Backend — SQLAlchemy ORM Models

Tables:
  users, projects, project_members, tasks, task_dependencies,
  messages, telegram_messages, credit_accounts, credit_ledger,
  referrals, ad_sessions, feature_entitlements,
  solution_runs, research_runs, audit_events
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from src.db.session import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    """Application user profile — identity provided by Firebase Auth."""
    __tablename__ = "users"

    id = Column(String(128), primary_key=True)           # Firebase UID
    email = Column(String(255), nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(String(512), nullable=True)
    role = Column(String(30), nullable=False, default="member")  # member | admin
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    credit_account = relationship("CreditAccount", back_populates="user", uselist=False, cascade="all, delete-orphan")
    referrals_sent = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer")
    referrals_received = relationship("Referral", foreign_keys="Referral.referee_id", back_populates="referee")
    entitlements = relationship("FeatureEntitlement", back_populates="user", cascade="all, delete-orphan")
    solution_runs = relationship("SolutionRun", back_populates="user", cascade="all, delete-orphan")
    research_runs = relationship("ResearchRun", back_populates="user", cascade="all, delete-orphan")
    telegram_messages = relationship("TelegramMessage", back_populates="user")
    audit_events = relationship("AuditEvent", back_populates="user")


# ── Projects & Membership ────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    github_repo_full_name = Column(String(255), nullable=True)   # owner/repo
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="member")  # owner | leader | member
    joined_at = Column(DateTime, default=_now, nullable=False)

    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")


# ── Tasks ────────────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="open")   # open|in_progress|blocked|done
    priority = Column(String(20), nullable=False, default="medium")  # low|medium|high|critical
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    project = relationship("Project", back_populates="tasks")
    dependencies = relationship(
        "TaskDependency", foreign_keys="TaskDependency.task_id",
        back_populates="task", cascade="all, delete-orphan",
    )
    blockers = relationship(
        "TaskDependency", foreign_keys="TaskDependency.depends_on_id",
        back_populates="depends_on",
    )


class TaskDependency(Base):
    """task_id depends on depends_on_id — circular dependencies must be checked at service layer."""
    __tablename__ = "task_dependencies"
    __table_args__ = (UniqueConstraint("task_id", "depends_on_id", name="uq_task_dep"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_id], back_populates="blockers")


# ── Messages ─────────────────────────────────────────────────────────────────

class Message(Base):
    """Team messages normalised from Telegram, GitHub, or direct API."""
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_src_ext", "source", "external_id"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    source = Column(String(30), nullable=False, default="api")       # api|telegram|github
    external_id = Column(String(100), nullable=True, index=True)
    content = Column(Text, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    ai_classification = Column(String(50), nullable=True)             # task_update|blocker|question|info|ambiguous
    linked_task_id = Column(String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    project = relationship("Project", back_populates="messages")
    user = relationship("User")


class TelegramMessage(Base):
    """Raw Telegram update — stored as-is for evidence before AI processing."""
    __tablename__ = "telegram_messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    update_id = Column(BigInteger, nullable=False, unique=True, index=True)
    chat_id = Column(String(50), nullable=False, index=True)
    from_user_id = Column(String(50), nullable=True)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    text = Column(Text, nullable=True)
    raw_payload = Column(JSON, nullable=False)
    processed = Column(Boolean, nullable=False, default=False)
    processing_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    user = relationship("User", back_populates="telegram_messages")


# ── Credits ───────────────────────────────────────────────────────────────────

class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    balance = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    user = relationship("User", back_populates="credit_account")
    ledger = relationship("CreditLedger", back_populates="account", cascade="all, delete-orphan")


class CreditLedger(Base):
    """Immutable append-only transaction ledger."""
    __tablename__ = "credit_ledger"

    id = Column(String(36), primary_key=True, default=_uuid)
    account_id = Column(String(36), ForeignKey("credit_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    amount = Column(Integer, nullable=False)              # positive = credit, negative = debit
    balance_after = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    # reason values: new_user_grant|referral_reward|referee_bonus|solution_charge|
    #                research_charge|ad_reward|admin_grant|refund
    operation_ref = Column(String(100), nullable=True, index=True)
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    account = relationship("CreditAccount", back_populates="ledger")


# ── Referrals ────────────────────────────────────────────────────────────────

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String(36), primary_key=True, default=_uuid)
    referrer_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referee_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referral_code = Column(String(20), nullable=False, unique=True, index=True)
    status = Column(String(30), nullable=False, default="pending")
    # status: pending|activated|rewarded|invalid
    activated_at = Column(DateTime, nullable=True)
    rewarded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_sent")
    referee = relationship("User", foreign_keys=[referee_id], back_populates="referrals_received")


# ── Rewarded Ads & Entitlements ───────────────────────────────────────────────

class AdSession(Base):
    """Server-generated ad session. Provider SSV callback completes this record."""
    __tablename__ = "ad_sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_key = Column(String(50), nullable=False)
    provider_transaction_id = Column(String(200), nullable=True, unique=True, index=True)
    status = Column(String(30), nullable=False, default="pending")
    # status: pending|completed|expired|rejected
    verification_payload = Column(JSON, nullable=True)
    test_mode = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class FeatureEntitlement(Base):
    """Temporary feature unlock record."""
    __tablename__ = "feature_entitlements"
    __table_args__ = (Index("ix_ent_user_feature", "user_id", "feature_key"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_key = Column(String(50), nullable=False)
    grant_source = Column(String(30), nullable=False)  # rewarded_ad|admin_grant
    ad_session_id = Column(String(36), ForeignKey("ad_sessions.id", ondelete="SET NULL"), nullable=True)
    starts_at = Column(DateTime, nullable=False, default=_now)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    user = relationship("User", back_populates="entitlements")


# ── AI Solution Runs ──────────────────────────────────────────────────────────

class SolutionRun(Base):
    __tablename__ = "solution_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    problem_statement = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    # pending|in_progress|completed|failed|refunded
    credit_charge = Column(Integer, nullable=True)
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    user = relationship("User", back_populates="solution_runs")


# ── Research Runs ─────────────────────────────────────────────────────────────

class ResearchRun(Base):
    __tablename__ = "research_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    # pending|in_progress|completed|failed|partial
    credit_charge = Column(Integer, nullable=True)
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    reddit_status = Column(String(30), nullable=True)     # success|empty|error|unsupported
    linkedin_status = Column(String(30), nullable=True)
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    user = relationship("User", back_populates="research_runs")


# ── Audit Events ──────────────────────────────────────────────────────────────

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(128), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    actor = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)    # project|task|solution|research|referral|credit
    resource_id = Column(String(36), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=_now, nullable=False)

    user = relationship("User", back_populates="audit_events")
