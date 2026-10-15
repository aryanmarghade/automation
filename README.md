# NexusFlow AI — User & Architecture Manual

NexusFlow AI is a native Windows 11, local-first AI agent and visual workflow automation platform combining an autonomous ReAct loop, n8n-style visual DAG canvas, and real desktop tools (Excel/CSV analysis, PDF citation intelligence, Playwright browser search, and Windows UIAutomation).

---

## 1. Quick Start Guide (Windows 11)

### Double-Click Launch:
Simply double-click [start_nexusflow.bat](file:///d:/projects/Automation/start_nexusflow.bat) in the project root to start both backend and frontend servers in separate console windows.

### Manual Console Commands:
- **Backend (FastAPI + SQLite)**:
  ```powershell
  cd d:\projects\Automation\backend
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Frontend (Next.js + React Flow)**:
  ```powershell
  cd d:\projects\Automation\frontend
  npm run dev
  ```
- **Access Endpoints**:
  - Web UI: `http://localhost:3000`
  - Backend API & Interactive Docs: `http://127.0.0.1:8000/docs`

---

## 2. Core Operational Modes

### Mode A: Autonomous AI Agent
1. Navigate to `/agent`.
2. Select your autonomy level:
   - **Supervised**: Plans steps and waits for your confirmation.
   - **Autonomous**: Formulates plan and immediately executes the tool chain.
   - **Assist**: Pauses and gates higher-risk actions.
3. Type any natural language objective (e.g. *"Analyze test_sales.csv, detect anomalies, and generate a category revenue chart"*).
4. The agent will formulate a plan, execute the tool pipeline, and return real deliverables and telemetry.

### Mode B: Visual Workflow Builder
1. Navigate to `/builder`.
2. Drag or click any node from the **Available Nodes** palette (Manual Trigger, Tabular Analyzer, PDF Analyzer, Browser, Condition, HTTP).
3. Connect ports to form your DAG pipeline.
4. Click **Execute DAG** to validate graph connectivity and run topological execution.
5. Save workflows into the persistent SQLite library for reuse or inspection.

---

## 3. Tool Capabilities

- **Spreadsheets & Tabular Data (`excel_tabular_analyzer`)**:
  - Reads `.xlsx`, `.xls`, and `.csv`.
  - Statistical summaries, duplicate detection, and Z-score outlier detection.
  - In-memory SQL queries via DuckDB.
  - PNG chart generation with Matplotlib.
- **PDF Documents (`pdf_document_analyzer`)**:
  - Metadata inspection, multi-page text extraction, table extraction via `pdfplumber`, keyword citation references.
- **Browser & Search (`browser_playwright`)**:
  - DuckDuckGo research queries, live DOM text parsing and HTML cleanup.
- **Windows Automation (`windows_desktop_automation`)**:
  - Host hardware metrics, running process/window inspection via `pywinauto`, whitelisted app launcher.

---

## 4. Automated Tests
Run pytest in the backend directory to verify all subsystems:
```powershell
cd d:\projects\Automation\backend
python -m pytest
```
