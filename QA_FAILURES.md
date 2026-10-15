# NexusFlow AI — QA Failure & Defect Log

**Status as of Milestone 10 (Stable Release & Demo Packaging):**
All test suites (30 backend pytest units, Next.js 16 production build, real Playwright browser E2E, backup isolation tests, and automated smoke tests) are passing with **0 unresolved defects**.

---

## 1. Verified Fixes & Hardening in Milestone 10

### Issue QA-M10-01: Windows Startup Script Race Condition & Missing Port Conflict Handling
- **Severity:** Medium (Operational / Developer Experience)
- **Description:** Previous `.bat` launchers blindly spawned processes without checking if ports 8000/3000 were occupied, nor did they wait for HTTP health endpoints to respond before claiming platform readiness.
- **Fix Applied:** Upgraded `start_nexusflow.bat`, `start_backend.bat`, and `start_frontend.bat` with dependency detection (`where python`, `where npm`), port conflict detection (`netstat -ano`), health polling (`curl -s http://127.0.0.1:8000/health`), and provided a targeted shutdown utility (`stop_nexusflow.bat`).
- **Verification:** Verified through PowerShell execution runs and port inspection.

### Issue QA-M10-02: Live SQLite Copy Risk in Backup Procedures
- **Severity:** High (Data Integrity)
- **Description:** Traditional file copies of active SQLite databases during simultaneous read/write cycles risk corrupting the backed up copy due to journal/WAL tearing.
- **Fix Applied:** Built `backup_restore.py` leveraging Python's `sqlite3.Connection.backup()` online streaming API with mandatory `PRAGMA integrity_check;` validation.
- **Verification:** Verified via `python backup_restore.py verify-isolated-restore`.

### Issue QA-M10-03: Production Launch Mode for Next.js Web UI
- **Severity:** Medium (Deployment / Demo Stability)
- **Description:** Only development server (`npm run dev`) was configured in startup scripts, exposing demos to development overhead and recompilation delays.
- **Fix Applied:** Verified `npm run build` static compilation (15 static routes prerendered) and created `start_frontend_prod.bat` for serving optimized production artifacts via `next start`.

---

## 2. Unresolved Defects & Known Environment Limitations

* **Current Unresolved Defects:** **0**
* **Release Blockers:** **None**
* **Environment Caveats (Expected & Handled Gracefully):**
  1. *Ollama LLM Engine:* If Ollama is not installed or running on port 11434, NexusFlow AI gracefully degrades to its built-in rule-based heuristic planner.
  2. *Windows UIAutomation:* In headless CI or non-interactive sessions, Windows desktop UI interactions operate in fallback mode while all core API and workflow capabilities remain fully functional.
