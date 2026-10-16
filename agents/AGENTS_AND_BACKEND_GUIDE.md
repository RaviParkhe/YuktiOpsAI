# YuktiOps Agents Architecture & Backend Integration Guide

## 1. Tech Stack Used to Build the Agents

The YuktiOps Agent service is built using an asynchronous, type-safe Python 3.12 architecture designed for deterministic orchestration, strict security boundaries, and reliable human-in-the-loop control.

| Layer | Technology | Version | Purpose in Agent Service |
|---|---|---|---|
| **Agent Orchestrator** | `langgraph` | `>=0.2.35` | Deterministic StateGraph with checkpointing (`MemorySaver` / persistent checkpointer) and state interruptions for human approval. |
| **LLM Framework** | `langchain-google-genai` | `>=4.4.0` | Integration with Google Gemini API models (`gemini-1.5-flash` or `gemini-1.5-pro`). |
| **LLM Core / Schemas** | `langchain-core` | `>=0.3.0` | System/Human prompt representations (`SystemMessage`, `HumanMessage`). |
| **LLM Model** | **Google Gemini** | `gemini-1.5-flash` | High-throughput, low-latency code analysis, vulnerability scanning, and patch synthesis. |
| **Web API / HTTP** | `fastapi` & `uvicorn` | `fastapi>=0.115`, `uvicorn>=0.32` | REST API layer exposing webhooks, analysis triggers, and proposal review endpoints. |
| **Validation & Config** | `pydantic` & `pydantic-settings` | `>=2.9` | Request/response schemas, environment configuration, and HMAC secret validation. |
| **Database & ORM** | `sqlalchemy[asyncio]`, `asyncpg`, `aiosqlite` | `>=2.0.35` | Async ORM supporting PostgreSQL (Supabase / RDS) with automatic SQLite fallback for zero-dependency local runs. |
| **Async Task Queue** | `arq` & `redis` | `arq>=0.26`, `redis>=5.1` | Asynchronous background worker queue for heavy analysis jobs with non-blocking fallback to `asyncio.create_task`. |
| **HTTP Client** | `httpx` | `>=0.27.2` | Async client for GitHub App API calls and Telegram Bot notifications. |
| **Testing** | `pytest`, `pytest-asyncio` | `pytest>=8.3`, `pytest-asyncio>=0.24` | Comprehensive automated test suite for prompt sanitization, deduplication, and workflows. |

---

## 2. Specialized Logical Agents Overview

Instead of running unconstrained autonomous agents, YuktiOps uses a **single deterministic LangGraph state machine** managing specialized logical nodes. All agents communicate strictly through a typed state dictionary (`AgentState`).

```
GitHub Webhook / API Trigger
           │
           ▼
   [0. Ingestion Node] (src/graph/nodes/ingest.py)
           │
           ▼
   [1. Code & Security Analyst] (src/graph/nodes/analyst.py + src/services/llm.py)
           │
           ▼
   [2. Triage & Risk Agent] (src/graph/nodes/triage.py)
           │
           ▼
   [3. Solution Agent] (src/graph/nodes/solution.py + src/services/llm.py)
           │
           ▼
   [4. Notification Agent] (src/graph/nodes/notifier.py + src/services/telegram.py)
           │
           ▼
   ┌────────────────────────────────────────┐
   │ HUMAN APPROVAL CHECKPOINT (INTERRUPT)  │
   │ Graph pauses here; waits for approval  │
   └────────────────────────────────────────┘
           │
       ┌───┴────────────────────────┐
       ▼                            ▼
   [APPROVED]                   [REJECTED]
       │                            │
[5. Approval & Action Node]    [Audit Log Recorded]
(src/graph/nodes/approval.py)   (src/services/audit.py)
Creates GitHub Draft PR
```

### Agent Details

#### 1. Ingestion Agent (`src/graph/nodes/ingest.py`)
- **Role:** Bounds and sanitizes PR context before any AI processing begins.
- **Inputs:** `repo_owner`, `repo_name`, `pr_number`, `commit_sha`.
- **Actions:** Fetches git diff via GitHub App API, inspects latest CI status, truncates diffs exceeding `MAX_DIFF_LINES` (1,200) or `MAX_DIFF_BYTES` (60,000).
- **Outputs to State:** `raw_diff`, `ci_status`.

