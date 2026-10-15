import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from app.core.database import AsyncSessionLocal
from app.models.entities import Schedule, Workflow, Execution, Notification
from app.engine.runtime import WorkflowRuntime
from app.schemas.workflow import WorkflowNode, WorkflowEdge

logger = logging.getLogger("nexusflow.scheduler")

class SchedulerManager:
    _instance: Optional['SchedulerManager'] = None
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    @classmethod
    def get_instance(cls) -> 'SchedulerManager':
        if cls._instance is None:
            cls._instance = SchedulerManager()
        return cls._instance

    def start(self):
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("NexusFlow Background Scheduler started.")

    def shutdown(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("NexusFlow Background Scheduler shutdown.")

    async def reload_all_schedules(self):
        """Loads and activates all enabled schedules from the database on startup or sync."""
        self.scheduler.remove_all_jobs()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Schedule).where(Schedule.is_active == True))
            schedules = result.scalars().all()
            for s in schedules:
                try:
                    self._register_job(s)
                except Exception as e:
                    logger.error(f"Failed to register schedule '{s.id}': {str(e)}")

    def _register_job(self, schedule: Schedule):
        job_id = f"schedule_{schedule.id}"
        
        # Remove existing job if present
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

        trigger = None
        if schedule.schedule_type == "one_time" and schedule.one_time_run_at:
            trigger = DateTrigger(run_date=schedule.one_time_run_at, timezone=schedule.timezone or "UTC")
        elif schedule.interval_seconds and schedule.interval_seconds > 0:
            trigger = IntervalTrigger(seconds=schedule.interval_seconds, timezone=schedule.timezone or "UTC")
        elif schedule.cron_expression:
            parts = schedule.cron_expression.strip().split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4],
                    timezone=schedule.timezone or "UTC"
                )

        if trigger:
            self.scheduler.add_job(
                func=execute_scheduled_workflow_job,
                trigger=trigger,
                args=[schedule.id, schedule.workflow_id],
                id=job_id,
                name=schedule.name,
                replace_existing=True,
                misfire_grace_time=300
            )
            # Update next run timestamp safely if available
            try:
                job = self.scheduler.get_job(job_id)
                if job and getattr(job, "next_run_time", None):
                    schedule.next_run_at = job.next_run_time.replace(tzinfo=None)
            except Exception:
                pass

    def remove_schedule_job(self, schedule_id: str):
        job_id = f"schedule_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

async def execute_scheduled_workflow_job(schedule_id: str, workflow_id: str):
    """Callback function triggered by APScheduler to run workflow asynchronously in background."""
    async with AsyncSessionLocal() as db:
        # 1. Fetch workflow and schedule
        wf_res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        wf = wf_res.scalar_one_or_none()
        
        sched_res = await db.execute(select(Schedule).where(Schedule.id == schedule_id))
        sched = sched_res.scalar_one_or_none()

        if not wf:
            logger.error(f"Scheduled workflow {workflow_id} not found.")
            return

        # 2. Record notification: Started
        notif_start = Notification(
            title=f"Scheduled Run Started: {sched.name if sched else wf.name}",
            message=f"Executing background workflow '{wf.name}'",
            level="info",
            category="schedule",
            resource_id=wf.id
        )
        db.add(notif_start)

        # 3. Create Execution record
        exec_record = Execution(
            workflow_id=wf.id,
            mode="workflow",
            status="running",
            trigger_type="schedule",
            inputs={},
            logs=[]
        )
        db.add(exec_record)
        await db.commit()
        await db.refresh(exec_record)

        # 4. Instantiate and execute runtime
        nodes = [WorkflowNode(**n) for n in wf.nodes]
        edges = [WorkflowEdge(**e) for e in wf.edges]
        runtime = WorkflowRuntime(execution_id=exec_record.id, nodes=nodes, edges=edges)
        
        res = await runtime.run()

        # 5. Update execution details
        exec_record.status = res.get("status", "completed")
        exec_record.outputs = res.get("outputs", {})
        exec_record.error = res.get("error")
        exec_record.node_states = res.get("node_states", {})
        exec_record.logs = res.get("logs", [])
        exec_record.duration_ms = res.get("duration_ms", 0)
        exec_record.finished_at = datetime.utcnow()

        # 6. Update Schedule metrics
        if sched:
            sched.last_run_at = datetime.utcnow()
            sched.last_run_status = exec_record.status
            # If one-time schedule, mark inactive
            if sched.schedule_type == "one_time":
                sched.is_active = False

        # 7. Record completion/failure notification
        notif_done = Notification(
            title=f"Scheduled Run {exec_record.status.capitalize()}: {wf.name}",
            message=f"Workflow completed in {exec_record.duration_ms}ms" if exec_record.status == "completed" else f"Workflow failed: {exec_record.error}",
            level="success" if exec_record.status == "completed" else "error",
            category="schedule",
            resource_id=exec_record.id
        )
        db.add(notif_done)
        await db.commit()
