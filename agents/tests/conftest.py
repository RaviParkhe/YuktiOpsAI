import asyncio
import os
import pytest
from httpx import ASGITransport, AsyncClient

# Use a test SQLite database file so connections don't fight over event loop mutexes
TEST_DB_PATH = "./test_yuktiops.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test_webhook_secret_123"
os.environ["ENVIRONMENT"] = "testing"

import src.db.models  # noqa: F401 - ensure all models are registered on Base.metadata
from src.db.session import Base, async_session_factory, engine, get_db
from src.main import app


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


async def override_get_db():
    async with async_session_factory() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
