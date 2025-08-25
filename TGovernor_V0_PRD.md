# TokenGovernor – Product Requirements Document (PRD)

## 1. Overview

### Purpose
TokenGovernor is a standalone governance system for agentic coding workflows, managing token usage, enforcing priorities, requesting checkpoints, and scheduling task resumption. It integrates with external systems (e.g., LangChain, AutoGen) via APIs, using Claude-Code for code generation, Claude-Flow for workflow orchestration with deep inspection, and `ccusage` for token tracking, without orchestrating agents.

### Scope
- **Hierarchical monitoring**: Project → Agent → Task → Optional Subtasks
- **Token budget enforcement** with heuristics and `ccusage`
- **Checkpoint management** for task safety
- **Scheduler** for paused tasks/packages
- **Status reporting** via CLI, API, and dashboard
- **GitHub-based change management** with PR process
- **Claude-Flow orchestration** with dynamic agent allocation
- **Minimal MVP** with scalability and usability focus

## 2. Goals & Success Criteria

### Goals
- Govern token usage with accurate tracking and priority enforcement.
- Monitor task progress at multiple levels.
- Request checkpoints at adaptive thresholds or preemptively.
- Schedule paused tasks/packages with user control.
- Deliver concise reports via CLI, API, dashboard.
- Ensure usability with <15-minute setup.
- **Initialize GitHub repo with Claude-Code/Claude-Flow, using deep inspection to allocate agents.**
- **Enforce commits, PRs, and reviews for all changes.**
- **Orchestrate workflows with Claude-Flow, dynamically adjusting agents.**
- **Optimize token budgets and scheduling with `ccusage` and ML.**
- Remain lightweight, modular, reusable.

### Success Criteria
- Tasks within 5% of token budgets, validated by `ccusage`.
- Checkpoints within 95% of adaptive thresholds; no work lost.
- Scheduler resumes with 90% accuracy.
- Reports <200 tokens, accessible via CLI/API/dashboard.
- Setup <15 minutes, including GitHub repo.
- Integration with LangChain/AutoGen via SDKs.
- **Phase 0: GitHub repo initialized with dynamic agent allocation; PR process enforced with <2% token overhead.**
- **Phase 1: Core governance with <10% estimation error.**
- **Phase 2: Dashboard deployed; simulations with `ccusage`.**
- **Phase 3: Scheduling efficiency improved by 15% with ML.**

## 3. System Components

### 3.1 Project Registry
- Projects register via REST API/CLI.
- **Metadata**:
  - Project ID (UUID)
  - Token budget (integer)
  - Priority tier (Tier 1: high, Tier 2: low)
  - Owner (GitHub handle/email)
- **Implementation**:
  - SQLite; API: `POST /projects/register`.
  - **Phase 0: Claude-Code generates config files; Claude-Flow Setup Agent links to GitHub repo after inspection.**
- **Usability**: CLI (`token-gov register --id <uuid> --budget <int>`); Phase 2 dashboard (`/dashboard/projects`).

### 3.2 Agents
- Ephemeral, created per task step by external systems.
- Classified by task type (Tier 1/2).
- Monitored via task-level budgets.
- **Implementation**: UUIDs in task metadata.
- **Usability**: Transparent; Phase 2 dashboard (`/dashboard/agents`).

### 3.3 Agent Tasks
- Execution units from external systems or Claude simulations.
- **Metadata**:
  - Task ID (UUID)
  - Parent agent ID (UUID)
  - Complexity (Simple: <1k, Complex: 1k-5k, Very Complex: >5k)
  - Estimated tokens (heuristic in Phase 0, `ccusage` in Phase 1, ML in Phase 3)
  - Subtasks (list of UUIDs)
  - Checkpoint state (None, Requested, Saved)
- **Checkpointing**:
  - Automatic at adaptive thresholds (default 90%) or preemptively.
  - External storage; tracks URI references.
  - **Phase 2: Context compression (SentenceTransformers).**
- **Implementation**:
  - API: `POST /tasks/register`.
  - **Phase 0: Claude-Code generates templates; Claude-Flow PR Agent commits via PRs.**
  - **Phase 1: `ccusage` parses JSONL for estimates.**
