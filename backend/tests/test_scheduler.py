import pytest
import asyncio
from datetime import datetime
from app.models.entities import Workflow, Schedule, Execution
from app.services.scheduler_service import SchedulerManager, execute_scheduled_workflow_job
from app.core.database import AsyncSessionLocal, engine, Base
from sqlalchemy.future import select
import app.tools.init_tools

@pytest.mark.asyncio
async def test_scheduler_lifecycle_and_job_execution():
    # Ensure database tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Create test workflow
        wf = Workflow(
            name="Scheduled Test Workflow",
            nodes=[
                {"id": "t1", "type": "trigger_manual", "position": {"x": 0, "y": 0}, "data": {}},
                {"id": "t2", "type": "data_transform", "position": {"x": 100, "y": 0}, "data": {"input_data": {"count": 42}, "operation": "pick_keys", "keys": "count"}}
            ],
            edges=[{"id": "e1-2", "source": "t1", "target": "t2"}],
            is_active=True
        )
        db.add(wf)
        await db.commit()
        await db.refresh(wf)

        # 2. Create test schedule
        sched = Schedule(
            workflow_id=wf.id,
            name="Hourly Test Schedule",
            interval_seconds=3600,
            schedule_type="interval",
            is_active=True
        )
        db.add(sched)
        await db.commit()
        await db.refresh(sched)

        # 3. Test APScheduler registration
        mgr = SchedulerManager.get_instance()
        mgr._register_job(sched)
        
        job_id = f"schedule_{sched.id}"
        job = mgr.scheduler.get_job(job_id)
        assert job is not None
        assert job.name == "Hourly Test Schedule"

        # 4. Trigger direct execution of scheduled workflow callback
        await execute_scheduled_workflow_job(sched.id, wf.id)

        # 5. Verify Execution record created in SQLite
        exec_res = await db.execute(select(Execution).where(Execution.workflow_id == wf.id))
        executions = exec_res.scalars().all()
        assert len(executions) >= 1
        latest_exec = executions[-1]
        assert latest_exec.status == "completed"
        assert latest_exec.trigger_type == "schedule"
        assert "t2" in latest_exec.node_states

        # 6. Test pause / remove
        mgr.remove_schedule_job(sched.id)
        assert mgr.scheduler.get_job(job_id) is None
