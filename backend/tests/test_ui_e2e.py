import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from pathlib import Path
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_full_system_api_routes_and_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # 2. Tools list
        tools_resp = await client.get("/api/v1/tools")
        assert tools_resp.status_code == 200
        tools = tools_resp.json()
        assert len(tools) >= 5
        tool_ids = [t["id"] for t in tools]
        assert "browser_playwright" in tool_ids
        assert "windows_desktop_automation" in tool_ids
        assert "pdf_document_analyzer" in tool_ids
        assert "excel_tabular_analyzer" in tool_ids

        # 3. Workflows CRUD
        wf_payload = {
            "name": "E2E Automated Test Workflow",
            "description": "Created for E2E journey verification",
            "nodes": [
                {"id": "t1", "type": "trigger_manual", "position": {"x": 0, "y": 0}, "data": {}},
                {"id": "t2", "type": "data_transform", "position": {"x": 100, "y": 0}, "data": {"input_data": {"val": 50}, "operation": "sum_values", "keys": "val"}}
            ],
            "edges": [{"id": "e1-2", "source": "t1", "target": "t2"}],
            "is_active": True
        }
        create_wf = await client.post("/api/v1/workflows", json=wf_payload)
        assert create_wf.status_code == 200
        wf_data = create_wf.json()
        wf_id = wf_data["id"]

        # Validate DAG
        val_resp = await client.post("/api/v1/workflows/validate", json={"nodes": wf_payload["nodes"], "edges": wf_payload["edges"]})
        assert val_resp.status_code == 200
        assert val_resp.json()["is_valid"] is True

        # Run workflow
        run_resp = await client.post(f"/api/v1/workflows/{wf_id}/run", json={"inputs": {}})
        assert run_resp.status_code == 200
        exec_data = run_resp.json()
        assert exec_data["status"] == "completed"

        # 4. Schedules lifecycle
        sched_payload = {
            "workflow_id": wf_id,
            "name": "E2E Test Schedule",
            "schedule_type": "interval",
            "interval_seconds": 1800,
            "is_active": True
        }
        create_sched = await client.post("/api/v1/schedules", json=sched_payload)
        assert create_sched.status_code == 200
        sched_id = create_sched.json()["id"]

        # Pause and resume schedule
        pause_resp = await client.post(f"/api/v1/schedules/{sched_id}/pause")
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"

        resume_resp = await client.post(f"/api/v1/schedules/{sched_id}/resume")
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "resumed"

        # Delete schedule
        del_sched = await client.delete(f"/api/v1/schedules/{sched_id}")
        assert del_sched.status_code == 200

        # Clean up workflow
        del_wf = await client.delete(f"/api/v1/workflows/{wf_id}")
        assert del_wf.status_code == 200

        # 5. Agent plan and execute
        plan_resp = await client.post("/api/v1/agent/plan", json={
            "objective": "Summarize financial numbers and extract spreadsheet anomalies",
            "attached_files": [],
            "model_provider": "ollama",
            "model_name": "llama3.2:latest"
        })
        assert plan_resp.status_code == 200
        plan = plan_resp.json()
        assert "steps" in plan
        assert len(plan["steps"]) >= 1

        # 6. Notifications
        notif_resp = await client.get("/api/v1/notifications")
        assert notif_resp.status_code == 200
        assert isinstance(notif_resp.json(), list)

        # 7. Workspace files
        files_resp = await client.get("/api/v1/workspace/files")
        assert files_resp.status_code == 200
        assert isinstance(files_resp.json(), list)

@pytest.mark.asyncio
async def test_journey_file_intelligence_and_sql_query():
    # Create disposable test CSV
    csv_file = settings.WORKSPACE_DIR / "disposable_test_metrics.csv"
    csv_file.write_text("category,revenue,units\nAlpha,100,5\nBeta,200,10\nAlpha,150,8\n", encoding="utf-8")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Query spreadsheet with DuckDB SQL via tools API
        res = await client.post("/api/v1/tools/excel_tabular_analyzer/test", json={
            "operation": "query_sql",
            "file_path": str(csv_file),
            "sql_query": "SELECT category, SUM(revenue) AS total_rev FROM df GROUP BY category ORDER BY total_rev DESC"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["is_success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["category"] == "Alpha"
        assert data["data"][0]["total_rev"] == 250

@pytest.mark.asyncio
async def test_journey_browser_research_and_desktop_inspection():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Browser research action
        browser_res = await client.post("/api/v1/tools/browser_playwright/test", json={
            "action": "research_topic",
            "query": "Autonomous Agent Systems"
        })
        assert browser_res.status_code == 200
        b_data = browser_res.json()
        assert b_data["is_success"] is True
        assert len(b_data["sources_consulted"]) > 0

        # Desktop system metrics
        desktop_res = await client.post("/api/v1/tools/windows_desktop_automation/test", json={
            "action": "get_system_info"
        })
        assert desktop_res.status_code == 200
        d_data = desktop_res.json()
        assert d_data["is_success"] is True
        assert "cpu_count" in d_data

