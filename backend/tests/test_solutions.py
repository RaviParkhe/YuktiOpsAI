"""
Tests for AI solution generation, credit deductions, fallback mode, and failure refunds.
"""
from unittest.mock import AsyncMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.credits import apply_credit, get_balance
from src.services.solution import solution_service


@pytest.mark.asyncio
async def test_solution_generation_with_credits(db_session: AsyncSession):
    user_id = "sol-user-001"
    # User gets 50 welcome credits
    await apply_credit(db_session, user_id, 50, "welcome")

    run = await solution_service.generate(
        session=db_session,
        user_id=user_id,
        problem_statement="How to design a scalable asynchronous task worker architecture with Redis?",
        project_id=None,
        idempotency_key="sol-key-001",
    )
    assert run.status == "completed"
    assert run.result is not None
    assert "proposed_solution" in run.result
    assert "architecture" in run.result
    assert "sources_note" in run.result

    # 10 credits deducted (cost is 10)
    balance = await get_balance(db_session, user_id)
    assert balance == 40


@pytest.mark.asyncio
async def test_solution_fails_when_credits_insufficient(db_session: AsyncSession):
    user_id = "sol-user-broke"
    # 0 credits
    run = await solution_service.generate(
        session=db_session,
        user_id=user_id,
        problem_statement="Need architecture advice for high throughput queues.",
        project_id=None,
        idempotency_key="sol-key-fail",
    )
    assert run.status == "failed"
    assert "Insufficient credits" in run.error_message


@pytest.mark.asyncio
async def test_solution_failure_refunds_credits(db_session: AsyncSession):
    user_id = "sol-user-refund"
    await apply_credit(db_session, user_id, 30, "grant")

    # Mock LLM generation raising an unexpected error
    with patch.object(solution_service, "_invoke_llm", side_effect=RuntimeError("LLM provider rate limit exceeded")):
        run = await solution_service.generate(
            session=db_session,
            user_id=user_id,
            problem_statement="Build a complex workflow system.",
            project_id=None,
            idempotency_key="sol-key-err",
        )
        assert run.status == "failed"

        # Credits must be refunded back to 30
        balance = await get_balance(db_session, user_id)
        assert balance == 30
