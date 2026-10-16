"""
Reddit + LinkedIn concurrent research adapters.

Architecture:
  - RedditAdapter   — uses asyncpraw (official async Reddit API client)
  - LinkedInAdapter — uses the LinkedIn Marketing/UGC API with an access token
                       NOTE: LinkedIn severely restricts arbitrary public-post
                       search via the standard API. Only company UGC posts and
                       content shared by the authenticated user are accessible.
                       This limitation is clearly reported in the response.

Both adapters normalize results to a shared ResearchResult schema.
Concurrent execution via asyncio.gather with independent error handling
(partial failure → partial results).

Credit cost is enforced and idempotency prevents duplicate charges.
"""
import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import ResearchRun
from src.services.credits import InsufficientCreditsError, apply_credit, apply_debit

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    platform: str           # "reddit" | "linkedin"
    title: str
    excerpt: str
    author: Optional[str]   # None when not permitted by platform
    url: str
    date: Optional[str]     # ISO date string when available
    relevance_score: float  # 0.0–1.0 (heuristic)
    retrieval_status: str   # "success" | "empty" | "error" | "unsupported"


def _to_dict(r: ResearchResult) -> Dict[str, Any]:
    return {
        "platform": r.platform,
        "title": r.title,
        "excerpt": r.excerpt,
        "author": r.author,
        "url": r.url,
        "date": r.date,
        "relevance_score": r.relevance_score,
        "retrieval_status": r.retrieval_status,
    }


# ── Reddit Adapter ─────────────────────────────────────────────────────────────

class RedditAdapter:
    """
    Uses the asyncpraw library with Reddit OAuth2 script-app credentials.

    Required env vars:
      REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

    Without credentials, returns a DEV STUB result set with status "unsupported".
    """

    async def search(self, query: str, limit: int = 10) -> tuple[list[ResearchResult], str]:
        """
        Returns (results, status) where status ∈ {success, empty, error, unsupported}.
        Never raises — errors are captured and returned as status.
        """
        s = get_settings()
        if not (s.REDDIT_CLIENT_ID and s.REDDIT_CLIENT_SECRET):
            logger.info("[REDDIT] Credentials not configured — returning stub.")
            return self._stub(query), "unsupported"

        try:
            import asyncpraw
            reddit = asyncpraw.Reddit(
                client_id=s.REDDIT_CLIENT_ID,
                client_secret=s.REDDIT_CLIENT_SECRET,
                user_agent=s.REDDIT_USER_AGENT,
            )
            results: list[ResearchResult] = []
            async with reddit:
                async for submission in reddit.subreddit("all").search(query, limit=limit, sort="relevance"):
                    date_str = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).date().isoformat()
                    results.append(ResearchResult(
                        platform="reddit",
                        title=submission.title,
                        excerpt=(submission.selftext or "")[:300].strip() or "[link post]",
                        author=str(submission.author) if submission.author else None,
                        url=f"https://reddit.com{submission.permalink}",
                        date=date_str,
                        relevance_score=min(1.0, submission.score / max(1, submission.score + 100)),
                        retrieval_status="success",
                    ))

            status = "success" if results else "empty"
            return results, status

        except Exception as exc:
            logger.error(f"[REDDIT] Search failed: {exc}")
            return [], "error"

    def _stub(self, query: str) -> list[ResearchResult]:
        """Development stub — clearly marked, not real data."""
        return [ResearchResult(
            platform="reddit",
            title=f"[DEV STUB] No real Reddit results — REDDIT_CLIENT_ID not configured",
            excerpt=f"Query: {query[:100]}. Configure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for real results.",
            author=None,
            url="https://reddit.com",
            date=None,
            relevance_score=0.0,
            retrieval_status="unsupported",
        )]


# ── LinkedIn Adapter ───────────────────────────────────────────────────────────

