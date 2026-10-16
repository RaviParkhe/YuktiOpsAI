import pytest
from langgraph.checkpoint.memory import MemorySaver
from src.graph.state import AgentState
from src.graph.workflow import create_agent_workflow


@pytest.mark.asyncio
async def test_end_to_end_agent_workflow_and_human_approval():
    # Setup test workflow with isolated in-memory checkpointer
    saver = MemorySaver()
    workflow = create_agent_workflow(checkpointer=saver)

    run_id = "test-run-101"
    config = {"configurable": {"thread_id": run_id}}

    vulnerable_diff = (
        "diff --git a/app/routes.py b/app/routes.py\n"
        "--- a/app/routes.py\n"
        "+++ b/app/routes.py\n"
        "@@ -10,3 +10,4 @@ def get_user(user_id: str):\n"
        "-    return db.query(User).filter_by(id=user_id).first()\n"
        "+    query = f\"SELECT * FROM users WHERE id = '{user_id}'\"\n"
        "+    return db.execute(query)\n"
    )

    initial_state: AgentState = {
        "run_id": run_id,
        "repo_owner": "TechSena",
        "repo_name": "YuktiOps",
        "pr_number": 15,
        "commit_sha": "f00ba4",
        "pr_title": "Update database query",
        "pr_description": "Use direct SQL query",
        "raw_diff": vulnerable_diff,
        "ci_status": "SUCCESS",
        "audit_logs": [],
    }

    # 1. Run until human-in-the-loop approval checkpoint
    state_after_analysis = await workflow.ainvoke(initial_state, config=config)

    # Verify findings detected and triaged
    triaged = state_after_analysis.get("triaged_findings", [])
    assert len(triaged) > 0
    assert state_after_analysis.get("highest_severity") == "CRITICAL"

    # Verify fix proposal was generated
    proposals = state_after_analysis.get("fix_proposals", [])
    assert len(proposals) > 0
    assert proposals[0]["status"] == "PROPOSED"
    assert "diff_patch" in proposals[0]

    # Verify workflow stopped at checkpoint before executing action
    current_state = workflow.get_state(config)
    assert "approval_and_action" in current_state.next

    # 2. Simulate Human Approval
    workflow.update_state(
        config,
        {
            "approval_status": "APPROVED",
            "reviewer_id": "senior_dev_alice",
            "reviewer_notes": "LGTM, create draft PR.",
        },
        as_node="notification_agent",
    )

    # 3. Resume workflow to execute action
    resumed_state = await workflow.ainvoke(None, config=config)

    # Verify proposal was executed and draft PR URL generated
    resumed_proposals = resumed_state.get("fix_proposals", [])
    assert resumed_proposals[0]["status"] == "EXECUTED"
    assert resumed_state.get("draft_pr_url") is not None
    assert "github.com/TechSena/YuktiOps/pull/draft-preview" in resumed_state.get("draft_pr_url")

    # 4. Verify complete audit trail
    audit_logs = resumed_state.get("audit_logs", [])
    actions = [entry.get("action") for entry in audit_logs]
    assert "context_ingested" in actions
    assert "logical_analysis_completed" in actions
    assert "triage_completed" in actions
    assert "proposals_generated" in actions
    assert "draft_pr_created" in actions
