"""
Rewarded Ad service — server-controlled session and entitlement management.

Flow:
  1. Client calls POST /ads/session  → server creates AdSession, returns session_id
  2. Client shows ad (provider SDK)
  3. Provider (AdMob) calls POST /ads/verify/admob (SSV callback) with signed payload
     OR client calls POST /ads/complete/:session_id (dev/test mode only)
  4. Server verifies signature / test_mode flag, creates FeatureEntitlement
  5. Protected endpoints check entitlement before serving feature

PRODUCTION NOTE:
  Real AdMob SSV sends a GET callback to a URL you register.
  ADMOB_SERVER_SIDE_VERIFICATION_SECRET is the HMAC key for verifying the signature.
  This implementation validates the signature when the secret is configured.
  Without it, only TEST MODE is active — always log this prominently.

FEATURE ENFORCEMENT:
  Call `require_entitlement(session, user_id, feature_key)` as a dependency
  on protected endpoints. It checks the DB — not the client claim.
"""
import hashlib
import hmac
import logging
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import AdSession, FeatureEntitlement

logger = logging.getLogger(__name__)


class AdVerificationError(Exception):
    pass


class RewardedAdService:
    def __init__(self):
        self._s = get_settings()

    # ── Session creation ──────────────────────────────────────────────────────

    async def create_session(
        self, session: AsyncSession, user_id: str, feature_key: str
    ) -> AdSession:
        s = get_settings()
        if feature_key not in s.rewarded_ad_features_list:
            raise ValueError(f"Feature '{feature_key}' is not eligible for rewarded ads")

        ad_session = AdSession(
            user_id=user_id,
            feature_key=feature_key,
            status="pending",
            test_mode=s.REWARDED_ADS_TEST_MODE,
        )
        session.add(ad_session)
        await session.flush()
        logger.info(f"[ADS] Session created: {ad_session.id} feature={feature_key} test={ad_session.test_mode}")
        return ad_session

    # ── AdMob SSV verification ────────────────────────────────────────────────

    def verify_admob_ssv(self, query_string: str, settings: Optional[any] = None) -> bool:
        """
        Verify an AdMob Server-Side Verification callback.

        AdMob sends: key_id, signature, and the full query string.
        We verify HMAC-SHA256(query_without_sig, secret) == signature.

        Returns True only when ADMOB_SERVER_SIDE_VERIFICATION_SECRET is set
        and the signature matches. Returns False otherwise.

        In TEST MODE, this check is bypassed (but logged clearly).
        """
        s = settings or get_settings()
        if s.REWARDED_ADS_TEST_MODE:
            logger.warning("[ADS] TEST MODE — AdMob SSV signature check BYPASSED. Not for production.")
            return True

        if not s.ADMOB_SERVER_SIDE_VERIFICATION_SECRET:
            logger.error("[ADS] ADMOB_SERVER_SIDE_VERIFICATION_SECRET not set — rejecting all SSV callbacks.")
            return False

        # Parse query string; remove 'signature' and 'key_id' for hash input
        params = dict(urllib.parse.parse_qsl(query_string))
        signature = params.pop("signature", None)
        params.pop("key_id", None)
        if not signature:
            return False

        # Reconstruct sorted query for hashing (AdMob convention)
        sorted_query = urllib.parse.urlencode(sorted(params.items()))
        mac = hmac.new(
            s.ADMOB_SERVER_SIDE_VERIFICATION_SECRET.encode(),
            sorted_query.encode(),
            hashlib.sha256,
        )
        return hmac.compare_digest(mac.hexdigest(), signature)

    # ── Complete session and grant entitlement ────────────────────────────────

    async def complete_session(
        self,
        session: AsyncSession,
        ad_session_id: str,
        user_id: str,
        provider_transaction_id: Optional[str] = None,
        verification_payload: Optional[dict] = None,
    ) -> FeatureEntitlement:
        """
        Mark an AdSession complete and create the FeatureEntitlement.

        - Idempotent: if provider_transaction_id already exists, returns existing entitlement.
        - Only completes sessions belonging to user_id.
        """
        s = get_settings()

        # Idempotency by provider transaction ID
        if provider_transaction_id:
            existing_session = await session.execute(
                select(AdSession).where(AdSession.provider_transaction_id == provider_transaction_id)
            )
            es = existing_session.scalar_one_or_none()
            if es and es.status == "completed":
                logger.info(f"[ADS] Duplicate SSV callback for tx={provider_transaction_id} — returning existing")
                existing_ent = await session.execute(
                    select(FeatureEntitlement).where(FeatureEntitlement.ad_session_id == es.id)
                )
                ent = existing_ent.scalar_one_or_none()
                if ent:
                    return ent

        # Fetch the session
        result = await session.execute(
            select(AdSession).where(AdSession.id == ad_session_id, AdSession.user_id == user_id)
        )
        ad_sess = result.scalar_one_or_none()
        if not ad_sess:
            raise AdVerificationError(f"Ad session {ad_session_id} not found or does not belong to user")
        if ad_sess.status in ("completed", "rejected"):
            raise AdVerificationError(f"Ad session already in status '{ad_sess.status}'")
        if ad_sess.status == "expired":
            raise AdVerificationError("Ad session has expired")

        # Mark session complete
        ad_sess.status = "completed"
        ad_sess.completed_at = datetime.now(timezone.utc)
        ad_sess.verification_payload = verification_payload
        if provider_transaction_id:
            ad_sess.provider_transaction_id = provider_transaction_id

        # Create entitlement
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=s.REWARDED_AD_UNLOCK_DURATION_SECONDS)
        entitlement = FeatureEntitlement(
            user_id=user_id,
            feature_key=ad_sess.feature_key,
            grant_source="rewarded_ad",
            ad_session_id=ad_sess.id,
            starts_at=now,
            expires_at=expires,
            is_active=True,
        )
        session.add(entitlement)
        await session.flush()
        logger.info(
            f"[ADS] Entitlement granted: user={user_id} feature={ad_sess.feature_key} "
            f"expires={expires.isoformat()} test={ad_sess.test_mode}"
        )
        return entitlement

    # ── Entitlement check ─────────────────────────────────────────────────────

    async def has_entitlement(
        self, session: AsyncSession, user_id: str, feature_key: str
    ) -> bool:
        """Check if user has an active, non-expired entitlement for a feature."""
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(FeatureEntitlement).where(
                FeatureEntitlement.user_id == user_id,
                FeatureEntitlement.feature_key == feature_key,
                FeatureEntitlement.is_active == True,
                FeatureEntitlement.expires_at > now,
            )
        )
        return result.scalar_one_or_none() is not None


rewarded_ad_service = RewardedAdService()
