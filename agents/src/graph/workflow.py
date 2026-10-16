import logging
from typing import Any, Literal, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from src.graph.nodes import (
    approval_and_action_node,
    code_and_security_analysis_node,
    ingest_context_node,
    notification_node,
    solution_agent_node,
    triage_and_risk_node,
)
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

# Shared in-memory checkpointer for human-in-the-loop state persistence
_checkpointer = MemorySaver()


def route_after_notification(state: AgentState) -> Literal["approval_and_action", "__end__"]:
    """Conditional router determining if human approval pause is required."""
    proposals = state.get("fix_proposals", [])
    if proposals and state.get("approval_required", True):
        return "approval_and_action"
    return END


def create_agent_workflow(checkpointer: Optional[Any] = None):
    """Build the deterministic orchestrator graph with specialized logical agents.

    Architecture:
    [START]
       │
       ▼
    [ingest_context] (Bounded diff + CI status)
       │
       ▼
    [code_and_security_analysis] (Logical Code & Security Analyst)
       │
       ▼
    [triage_and_risk] (Deterministic deduplication & risk scoring)
       │
       ▼
    [solution_agent] (Generates proposed fix diffs)
       │
       ▼
    [notification_agent] (Telegram alert thresholding)
       │
       ├── (Proposals exist) ──► [approval_and_action] (Pauses for human approval) ──► [END]
       │
       └── (No proposals) ─────────────────────────────────────────────────────────► [END]
    """
    workflow = StateGraph(AgentState)

    # Register specialized logical nodes
    workflow.add_node("ingest_context", ingest_context_node)
    workflow.add_node("code_and_security_analysis", code_and_security_analysis_node)
    workflow.add_node("triage_and_risk", triage_and_risk_node)
    workflow.add_node("solution_agent", solution_agent_node)
    workflow.add_node("notification_agent", notification_node)
    workflow.add_node("approval_and_action", approval_and_action_node)

    # Linear orchestrator pipeline
    workflow.add_edge(START, "ingest_context")
    workflow.add_edge("ingest_context", "code_and_security_analysis")
    workflow.add_edge("code_and_security_analysis", "triage_and_risk")
    workflow.add_edge("triage_and_risk", "solution_agent")
    workflow.add_edge("solution_agent", "notification_agent")

    # Conditional routing to human approval or completion
    workflow.add_conditional_edges(
        "notification_agent",
        route_after_notification,
        {
            "approval_and_action": "approval_and_action",
            END: END,
        },
    )
    workflow.add_edge("approval_and_action", END)

    saver = checkpointer if checkpointer is not None else _checkpointer

    # Interrupt before approval_and_action so human review is required before GitHub Draft PR creation
    compiled = workflow.compile(
        checkpointer=saver,
        interrupt_before=["approval_and_action"],
    )
    return compiled


app_workflow = create_agent_workflow()