#### 2. Code & Security Analyst (`src/graph/nodes/analyst.py` & `src/services/llm.py`)
- **Role:** High-precision inspection for bugs, OWASP vulnerabilities, hardcoded secrets, and CI failures.
- **LLM Call:** Uses Google Gemini (`gemini-1.5-flash`). Repository diffs are wrapped inside XML isolation tags (`<untrusted_diff>`) with closing tag neutralization to block prompt injection attacks.
- **Fallback:** If `GEMINI_API_KEY` is not set, automatically runs a deterministic regex heuristic scanner (detects exposed API keys, SQL injection patterns, dynamic `eval`/`exec`).
- **Outputs to State:** `findings` (category, severity, file path, line number, description, recommendation).

#### 3. Triage & Risk Agent (`src/graph/nodes/triage.py`)
- **Role:** Deterministic deduplication and severity ranking.
- **Logic (Non-LLM):** Computes SHA-256 fingerprint for each finding: `sha256(f"{category}:{file_path}:{line_number}:{title}")`. Eliminates duplicates and sorts strictly: `CRITICAL > HIGH > MEDIUM > LOW > INFO`.
- **Outputs to State:** `triaged_findings`, `highest_severity`.

#### 4. Solution Agent (`src/graph/nodes/solution.py` & `src/services/llm.py`)
- **Role:** Generates surgical, minimal unified git diff patches to fix HIGH and CRITICAL issues.
- **LLM Call:** Uses Gemini with a specialized system prompt enforcing unified diff patch format (`--- a/... +++ b/...`).
- **Safety Boundary:** Only generates proposed diff text; never touches git or modifies files directly.
- **Outputs to State:** `fix_proposals` with status `PROPOSED`.

#### 5. Notification & Escalation Agent (`src/graph/nodes/notifier.py` & `src/services/telegram.py`)
- **Role:** Sends alerts for high-severity issues to human maintainers.
- **Logic:** Checks if `highest_severity >= SEVERITY_NOTIFICATION_THRESHOLD` (default: `HIGH`). If yes, dispatches an alert via Telegram Bot API with issue summary and dashboard review links.
- **Outputs to State:** `notification_sent: True/False`.

#### 6. Approval & Action Node (`src/graph/nodes/approval.py` & `src/services/github.py`)
- **Role:** Enforces human-in-the-loop safety before any external change is made.
- **Checkpoint:** LangGraph interrupts execution immediately prior to this node. The workflow will NOT proceed until an authorized human calls `/api/v1/proposals/{id}/approve`.
- **Action:** If approved, calls GitHub API to create a Draft Pull Request with the proposed fix patch.
- **Outputs to State:** `draft_pr_url`, proposals marked `EXECUTED`.

---

## 3. Which Files Connect to Backend Code

Here is the exact mapping of files and how external services, the database, workers, and APIs connect:

### 1. External Ingress & API Routers (`src/api/`)
These files handle HTTP requests from GitHub, the frontend dashboard, or internal services:

| File | Connection / Purpose | Key Endpoints |
|---|---|---|
| `src/api/routes_webhooks.py` | **GitHub Webhook Ingress:** Verifies HMAC SHA-256 signatures (`X-Hub-Signature-256`), stores raw webhook events in DB, and enqueues background PR analysis. | `POST /api/v1/webhooks/github` |
| `src/api/routes_analysis.py` | **Analysis API:** Allows frontend or backend to trigger PR analysis manually, query analysis status, list detected findings, and view audit trails. | `POST /api/v1/analysis/trigger`<br>`GET /api/v1/analysis/{run_id}`<br>`GET /api/v1/analysis/{run_id}/audit-trail` |
| `src/api/routes_proposals.py` | **Human-in-the-Loop Review:** Allows developers to inspect proposed fix patches, approve them (triggering draft PR creation), or reject them. | `GET /api/v1/proposals/{proposal_id}`<br>`POST /api/v1/proposals/{proposal_id}/approve`<br>`POST /api/v1/proposals/{proposal_id}/reject` |

