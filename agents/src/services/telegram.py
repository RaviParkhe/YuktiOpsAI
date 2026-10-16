import html
import logging
from typing import Any, Dict, List, Optional
import httpx
from src.config import get_settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Dispatches notifications and escalation alerts to Telegram."""

    def __init__(self):
        self.settings = get_settings()
        self.bot_token = self.settings.TELEGRAM_BOT_TOKEN
        self.chat_id = self.settings.TELEGRAM_ALERT_CHAT_ID

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    async def send_finding_alert(
        self,
        repo_full_name: str,
        pr_number: int,
        run_id: str,
        highest_severity: str,
        findings: List[Dict[str, Any]],
        proposal_id: Optional[str] = None,
    ) -> bool:
        """Send rich Telegram notification for high/critical findings and fix proposals."""
        if not self.is_configured:
            logger.info(
                f"[Telegram Mock Alert] Repo: {repo_full_name} | PR #{pr_number} | "
                f"Severity: {highest_severity} | Findings: {len(findings)} | Run ID: {run_id}"
            )
            return True

        severity_icon = {
            "CRITICAL": "🚨 *CRITICAL ALERT*",
            "HIGH": "⚠️ *HIGH SEVERITY*",
            "MEDIUM": "ℹ️ *MEDIUM NOTICE*",
            "LOW": "📝 *LOW*",
            "INFO": "💡 *INFO*",
        }.get(highest_severity.upper(), "⚠️ *ALERT*")

        lines = [
            f"{severity_icon}",
            f"*Repository:* `{html.escape(repo_full_name)}`",
            f"*Pull Request:* [#{pr_number}](https://github.com/{repo_full_name}/pull/{pr_number})",
            f"*Run ID:* `{run_id}`",
            "",
            "*Key Findings Detected:*",
        ]

        for finding in findings[:3]:
            title = finding.get("title", "Issue")
            cat = finding.get("category", "GENERAL")
            file_path = finding.get("file_path") or "general"
            lines.append(f"• *[{cat}]* {html.escape(title)} (`{html.escape(file_path)}`)")

        if len(findings) > 3:
            lines.append(f"_...and {len(findings) - 3} more issue(s)_")

        if proposal_id:
            lines.append("")
            lines.append(f"🛠️ *Fix Proposal Generated:* `{proposal_id}`")
            lines.append("Review and approve via Dashboard or API before GitHub Draft PR creation.")

        message_text = "\n".join(lines)
        return await self._send_message(message_text)

    async def _send_message(self, text: str) -> bool:
        """Call Telegram Bot API sendMessage endpoint."""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    logger.info("Telegram notification delivered successfully.")
                    return True
                else:
                    logger.error(f"Telegram API delivery failed: {resp.status_code} {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Telegram client exception: {e}")
            return False