- **Usability**: CLI (`token-gov task add`, `token-gov estimate`, `token-gov simulate --ccusage`); Phase 2 dashboard (`/dashboard/tasks`).

### 3.4 Task Packages (Optional)
- Collections of related tasks.
- **Metadata**: Package ID, Project ID, task IDs, token estimate, priority, timeline.
- **Implementation**: API: `POST /packages/register`; SQLite.
- **Usability**: CLI (`token-gov package add`); Phase 2 dashboard (`/dashboard/packages`).

### 3.5 TokenInspector / Governor Agent
- **Functions**:
  - Tracks tokens via async listeners and `ccusage`.
  - Enforces budgets and priorities.
  - Requests checkpoints at adaptive thresholds.
  - Manages paused task/package queue.
  - API interfaces (e.g., `POST /tasks/pause`).
  - **Phase 0: Tracks Claude-Code/Claude-Flow tokens; logs PR metadata.**
  - **Phase 1: `ccusage` for estimates; adaptive thresholds; error notifications.**
  - **Phase 3: ML-driven threshold adjustments.**
- **Implementation**:
  - Python with FastAPI; asyncio.
  - SQLite; Redis (Phase 3).
  - **Adapted `ccusage` logic in Python; `ccusage blocks --live` for dashboard.**
  - **Phase 0: Rate-limits Claude API (5/min per agent); logs setup tokens.**
  - **Phase 1: Error logging; retries (3 attempts, exponential backoff); webhook alerts.**
  - **AES-256 encrypted JSONL.**
- **Usability**: CLI (`token-gov config --adaptive-threshold`, `token-gov measure --ccusage`, `token-gov errors --notify`); Phase 2 dashboard (`/dashboard/inspector`).

### 3.6 Scheduler
- **Prioritization**: Rule-based (Phase 1); **ML-driven with `ccusage` (Phase 3).**
- **Rate-Limiting**: 10 tasks/min.
- **Implementation**:
  - Python with asyncio; JSON rules.
  - **Worker pool for 100 tasks/min.**
  - **Phase 0: PR process for config changes.**
- **Usability**: CLI (`token-gov scheduler resume`, `token-gov optimize --ccusage`); Phase 2 dashboard (`/dashboard/scheduler`).

### 3.7 Status Reporting
- **Levels**: Project, Agent, Task/Package.
- **Format**: JSON (`GET /status/{level}/{id}`); CLI; **Phase 2: React dashboard with Chart.js.**
- **Frequency**: Periodic (5 min), on-demand, event-triggered.
- **Implementation**:
  - FastAPI; CLI (`token-gov status --ccusage`).
  - **Phase 0: Reports repo setup, PR status, inspection results.**
  - **Phase 2: Dashboard with line charts (token usage), tables (tasks/PRs).**
- **Usability**: CLI with compact tables; JSON; dashboard with dark/light themes, mobile responsiveness.

### 3.8 Claude-Flow Configuration
- **Deep Inspection**:
  - Analyzes `project_config.json` (file count, API calls, task complexity) to allocate 1–5 agents.
  - Criteria: 1 agent (<10 files, <20 calls), 2–3 (10–50 files, 20–100 calls), 4–5 (>50 files, >100 calls).
  - Outputs `workflow_plan.json` (agent roles, token estimates), stored in SQLite, committed via PR.
- **Agents**:
  - **Setup Agent(s) (Phase 0)**: Initializes GitHub repo, branches, Actions via `PyGitHub`. Scales based on inspection.
  - **PR Agent(s) (Phase 0)**: Creates commits/PRs with templates; tracks tokens via `ccusage`.
  - **Simulation Agent(s) (Phase 2)**: Runs Claude-Code tasks; coordinates with `ccusage`.
- **Number**: Dynamically allocated (1–5) based on inspection; max 5 to cap overhead.
- **Memory**: Stateless, 8k token context window; SQLite for persistent data (e.g., `workflow_plan.json`, PR status).
- **Rate-Limiting**: 5 API calls/min per agent, adjusted per inspection; enforced via `ratelimiter`.
- **Error Handling**: 3 retries with exponential backoff; webhook alerts for failures.
- **Workflows**: JSON templates (`.github/workflows/setup_workflow.json`, `pr_workflow.json`, `simulation_workflow.json`).
- **Implementation**:
  - Python scripts (`init_repo.py`, `simulate.py`) call Claude-Flow APIs.
  - **Token usage tracked by `ccusage`; logged to SQLite.**
