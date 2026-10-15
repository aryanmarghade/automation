import pytest
import asyncio
from app.agent.orchestrator import AgentOrchestrator, AgentExecutionState
from app.tools.core_tools import register_core_tools
from app.tools.excel_tool import ExcelAnalysisTool
from app.tools.pdf_tool import PDFDocumentTool
from app.tools.browser_tool import BrowserAutomationTool
from app.tools.registry import registry

register_core_tools()
registry.register(ExcelAnalysisTool())
registry.register(PDFDocumentTool())
registry.register(BrowserAutomationTool())

@pytest.mark.asyncio
async def test_agent_planning_and_tool_selection():
    orchestrator = AgentOrchestrator()
    # Planning with Excel file target
    plan = await orchestrator.create_plan(
        objective="Analyze quarterly sales from test_sales.csv and make a bar chart",
        attached_files=["test_sales.csv"]
    )
    assert "steps" in plan
    assert len(plan["steps"]) >= 2
    step_tools = [s["tool_id"] for s in plan["steps"]]
    assert "excel_tabular_analyzer" in step_tools

@pytest.mark.asyncio
async def test_agent_execution_and_artifact_streaming():
    orchestrator = AgentOrchestrator()
    plan = {
        "objective": "Inspect test_sales.csv and compute metrics",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "excel_tabular_analyzer",
                "description": "Inspect test_sales.csv",
                "parameters": {"file_path": "test_sales.csv", "operation": "inspect"}
            },
            {
                "step_id": "step_2",
                "tool_id": "excel_tabular_analyzer",
                "description": "Summary stats for test_sales.csv",
                "parameters": {"file_path": "test_sales.csv", "operation": "summary_stats"}
            }
        ]
    }

    state = AgentExecutionState(task_id="test_task_stream", plan=plan, autonomy_level="autonomous")
    events = []
    async for event in orchestrator.execute_task_stream(state):
        events.append(event)

    assert state.status == "completed"
    assert len(state.steps_history) == 2
    event_types = [e.get("type") for e in events]
    assert "step_start" in event_types
    assert "step_completed" in event_types
    assert "completed" in event_types

@pytest.mark.asyncio
async def test_agent_cancellation():
    orchestrator = AgentOrchestrator()
    plan = {
        "objective": "Long running test",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "excel_tabular_analyzer",
                "description": "Inspect test_sales.csv",
                "parameters": {"file_path": "test_sales.csv", "operation": "inspect"}
            },
            {
                "step_id": "step_2",
                "tool_id": "excel_tabular_analyzer",
                "description": "Summary stats for test_sales.csv",
                "parameters": {"file_path": "test_sales.csv", "operation": "summary_stats"}
            }
        ]
    }
    state = AgentExecutionState(task_id="test_cancel", plan=plan, autonomy_level="autonomous")
    
    # Cancel task immediately
    state.cancel()

    events = []
    async for event in orchestrator.execute_task_stream(state):
        events.append(event)

    assert state.status == "cancelled"

@pytest.mark.asyncio
async def test_plan_to_workflow_conversion():
    plan = {
        "objective": "Analyze spreadsheet",
        "steps": [
            {
                "step_id": "step_1",
                "tool_id": "excel_tabular_analyzer",
                "parameters": {"file_path": "test_sales.csv", "operation": "inspect"}
            }
        ]
    }
    wf = AgentOrchestrator.plan_to_visual_workflow(plan, "Converted Test Workflow")
    assert len(wf["nodes"]) == 2 # 1 trigger + 1 tool node
    assert len(wf["edges"]) == 1
    assert wf["nodes"][0]["type"] == "trigger_manual"
    assert wf["nodes"][1]["type"] == "excel_tabular_analyzer"
