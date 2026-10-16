"""
Tests for database models, constraints, CRUD, foreign keys, and rollbacks.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Project, ProjectMember, Task, User


@pytest.mark.asyncio
async def test_user_and_project_relationship(db_session: AsyncSession):
    # Create user
    user = User(id="usr_db_001", email="user@db.test", display_name="DB Tester")
    db_session.add(user)
    await db_session.flush()

    # Create project
    proj = Project(name="YuktiOps Core", owner_id=user.id)
    db_session.add(proj)
    await db_session.flush()

    # Add member
    member = ProjectMember(project_id=proj.id, user_id=user.id, role="owner")
    db_session.add(member)
    await db_session.flush()

    # Create task
    task = Task(project_id=proj.id, owner_id=user.id, title="Implement test suite")
    db_session.add(task)
    await db_session.flush()

    # Verify query
    result = await db_session.execute(select(Task).where(Task.project_id == proj.id))
    fetched_task = result.scalar_one()
    assert fetched_task.title == "Implement test suite"
    assert fetched_task.owner_id == user.id


@pytest.mark.asyncio
async def test_unique_member_constraint(db_session: AsyncSession):
    user = User(id="usr_dup_member", email="dup@db.test")
    proj = Project(name="Unique Member Project")
    db_session.add_all([user, proj])
    await db_session.flush()

    m1 = ProjectMember(project_id=proj.id, user_id=user.id, role="member")
    db_session.add(m1)
    await db_session.flush()

    # Duplicate membership should violate UniqueConstraint
    m2 = ProjectMember(project_id=proj.id, user_id=user.id, role="leader")
    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()