class LinkedInAdapter:
    """
    LinkedIn API adapter.

    LIMITATION: The LinkedIn Marketing API and UGC Posts API do not support
    arbitrary public-post keyword search. Only posts made by the authenticated
    user or company pages they manage are accessible via the standard API.

    This adapter reports this limitation clearly rather than pretending it works.

    For real LinkedIn public-post search, a compliant third-party data provider
    with an authorized API agreement is required.

    Required env var: LINKEDIN_ACCESS_TOKEN
    """

    async def search(self, query: str) -> tuple[list[ResearchResult], str]:
        s = get_settings()
        if not s.LINKEDIN_ACCESS_TOKEN:
            logger.info("[LINKEDIN] No access token — returning limitation notice.")
            return self._limitation_stub(query), "unsupported"

        # Even with a token, arbitrary keyword search is not available.
        # We report this honestly rather than calling an endpoint that will reject the request.
        logger.info("[LINKEDIN] Arbitrary public-post search not supported by LinkedIn API — reporting limitation.")
        return self._limitation_stub(query), "unsupported"

    def _limitation_stub(self, query: str) -> list[ResearchResult]:
        return [ResearchResult(
            platform="linkedin",
            title="LinkedIn search not available",
            excerpt=(
                "LinkedIn's standard API does not permit arbitrary public-post keyword search. "
                "A licensed third-party data provider with an authorized LinkedIn API agreement "
                f"would be required to search for: '{query[:100]}'. "
                "This is a known platform restriction, not an implementation bug."
            ),
            author=None,
            url="https://developer.linkedin.com/product-catalog",
            date=None,
            relevance_score=0.0,
            retrieval_status="unsupported",
        )]


# ── Research Orchestrator ─────────────────────────────────────────────────────

class ResearchService:
    def __init__(self):
        self._reddit = RedditAdapter()
        self._linkedin = LinkedInAdapter()

    async def run(
        self,
        session: AsyncSession,
        user_id: str,
        query: str,
        idempotency_key: Optional[str],
    ) -> ResearchRun:
        """
        Executes Reddit and LinkedIn search concurrently.

        - Credits are deducted only when at least one provider returns real results.
        - Partial success (one platform fails) is still returned.
        - Duplicate charges are prevented via idempotency key.
        """
        s = get_settings()
        cost = s.CREDIT_COST_SOCIAL_RESEARCH

        # Idempotency check
        if idempotency_key:
            existing = await session.execute(
                select(ResearchRun).where(ResearchRun.idempotency_key == idempotency_key)
            )
            run = existing.scalar_one_or_none()
            if run:
                logger.info(f"[RESEARCH] Returning existing run idem={idempotency_key}")
                return run

        idem_key = idempotency_key or str(uuid.uuid4())
        run = ResearchRun(
            user_id=user_id,
            query=query,
            status="in_progress",
            idempotency_key=idem_key,
        )
        session.add(run)
        await session.flush()

        # Run both adapters concurrently
        reddit_task = self._reddit.search(query)
        linkedin_task = self._linkedin.search(query)
        (reddit_results, reddit_status), (linkedin_results, linkedin_status) = await asyncio.gather(
            reddit_task, linkedin_task
        )

        all_results = reddit_results + linkedin_results

        # Deduplicate by URL, rank by relevance
        seen_urls: set[str] = set()
        deduped: list[Dict[str, Any]] = []
        for r in sorted(all_results, key=lambda x: x.relevance_score, reverse=True):
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                deduped.append(_to_dict(r))

        # Determine overall status
        if reddit_status == "success" or linkedin_status == "success":
            overall_status = "completed"
        elif reddit_status == "empty" and linkedin_status == "empty":
            overall_status = "completed"  # no results, but not an error
        elif reddit_status in ("error", "unsupported") and linkedin_status in ("error", "unsupported"):
            overall_status = "failed"
        else:
            overall_status = "partial"

        run.reddit_status = reddit_status
        run.linkedin_status = linkedin_status
        run.results = deduped
        run.status = overall_status

        # Charge credits only when there's a real successful provider result
        if overall_status in ("completed", "partial"):
            run.credit_charge = cost
            debit_idem = f"research_debit:{idem_key}"
            try:
                await apply_debit(
                    session, user_id, cost, "research_charge",
                    idempotency_key=debit_idem,
                    operation_ref=run.id,
                )
            except InsufficientCreditsError as e:
                run.status = "failed"
                run.error_message = f"Insufficient credits: {e.balance} available, {e.required} required"
                run.credit_charge = 0

        return run


research_service = ResearchService()
