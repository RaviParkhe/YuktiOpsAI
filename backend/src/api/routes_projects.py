"""
Projects and Tasks routes.

Access control:
- Project data is only visible to members of that project.
- Only project owners/leaders can add members, update member roles, and delete projects.
- Task owners can update their own tasks; leaders can update any task in their project.
- All changes are recorded in the audit log.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth import VerifiedUser, get_current_user
from src.db.models import AuditEvent, Message, Project, ProjectMember, Task, TaskDependency
from src.db.session import get_db
from src.schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    github_repo_full_name: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: Optional[str]
    github_repo_full_name: Optional[str]
    is_active: bool
    created_at: datetime


class MemberAdd(BaseModel):
    user_id: str = Field(..., min_length=1)
    role: str = Field(default="member", pattern="^(owner|leader|member)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    role: str
    joined_at: datetime


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner_id: Optional[str] = None
    status: str = Field(default="open", pattern="^(open|in_progress|blocked|done)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    owner_id: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(open|in_progress|blocked|done)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    owner_id: Optional[str]
    status: str
    priority: str
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _require_member(db: AsyncSession, project_id: str, user_id: str) -> ProjectMember:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "NOT_A_MEMBER", "message": "You are not a member of this project"},
        )
    return member


async def _require_leader(db: AsyncSession, project_id: str, user_id: str) -> ProjectMember:
    member = await _require_member(db, project_id, user_id)
    if member.role not in ("owner", "leader"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INSUFFICIENT_ROLE", "message": "Only owners and leaders can perform this action"},
        )
    return member


# ── Projects ──────────────────────────────────────────────────────────────────

@router.post("", response_model=APIResponse[ProjectResponse], status_code=201, tags=["Projects"])
async def create_project(
    req: ProjectCreate,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = Project(
        name=req.name,
        description=req.description,
        owner_id=current_user.uid,
        github_repo_full_name=req.github_repo_full_name,
    )
    db.add(project)
    await db.flush()

    # Creator is automatically owner
    db.add(ProjectMember(project_id=project.id, user_id=current_user.uid, role="owner"))
    db.add(AuditEvent(
        user_id=current_user.uid, project_id=project.id,
        actor=f"user:{current_user.uid}", action="project_created",
        resource_type="project", resource_id=project.id,
    ))
    return APIResponse(
        success=True, message="Project created",
        data=ProjectResponse(
            id=project.id, name=project.name, description=project.description,
            owner_id=project.owner_id, github_repo_full_name=project.github_repo_full_name,
            is_active=project.is_active, created_at=project.created_at,
        ),
    )


@router.get("", response_model=APIResponse[List[ProjectResponse]], tags=["Projects"])
async def list_projects(
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns only projects the user is a member of."""
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == current_user.uid, Project.is_active == True)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            ProjectResponse(
                id=p.id, name=p.name, description=p.description,
                owner_id=p.owner_id, github_repo_full_name=p.github_repo_full_name,
                is_active=p.is_active, created_at=p.created_at,
            )
            for p in projects
        ],
    )


@router.get("/{project_id}", response_model=APIResponse[ProjectResponse], tags=["Projects"])
async def get_project(
    project_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, project_id, current_user.uid)
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(404, detail={"code": "NOT_FOUND", "message": "Project not found"})
    return APIResponse(
        success=True,
        data=ProjectResponse(
            id=p.id, name=p.name, description=p.description, owner_id=p.owner_id,
            github_repo_full_name=p.github_repo_full_name, is_active=p.is_active, created_at=p.created_at,
        ),
    )


# ── Members ───────────────────────────────────────────────────────────────────

@router.post("/{project_id}/members", response_model=APIResponse[MemberResponse], tags=["Projects"])
async def add_member(
    project_id: str,
    req: MemberAdd,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_leader(db, project_id, current_user.uid)
    existing = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == req.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, detail={"code": "ALREADY_MEMBER", "message": "User is already a member"})
    member = ProjectMember(project_id=project_id, user_id=req.user_id, role=req.role)
    db.add(member)
    db.add(AuditEvent(
        user_id=current_user.uid, project_id=project_id,
        actor=f"user:{current_user.uid}", action="member_added",
        resource_type="project_member", resource_id=req.user_id,
        details={"role": req.role},
    ))
    return APIResponse(
        success=True, message="Member added",
        data=MemberResponse(
            id=member.id, user_id=member.user_id, project_id=project_id,
            role=member.role, joined_at=member.joined_at,
        ),
    )


