import hashlib
import logging
from typing import Any, Dict, List
from src.config import SeverityLevel
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

SEVERITY_WEIGHTS = {
    SeverityLevel.CRITICAL.value: 4,
    SeverityLevel.HIGH.value: 3,
    SeverityLevel.MEDIUM.value: 2,
    SeverityLevel.LOW.value: 1,
    SeverityLevel.INFO.value: 0,
}


def compute_finding_fingerprint(finding: Dict[str, Any]) -> str:
    """Compute deterministic fingerprint for finding deduplication."""
    category = str(finding.get("category", "")).strip().upper()
    file_path = str(finding.get("file_path", "")).strip().lower()
    line_number = str(finding.get("line_number") or 0)
    title = str(finding.get("title", "")).strip().lower()
    raw = f"{category}:{file_path}:{line_number}:{title}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


async def triage_and_risk_node(state: AgentState) -> Dict[str, Any]:
    """Triage & Risk Agent.

    Deterministically deduplicates findings, scores severity, and normalizes findings.
    Does NOT use expensive LLM calls for sorting or deduplication.
    """
    raw_findings = state.get("raw_findings", [])
    deduped_map: Dict[str, Dict[str, Any]] = {}

    for item in raw_findings:
        fp = compute_finding_fingerprint(item)
        if fp not in deduped_map:
            normalized = dict(item)
            normalized["fingerprint"] = fp
            # Ensure severity is valid enum string
            sev = str(normalized.get("severity", "INFO")).upper()
            if sev not in SEVERITY_WEIGHTS:
                sev = SeverityLevel.INFO.value
            normalized["severity"] = sev
            deduped_map[fp] = normalized

    triaged = list(deduped_map.values())

    # Rank by severity descending
    triaged.sort(
        key=lambda f: SEVERITY_WEIGHTS.get(f.get("severity", SeverityLevel.INFO.value), 0),
        reverse=True,
    )

    highest_sev = SeverityLevel.INFO.value
    if triaged:
        highest_sev = triaged[0].get("severity", SeverityLevel.INFO.value)

    audit_entry = {
        "node": "triage_and_risk",
        "action": "triage_completed",
        "total_findings": len(triaged),
        "highest_severity": highest_sev,
    }

    logs = list(state.get("audit_logs", []))
    logs.append(audit_entry)

    return {
        "triaged_findings": triaged,
        "highest_severity": highest_sev,
        "audit_logs": logs,
    }
