# NexusFlow AI — Release & Operational Checklist

This checklist defines the operational verification steps required prior to running NexusFlow AI in production or presentation environments on Windows.

---

## 1. System Requirements & Prerequisites

- [x] **Operating System:** Windows 10/11 64-bit
- [x] **Python Runtime:** Python 3.11+ installed and available on PATH
- [x] **Node.js Runtime:** Node.js v20+ with npm installed
- [x] **Browser Engine:** Playwright Chromium binaries installed (`playwright install chromium`)
- [x] **Database:** SQLite 3 (stored locally in `backend/backend/data/nexusflow.db`)
- [x] **Workspace:** Persistent workspace active in `backend/workspace/`
- [ ] *(Optional)* **Local LLM Engine:** Ollama running on `http://localhost:11434` with model `llama3.2` or fallback planner enabled

---

## 2. Pre-Demo Diagnostics & Backup

- [x] **Run Health Check:** `python health_check.py` (all core checks pass).
- [x] **Verify Isolated Restore:** `python backup_restore.py verify-isolated-restore` (passes without affecting live DB).
- [x] **Create Release Snapshot:** `python backup_restore.py backup --name pre_demo_snapshot`.

---

## 3. Platform Launch Procedure

- [x] **Development Mode Launch:** Run `start_nexusflow.bat` (launches backend and dev UI).
- [x] **Production Mode Launch:** Run `start_frontend_prod.bat` (serves optimized Next.js static build on port 3000).
- [x] **Backend Service:** Verify `http://127.0.0.1:8000/health` returns status `healthy`.
- [x] **Frontend Interface:** Verify `http://localhost:3000` loads dashboard.

---

## 4. Acceptance Smoke Test Run

Execute the end-to-end smoke verification script:
```powershell
python smoke_test.py
```
- [x] Step 1: Agent Task Planning (Heuristic / Ollama)
- [x] Step 2: DAG Validation & Runtime Execution
- [x] Step 3: File Intelligence & Tabular Inspection
- [x] Step 4: Schedule Creation & DB Persistence
- [x] Step 5: History & Artifact Generation
- [x] Step 6: Optional Integrations State Verification

---

## 5. Graceful Teardown & Process Cleanup

- [x] Run `stop_nexusflow.bat` to cleanly terminate backend (port 8000) and frontend (port 3000) processes without terminating unrelated system programs.
- [x] Verify no orphaned browser or background tasks remain.
- [x] Confirm database records and user files remain completely intact.
