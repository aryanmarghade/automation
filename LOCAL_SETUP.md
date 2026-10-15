# NexusFlow AI — Verified Local Windows Setup & Operations Guide

**Platform:** Windows 10 / Windows 11 (Native, x64)  
**Dependencies:** Python 3.10+, Node.js 18+, Playwright  
**Docker/WSL Required:** NO (100% Windows Native)

---

## 1. Prerequisites Installation

1. **Python 3.11:** Install from [python.org](https://www.python.org/) (ensure "Add Python to PATH" is checked).
2. **Node.js 18+:** Install LTS from [nodejs.org](https://nodejs.org/).
3. **Playwright Chromium:** Run `playwright install chromium` after setting up Python dependencies.

---

## 2. Quick Start Scripts

NexusFlow AI provides batch scripts in the project root for starting services:

### Option A: One-Click Startup (Recommended)
Double-click or run from PowerShell/CMD:
```powershell
.\start_nexusflow.bat
```
This automatically starts both the FastAPI backend on port 8000 and the Next.js frontend on port 3000 in separate console windows.

### Option B: Individual Service Startup

#### Backend Service (FastAPI + APScheduler + SQLite)
```powershell
cd D:\projects\Automation\backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend Dashboard (Next.js)
```powershell
cd D:\projects\Automation\frontend
npm run dev
```

Open your browser at `http://localhost:3000`.

---

## 3. Running Automated Verification Tests

### Run Backend Unit & Integration Tests:
```powershell
cd D:\projects\Automation\backend
python -m pytest tests\ -v
```

### Run Frontend Production Build Check:
```powershell
cd D:\projects\Automation\frontend
npm run build
```

---

## 4. Troubleshooting & FAQ

- **Port 8000 in use:** Check if another uvicorn instance is running with `netstat -ano | findstr :8000` and terminate the PID.
- **Ollama Status:** If Ollama is not installed or running, NexusFlow automatically falls back to its deterministic heuristic ReAct planner without errors. To enable real local LLM inference, install Ollama from [ollama.com](https://ollama.com) and run `ollama run llama3.2`.
- **Database Location:** All data is safely stored in `backend/data/nexusflow.db`. Do not manually delete this file unless you intend to reset the platform state.
