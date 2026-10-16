"""
Telegram Bot service for the YuktiOps backend.

Responsibilities:
  1. Outbound: send bot replies to any chat.
  2. Inbound: normalise and persist incoming Telegram updates.
  3. Deduplication: reject already-seen update_ids (stored in DB).
  4. Webhook registration: call setWebhook against the Telegram Bot API.

Delivery approach
-----------------
The preferred approach is **webhook** (event-driven, no polling loop needed in
production). For local development without a public HTTPS URL, long-polling
is available via `run_polling()` — run it as a background asyncio task.

Webhook setup requires:
  - A public HTTPS base URL (use ngrok or similar for local dev).
  - TELEGRAM_BOT_TOKEN set in the environment.
  - TELEGRAM_WEBHOOK_SECRET set (random string, sent as X-Telegram-Bot-Api-Secret-Token).

The backend registers the webhook at startup when PUBLIC_BASE_URL is configured.
"""
import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


class TelegramBotService:
    def __init__(self):
        from src.config import get_settings
        s = get_settings()
        self.token: Optional[str] = s.TELEGRAM_BOT_TOKEN
        self.alert_chat_id: Optional[str] = s.TELEGRAM_ALERT_CHAT_ID
        self.webhook_secret: Optional[str] = s.TELEGRAM_WEBHOOK_SECRET
        self.public_base_url: Optional[str] = s.PUBLIC_BASE_URL

    @property
    def is_configured(self) -> bool:
        return bool(self.token)

    def _url(self, method: str) -> str:
        return TELEGRAM_API.format(token=self.token, method=method)

    # ── Verification ──────────────────────────────────────────────────────────

    def verify_secret_token(self, header_value: Optional[str]) -> bool:
        """
        Verify the X-Telegram-Bot-Api-Secret-Token header.
        Returns True if no secret is configured (open dev setup) or header matches.
        """
        if not self.webhook_secret:
            return True   # No secret configured — accept all (dev only)
        if not header_value:
            return False
        return hmac.compare_digest(header_value, self.webhook_secret)

    # ── Outbound ──────────────────────────────────────────────────────────────

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """Send a message. Returns True on success, False (with log) on failure."""
        if not self.is_configured:
            logger.info(f"[TG MOCK] → chat={chat_id}: {text[:120]}")
            return True

        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self._url("sendMessage"), json=payload)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                logger.error(f"[TG] sendMessage failed: {resp.status_code} {resp.text[:200]}")
                return False
        except Exception as exc:
            logger.error(f"[TG] sendMessage exception: {exc}")
            return False

    async def send_alert(self, text: str) -> bool:
        """Send a message to the configured alert chat."""
        if not self.alert_chat_id:
            logger.info(f"[TG ALERT MOCK] {text[:200]}")
            return True
        return await self.send_message(self.alert_chat_id, text)

    # ── Webhook registration ───────────────────────────────────────────────────

    async def register_webhook(self) -> Dict[str, Any]:
        """
        Register this service as the Telegram webhook.

        Prerequisites:
          - TELEGRAM_BOT_TOKEN set
          - PUBLIC_BASE_URL set to a publicly reachable HTTPS URL
          - TELEGRAM_WEBHOOK_SECRET set (recommended)

        The webhook endpoint will be: {PUBLIC_BASE_URL}/api/v1/telegram/webhook
        """
        if not self.is_configured:
            return {"ok": False, "description": "TELEGRAM_BOT_TOKEN not configured"}

        if not self.public_base_url:
            return {"ok": False, "description": "PUBLIC_BASE_URL not configured — needed for webhook registration"}

        url = f"{self.public_base_url.rstrip('/')}/api/v1/telegram/webhook"
        payload: Dict[str, Any] = {"url": url, "allowed_updates": ["message", "callback_query"]}
        if self.webhook_secret:
            payload["secret_token"] = self.webhook_secret

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(self._url("setWebhook"), json=payload)
                data = resp.json()
                if data.get("ok"):
                    logger.info(f"[TG] Webhook registered: {url}")
                else:
                    logger.error(f"[TG] Webhook registration failed: {data}")
                return data
        except Exception as exc:
            logger.error(f"[TG] Webhook registration exception: {exc}")
            return {"ok": False, "description": str(exc)}

    async def get_webhook_info(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"ok": False}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self._url("getWebhookInfo"))
            return resp.json()

    async def delete_webhook(self) -> Dict[str, Any]:
        """Remove webhook (switches bot to polling mode)."""
        if not self.is_configured:
            return {"ok": False}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self._url("deleteWebhook"), json={"drop_pending_updates": False})
            return resp.json()

    # ── Long-polling fallback (local dev without ngrok) ───────────────────────

    async def run_polling(self, process_update_fn) -> None:
        """
        Simple long-polling loop for local development.

        Usage (in startup event):
            import asyncio
            asyncio.create_task(telegram_service.run_polling(handle_update))

        process_update_fn is called with the raw update dict and must be an async function.
        """
        if not self.is_configured:
            logger.warning("[TG] Polling requested but bot token is not configured.")
            return

        logger.info("[TG] Starting long-polling loop (local dev mode).")
        offset: Optional[int] = None
        while True:
            try:
                params: Dict[str, Any] = {"timeout": 30, "allowed_updates": ["message", "callback_query"]}
                if offset is not None:
                    params["offset"] = offset
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.get(self._url("getUpdates"), params=params)
                    data = resp.json()
                    if not data.get("ok"):
                        logger.error(f"[TG] getUpdates error: {data}")
                        continue
                    for update in data.get("result", []):
                        update_id = update["update_id"]
                        offset = update_id + 1
                        try:
                            await process_update_fn(update)
                        except Exception as exc:
                            logger.error(f"[TG] Error processing update {update_id}: {exc}")
            except Exception as exc:
                import asyncio
                logger.error(f"[TG] Polling loop error: {exc}")
                await asyncio.sleep(5)


telegram_service = TelegramBotService()
