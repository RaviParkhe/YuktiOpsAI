"""
Tests for concurrent social research (Reddit + LinkedIn adapters) and limitation notices.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.credits import apply_credit, get_balance
from src.services.research import ResearchResult, research_service


@pytest.mark.asyncio
async def test_social_research_stub_execution(db_session: AsyncSession):
    user_id = "res-user-001"
    # User gets credits
    await apply_credit(db_session, user_id, 20, "grant")

    run = await research_service.run(
        session=db_session,
        user_id=user_id,
        query="FastAPI PostgreSQL best practices",
        idempotency_key="res-idem-1",
    )
    assert run.query == "FastAPI PostgreSQL best practices"
    assert run.results is not None
    assert len(run.results) > 0
    # Confirm platforms represented
    platforms = [r["platform"] for r in run.results]
    assert "reddit" in platforms
    assert "linkedin" in platforms

    # LinkedIn limitation notice is clearly disclosed
    linkedin_item = next(r for r in run.results if r["platform"] == "linkedin")
    assert "limitation" in linkedin_item["excerpt"].lower() or "not available" in linkedin_item["title"].lower()


@pytest.mark.asyncio
async def test_social_research_with_successful_provider(db_session: AsyncSession):
    user_id = "res-user-002"
    await apply_credit(db_session, user_id, 20, "grant")

    mock_reddit_results = [
        ResearchResult(
            platform="reddit",
            title="FastAPI + SQLAlchemy async tutorial",
            excerpt="Here is how to set up asyncpg with FastAPI...",
            author="dev_reddit",
            url="https://reddit.com/r/python/123",
            date="2026-10-17",
            relevance_score=0.95,
            retrieval_status="success",
        )
    ]

    async def mock_search(query, limit=10):
        return mock_reddit_results, "success"

    with pytest.MonkeyPatch.context() as m:
        m.setattr(
            research_service._reddit,
            "search",
            mock_search,
        )
        run = await research_service.run(
            session=db_session,
            user_id=user_id,
            query="Async SQLAlchemy",
            idempotency_key="res-mock-1",
        )
        assert run.status == "completed"
        # 5 credits charged for research
        balance = await get_balance(db_session, user_id)
        assert balance == 15
