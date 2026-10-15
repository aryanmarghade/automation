from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
import shutil
from pathlib import Path
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import Workflow, Execution, AgentTask, Schedule, ToolConfig, WorkspaceFile, Notification
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    ExecutionRequest, ExecutionResponse, WorkflowValidationResponse,
    WorkflowValidationRequest
)
from app.engine.dag_validator import DAGValidator
from app.engine.runtime import WorkflowRuntime
from app.tools.registry import registry
from app.agent.orchestrator import AgentOrchestrator
from app.services.ai_provider import OllamaProvider
from app.services.scheduler_service import SchedulerManager

api_router = APIRouter()

# ----------------- WORKFLOW ENDPOINTS -----------------

@api_router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).order_by(Workflow.updated_at.desc()))
    return result.scalars().all()

@api_router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(payload: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    wf = Workflow(
        name=payload.name,
        description=payload.description,
        nodes=[n.dict() for n in payload.nodes],
        edges=[e.dict() for e in payload.edges],
        viewport=payload.viewport,
        is_active=payload.is_active,
        tags=payload.tags
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf

@api_router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@api_router.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, payload: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if payload.name is not None: wf.name = payload.name
    if payload.description is not None: wf.description = payload.description
    if payload.nodes is not None: wf.nodes = [n.dict() for n in payload.nodes]
    if payload.edges is not None: wf.edges = [e.dict() for e in payload.edges]
    if payload.viewport is not None: wf.viewport = payload.viewport
    if payload.is_active is not None: wf.is_active = payload.is_active
    if payload.tags is not None: wf.tags = payload.tags
    
    await db.commit()
    await db.refresh(wf)
    return wf

@api_router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    await db.delete(wf)
    await db.commit()
    return {"status": "deleted", "id": workflow_id}

@api_router.post("/workflows/validate", response_model=WorkflowValidationResponse)
async def validate_workflow(payload: WorkflowValidationRequest):
    return DAGValidator.validate(payload.nodes, payload.edges)

# ----------------- EXECUTION ENDPOINTS -----------------

@api_router.post("/workflows/{workflow_id}/run")
async def run_workflow(workflow_id: str, payload: ExecutionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    wf = result.scalar_one_or_none()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Instantiate Execution in DB
    exec_record = Execution(
        workflow_id=wf.id,
        mode="workflow",
        status="running",
        trigger_type=payload.trigger_type,
        inputs=payload.inputs,
        logs=[]
    )
    db.add(exec_record)
    await db.commit()
    await db.refresh(exec_record)

    from app.schemas.workflow import WorkflowNode, WorkflowEdge
    nodes = [WorkflowNode(**n) for n in wf.nodes]
    edges = [WorkflowEdge(**e) for e in wf.edges]

    runtime = WorkflowRuntime(
        execution_id=exec_record.id,
        nodes=nodes,
        edges=edges,
        initial_inputs=payload.inputs
    )
    
    run_result = await runtime.run()

    # Update execution record
    exec_record.status = run_result["status"]
    exec_record.outputs = run_result.get("outputs", {})
    exec_record.error = run_result.get("error")
    exec_record.node_states = run_result.get("node_states", {})
    exec_record.logs = run_result.get("logs", [])
    exec_record.duration_ms = run_result.get("duration_ms")
    exec_record.finished_at = datetime.utcnow()
    
    # Record notification
    notif = Notification(
        title=f"Workflow {exec_record.status.capitalize()}: {wf.name}",
        message=f"Completed in {exec_record.duration_ms}ms" if exec_record.status == "completed" else f"Error: {exec_record.error}",
        level="success" if exec_record.status == "completed" else "error",
        category="workflow",
        resource_id=exec_record.id
    )
    db.add(notif)

    await db.commit()
    await db.refresh(exec_record)
    return exec_record

@api_router.get("/executions", response_model=List[ExecutionResponse])
async def list_executions(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Execution).order_by(Execution.started_at.desc()).limit(limit))
    return result.scalars().all()

@api_router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    exec_record = result.scalar_one_or_none()
    if not exec_record:
        raise HTTPException(status_code=404, detail="Execution not found")
    return exec_record

@api_router.post("/executions/{execution_id}/retry")
async def retry_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Execution).where(Execution.id == execution_id))
    prev_exec = result.scalar_one_or_none()
    if not prev_exec:
        raise HTTPException(status_code=404, detail="Execution record not found")
    
    # Run new execution retry
    return await run_workflow(
        workflow_id=prev_exec.workflow_id,
        payload=ExecutionRequest(trigger_type="retry", inputs=prev_exec.inputs or {}),
        db=db
    )

# ----------------- SCHEDULER ENDPOINTS -----------------

@api_router.get("/schedules")
async def list_schedules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Schedule).order_by(Schedule.created_at.desc()))
    return result.scalars().all()

