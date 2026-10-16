"""
Pytest configuration and shared test fixtures for the YuktiOps backend.
"""
import asyncio
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.auth import VerifiedUser, get_current_user
from src.db.models import Base
from src.db.session import get_db
from src.main import app

# Isolated in-memory async SQLite engine for deterministic unit & integration tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean in-memory database session for each test function."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_user_alice():
    return VerifiedUser(uid="alice-uid-101", email="alice@example.com", is_stub=False)


@pytest.fixture
def mock_user_bob():
    return VerifiedUser(uid="bob-uid-202", email="bob@example.com", is_stub=False)


@pytest.fixture
def client(db_session: AsyncSession, mock_user_alice: VerifiedUser, monkeypatch):
    """TestClient with database and authenticated user overridden to Alice."""
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return mock_user_alice

    async def noop_init_db():
        pass

    # Ensure test lifespan and readiness probe use the test engine
    monkeypatch.setattr("src.main.engine", test_engine)
    monkeypatch.setattr("src.main.init_db", noop_init_db)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client_unauthenticated(db_session: AsyncSession, monkeypatch):
    """TestClient with database overridden, but real authentication dependencies intact."""
    async def override_get_db():
        yield db_session

    async def noop_init_db():
        pass

    monkeypatch.setattr("src.main.engine", test_engine)
    monkeypatch.setattr("src.main.init_db", noop_init_db)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
