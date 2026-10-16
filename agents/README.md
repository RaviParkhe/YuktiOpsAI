# YuktiOps Agent Service

The **YuktiOps Agent** is a production-minded, minimal AI agent service designed to orchestrate automated code analysis, triage issues, propose fixes, and route alerts for GitHub Pull Requests.

---

## 🏛️ Architecture Overview

The system follows a **single deterministic orchestrator** managing **specialized logical agents** rather than multiple autonomous agents per feature. AI analysis and proposed fixes remain strictly separated from backend permission checks, database writes, and executed GitHub actions.

```
                      GitHub Webhook (PR opened / synchronize)
                                      │
                                      ▼
                        [HMAC SHA-256 Verification]
                                      │
                                      ▼
                           [Persist & Queue Job]
                                      │
                                      ▼
                     ┌──────────────────────────────────┐
                     │    LangGraph Orchestrator        │
                     └──────────────────────────────────┘
                                      │
           1. Ingestion Node (Fetch bounded diff + CI status)
                                      │
                                      ▼
           2. Code Analyst + Quality & Security Analyst (LLM bounded)
                                      │
                                      ▼
           3. Triage & Risk Agent (Deterministic dedupe + severity ranking)
                                      │
                                      ▼
           4. Solution Agent (Generates bounded fix diff patches)
                                      │
                                      ▼
           5. Notification & Escalation Agent (Telegram alert thresholding)
                                      │
                                      ▼
     [Human Approval Checkpoint: LangGraph State Interrupt]
                                      │
                     Human Decision (via Dashboard / API)
                                      ├── REJECT ──► [Audit Log & Finalize]
                                      │
                                      └── APPROVE ─► [Action: Create GitHub Draft PR]
```

### Specialized Logical Agents

1. **Context Ingestion Node**: Deterministically bounds diffs (`MAX_DIFF_LINES`, `MAX_DIFF_BYTES`) and checks CI status before LLM invocation.
2. **Code Analyst & Quality/Security Analyst**: Inspects diffs for bugs, anti-patterns, OWASP risks, and leaked secrets. Repository text is enclosed in strict `<untrusted_diff>` blocks with prompt injection defense.
3. **Triage & Risk Agent**: Deterministic deduplication via SHA-256 fingerprinting (`hash(category + file + line + title)`) and ranking by severity (`CRITICAL > HIGH > MEDIUM > LOW > INFO`).
4. **Solution Agent**: Produces surgical, bounded unified diff patches for high-confidence/critical findings. Proposes changes without writing to repositories.
5. **Notification & Escalation Agent**: Formats and dispatches high/critical alerts to Telegram with links to review and approve proposed fixes.
6. **Approval & Action Node**: Checkpoints the workflow. Fixes begin as proposed diffs; creating a draft PR requires explicit human authorization (`/api/v1/proposals/{id}/approve`).

---

## 📁 Project Structure

```
agents/
├── docker-compose.yml           # PostgreSQL 16 & Redis 7 services
├── .env.example                 # Configuration template
├── pyproject.toml               # Python 3.12 dependencies and pytest settings
├── README.md                    # Service documentation & API guide
├── src/
│   ├── config.py                # Pydantic Settings & environment variables
│   ├── main.py                  # FastAPI application with CORS and error handling
│   ├── api/
│   │   ├── routes_webhooks.py   # GitHub HMAC signature verification & webhook ingestion
│   │   ├── routes_analysis.py   # PR analysis trigger & run status retrieval
│   │   └── routes_proposals.py  # Human approval & rejection endpoints
│   ├── db/
│   │   ├── models.py            # AnalysisRun, Finding, FixProposal, AuditEvent, WebhookEvent
│   │   └── session.py           # Async SQLAlchemy session (Postgres & SQLite support)
│   ├── graph/
│   │   ├── state.py             # AgentState TypedDict
│   │   ├── workflow.py          # LangGraph state machine with human-in-the-loop interrupt
│   │   └── nodes/               # Ingest, Analyst, Triage, Solution, Notifier, Approval nodes
│   ├── services/
│   │   ├── github.py            # GitHub App API client, diff fetcher & draft PR creator
│   │   ├── llm.py               # LLM client with prompt injection sanitization & heuristics
│   │   ├── telegram.py          # Telegram Bot notifier
│   │   └── audit.py             # Persistent audit trail recorder
│   └── worker/
│       └── jobs.py              # ARQ Redis background worker & async fallback
└── tests/
    ├── conftest.py              # In-memory test database and client fixtures
    ├── test_webhook_verification.py
    ├── test_prompt_sanitization.py
    ├── test_triage_deduplication.py
    └── test_workflow_execution.py
```

