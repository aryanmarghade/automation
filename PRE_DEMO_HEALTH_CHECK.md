# NexusFlow AI — Pre-Demo Diagnostic Health Check Guide

The pre-demo health check utility (`health_check.py`) inspects system readiness across required core dependencies and optional environment integrations before live demonstrations.

---

## 1. Running the Diagnostic Check

Execute from the project root in PowerShell or Command Prompt:

```powershell
python health_check.py
```

---

## 2. Expected Output (Clean Baseline)

```text
======================================================================
           NEXUSFLOW AI — PRE-DEMO HEALTH CHECK
======================================================================
Timestamp: Windows-10-10.0.26200-SP0 | Architecture: AMD64
----------------------------------------------------------------------

--- [ REQUIRED CORE DEPENDENCIES ] ---
[OK]     Database Connectivity: SQLite database integrity verified (7 tables present: workflows, agent_tasks, notifications, tool_configs, workspace_files, executions, schedules)
[OK]     Workspace Storage & Write Permissions: Workspace is writable at D:\projects\Automation\backend\workspace
[OK]     Browser Automation (Playwright): Playwright Chromium headless browser engine is installed and operational

--- [ OPTIONAL & ENVIRONMENT CAPABILITIES ] ---
[INFO]   Ollama LLM Engine: Ollama local LLM server is offline (Optional: Built-in heuristic fallback planner will be used)
[OK]     Windows Automation: Windows UIAutomation / pywinauto is initialized (0 window targets accessible)

======================================================================
SUMMARY: ALL CRITICAL PRE-DEMO CHECKS PASSED. Ready for demonstration.
======================================================================
```

---

## 3. Dependency Diagnostics & Troubleshooting

| Check Item | Type | Pass Condition | Troubleshooting Remediation |
| :--- | :--- | :--- | :--- |
| **Backend API** | Required (When active) | HTTP 200 on `/health` | Check `start_backend.bat` console for port conflicts on 8000 or missing Python packages. |
| **Frontend UI** | Required (When active) | HTTP 200 on `http://localhost:3000` | Verify `npm run build` succeeds and port 3000 is open. |
| **SQLite Database** | Required | `nexusflow.db` exists, integrity is `ok`, all 7 tables present. | Run `python backup_restore.py verify-isolated-restore` or restore from snapshot. |
| **Workspace Storage** | Required | Workspace folder writable, disk permissions valid. | Verify directory write permissions on `backend/workspace/`. |
| **Playwright Browser** | Required | Chromium headless launches and evaluates DOM. | Run `playwright install chromium` if browser binary is missing. |
| **Ollama Local LLM** | **Optional** | HTTP 200 on `http://127.0.0.1:11434/api/tags` | Optional: Launch Ollama (`ollama serve`). If offline, NexusFlow AI automatically falls back to its deterministic heuristic planner. |
| **Windows Automation** | **Optional** | Pywinauto/UIAutomation initializes desktop interface. | Enabled on Windows desktop sessions; operates in mock/restricted mode in non-interactive sessions. |

---

## 4. Security & Privacy Guarantee

* The health check script **never** outputs API keys, secrets, tokens, or private environment variables to stdout or log files.
* Network socket tests are strictly bound to local loopback addresses (`127.0.0.1`, `localhost`).
