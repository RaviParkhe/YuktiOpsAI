import json
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from src.db.models import AuditEvent, FixProposal, GitHubEvidence, Project, ProjectMember, Task, TaskMessage
from src.db.session import async_session_factory
from src.services.llm import LLMService


@pytest.fixture
async def seeded_project(client: AsyncClient):
    """Seed a project, authorized members, and an active task for testing."""
    async with async_session_factory() as session:
        proj_id = str(uuid.uuid4())
        project = Project(
            id=proj_id,
            name="YuktiOps Core",
            key="YUK",
            repo_name="TechSena/YuktiOps",
        )
        session.add(project)

        lead = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            user_id="lead_alice",
            name="Alice Lead",
            role="team_lead",
            telegram_user_id="alice_lead_tg",
        )
        dev = ProjectMember(
            id=str(uuid.uuid4()),
            project_id=proj_id,
            user_id="dev_bob",
            name="Bob Dev",
            role="developer",
            telegram_user_id="bob_dev_tg",
        )
        session.add(lead)
        session.add(dev)

        task = Task(
            id=str(uuid.uuid4()),
            task_key="YUK-101",
            project_id=proj_id,
            title="User Login Integration",
            description="Build login UI and integrate with backend auth API.",
            status="in_progress",
            assignee_id="dev_bob",
            dependencies=["YUK-100"],
            acceptance_criteria="Login UI renders and validates credentials via backend API.",
            version=1,
        )
        session.add(task)
        await session.commit()

        return {
            "project_id": proj_id,
            "task_id": task.id,
            "task_key": task.task_key,
            "lead_id": lead.user_id,
            "dev_id": dev.user_id,
        }


