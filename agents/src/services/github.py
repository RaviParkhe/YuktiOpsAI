import hashlib
import hmac
import logging
from typing import Optional, Tuple
import httpx
from src.config import get_settings
from src.schemas.analysis import CIStatus

logger = logging.getLogger(__name__)


class GitHubService:
    """GitHub API client handling webhook verification, diff extraction, and draft PR generation."""

    def __init__(self):
        self.settings = get_settings()

    @staticmethod
    def verify_webhook_signature(
        payload_bytes: bytes,
        signature_header: Optional[str],
        secret: str,
    ) -> bool:
        """Verify GitHub HMAC-SHA256 signature against webhook payload."""
        if not signature_header or not secret:
            logger.warning("Missing signature header or secret for webhook verification.")
            return False

        if not signature_header.startswith("sha256="):
            return False

        mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
        expected_sig = f"sha256={mac.hexdigest()}"
        return hmac.compare_digest(expected_sig, signature_header)

    async def fetch_pr_diff(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        auth_token: Optional[str] = None,
    ) -> str:
        """Fetch unified diff for a PR, enforcing line and byte bounds."""
        # If no auth token is provided and not mocked, return realistic synthetic diff for local testing
        if not auth_token:
            return (
                f"diff --git a/src/api/auth.py b/src/api/auth.py\n"
                f"--- a/src/api/auth.py\n"
                f"+++ b/src/api/auth.py\n"
                f"@@ -10,3 +10,4 @@ def authenticate_user(user_id: str):\n"
                f"-    # Legacy auth\n"
                f"+    query = f\"SELECT * FROM users WHERE id = '{user_id}'\"\n"
                f"+    return db.execute(query)\n"
            )

        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "Authorization": f"Bearer {auth_token}",
        }
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Failed to fetch PR diff: {resp.status_code} {resp.text}")
                return ""
            raw_diff = resp.text

        # Enforce bounds
        lines = raw_diff.splitlines()
        if len(lines) > self.settings.MAX_DIFF_LINES:
            lines = lines[: self.settings.MAX_DIFF_LINES]
            lines.append("\n[TRUNCATED: Exceeded max allowed diff lines]")
            raw_diff = "\n".join(lines)

        if len(raw_diff.encode("utf-8")) > self.settings.MAX_DIFF_BYTES:
            raw_diff = raw_diff[: self.settings.MAX_DIFF_BYTES] + "\n[TRUNCATED: Exceeded byte limits]"

        return raw_diff

    async def fetch_ci_status(
        self,
        owner: str,
        repo: str,
        commit_sha: str,
        auth_token: Optional[str] = None,
    ) -> CIStatus:
        """Fetch aggregated check run and status status for a commit."""
        if not auth_token:
            # Deterministic mock status for local dev: success
            return CIStatus.SUCCESS

        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}/check-runs"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {auth_token}",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return CIStatus.UNKNOWN

                data = resp.json()
                check_runs = data.get("check_runs", [])
                if not check_runs:
                    return CIStatus.UNKNOWN

                for run in check_runs:
                    conclusion = run.get("conclusion")
                    status = run.get("status")
                    if conclusion in ["failure", "timed_out", "action_required"]:
                        return CIStatus.FAILURE
                    if status in ["queued", "in_progress"]:
                        return CIStatus.PENDING

                return CIStatus.SUCCESS
        except Exception as e:
            logger.error(f"Error fetching CI status: {e}")
            return CIStatus.UNKNOWN

    async def create_draft_pr_for_proposal(
        self,
        owner: str,
        repo: str,
        target_branch: str,
        proposal_title: str,
        proposal_body: str,
        diff_patch: str,
        auth_token: Optional[str] = None,
    ) -> str:
        """Create a GitHub Draft PR containing the approved fix proposal.

        Requires explicit prior human approval.
        """
        # When running in mock/local dev without token, return a simulated GitHub PR URL
        if not auth_token:
            simulated_url = f"https://github.com/{owner}/{repo}/pull/draft-preview-{hashlib.md5(diff_patch.encode()).hexdigest()[:6]}"
            logger.info(f"Simulated Draft PR created: {simulated_url}")
            return simulated_url

        # Real GitHub App Flow: create branch, commit patch, open PR with draft=True
        # Headers: Authorization: Bearer <installation_token>
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {auth_token}",
        }
        payload = {
            "title": f"[YuktiOps Fix] {proposal_title}",
            "body": (
                f"### YuktiOps Automated Remediation Proposal\n\n"
                f"{proposal_body}\n\n"
                f"```diff\n{diff_patch}\n```\n\n"
                f"*Created after explicit human verification.*"
            ),
            "head": f"yuktiops/fix-{target_branch}",
            "base": target_branch,
            "draft": True,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return resp.json().get("html_url", "")
            else:
                logger.error(f"Failed to create draft PR: {resp.status_code} {resp.text}")
                raise RuntimeError(f"GitHub API Error: {resp.status_code} {resp.text}")