- **Usability**: CLI (`token-gov init --inspect`, `token-gov init --status`, `token-gov simulate --ccusage`); Phase 2 dashboard displays agent status, inspection results.

## 4. Workflow
1. **Phase 0: Initialization**:
   - Claude-Flow inspects `project_config.json`; generates `workflow_plan.json` (1–5 agents).
   - Setup Agent creates GitHub repo, branches, Actions; Claude-Code generates files.
   - PR Agent commits files via PRs with templates; `ccusage` tracks tokens.
2. **Project Registration**: API/CLI; validated for budget, tier.
3. **Task/Package Registration**: Validated with heuristic/`ccusage` estimates.
4. **Execution**: External systems execute tasks; TokenInspector monitors via `ccusage`.
5. **Checkpointing**: Adaptive thresholds; external storage.
6. **Pausing**: Exceeding tasks paused; queued.
7. **Scheduling**: Resumes tasks when tokens available.
8. **Reporting**: CLI/API/dashboard; <200 tokens.

## 5. Constraints & Assumptions
- **MVP**: Single project; multi-project in Phase 3.
- **Agents**: Ephemeral; budgets at task/package level.
- **Subtasks**: Handled externally; monitored aggregately.
- **Overhead**: Monitoring/reporting <5% of budget; Phase 0 <2%.
- **Usability**: CLI/API/dashboard; setup <15 minutes.
- **GitHub**: All changes via PRs; Claude-generated files tracked.
- **Claude-Flow**: Dynamic 1–5 agents, stateless, 8k token context, 5 calls/min.

## 6. Milestones
1. **Phase 0: GitHub Setup and Change Management (Weeks 1-2, Aug 26-Sep 8, 2025)**:
   - Claude-Flow inspects project; generates `workflow_plan.json` (1–5 agents).
   - Claude-Code generates repo files (e.g., `main.py`, `.github/pull_request_template.md`).
   - Setup Agent initializes repo via `PyGitHub`; PR Agent commits via PRs.
   - `ccusage` tracks tokens (<2% overhead); SQLite stores metadata.
   - CLI (`token-gov init --inspect`, `token-gov commit --pr --template`).
   - Heuristic token estimation; basic error logging.
2. **Phase 1: Core Governance and CLI (Weeks 3-7, Sep 9-Oct 13)**:
   - Project/Task/Package registry with SQLite, API, CLI.
   - TokenInspector with async tracking, adaptive thresholds, `ccusage`, error notifications (webhooks).
   - Basic Scheduler with rule-based prioritization.
3. **Phase 2: Dashboard and Simulations (Weeks 8-12, Oct 14-Nov 17)**:
   - React dashboard (Chart.js) for Project Overview, Task Status, PR History, inspection results.
   - Claude-Flow Simulation Agent runs Claude-Code tasks with `ccusage`.
   - Context compression for checkpoints.
4. **Phase 3: Optimizations and Scalability (Weeks 13-16, Nov 18-Dec 16)**:
   - ML-driven optimizations for token estimation, scheduling.
   - Dependency tracking (DAG in SQLite).
   - Multi-project with Redis.
   - End-to-end testing; release MVP with SDKs (Dec 16, 2025).

## 7. Future Enhancements
- **Multi-Project**: Global token limits with Redis.
- **Advanced Learning**: Neural networks for patterns.
- **Dependency Tracking**: DAG visualizations in dashboard.
- **Security**: OAuth for dashboard; risk assessments.
- **API Extensions**: Enhanced MCP with `ccusage`.

## 8. Key Features
- **Hierarchy**: Project → Agent → Task → Subtasks
- **Governance**: Token monitoring, checkpoints, scheduling
- **GitHub Integration**: Claude-driven repo setup, PR process
- **Claude-Flow**: Dynamic 1–5 agents via deep inspection, stateless, rate-limited
- **Usability**: CLI, API, dashboard; <15-min setup
- **Efficiency**: Async monitoring, `ccusage` estimates
- **Modularity**: Reusable for agentic frameworks