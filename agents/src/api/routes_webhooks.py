import json
import logging
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from src.db.models import AnalysisRun, AuditEvent, WebhookEvent
from src.db.session import get_db
from src.schemas.analysis import AnalysisRunStatus, CIStatus
from src.schemas.common import APIResponse, ErrorDetail, ErrorResponse
from src.schemas.webhooks import WebhookEventResponse
from src.services.github import GitHubService
from src.worker.jobs import enqueue_pr_analysis

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/github",
    response_model=APIResponse[WebhookEventResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid Webhook Signature"},
        400: {"model": ErrorResponse, "description": "Malformed JSON Payload"},
    },
)
async def handle_github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header("unknown", alias="X-GitHub-Event"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
    db: AsyncSession = Depends(get_db),
):
    """Receive, verify HMAC signature, persist, and queue GitHub webhook events."""
    settings = get_settings()
    body_bytes = await request.body()

    # 1. Verify HMAC SHA-256 signature
    is_valid = GitHubService.verify_webhook_signature(
        payload_bytes=body_bytes,
        signature_header=x_hub_signature_256,
        secret=settings.GITHUB_WEBHOOK_SECRET,
    )
    if not is_valid:
        logger.warning(f"Rejected webhook delivery {x_github_delivery}: Invalid HMAC signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_SIGNATURE", "message": "X-Hub-Signature-256 mismatch or missing"},
        )

    # 2. Parse JSON payload
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PAYLOAD", "message": f"Malformed JSON: {e}"},
        )

    action = payload.get("action")
    event_id = str(uuid.uuid4())

    # 3. Persist raw webhook event
    webhook_record = WebhookEvent(
        id=event_id,
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        action=action,
        payload=payload,
        status="queued",
    )
    db.add(webhook_record)

    # 4. Filter and dispatch PR analysis
    if x_github_event == "pull_request" and action in ("opened", "synchronize", "reopened"):
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})

        repo_owner = repo_data.get("owner", {}).get("login", "")
        repo_name = repo_data.get("name", "")
        pr_number = pr_data.get("number")
        commit_sha = pr_data.get("head", {}).get("sha", "")
        pr_title = pr_data.get("title", "")
        pr_description = pr_data.get("body", "")

        run_id = str(uuid.uuid4())
        analysis_run = AnalysisRun(
            id=run_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            status=AnalysisRunStatus.QUEUED.value,
            ci_status=CIStatus.UNKNOWN.value,
        )
        db.add(analysis_run)

        # Audit initial webhook trigger
        db.add(
            AuditEvent(
                run_id=run_id,
                actor="system:webhook",
                action="pr_webhook_received",
                details={
                    "event": x_github_event,
                    "action": action,
                    "delivery_id": x_github_delivery,
                },
            )
        )

        await db.commit()

        # Enqueue for async execution
        await enqueue_pr_analysis(
            run_id=run_id,
            repo_owner=repo_owner,
            repo_name=repo_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            pr_title=pr_title,
            pr_description=pr_description,
        )
        logger.info(f"Queued PR analysis run {run_id} for {repo_owner}/{repo_name}#{pr_number}")
    else:
        # Non-PR or unhandled event recorded as ignored
        webhook_record.status = "ignored"
        await db.commit()

    return APIResponse(
        success=True,
        message="GitHub webhook event received and queued",
        data=WebhookEventResponse(
            event_id=event_id,
            delivery_id=x_github_delivery,
            event_type=x_github_event,
            action=action,
            status=webhook_record.status,
        ),
    )
