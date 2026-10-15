# NexusFlow AI — Release Notes (v1.0.0 Stable Release)

**Release Version:** `v1.0.0-GA`  
**Release Date:** October 2026  
**Platform:** Windows 10 / Windows 11 (64-bit)  
**Authoritative Workspace:** `D:\projects\Automation`

---

## 1. Executive Summary

NexusFlow AI is a self-contained, enterprise-grade AI Workflow Automation platform engineered specifically for native Windows environments. It bridges visual workflow authoring (DAG orchestration), natural language agent task decomposition, web browser automation (Playwright), tabular data intelligence (DuckDB/Pandas/Excel), and desktop automation (pywinauto/UIAutomation) into a unified, privacy-first system.

Milestone 10 delivers full production stabilization, atomic online SQLite backup & disaster recovery, comprehensive pre-demo diagnostics, hardened Windows startup scripts, and complete verification across all sub-systems.

---

## 2. What's Included in this Release

### A. Core Engine & Orchestration
* **Visual Graph Execution:** High-performance topological execution runtime with step logging, branch condition routing, and cycle validation.
* **Autonomous Task Agent:** Multi-step agent planning with live execution streaming, tool selection, and fallback heuristic planning when external LLMs are offline.
* **Tabular & File Intelligence:** In-memory DuckDB SQL analytics, automated Excel/CSV anomaly detection, chart rendering (Matplotlib), and schema inspections.
* **Web & Desktop Automation:** Playwright Chromium headless engine with SSRF security boundary enforcement and sandboxed Windows application automation.
* **Persistent Task Scheduler:** Integrated cron/interval background scheduler backed by SQLite.

### B. Windows Startup & Lifecycle Hardening
* `start_nexusflow.bat`: Master Windows launcher with automated Python/Node dependency checks, health polling readiness, and conflict detection.
* `start_backend.bat`: Launches FastAPI / Uvicorn ASGI server with port conflict detection.
* `start_frontend.bat`: Launches Next.js development server.
* `start_frontend_prod.bat`: Serves optimized, prerendered Next.js production build (`next start`).
* `stop_nexusflow.bat`: Targeted process termination for ports 8000 and 3000 without affecting unrelated user programs.

### C. Backup, Recovery & Pre-Demo Tools
* `backup_restore.py`: Consistent, online SQLite database backup tool with `PRAGMA integrity_check` verification and non-destructive isolated restore validation (`verify-isolated-restore`).
* `health_check.py`: Pre-demo system diagnostic script checking DB integrity, storage write permissions, Playwright binaries, Ollama availability, and desktop automation.
* `smoke_test.py`: Standalone end-to-end smoke verification runner.

---

## 3. System Requirements & Prerequisites

* **Operating System:** Windows 10 21H2+ or Windows 11 (64-bit)
* **Python Runtime:** Python 3.11.x (with `pip`)
* **Node.js Runtime:** Node.js v20.x or v24.x (with `npm`)
* **Browser Engine:** Playwright Chromium (`python -m playwright install chromium`)
* **Database:** SQLite 3 (built into Python; zero external database setup required)
* **(Optional) Local LLM:** Ollama with `llama3.2` or `qwen2.5:7b` (built-in heuristic fallback planner active if omitted)

---

## 4. Known Limitations & Environment Handling

* **Secrets & Keys:** No credentials, API tokens, or secrets are bundled with the release.
* **Local Machine Isolation:** Database and workspace assets reside strictly within local project directories (`backend/data/` and `backend/workspace/`).
* **Non-Interactive Windows Sessions:** When running in headless environments without an interactive desktop session, Windows UI automation operates in restricted fallback mode while all core features remain fully available.