@router.get("/{project_id}/members", response_model=APIResponse[List[MemberResponse]], tags=["Projects"])
async def list_members(
    project_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, project_id, current_user.uid)
    result = await db.execute(
        select(ProjectMember).where(ProjectMember.project_id == project_id)
    )
    members = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            MemberResponse(id=m.id, user_id=m.user_id, project_id=project_id,
                           role=m.role, joined_at=m.joined_at)
            for m in members
        ],
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.post("/{project_id}/tasks", response_model=APIResponse[TaskResponse], status_code=201, tags=["Tasks"])
async def create_task(
    project_id: str,
    req: TaskCreate,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, project_id, current_user.uid)
    task = Task(
        project_id=project_id,
        owner_id=req.owner_id or current_user.uid,
        title=req.title,
        description=req.description,
        status=req.status,
        priority=req.priority,
        deadline=req.deadline,
    )
    db.add(task)
    db.add(AuditEvent(
        user_id=current_user.uid, project_id=project_id,
        actor=f"user:{current_user.uid}", action="task_created",
        resource_type="task", resource_id=task.id,
        details={"title": task.title},
    ))
    return APIResponse(
        success=True, message="Task created",
        data=TaskResponse(
            id=task.id, project_id=task.project_id, title=task.title,
            description=task.description, owner_id=task.owner_id,
            status=task.status, priority=task.priority,
            deadline=task.deadline, created_at=task.created_at, updated_at=task.updated_at,
        ),
    )


@router.get("/{project_id}/tasks", response_model=APIResponse[List[TaskResponse]], tags=["Tasks"])
async def list_tasks(
    project_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _require_member(db, project_id, current_user.uid)
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return APIResponse(
        success=True,
        data=[
            TaskResponse(
                id=t.id, project_id=t.project_id, title=t.title, description=t.description,
                owner_id=t.owner_id, status=t.status, priority=t.priority,
                deadline=t.deadline, created_at=t.created_at, updated_at=t.updated_at,
            )
            for t in tasks
        ],
    )


@router.patch("/{project_id}/tasks/{task_id}", response_model=APIResponse[TaskResponse], tags=["Tasks"])
async def update_task(
    project_id: str,
    task_id: str,
    req: TaskUpdate,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await _require_member(db, project_id, current_user.uid)
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.project_id == project_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, detail={"code": "TASK_NOT_FOUND", "message": "Task not found"})

    # Leaders can edit any task; members can only edit their own
    if member.role == "member" and task.owner_id != current_user.uid:
        raise HTTPException(403, detail={"code": "FORBIDDEN", "message": "You can only update your own tasks"})

    changes: dict = {}
    if req.title is not None:
        changes["title"] = req.title
        task.title = req.title
    if req.description is not None:
        changes["description"] = req.description
        task.description = req.description
    if req.owner_id is not None:
        changes["owner_id"] = req.owner_id
        task.owner_id = req.owner_id
    if req.status is not None:
        changes["status"] = req.status
        task.status = req.status
    if req.priority is not None:
        changes["priority"] = req.priority
        task.priority = req.priority
    if req.deadline is not None:
        changes["deadline"] = str(req.deadline)
        task.deadline = req.deadline

    db.add(AuditEvent(
        user_id=current_user.uid, project_id=project_id,
        actor=f"user:{current_user.uid}", action="task_updated",
        resource_type="task", resource_id=task_id, details=changes,
    ))
    return APIResponse(
        success=True, message="Task updated",
        data=TaskResponse(
            id=task.id, project_id=task.project_id, title=task.title,
            description=task.description, owner_id=task.owner_id,
            status=task.status, priority=task.priority,
            deadline=task.deadline, created_at=task.created_at, updated_at=task.updated_at,
        ),
    )


@router.get("/{project_id}/audit", response_model=APIResponse[List[dict]], tags=["Projects"])
async def get_project_audit(
    project_id: str,
    current_user: VerifiedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chronological audit trail for a project (members only)."""
    await _require_member(db, project_id, current_user.uid)
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.project_id == project_id)
        .order_by(AuditEvent.timestamp.asc())
        .limit(200)
    )
    events = result.scalars().all()
    return APIResponse(
        success=True,
        data=[{
            "id": e.id, "actor": e.actor, "action": e.action,
            "resource_type": e.resource_type, "resource_id": e.resource_id,
            "details": e.details, "timestamp": e.timestamp.isoformat(),
        } for e in events],
    )