### 2. Application Core & Lifecycle (`src/`)
| File | Connection / Purpose |
|---|---|
| `src/main.py` | **FastAPI Entrypoint:** Initializes FastAPI app, attaches CORS middleware, registers routers, and runs database migration/initialization on startup. |
| `src/config.py` | **Configuration System:** Reads environment variables (`.env`) for Gemini API key, Database URL, Redis URL, GitHub secrets, and CORS origins. |

### 3. Background Workers & Queue (`src/worker/`)
| File | Connection / Purpose |
|---|---|
| `src/worker/jobs.py` | **Task Enqueuer & ARQ Worker:** Connects FastAPI routes to the LangGraph workflow. Enqueues jobs into Redis via `arq`. If Redis is offline, seamlessly falls back to in-process `asyncio.create_task` with error logging. |

### 4. Graph Orchestrator (`src/graph/`)
| File | Connection / Purpose |
|---|---|
| `src/graph/workflow.py` | **StateGraph Definition:** Glues all 6 agent nodes together in sequential order and configures the `interrupt_before=["approval_and_action"]` human approval barrier. |
| `src/graph/state.py` | **AgentState TypedDict:** The shared memory contract passed between all nodes and checkpointers. |
| `src/graph/nodes/*.py` | The individual business logic nodes described in Section 2. |

### 5. Services & Integrations (`src/services/`)
These files connect the agents to external platforms and storage:

| File | Connection / Purpose |
|---|---|
| `src/services/llm.py` | **Google Gemini Service:** Uses `ChatGoogleGenerativeAI` to communicate with Google AI Studio / Gemini API. Includes prompt sanitization and fallback heuristics. |
| `src/services/github.py` | **GitHub REST API:** Authenticates as a GitHub App or Personal Access Token to pull raw diffs and create draft PR branches. |
| `src/services/telegram.py` | **Telegram Bot API:** Dispatches structured Markdown alerts to configured Telegram channels or groups. |
| `src/services/audit.py` | **Database Audit Logger:** Writes immutable audit entries to the `audit_events` database table at each step of the pipeline. |

### 6. Database Layer (`src/db/`)
| File | Connection / Purpose |
|---|---|
| `src/db/session.py` | **Async Engine & Sessionmaker:** Configures async SQLAlchemy connections to PostgreSQL (Supabase) or SQLite. Contains `init_db()` for table creation. |
| `src/db/models.py` | **Relational ORM Schema:** Defines tables: `AnalysisRunModel`, `FindingModel`, `FixProposalModel`, `AuditEventModel`, and `WebhookEventModel`. |

---

## 4. End-to-End Request Flow Diagram

```
[GitHub PR] ──► Webhook POST /api/v1/webhooks/github
                     │
                     ▼
             HMAC Verification (routes_webhooks.py)
                     │
                     ▼
             Database Record Created (db/models.py)
                     │
                     ▼
             enqueue_pr_analysis (worker/jobs.py)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    [Redis / ARQ]     [Asyncio Task Fallback]
         │                       │
         └───────────┬───────────┘
                     ▼
            create_agent_workflow() (graph/workflow.py)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ingest.py    analyst.py    triage.py
   (GitHub)      (Gemini)    (SHA-256)
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   solution.py               notifier.py
   (Gemini Diff)             (Telegram)
                     │
                     ▼
        [PAUSED AT APPROVAL CHECKPOINT]
                     │
    Frontend calls POST /api/v1/proposals/{id}/approve
                     │
                     ▼
          workflow.ainvoke(None) (Resumed)
                     │
                     ▼
        approval.py ──► GitHub API (Draft PR Created)
                     │
                     ▼
            audit.py ──► DB Audit Log Saved
```

---

## 5. Quick Reference: Environment Configuration for Gemini

In `agents/.env`:

```ini
# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash

# Database (Supabase PostgreSQL async connection)
DATABASE_URL=postgresql+asyncpg://postgres.xxxx:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:5432/postgres

# Redis (Upstash or local)
REDIS_URL=redis://localhost:6379/0

# GitHub App Integration
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret_here

# Telegram Alerts
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALERT_CHAT_ID=

# CORS Allowed Origins
ALLOWED_ORIGINS=http://localhost:3000
```