---

## 🚀 Getting Started

### 1. Requirements
- Python 3.12+
- `uv` (recommended) or `pip`
- Docker & Docker Compose (optional for local SQLite development)

### 2. Setup Environment

```bash
cd agents
cp .env.example .env
```

Install dependencies:
```bash
# Using uv (fastest):
uv venv --python 3.12
.venv\Scripts\activate      # Windows
# or: source .venv/bin/activate (macOS/Linux)
uv pip install -e ".[dev]"
```

### 3. Start Database & Redis (Docker)

To launch PostgreSQL and Redis via Docker Compose:
```bash
docker compose up -d
```

*(Note: If running without Docker, the service automatically falls back to an in-memory or file-based SQLite database and asyncio task queue).*

### 4. Run the Agent API

```bash
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Open **[http://localhost:8000/docs](http://localhost:8000/docs)** to inspect the interactive Swagger API documentation.

### 5. Run Background Worker (Optional when using Redis)

```bash
uv run arq src.worker.jobs.WorkerSettings
```

---

## 🧪 Testing Locally

Run the complete test suite with verbose output:

```bash
uv run pytest -v
```

All 8 tests verify:
- GitHub webhook HMAC signature verification & rejection of tampered payloads.
- Neutralization of prompt injection tags in untrusted repo text.
- Deterministic deduplication and severity ranking in the Triage Agent.
- End-to-end execution of the LangGraph state machine through human-in-the-loop approval.

---

## 🔌 API Integration Guide

### 1. GitHub Webhook Ingestion
- **Method / Path:** `POST /api/v1/webhooks/github`
- **Headers:**
  - `X-Hub-Signature-256`: `sha256=<hmac_sha256_hex>`
  - `X-GitHub-Event`: `pull_request`
  - `X-GitHub-Delivery`: `<uuid>`

Verifies the signature, logs the event to the database, queues PR analysis asynchronously, and immediately returns HTTP 202:
```json
{
  "success": true,
  "message": "GitHub webhook event received and queued",
  "data": {
    "event_id": "8bbbb944-f187-4d92-a968-3e1a06ca2a96",
    "delivery_id": "delivery-001",
    "event_type": "pull_request",
    "action": "opened",
    "status": "queued"
  }
}
```

---

### 2. Trigger PR Analysis Manually (from Backend or Dashboard)
- **Method / Path:** `POST /api/v1/analysis/trigger`
- **Request Body:**
```json
{
  "repo_owner": "TechSena",
  "repo_name": "YuktiOps",
  "pr_number": 42,
  "commit_sha": "a1b2c3d4"
}
```
- **Response:** HTTP 202 with `run_id`.

---

### 3. Query Analysis Run & Findings
- **Method / Path:** `GET /api/v1/analysis/{run_id}`
- **Response:**
```json
{
  "success": true,
  "data": {
    "run_id": "8bbbb944-f187-4d92-a968-3e1a06ca2a96",
    "repo_full_name": "TechSena/YuktiOps",
    "pr_number": 42,
    "commit_sha": "a1b2c3d4",
    "status": "WAITING_APPROVAL",
    "ci_status": "SUCCESS",
    "total_findings": 1,
    "highest_severity": "CRITICAL",
    "findings": [
      {
        "id": "finding-01",
        "category": "SECURITY_VULNERABILITY",
        "severity": "CRITICAL",
        "title": "Potential SQL Injection Detected",
        "file_path": "db/query.py",
        "line_number": 10,
        "description": "Detected dynamic string formatting inside SQL query.",
        "recommendation": "Use parameterized queries."
      }
    ]
  }
}
```

---

### 4. Review & Approve Proposed Fix
- **Get Proposal Diff:** `GET /api/v1/proposals/{proposal_id}`
- **Approve & Create Draft PR:** `POST /api/v1/proposals/{proposal_id}/approve`
```json
{
  "reviewer_id": "alice_tech_lead",
  "comments": "Approved. Safe parameterization applied.",
  "create_draft_pr": true
}
```
This resumes the paused LangGraph workflow and creates a draft PR on GitHub.

- **Reject Proposal:** `POST /api/v1/proposals/{proposal_id}/reject`
```json
{
  "reviewer_id": "alice_tech_lead",
  "reason": "Fix addressed in separate branch."
}
```

---

### 5. Query Audit Trail
- **Method / Path:** `GET /api/v1/analysis/{run_id}/audit-trail`
- **Response:** A chronological log of every logical agent decision, threshold check, and human approval action.
