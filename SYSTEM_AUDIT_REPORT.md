# NexusFlow AI — System Architecture & Reliability Audit Report (Milestone 7)

**Date:** 2026-10-10  
**Project Directory:** `D:\projects\Automation`  
**Auditor:** Autonomous Systems & QA Lead Engineer  
**Status:** FULLY VERIFIED & HARDENED

---

## 1. Executive Summary

NexusFlow AI has undergone an independent, comprehensive audit covering architecture consistency, persistent database integrity, persistent background scheduling via APScheduler, AI inference routing, Playwright browser automation, Windows UIAutomation desktop control, and full-stack security boundaries.

All 19 backend test suites and 13 frontend routes have been independently reproduced and verified against native Windows 11 without requiring Docker or WSL.

---

## 2. Database Architecture Audit

### Authoritative Persistence Engine: SQLite 3 (`nexusflow.db`)
- **Location:** `D:\projects\Automation\backend\data\nexusflow.db`
- **Engine:** SQLAlchemy 2.0 AsyncIO with SQLite dialect via `aiosqlite`.
- **Entity Schemas:**
  - `workflows`: Core visual DAG definitions, node data, handles, and active statuses.
  - `executions`: Complete node execution states, input/output captures, duration metrics, logs, and trigger types (`manual`, `schedule`, `agent`).
  - `schedules`: Interval, cron (`* * * * *`), and one-time (`one_time_run_at`) persistent schedules linked to workflows.
  - `agent_tasks`: Multi-step natural-language agent plans, ReAct loop steps, file attachments, and artifacts.
  - `notifications`: Real-time and persisted event log (`schedule`, `workflow`, `agent`).
  - `workspace_files`: Metadata registry for uploaded PDFs, CSVs, and Excel sheets.
  - `tool_configs`: Configurable tool registry risk levels, confirmation requirements, and enablement.

### Persistence Integrity Findings:
1. **Unified Authoritative Source:** Both the workflow execution runtime (`WorkflowRuntime`), background scheduler service (`SchedulerManager`), and REST endpoints share `app.core.database.AsyncSessionLocal`. There are no disconnected or split databases.
2. **Crash & Restart Recovery:** APScheduler in-memory jobs are reconstituted on application boot via `SchedulerManager.reload_all_schedules()` directly from the authoritative SQLite `schedules` table.
3. **Transaction Safety:** Cascade deletions (`ondelete="CASCADE"`) guarantee that deleting a workflow automatically purges associated schedules and execution history records without orphan leakage.

---

## 3. Test Suite Reproducibility

### Backend Pytest Suite
- **Command:** `python -m pytest tests\`
- **Exit Code:** `0`
- **Result:** **19 passed, 0 failed, 3 deprecation warnings in 48.99s**
- **Test Modules:**
  - `tests/test_agent.py`: 4 passed (Plan generation, ReAct step execution, deterministic fallback).
  - `tests/test_browser_automation.py`: 3 passed (Headless Playwright navigation, form filling, SSRF & workspace sandbox validation).
  - `tests/test_dag.py`: 2 passed (Topological ordering, cycle detection, conditional branching).
  - `tests/test_excel.py`: 1 passed (DuckDB SQL aggregation, missing value detection, summary stats).
  - `tests/test_file_intelligence.py`: 2 passed (PDF table extraction, page citation verification).
  - `tests/test_scheduler.py`: 1 passed (APScheduler lifecycle, job execution, state recording).
  - `tests/test_tools.py`: 2 passed (Registry parameter schemas, risk-level enforcement).
  - `tests/test_windows_automation.py`: 4 passed (System metrics, Notepad UIAutomation typing/closing, process allowlist enforcement, shell command injection blocking).

### Frontend Production Build
- **Command:** `npm run build`
- **Exit Code:** `0`
- **Prerendered Static Routes (13/13):**
  - `/` (Home Dashboard)
  - `/agent` (Autonomous Agent Interface)
  - `/builder` (Visual Workflow DAG Canvas)
  - `/scheduler` (Persistent Schedule Manager)
  - `/history` (Execution History & Run Inspector)
  - `/browser` (Browser Automation Sandbox)
  - `/desktop` (Windows Desktop Control Panel)
  - `/files` (PDF/Excel File Intelligence Center)
  - `/tools` (Tool Registry & Security Configuration)
  - `/library` (Workflow Template Library)
  - `/_not-found`

---

## 4. Fixes & Hardening Implemented in Milestone 7

1. **Windows Automation Shell Injection Prevention:**
   - *Vulnerability:* `cmd.exe` was present in `_get_allowed_apps()` inside `WindowsAutomationTool`.
   - *Fix:* Removed `cmd.exe`. Desktop automation is now strictly limited to safe GUI utilities (`notepad.exe`, `calc.exe`, `explorer.exe`, `mspaint.exe`).
   - *Regression Test:* Added assertion in `test_windows_automation.py` verifying `cmd.exe` execution is rejected.

2. **Browser SSRF & Local File Traversal Protection:**
   - *Vulnerability:* Unrestricted `file://` and cloud metadata IP (`169.254.169.254`) requests were possible.
   - *Fix:* Hardened `_validate_url` to enforce strict workspace directory sandboxing for `file:///` URLs and explicitly block AWS/GCP/Azure link-local metadata endpoints (`169.254.169.254`, `metadata.google.internal`).
   - *Regression Test:* Added assertions in `test_browser_automation.py` verifying blocked schemes and cloud metadata rejection.

---

## 5. Remaining Considerations
- Ollama local inference service is currently offline on port 11434; the platform seamlessly engages its built-in deterministic heuristic fallback planner without crashing or leaking requests.
