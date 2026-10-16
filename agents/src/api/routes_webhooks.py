import json
import logging
import re
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import get_settings
from src.db.models import AnalysisRun, AuditEvent, GitHubEvidence, Task, TaskMessage, WebhookEvent
from src.db.session import get_db
from src.schemas.analysis import AnalysisRunStatus, CIStatus
from src.schemas.common import APIResponse, ErrorDetail, ErrorResponse
from src.schemas.webhooks import WebhookEventResponse
from src.services.github import GitHubService
from src.worker.jobs import enqueue_pr_analysis, enqueue_task_message

logger = logging.getLogger(__name__)
router = APIRouter()


class TelegramWebhookPayload(BaseModel):
    update_id: Optional[int] = None
    message: Optional[Dict[str, Any]] = None
    # Direct payload support for API clients & tests
    sender_id: Optional[str] = None
    message_text: Optional[str] = None
    source_event_id: Optional[str] = None
    project_id: Optional[str] = None
    task_id: Optional[str] = None


@router.post(
    "/telegram",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Receive Telegram Chat Message or Webhook Update",
)
async def handle_telegram_webhook(
    request: Request,
    payload: TelegramWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Receive Telegram message, normalize into common agent input, deduplicate, and enqueue."""
    # 1. Normalize Telegram update into standard input fields
    sender_id = payload.sender_id
    message_text = payload.message_text
    source_event_id = payload.source_event_id
    project_id = payload.project_id
    task_id = payload.task_id

    if payload.message:
        msg_obj = payload.message
        msg_id = msg_obj.get("message_id")
        date = msg_obj.get("date")
        if not source_event_id and msg_id:
            source_event_id = f"tg_{msg_id}_{date}"

        if not message_text:
            message_text = msg_obj.get("text", "")

        if not sender_id:
            from_obj = msg_obj.get("from", {})
            sender_id = from_obj.get("username") or from_obj.get("first_name") or str(from_obj.get("id", "unknown"))

    if not message_text:
        return APIResponse(
            success=True,
            message="Ignored non-text Telegram message",
            data={"status": "ignored"},
        )

    sender_id = sender_id or "anonymous"
    source_event_id = source_event_id or f"msg_{uuid.uuid4().hex[:12]}"

    # 2. Deduplicate repeated source events
    dup_stmt = select(TaskMessage).where(TaskMessage.source_event_id == source_event_id)
    dup_res = await db.execute(dup_stmt)
    if dup_res.scalar_one_or_none():
        logger.info(f"Duplicate Telegram event {source_event_id} received. Ignoring to prevent duplicate proposals.")
        return APIResponse(
            success=True,
            message="Duplicate event ignored",
            data={"source_event_id": source_event_id, "status": "duplicate_ignored"},
        )

    # 3. Persist incoming task message
    msg_id = str(uuid.uuid4())
    task_message = TaskMessage(
        id=msg_id,
        project_id=project_id,
        task_id=task_id,
        sender_id=sender_id,
        source_platform="telegram",
        source_event_id=source_event_id,
        message_text=message_text,
    )
    db.add(task_message)

    # 4. Audit message receipt
    run_id = str(uuid.uuid4())
    db.add(
        AuditEvent(
            run_id=run_id,
            actor=f"user:{sender_id}",
            action="telegram_message_received",
            details={
                "message_text": message_text,
                "source_event_id": source_event_id,
                "task_id": task_id,
            },
        )
    )
    await db.commit()

    # 5. Enqueue for asynchronous agent pipeline execution
    await enqueue_task_message(
        run_id=run_id,
        sender_id=sender_id,
        message_text=message_text,
        project_id=project_id,
        task_id=task_id,
        source_event_id=source_event_id,
        source_platform="telegram",
    )

    return APIResponse(
        success=True,
        message="Telegram message accepted and queued for agent reasoning",
        data={
            "run_id": run_id,
            "message_id": msg_id,
            "source_event_id": source_event_id,
            "status": "queued",
        },
    )


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
    """Receive, verify HMAC signature, normalize GitHub events as task evidence, and queue."""
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

    # 4. Attach GitHub event as supporting evidence to matching Task
    # Rule: GitHub events are normalized as evidence records linked to a task, not as standalone triggers.
    # Check if event text mentions a task key (e.g. YUK-101)
    search_texts = []
    pr_data = payload.get("pull_request", {})
    if pr_data:
        search_texts.extend([pr_data.get("title", ""), pr_data.get("body", ""), pr_data.get("head", {}).get("ref", "")])
    commits = payload.get("commits", [])
    for c in commits:
        search_texts.append(c.get("message", ""))

    matched_task = None
    for text in search_texts:
        m = re.search(r"\b([A-Za-z]{2,10}-\d+)\b", text)
        if m:
            task_res = await db.execute(select(Task).where(Task.task_key == m.group(1).upper()))
            matched_task = task_res.scalar_one_or_none()
            if matched_task:
                break

    if matched_task:
        evidence = GitHubEvidence(
            id=str(uuid.uuid4()),
            task_id=matched_task.id,
            project_id=matched_task.project_id,
            event_type=x_github_event,
            delivery_id=x_github_delivery,
            commit_sha=payload.get("head_commit", {}).get("id") or pr_data.get("head", {}).get("sha"),
            pr_number=pr_data.get("number"),
            branch=pr_data.get("head", {}).get("ref") or payload.get("ref"),
            details={"action": action, "summary": f"GitHub {x_github_event} event recorded as supporting evidence"},
        )
        db.add(evidence)
        logger.info(f"Attached GitHub {x_github_event} as supporting evidence to task {matched_task.task_key}")

    # 5. Maintain PR code review analysis trigger for PR open/synchronize
    if x_github_event == "pull_request" and action in ("opened", "synchronize", "reopened"):
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
        webhook_record.status = "processed"
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
