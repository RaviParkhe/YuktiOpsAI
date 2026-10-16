import pytest
from src.graph.nodes.triage import compute_finding_fingerprint, triage_and_risk_node
from src.graph.state import AgentState


def test_fingerprint_deterministic_for_same_finding():
    finding_a = {
        "category": "SECURITY_VULNERABILITY",
        "file_path": "src/api/auth.py",
        "line_number": 12,
        "title": "SQL Injection in User Lookup",
    }
    finding_b = {
        "category": "security_vulnerability",
        "file_path": "src/api/auth.py",
        "line_number": 12,
        "title": "SQL Injection in User Lookup",
    }

    fp_a = compute_finding_fingerprint(finding_a)
    fp_b = compute_finding_fingerprint(finding_b)

    assert fp_a == fp_b
    assert len(fp_a) == 16


@pytest.mark.asyncio
async def test_triage_deduplicates_and_ranks_by_severity():
    state: AgentState = {
        "raw_findings": [
            {
                "category": "CODE_QUALITY",
                "severity": "LOW",
                "title": "Unused import",
                "file_path": "app.py",
                "line_number": 1,
            },
            {
                "category": "SECURITY_VULNERABILITY",
                "severity": "CRITICAL",
                "title": "SQL Injection",
                "file_path": "db.py",
                "line_number": 10,
            },
            # Exact duplicate of the first finding
            {
                "category": "CODE_QUALITY",
                "severity": "LOW",
                "title": "Unused import",
                "file_path": "app.py",
                "line_number": 1,
            },
            {
                "category": "BUG_RISK",
                "severity": "HIGH",
                "title": "Null pointer access",
                "file_path": "service.py",
                "line_number": 44,
            },
        ],
        "audit_logs": [],
    }

    result = await triage_and_risk_node(state)
    triaged = result["triaged_findings"]

    # 4 items with 1 duplicate -> 3 unique triaged findings
    assert len(triaged) == 3

    # Must be ranked by severity descending: CRITICAL -> HIGH -> LOW
    assert triaged[0]["severity"] == "CRITICAL"
    assert triaged[1]["severity"] == "HIGH"
    assert triaged[2]["severity"] == "LOW"

    # Highest severity recorded
    assert result["highest_severity"] == "CRITICAL"
