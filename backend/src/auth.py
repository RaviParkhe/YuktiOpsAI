"""
Firebase ID token verification middleware.

In development (no FIREBASE_PROJECT_ID set), the service runs in STUB mode:
  - Any 'Bearer <token>' is accepted.
  - Use 'Bearer dev:<uid>' to simulate a specific Firebase UID.
  - Stub mode is logged clearly; never silently activated in production.

In production:
  - FIREBASE_PROJECT_ID must be set.
  - FIREBASE_SERVICE_ACCOUNT_JSON (full JSON string) or Application Default
    Credentials must be available.
  - Tokens are verified including revocation check.
"""
import json
import logging
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

logger = logging.getLogger(__name__)

_firebase_app = None    # None = uninitialised, False = stub mode, object = real
_firebase_auth = None


def _init() -> bool:
    """Initialise Firebase once. Returns True when real credentials are loaded."""
    global _firebase_app, _firebase_auth
    if _firebase_app is not None:
        return bool(_firebase_auth)

    from pathlib import Path
    from src.config import Environment, get_settings
    s = get_settings()

    if s.ENVIRONMENT == Environment.PRODUCTION:
        if not s.FIREBASE_PROJECT_ID:
            logger.critical("[AUTH] Production requires FIREBASE_PROJECT_ID to be set.")
            raise RuntimeError("FIREBASE_PROJECT_ID must be set in production. Stub mode is forbidden.")

    if not s.FIREBASE_PROJECT_ID:
        logger.warning(
            "[AUTH] FIREBASE_PROJECT_ID is not set — running in DEVELOPMENT STUB MODE. "
            "All Bearer tokens are accepted. Set FIREBASE_PROJECT_ID + "
            "FIREBASE_SERVICE_ACCOUNT_FILE or FIREBASE_SERVICE_ACCOUNT_JSON for production token verification."
        )
        _firebase_app = False
        return False

    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        cred = None
        if s.FIREBASE_SERVICE_ACCOUNT_FILE:
            file_path = Path(s.FIREBASE_SERVICE_ACCOUNT_FILE)
            if not file_path.is_absolute():
                base_dir = Path(__file__).resolve().parent.parent
                file_path = base_dir / file_path
            if file_path.exists():
                cred = credentials.Certificate(str(file_path))
                logger.info(f"[AUTH] Loaded credentials from file: {file_path.name}")
            else:
                logger.warning(f"[AUTH] Service account file not found: {file_path}")

        if cred is None and s.FIREBASE_SERVICE_ACCOUNT_JSON:
            cred = credentials.Certificate(json.loads(s.FIREBASE_SERVICE_ACCOUNT_JSON))
            logger.info("[AUTH] Loaded credentials from FIREBASE_SERVICE_ACCOUNT_JSON")

        if cred is None:
            cred = credentials.ApplicationDefault()
            logger.info("[AUTH] Attempting Application Default Credentials")

        options = {"projectId": s.FIREBASE_PROJECT_ID} if s.FIREBASE_PROJECT_ID else None
        if not firebase_admin._apps:
            _firebase_app = firebase_admin.initialize_app(cred, options)
        else:
            _firebase_app = firebase_admin.get_app()

        _firebase_auth = auth
        logger.info(f"[AUTH] Firebase Admin SDK ready — project: {s.FIREBASE_PROJECT_ID}")
        return True
    except Exception as exc:
        if s.ENVIRONMENT == Environment.PRODUCTION:
            logger.critical(f"[AUTH] Firebase initialization failed in PRODUCTION: {exc}")
            raise RuntimeError(f"Firebase initialization failed in production: {exc}")
        logger.error(f"[AUTH] Firebase initialisation failed: {exc}. Falling back to STUB mode.")
        _firebase_app = False
        return False


def get_auth_status() -> dict:
    """Return non-sensitive authentication status."""
    from src.config import get_settings
    s = get_settings()
    has_real = _init()
    return {
        "is_stub_mode": not has_real,
        "auth_provider": "Firebase Admin SDK" if has_real else "Development Stub",
        "project_id": s.FIREBASE_PROJECT_ID if has_real else None,
        "environment": s.ENVIRONMENT.value,
    }


class VerifiedUser:
    """Verified Firebase user identity — never trust client-supplied values."""

    __slots__ = ("uid", "email", "is_stub")

    def __init__(self, uid: str, email: Optional[str], is_stub: bool = False):
        self.uid = uid
        self.email = email
        self.is_stub = is_stub

    def __repr__(self) -> str:
        return f"<VerifiedUser uid={self.uid} email={self.email} stub={self.is_stub}>"


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> VerifiedUser:
    """
    FastAPI dependency — returns a verified user or raises 401.

    Dev stub: 'Bearer dev:<uid>' → VerifiedUser(uid=<uid>)
    """
    has_firebase = _init()

    if not has_firebase:
        uid, email = "dev-user", "dev@yuktiops.local"
        if authorization and authorization.startswith("Bearer dev:"):
            uid = authorization[len("Bearer dev:"):].strip() or uid
        return VerifiedUser(uid=uid, email=email, is_stub=True)

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "MISSING_TOKEN", "message": "Authorization: Bearer <firebase-id-token> required"},
        )

    token = authorization[7:].strip()
    if not token or token.startswith("dev:"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Development tokens are rejected when real Firebase verification is active"},
        )

    try:
        decoded = _firebase_auth.verify_id_token(token, check_revoked=True)
        return VerifiedUser(uid=decoded["uid"], email=decoded.get("email"), is_stub=False)
    except Exception as exc:
        logger.warning(f"[AUTH] Token rejected: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Firebase ID token is invalid or expired"},
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[VerifiedUser]:
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
