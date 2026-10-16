"""
Telegram Bot routes.

POST /telegram/webhook   — receives Telegram updates (webhook mode)
GET  /telegram/status    — webhook info and bot status
POST /telegram/register  — register webhook with Telegram API (requires PUBLIC_BASE_URL)
POST /telegram/delete    — delete webhook (switches to polling mode)

Incoming update flow:
  1. Verify X-Telegram-Bot-Api-Secret-Token header.
  2. Check update_id for deduplication (reject already-processed).
  3. Store raw update in telegram_messages table as evidence.
  4. Look up linked Firebase user by Telegram from_id (if mapped).
  5. Classify message text with MessageClassifier.
  6. If ambiguous → reply asking for clarification.
  7. If task_update / blocker → persist as Message, optionally link task.
  8. Reply to Telegram confirming receipt.
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import VerifiedUser, get_current_user
from src.db.models import AuditEvent, Message, Task, TelegramMessage
from src.db.session import get_db
from src.schemas.common import APIResponse
from src.services.classifier import message_classifier
from src.services.telegram import telegram_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Webhook ───────────────────────────────────────────────────────────────────

@router.post("/webhook", status_code=200, tags=["Telegram"])
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receive Telegram update via webhook.

    Secret token verification is always performed if TELEGRAM_WEBHOOK_SECRET is set.
    Respond 200 immediately to prevent Telegram retries; process asynchronously.
    """
    # 1. Verify secret token
    if not telegram_service.verify_secret_token(x_telegram_bot_api_secret_token):
        logger.warning("[TG WEBHOOK] Invalid secret token — rejecting update")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_SECRET", "message": "Invalid X-Telegram-Bot-Api-Secret-Token"},
        )

    # 2. Parse body
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(400, detail={"code": "INVALID_JSON", "message": "Malformed JSON body"})

    update_id = body.get("update_id")
    if update_id is None:
        raise HTTPException(400, detail={"code": "MISSING_UPDATE_ID", "message": "update_id missing"})

    # 3. Deduplicate
    existing = await db.execute(
        select(TelegramMessage).where(TelegramMessage.update_id == update_id)
    )
    if existing.scalar_one_or_none():
        logger.info(f"[TG WEBHOOK] Duplicate update_id={update_id} — skipped")
        return {"ok": True, "deduplicated": True}

    # 4. Extract message details
    msg = body.get("message") or body.get("edited_message") or {}
    chat_id = str(msg.get("chat", {}).get("id", ""))
    from_user = msg.get("from", {})
    from_user_id = str(from_user.get("id", "")) if from_user else None
    text = msg.get("text") or ""

    # 5. Persist raw update as evidence (before any AI processing)
    tg_record = TelegramMessage(
        update_id=update_id,
        chat_id=chat_id,
        from_user_id=from_user_id,
        text=text or None,
        raw_payload=body,
        processed=False,
    )
    db.add(tg_record)
    await db.flush()

    # 6. Only process text messages
    if not text:
        tg_record.processed = True
        return {"ok": True}

    # 7. Classify the message
    try:
        classification = await message_classifier.classify(text)
    except Exception as exc:
        logger.error(f"[TG WEBHOOK] Classification error: {exc}")
        tg_record.processing_error = str(exc)
        return {"ok": True}

    category = classification.get("category", "info")
    clarification_needed = classification.get("clarification_needed", False)

    # 8. Persist as Message
    db.add(Message(
        source="telegram",
        external_id=str(update_id),
        content=text,
        raw_payload=body,
        ai_classification=category,
    ))

    # 9. Compose reply
    if clarification_needed or category == "ambiguous":
        reply = (
            "🤔 <b>Clarification needed</b>\n"
            "I couldn't match your message to a specific task. Could you please mention the task name or ID?"
        )
    elif category == "blocker":
        reply = (
            "🚨 <b>Blocker detected</b>\n"
            "Your message has been logged as a blocker. A project leader will follow up.\n"
            f"<i>Classification confidence: {classification.get('confidence', 'n/a')}</i>"
        )
    elif category == "task_update":
        reply = (
            "✅ <b>Task update received</b>\n"
            "Your progress update has been recorded."
        )
    else:
        reply = "📩 Message received and logged."

    tg_record.processed = True
    await telegram_service.send_message(chat_id, reply)
    return {"ok": True}


# ── Status and Management ─────────────────────────────────────────────────────

@router.get("/status", response_model=APIResponse[dict], tags=["Telegram"])
async def telegram_status(current_user: VerifiedUser = Depends(get_current_user)):
    """Return current webhook info and bot configuration status."""
    info = await telegram_service.get_webhook_info()
    return APIResponse(
        success=True,
        data={
            "bot_configured": telegram_service.is_configured,
            "test_mode": not telegram_service.is_configured,
            "webhook_info": info,
            "public_base_url": telegram_service.public_base_url,
        },
    )


@router.post("/register", response_model=APIResponse[dict], tags=["Telegram"])
async def register_webhook(current_user: VerifiedUser = Depends(get_current_user)):
    """Register the Telegram webhook. Requires PUBLIC_BASE_URL and TELEGRAM_BOT_TOKEN."""
    result = await telegram_service.register_webhook()
    if not result.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "WEBHOOK_FAILED", "message": result.get("description", "Telegram API error")},
        )
    return APIResponse(success=True, message="Webhook registered", data=result)


@router.post("/delete", response_model=APIResponse[dict], tags=["Telegram"])
async def delete_webhook(current_user: VerifiedUser = Depends(get_current_user)):
    """Remove the Telegram webhook (switches bot to polling mode)."""
    result = await telegram_service.delete_webhook()
    return APIResponse(success=True, message="Webhook deleted", data=result)
