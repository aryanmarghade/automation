import asyncio
import json
import sqlite3
import datetime
from pathlib import Path
import httpx

BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR / "backend" / "workspace"
DB_PATH = BASE_DIR / "backend" / "backend" / "data" / "nexusflow.db"

async def run_smoke_test():
    print("=" * 70)
    print("       NEXUSFLOW AI — END-TO-END DEMO SMOKE TEST")
    print("=" * 70)
    
    results = {}
    
    # 0. Ensure Tools are registered
    import app.tools.init_tools
    
    # 1. Backend Direct Engine Tests
    print("\n[Step 1] Submitting Agent Task via Direct Orchestrator...")
    from app.agent.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    smoke_task_prompt = "SMOKE_TEST: Analyze disposable sample file test_records.csv and calculate budget summaries."
    
    plan = await orchestrator.create_plan(smoke_task_prompt)
    print(f"  Plan created: {plan.get('title', 'Heuristic Plan')} ({len(plan.get('steps', []))} steps)")
    assert len(plan.get("steps", [])) > 0, "Agent failed to create plan"
    results["agent_planning"] = "PASS"
    
    # 2. Workflow Validation and Execution
    print("\n[Step 2] Validating and Executing a Simple Workflow...")
    from app.engine.dag_validator import DAGValidator
    from app.engine.runtime import WorkflowRuntime
    from app.schemas.workflow import WorkflowNode, WorkflowEdge, NodePosition
    
    test_nodes = [
        WorkflowNode(
            id="node_1", 
            type="trigger_manual", 
            position=NodePosition(x=100.0, y=100.0), 
            data={"payload": {"source_file": "test_records.csv"}}
        ),
        WorkflowNode(
            id="node_2", 
            type="excel_tabular_analyzer", 
            position=NodePosition(x=350.0, y=100.0), 
            data={"file_path": "test_records.csv", "operation": "inspect"}
        )
    ]
    test_edges = [WorkflowEdge(id="e1-2", source="node_1", target="node_2")]
    
    validator = DAGValidator()
    val_res = validator.validate(test_nodes, test_edges)
    assert val_res.is_valid is True, f"DAG validation failed: {val_res}"
    print(f"  DAG Validation: VALID (Execution Order: {val_res.execution_order})")
    
    runtime = WorkflowRuntime("smoke_exec_001", test_nodes, test_edges)
    exec_res = await runtime.run()
    assert exec_res["status"] == "completed", f"Execution failed: {exec_res}"
    print(f"  Execution Status: {exec_res['status']} ({len(exec_res['node_states'])} step(s) executed successfully in {exec_res['duration_ms']}ms)")
    results["workflow_execution"] = "PASS"
    
    # 3. File Intelligence & Analysis on disposable sample
    print("\n[Step 3] Analyzing Disposable Sample File...")
    from app.tools.excel_tool import ExcelAnalysisTool
    excel_tool = ExcelAnalysisTool()
    sample_file = WORKSPACE_DIR / "test_records.csv"
    intel_res = await excel_tool.execute({"operation": "summary_stats", "file_path": "test_records.csv"})
    assert "error" not in intel_res, f"File inspection failed: {intel_res}"
    print(f"  File inspection columns: {intel_res.get('columns')} (Rows: {intel_res.get('total_rows')})")
    results["file_intelligence"] = "PASS"
    
    # 4. Short-lived Scheduler Creation & Verification
    print("\n[Step 4] Creating & Triggering a Short-Lived Schedule...")
    from app.services.scheduler_service import SchedulerManager
    from app.models.entities import Schedule
    from app.core.database import AsyncSessionLocal
    from sqlalchemy.future import select
    
    smoke_sched_id = f"smoke_sched_{int(datetime.datetime.now().timestamp())}"
    async with AsyncSessionLocal() as session:
        sched = Schedule(
            id=smoke_sched_id,
            name="Smoke Test Schedule",
            workflow_id="smoke_wf_001",
            cron_expression="* * * * *",
            is_active=False
        )
        session.add(sched)
        await session.commit()
        
        # Verify in DB
        verify_query = await session.execute(select(Schedule).where(Schedule.id == smoke_sched_id))
        found_sched = verify_query.scalar_one_or_none()
        assert found_sched is not None, "Failed to persist schedule"
        print(f"  Schedule created and verified in DB: {found_sched.id}")
        
        # Cleanup schedule immediately to keep live DB clean
        await session.delete(found_sched)
        await session.commit()
        print("  Cleaned up smoke schedule record.")
    results["scheduler"] = "PASS"
    
    # 5. Inspection of Execution History & Workspace Artifacts
    print("\n[Step 5] Verifying Artifacts and Execution Logs...")
    assert sample_file.exists(), "Sample test file missing"
    step_2_output = exec_res["node_states"].get("node_2", {}).get("output", {})
    assert "columns" in step_2_output or "rows" in step_2_output, f"Unexpected node_2 output: {step_2_output}"
    print(f"  Step 2 Inspection Output Verified (Columns: {step_2_output.get('columns')}, Rows: {step_2_output.get('rows')})")
    results["artifacts_and_history"] = "PASS"
    
    # 6. Optional Integrations Reporting Status
    print("\n[Step 6] Verifying Optional Integrations Status...")
    from health_check import check_ollama, check_windows_automation
    ollama_status, ollama_note = check_ollama()
    win_status, win_note = check_windows_automation()
    print(f"  Ollama Status: {'Active' if ollama_status else 'Offline / Fallback Heuristics Active'} ({ollama_note})")
    print(f"  Windows Desktop Automation: {'Active' if win_status else 'Restricted / Non-Interactive'} ({win_note})")
    results["optional_integrations"] = "PASS"
    
    print("\n" + "=" * 70)
    print("              ALL SMOKE TEST STEPS PASSED SUCCESSFULLY")
    print("=" * 70)
    for k, v in results.items():
        print(f"  {k:<30}: {v}")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(BASE_DIR / "backend"))
    asyncio.run(run_smoke_test())