@api_router.post("/schedules")
async def create_schedule(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    workflow_id = payload.get("workflow_id")
    wf_res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    if not wf_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Referenced workflow does not exist")

    schedule = Schedule(
        workflow_id=workflow_id,
        name=payload.get("name", "New Schedule"),
        cron_expression=payload.get("cron_expression"),
        interval_seconds=payload.get("interval_seconds"),
        schedule_type=payload.get("schedule_type", "recurring"),
        timezone=payload.get("timezone", "UTC"),
        is_active=payload.get("is_active", True)
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    # Register in APScheduler
    SchedulerManager.get_instance()._register_job(schedule)
    await db.commit()
    return schedule

@api_router.post("/schedules/{schedule_id}/pause")
async def pause_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    sched.is_active = False
    SchedulerManager.get_instance().remove_schedule_job(schedule_id)
    await db.commit()
    return {"status": "paused", "id": schedule_id}

@api_router.post("/schedules/{schedule_id}/resume")
async def resume_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    sched.is_active = True
    SchedulerManager.get_instance()._register_job(sched)
    await db.commit()
    return {"status": "resumed", "id": schedule_id}

@api_router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
    sched = res.scalar_one_or_none()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    SchedulerManager.get_instance().remove_schedule_job(schedule_id)
    await db.delete(sched)
    await db.commit()
    return {"status": "deleted", "id": schedule_id}

# ----------------- NOTIFICATIONS ENDPOINTS -----------------

@api_router.get("/notifications")
async def list_notifications(limit: int = 30, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Notification).order_by(Notification.created_at.desc()).limit(limit))
    return res.scalars().all()

@api_router.post("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Notification).where(Notification.id == notif_id))
    notif = res.scalar_one_or_none()
    if notif:
        notif.is_read = True
        await db.commit()
    return {"status": "marked_read"}

@api_router.delete("/notifications")
async def clear_all_notifications(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    await db.execute(delete(Notification))
    await db.commit()
    return {"status": "cleared"}

# ----------------- TOOL REGISTRY & INTEGRATION ENDPOINTS -----------------

@api_router.get("/tools")
async def get_tool_registry():
    return registry.list_tools()

@api_router.post("/tools/{tool_id}/test")
async def test_tool(tool_id: str, params: Dict[str, Any] = None):
    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return await tool.execute(params or {})

# ----------------- AI AGENT ORCHESTRATION ENDPOINTS -----------------

@api_router.post("/agent/plan")
async def plan_agent_task(payload: Dict[str, Any]):
    objective = payload.get("objective", "")
    attached_files = payload.get("attached_files", [])
    model_provider = payload.get("model_provider", "ollama")
    model_name = payload.get("model_name", "llama3.2:latest")

    orchestrator = AgentOrchestrator(model_provider=model_provider, model_name=model_name)
    plan = await orchestrator.create_plan(objective, attached_files)
    return plan

@api_router.post("/agent/execute")
async def execute_agent_task(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    objective = payload.get("objective", "")
    plan = payload.get("plan", {})
    autonomy_level = payload.get("autonomy_level", "supervised")
    model_provider = payload.get("model_provider", "ollama")
    model_name = payload.get("model_name", "llama3.2:latest")

    task = AgentTask(
        objective=objective,
        status="executing",
        autonomy_level=autonomy_level,
        model_provider=model_provider,
        model_name=model_name,
        plan=plan.get("steps", [])
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    from app.agent.orchestrator import AgentExecutionState, AgentTaskManager
    state = AgentExecutionState(task_id=task.id, plan=plan, autonomy_level=autonomy_level)
    AgentTaskManager.register(state)

    orchestrator = AgentOrchestrator(model_provider=model_provider, model_name=model_name)
    
    # Run full stream collecting results
    async for event in orchestrator.execute_task_stream(state):
        pass

    task.status = state.status
    task.steps_history = state.steps_history
    task.artifacts = state.artifacts
    task.final_summary = f"Executed {len(state.steps_history)} steps. Generated {len(state.artifacts)} artifacts."

    await db.commit()
    await db.refresh(task)
    return task

@api_router.post("/agent/tasks/{task_id}/pause")
async def pause_agent_task(task_id: str):
    from app.agent.orchestrator import AgentTaskManager
    state = AgentTaskManager.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active task not found")
    state.pause()
    return {"status": "paused", "task_id": task_id}

@api_router.post("/agent/tasks/{task_id}/resume")
async def resume_agent_task(task_id: str):
    from app.agent.orchestrator import AgentTaskManager
    state = AgentTaskManager.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active task not found")
    state.resume()
    return {"status": "resumed", "task_id": task_id}

@api_router.post("/agent/tasks/{task_id}/cancel")
async def cancel_agent_task(task_id: str):
    from app.agent.orchestrator import AgentTaskManager
    state = AgentTaskManager.get(task_id)
    if not state:
        raise HTTPException(status_code=404, detail="Active task not found")
    state.cancel()
    return {"status": "cancelled", "task_id": task_id}

@api_router.post("/agent/plan/convert-to-workflow")
async def convert_plan_to_workflow(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    plan = payload.get("plan", {})
    name = payload.get("workflow_name", "Generated Agent Workflow")
    
    from app.agent.orchestrator import AgentOrchestrator
    wf_dict = AgentOrchestrator.plan_to_visual_workflow(plan, workflow_name=name)
    
    wf = Workflow(
        name=wf_dict["name"],
        description=wf_dict["description"],
        nodes=wf_dict["nodes"],
        edges=wf_dict["edges"],
        is_active=True,
        tags=wf_dict.get("tags", [])
    )
    db.add(wf)
    await db.commit()
    await db.refresh(wf)
    return wf

@api_router.get("/agent/tasks")
async def list_agent_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AgentTask).order_by(AgentTask.created_at.desc()).limit(30))
    return result.scalars().all()

# ----------------- AI MODELS DISCOVERY -----------------

@api_router.get("/ai/models")
async def get_ai_models():
    ollama = OllamaProvider()
    models = await ollama.list_models()
    return {"ollama_models": models}

# ----------------- FILE WORKSPACE ENDPOINTS -----------------

@api_router.get("/workspace/files")
async def list_workspace_files():
    files = []
    for f in settings.WORKSPACE_DIR.glob("*.*"):
        files.append({
            "name": f.name,
            "path": str(f),
            "size_bytes": f.stat().st_size,
            "extension": f.suffix.lower()
        })
    return files

@api_router.post("/workspace/upload")
async def upload_file(file: UploadFile = File(...)):
    dest = settings.WORKSPACE_DIR / file.filename
    with open(dest, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "filename": file.filename,
        "size_bytes": dest.stat().st_size,
        "path": str(dest)
    }
