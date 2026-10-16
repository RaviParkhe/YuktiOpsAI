import logging
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import AuditEvent
from src.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def record_audit_event(
    actor: str,
    action: str,
    run_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    session: Optional[AsyncSession] = None,
) -> AuditEvent:
    """Record an audit trail event for decisions made by agents or humans."""
    event = AuditEvent(
        run_id=run_id,
        proposal_id=proposal_id,
        actor=actor,
        action=action,
        details=details or {},
    )

    if session:
        session.add(event)
        # caller will commit
    else:
        async with async_session_factory() as local_session:
            local_session.add(event)
            await local_session.commit()

    logger.info(f"[AUDIT] actor={actor} action={action} run_id={run_id} proposal_id={proposal_id}")
    return event
