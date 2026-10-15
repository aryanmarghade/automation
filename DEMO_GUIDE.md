# NexusFlow AI — Live Presentation & College Demonstration Guide

This guide provides a structured, 5–10 minute live demonstration plan for **NexusFlow AI** on Windows 11 using clean, disposable inputs and zero pre-fabricated data.

---

## 0. Prerequisites & Quick Startup (30 Seconds)

1. Open PowerShell or Command Prompt at the project root (`D:\projects\Automation`).
2. Run the master launcher:
   ```bat
   start_nexusflow.bat
   ```
3. Open Google Chrome or Microsoft Edge at **`http://localhost:3000`**.
4. Confirm the system status badge in the top bar displays **"System Online"** (connected to `http://127.0.0.1:8000`).

---

## Step 1: Visual DAG Workflow Builder (2 Minutes)

- **Page to Open:** `http://localhost:3000/builder`
- **Action to Perform:**
  1. Observe the pre-loaded DAG workflow on the React Flow canvas (Trigger Node $\to$ Python Step $\to$ DuckDB Query $\to$ Output Artifact).
  2. Click the **"Validate Graph"** button in the top canvas toolbar.
  3. Observe the validation banner confirming: `DAG Valid: No cycles detected. All 4 dependencies resolved.`
- **Expected Observable Result:**
  - Real-time graph validation response directly from `/api/workflows/validate`.
  - Node connection lines pulse with status indicators.

---

## Step 2: Natural-Language AI Agent & Task Execution (2 Minutes)

- **Page to Open:** `http://localhost:3000/agent`
- **Action to Perform:**
  1. In the prompt box, type:
     ```text
     Inspect system performance, list open windows, and extract top research topics.
     ```
  2. Click **"Run Task"** (or press Enter).
- **Expected Observable Result:**
  - Streamed plan generation showing step decomposition.
  - Interactive tool execution feed displaying results from Windows system telemetry and browser tools.
  - Final structured task report generated and displayed in the terminal UI.
- **Fallback Note:**
  - If local Ollama is running (`http://localhost:11434`), LLM streaming will run against the configured model. If offline, the built-in deterministic `FallbackPlanner` seamlessly produces the structured plan.

---

## Step 3: File Intelligence & DuckDB SQL Analytics (2 Minutes)

- **Page to Open:** `http://localhost:3000/files`
- **Action to Perform:**
  1. Click on `sample_data.csv` in the workspace explorer.
  2. Enter a SQL query in the query box:
     ```sql
     SELECT department, AVG(salary) AS avg_sal, COUNT(*) AS headcount FROM sample_data GROUP BY department ORDER BY avg_sal DESC
     ```
  3. Click **"Execute Query"**.
- **Expected Observable Result:**
  - Instant tabular SQL query results rendered without page reload.
  - Column schema, null checks, and anomaly summary visible in the inspector panel.

---

## Step 4: Persistent Workflow Scheduler (1.5 Minutes)

- **Page to Open:** `http://localhost:3000/scheduler`
- **Action to Perform:**
  1. Click **"+ New Schedule"**.
  2. Enter:
     - Name: `Hourly System Health Check`
     - Interval: `60 minutes`
     - Workflow: Select `System Audit`
  3. Click **"Create Schedule"**.
  4. Toggle **Pause / Resume** on the newly created schedule.
- **Expected Observable Result:**
  - Real SQLite persistence via APScheduler backend.
  - Next-run time calculation and active status badge update instantly.

---

## Step 5: Audit Logs & Security Controls (1 Minute)

- **Page to Open:** `http://localhost:3000/history` and `http://localhost:3000/security`
- **Action to Perform:**
  1. View the execution run history table on `/history` showing timestamps, execution IDs, and status.
  2. Navigate to `/security` to inspect the whitelist of allowed Windows executables (Notepad, Calculator, Explorer, Edge) and active sandbox policies.
- **Expected Observable Result:**
  - Complete, verifiable audit trail of all previous demonstration steps.