@pytest.mark.asyncio
async def test_telegram_webhook_deduplication(client: AsyncClient, seeded_project):
    """Test that Telegram messages are normalized and duplicate source events are ignored."""
    payload = {
        "sender_id": "dev_bob",
        "message_text": "Working on YUK-101 login integration",
        "source_event_id": "tg_event_unique_001",
        "project_id": seeded_project["project_id"],
        "task_id": seeded_project["task_id"],
    }

    # 1. First delivery should be accepted
    resp1 = await client.post("/api/v1/webhooks/telegram", json=payload)
    assert resp1.status_code == 202
    data1 = resp1.json()["data"]
    assert data1["status"] == "queued"
    assert data1["source_event_id"] == "tg_event_unique_001"

    # 2. Duplicate delivery must be ignored without creating duplicate tasks/messages
    resp2 = await client.post("/api/v1/webhooks/telegram", json=payload)
    assert resp2.status_code in (200, 202)
    data2 = resp2.json()["data"]
    assert data2["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_required_behavior_blocker_report(seeded_project):
    """Verify exact required behavior:
    'Login UI is ready, but I cannot finish integration because the backend API is not available'
    - Classifies as blocker_report
    - Records frontend UI progress
    - Proposes setting task to blocked with blocker 'Backend API is unavailable'
    - Proposes next action of requesting API endpoint from backend owner
    - Requires approval
    """
    llm = LLMService()
    message = "Login UI is ready, but I cannot finish integration because the backend API is not available"

    task_context = {
        "task_key": "YUK-101",
        "title": "User Login Integration",
        "status": "in_progress",
        "dependencies": ["YUK-100 (Auth Service)"],
    }

    result = await llm.classify_intent_and_action(
        message_text=message,
        task_context=task_context,
        sender_id="dev_bob",
    )

    assert result["intent"] == "blocker_report"
    assert result["proposed_action"] == "set_blocked"
    assert "Backend API is unavailable" in result["blocker_reason"]
    assert result["progress_note"] == "Frontend UI is ready"
    assert "Request API endpoint or contract" in result["next_action"]
    assert result["approval_required"] is True


@pytest.mark.asyncio
async def test_hinglish_and_all_intents():
    """Verify English & Hinglish intent classification across all 8 standard intents."""
    llm = LLMService()

    # 1. Hinglish Blocker
    res_hinglish = await llm.classify_intent_and_action(
        message_text="Login UI ready hai lekin backend API nahi mil rahi so kaam ruk gaya",
    )
    assert res_hinglish["intent"] == "blocker_report"
    assert res_hinglish["proposed_action"] == "set_blocked"

    # 2. Task Completed
    res_completed = await llm.classify_intent_and_action(
        message_text="User Login Integration is ready and integrated, all acceptance criteria verified",
    )
    assert res_completed["intent"] == "task_completed"
    assert res_completed["proposed_action"] == "mark_completed"

    # 3. Help Request
    res_help = await llm.classify_intent_and_action(
        message_text="Can someone help me with the token decoding in auth middleware?",
    )
    assert res_help["intent"] == "help_request"
    assert res_help["proposed_action"] == "flag_for_assistance"

    # 4. Task Assignment
    res_assign = await llm.classify_intent_and_action(
        message_text="Please assign this to dev_bob",
    )
    assert res_assign["intent"] == "task_assignment"
    assert res_assign["proposed_action"] == "assign_task"

    # 5. Status Question
    res_status = await llm.classify_intent_and_action(
        message_text="What is the status of YUK-101?",
    )
    assert res_status["intent"] == "status_question"
    assert res_status["approval_required"] is False

    # 6. Progress Update
    res_progress = await llm.classify_intent_and_action(
        message_text="Currently working on css layout and input form fields",
    )
    assert res_progress["intent"] == "progress_update"
    assert res_progress["proposed_action"] == "update_progress"

    # 7. General Message
    res_general = await llm.classify_intent_and_action(
        message_text="Good morning team, let's have a great sprint",
    )
    assert res_general["intent"] == "general_message"
    assert res_general["approval_required"] is False

    # 8. Ambiguous
    res_ambiguous = await llm.classify_intent_and_action(
        message_text="maybe sometime later xyz",
    )
    assert res_ambiguous["intent"] == "ambiguous"
    assert res_ambiguous["proposed_action"] == "request_clarification"


@pytest.mark.asyncio
async def test_strict_task_matching_and_clarification(client: AsyncClient, seeded_project):
    """Test that ambiguous messages without exact task matches trigger clarification and do NOT mutate state."""
    # Send message with no recognizable task key or open task match
    payload = {
        "sender_id": "dev_bob",
        "message_text": "Random update without task reference",
        "source_event_id": f"tg_unclear_{uuid.uuid4().hex[:6]}",
        "project_id": seeded_project["project_id"],
    }
    resp = await client.post("/api/v1/webhooks/telegram", json=payload)
    assert resp.status_code == 202

    # Verify no state-modifying proposals were created for an unverified task
    async with async_session_factory() as session:
        proposals = (await session.execute(
            select(FixProposal).where(FixProposal.source_event_id == payload["source_event_id"])
        )).scalars().all()
        # Should be empty because ambiguous tasks do not generate task mutation proposals
        assert len(proposals) == 0


@pytest.mark.asyncio
async def test_end_to_end_proposal_approval_and_task_transition(client: AsyncClient, seeded_project):
    """Test the complete flow:
    Proposal -> Persisted -> Team Lead Approves -> Validated Task Transition to blocked -> Audit Record.
    """
    task_id = seeded_project["task_id"]
    proj_id = seeded_project["project_id"]

    # 1. Manually seed a proposal as generated by the agent
    prop_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        prop = FixProposal(
            id=prop_id,
            task_id=task_id,
            project_id=proj_id,
            title="Task Mutation: set_blocked on YUK-101",
            description="Login UI is ready, but backend API is unavailable.",
            intent="blocker_report",
            proposed_action="set_blocked",
            blocker_reason="Backend API is unavailable",
            next_action="Request API contract from backend team",
            confidence="HIGH",
            expected_task_version=1,
            status="PROPOSED",
        )
        session.add(prop)
        await session.commit()

    # 2. RBAC check: regular developer (dev_bob) cannot approve
    unauthorized_resp = await client.post(
        f"/api/v1/proposals/{prop_id}/approve",
        json={"reviewer_id": "dev_bob", "comments": "I approve my own blocker"},
    )
    assert unauthorized_resp.status_code == 403
    assert "PERMISSION_DENIED" in unauthorized_resp.json()["error"]["code"]

    # 3. Team Lead (lead_alice) approves proposal
    approve_resp = await client.post(
        f"/api/v1/proposals/{prop_id}/approve",
        json={"reviewer_id": "lead_alice", "comments": "Approved. Escalating to backend lead."},
    )
    assert approve_resp.status_code == 200
    data = approve_resp.json()["data"]
    assert data["status"] == "EXECUTED"

    # 4. Verify task state in database was updated by validated backend logic
    async with async_session_factory() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one()
        assert task.status == "blocked"
        assert task.blocker_reason == "Backend API is unavailable"
        assert task.version == 2  # incremented concurrency version

        # 5. Verify audit trail was recorded
        audit = (await session.execute(
            select(AuditEvent).where(
                AuditEvent.task_id == task_id,
                AuditEvent.action == "task_action_approved_and_executed",
            )
        )).scalar_one_or_none()
        assert audit is not None
        assert audit.actor == "human:lead_alice"


@pytest.mark.asyncio
async def test_proposal_rejection_leaves_task_unchanged(client: AsyncClient, seeded_project):
    """Test that rejecting a proposal leaves the task in its previous state without mutation."""
    task_id = seeded_project["task_id"]
    proj_id = seeded_project["project_id"]

    prop_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        prop = FixProposal(
            id=prop_id,
            task_id=task_id,
            project_id=proj_id,
            title="Task Mutation: mark_completed on YUK-101",
            description="Mark task completed.",
            intent="task_completed",
            proposed_action="mark_completed",
            expected_task_version=1,
            status="PROPOSED",
        )
        session.add(prop)
        await session.commit()

    # Reject proposal
    reject_resp = await client.post(
        f"/api/v1/proposals/{prop_id}/reject",
        json={"reviewer_id": "lead_alice", "reason": "Integration tests have not run yet."},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["status"] == "REJECTED"

    # Verify task state is unchanged
    async with async_session_factory() as session:
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one()
        assert task.status == "in_progress"  # NOT completed!
        assert task.version == 1


@pytest.mark.asyncio
async def test_stale_proposal_rejected_for_concurrency(client: AsyncClient, seeded_project):
    """Test that if a task's version has changed since the proposal was created, approval is rejected."""
    task_id = seeded_project["task_id"]
    proj_id = seeded_project["project_id"]

    prop_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        # Mutate task version first
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one()
        task.version = 5
        await session.commit()

        prop = FixProposal(
            id=prop_id,
            task_id=task_id,
            project_id=proj_id,
            title="Stale Proposal",
            description="Stale proposal based on version 1",
            proposed_action="set_blocked",
            expected_task_version=1,  # Does not match task.version=5
            status="PROPOSED",
        )
        session.add(prop)
        await session.commit()

    resp = await client.post(
        f"/api/v1/proposals/{prop_id}/approve",
        json={"reviewer_id": "lead_alice", "comments": "Approve"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "STALE_PROPOSAL"


@pytest.mark.asyncio
async def test_github_event_attached_as_supporting_evidence_only(client: AsyncClient, seeded_project):
    """Test that a GitHub webhook event attaches as evidence to a matching task and does NOT drive state changes."""
    task_id = seeded_project["task_id"]

    # GitHub payload mentioning YUK-101 in PR title
    github_payload = {
        "action": "synchronize",
        "pull_request": {
            "number": 105,
            "title": "feat(auth): YUK-101 update login validation",
            "body": "Pushed commit with form validators",
            "head": {"sha": "c0ffee1234567890", "ref": "feature/YUK-101"},
        },
        "repository": {
            "owner": {"login": "TechSena"},
            "name": "YuktiOps",
        },
    }

    # Generate valid HMAC signature
    import hashlib
    import hmac
    secret = "test_webhook_secret_123"
    body_bytes = json.dumps(github_payload).encode("utf-8")
    sig = "sha256=" + hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    resp = await client.post(
        "/api/v1/webhooks/github",
        content=body_bytes,
        headers={
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-evidence-001",
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 202

    # Verify GitHubEvidence was attached to task
    async with async_session_factory() as session:
        evidence = (await session.execute(
            select(GitHubEvidence).where(GitHubEvidence.task_id == task_id)
        )).scalars().all()
        assert len(evidence) > 0
        assert evidence[0].pr_number == 105

        # Verify task status did NOT change automatically
        task = (await session.execute(select(Task).where(Task.id == task_id))).scalar_one()
        assert task.status == "in_progress"
