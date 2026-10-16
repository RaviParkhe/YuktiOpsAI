"""Deterministic Mock LLM Service for CI, testing, and offline evaluation.

Guarantees:
- Zero external network calls.
- Zero paid API usage.
- Deterministic, reproducible outputs across English and Hinglish.
- Token and latency tracking.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockLLMService:
    """Mock LLM Service mimicking LLMService interface without external dependencies."""

    def __init__(self, latency_sim_ms: float = 0.0):
        self.latency_sim_ms = latency_sim_ms
        self.call_count: int = 0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.latencies_ms: List[float] = []

    def reset_usage(self) -> None:
        """Reset token and call counters."""
        self.call_count = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.latencies_ms = []

    def get_usage(self) -> Dict[str, Any]:
        """Return model usage metrics."""
        return {
            "call_count": self.call_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }

    async def classify_intent_and_action(
        self,
        message_text: str,
        task_context: Optional[Dict[str, Any]] = None,
        sender_id: Optional[str] = None,
        evidence_summary: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Classify message intent offline and return structured action proposal."""
        start_t = time.perf_counter()
        self.call_count += 1
        prompt_chars = len(message_text or "")
        prompt_tokens = max(1, prompt_chars // 4)
        self.total_prompt_tokens += prompt_tokens

        text_lower = (message_text or "").lower().strip()

        # 0. Check for prompt injection attempts
        is_injection = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(ignore all previous instructions|ignore previous instructions)\b",
                r"\b(system override|disregard earlier instructions)\b",
                r"\b(drop table|grant admin|you are now a|execute rm -rf)\b",
                r"(</system>|</untrusted_diff>|<script>)",
            ]
        )
        if is_injection:
            result = {
                "intent": "ambiguous",
                "proposed_action": "request_clarification",
                "blocker_reason": None,
                "progress_note": None,
                "next_action": "Flagged potential prompt injection or malformed instruction",
                "confidence": "LOW",
                "approval_required": False,
            }
            self._record_completion(result, start_t)
            return result

        # 1. Blocker report (English & Hinglish)
        # Handle cases where user says component is done/ready but overall blocked
        is_blocker = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(cannot finish|cant finish|can't finish|unable to finish|not able to finish)\b",
                r"\b(cannott finish|cantt finish)\b",  # spelling variation
                r"\b(blocked|blocker|stuck|failing because|not available|unavailable|is down)\b",
                r"\b(blockrd|blcked|stck)\b",  # spelling variation
                r"\b(nahi ho raha|atak gaya|atki hui|ruk gaya|dikkat aa rahi|chal nahi raha)\b",
                r"\b(available nahi hai|api nahi mil rahi|api available nahi)\b",
            ]
        )
        if is_blocker:
            reason = "Backend API is unavailable"
            if "backend api" in text_lower or "backend" in text_lower:
                reason = "Backend API is unavailable"
            elif "database" in text_lower or "db" in text_lower:
                reason = "Database connection unavailable"
            elif "because" in text_lower:
                reason = message_text.split("because", 1)[1].strip().rstrip(".")
            elif "lekin" in text_lower:
                reason = message_text.split("lekin", 1)[1].strip().rstrip(".")

            progress_note = None
            if re.search(r"\b(ui is ready|frontend ready|ui ready|done with ui)\b", text_lower):
                progress_note = "Frontend UI is ready"
            elif "ready" in text_lower and ("ui" in text_lower or "frontend" in text_lower):
                progress_note = "Frontend UI is ready"

            next_action = "Request API endpoint or contract from the responsible backend owner"
            if task_context and task_context.get("dependencies"):
                deps = ", ".join(task_context.get("dependencies", []))
                next_action = f"Request API endpoint or contract from the responsible owner of {deps}"

            result = {
                "intent": "blocker_report",
                "proposed_action": "set_blocked",
                "blocker_reason": reason,
                "progress_note": progress_note,
                "next_action": next_action,
                "confidence": "HIGH",
                "approval_required": True,
            }
            self._record_completion(result, start_t)
            return result

        # 2. Task Completed (Must not have adversative but / lekin)
        has_adversative = bool(re.search(r"\b(but|however|lekin|magar|except)\b", text_lower))
        is_completed = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(is ready and integrated|task completed|finished the task|all done|work completed|merged)\b",
                r"\b(complted|finishe?d all|done with task)\b",
                r"\b(pura ho gaya|poora ho gaya|khatam ho gaya|complete ho gaya)\b",
            ]
        )
        if is_completed and not has_adversative:
            result = {
                "intent": "task_completed",
                "proposed_action": "mark_completed",
                "blocker_reason": None,
                "progress_note": "All acceptance criteria verified",
                "next_action": "Conduct final review and verify acceptance criteria",
                "confidence": "HIGH",
                "approval_required": True,
            }
            self._record_completion(result, start_t)
            return result

        # 3. Help Request
        is_help = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(need help|can someone assist|can someone help|help needed|stuck on|assistance needed)\b",
                r"\b(need halp|plz help|pls help)\b",
                r"\b(help chahiye|kisi ko pata hai|madad chahiye|bata do|help kar do)\b",
            ]
        )
        if is_help:
            result = {
                "intent": "help_request",
                "proposed_action": "flag_for_assistance",
                "blocker_reason": "Assistance requested by assignee",
                "progress_note": None,
                "next_action": "Notify team lead / peers for technical pairing",
                "confidence": "HIGH",
                "approval_required": True,
            }
            self._record_completion(result, start_t)
            return result

        # 4. Task Assignment
        is_assign = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(assign to|assign this to|reassign|re-assign|assigning to)\b",
                r"\b(asign to|re-asign)\b",
                r"\b(ko assign kardo|ko assign karo|main karunga|muje assign kardo)\b",
            ]
        )
        if is_assign:
            target_assignee = None
            m = re.search(r"assign(?:ed)?\s+(?:this\s+)?to\s+([a-zA-Z0-9_@]+)", text_lower)
            if m:
                target_assignee = m.group(1).lstrip("@")
            result = {
                "intent": "task_assignment",
                "proposed_action": "assign_task",
                "target_assignee": target_assignee,
                "blocker_reason": None,
                "progress_note": None,
                "next_action": f"Confirm reassignment to {target_assignee or 'requested owner'}",
                "confidence": "HIGH",
                "approval_required": True,
            }
            self._record_completion(result, start_t)
            return result

        # 5. Status Question
        is_status = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(what is the status|status of|how is progress|any update on|where are we|what's the update)\b",
                r"\b(status kya hai|kaha tak pahucha|update do|kya chal raha hai|kitna hua)\b",
            ]
        )
        if is_status:
            result = {
                "intent": "status_question",
                "proposed_action": "answer_status",
                "blocker_reason": None,
                "progress_note": None,
                "next_action": "Provide summary of current task status and dependencies",
                "confidence": "HIGH",
                "approval_required": False,
            }
            self._record_completion(result, start_t)
            return result

        # 6. Progress Update
        is_progress = any(
            re.search(pat, text_lower)
            for pat in [
                r"\b(working on|making progress|in progress|halfway done|partially done|pushed commit|pushed a commit)\b",
                r"\b(wrking on|in-progress|making gud progress)\b",
                r"\b(kaam chal raha hai|pragati par hai|bana raha hu|adha ho gaya|aadha kaam ho gaya)\b",
            ]
        )
        if is_progress:
            result = {
                "intent": "progress_update",
                "proposed_action": "update_progress",
                "blocker_reason": None,
                "progress_note": message_text,
                "next_action": "Continue development toward task completion",
                "confidence": "HIGH",
                "approval_required": True,
            }
            self._record_completion(result, start_t)
            return result

        # 7. General Message
        is_general = any(
            re.search(pat, text_lower)
            for pat in [
                r"^(hi|hello|hey|good morning|good evening|thanks|thank you|ok|okay|noted)\b",
                r"^(namaste|theek hai|dhanyawad|shukriya)\b",
            ]
        )
        if is_general:
            result = {
                "intent": "general_message",
                "proposed_action": "acknowledge",
                "blocker_reason": None,
                "progress_note": None,
                "next_action": None,
                "confidence": "HIGH",
                "approval_required": False,
            }
            self._record_completion(result, start_t)
            return result

        # 8. Ambiguous / Clarification required
        result = {
            "intent": "ambiguous",
            "proposed_action": "request_clarification",
            "blocker_reason": None,
            "progress_note": None,
            "next_action": "Request user clarification on task and intended action",
            "confidence": "LOW",
            "approval_required": False,
        }
        self._record_completion(result, start_t)
        return result

    def _record_completion(self, result: Dict[str, Any], start_t: float) -> None:
        """Record completion tokens and latency."""
        completion_chars = len(json.dumps(result))
        self.total_completion_tokens += max(1, completion_chars // 4)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        if self.latency_sim_ms > 0:
            elapsed_ms += self.latency_sim_ms
        self.latencies_ms.append(elapsed_ms)

    async def analyze_pr_changes(
        self,
        pr_diff: str,
        pr_title: str,
        pr_description: str,
        ci_status: str,
    ) -> List[Dict[str, Any]]:
        """Mock PR analysis returning deterministic mock findings."""
        self.call_count += 1
        return [
            {
                "category": "CODE_QUALITY",
                "severity": "LOW",
                "title": "Deterministic Mock Finding",
                "file_path": "src/mock.py",
                "line_number": 1,
                "description": "Mock PR analysis executed in offline evaluation mode.",
                "recommendation": "No action needed for evaluation.",
            }
        ]
