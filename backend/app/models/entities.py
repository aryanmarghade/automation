import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    viewport = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="workflow", cascade="all, delete-orphan")

class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=True)
    mode = Column(String(50), nullable=False, default="workflow") # "workflow", "agent_task", "step_test"
    status = Column(String(50), nullable=False, default="pending") # pending, queued, running, completed, failed, cancelled, timed_out
    trigger_type = Column(String(50), default="manual") # manual, schedule, webhook, agent, retry
    inputs = Column(JSON, nullable=True, default=dict)
    outputs = Column(JSON, nullable=True, default=dict)
    error = Column(Text, nullable=True)
    node_states = Column(JSON, nullable=True, default=dict) # status and outputs per node
    logs = Column(JSON, nullable=True, default=list)
    retry_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    workflow = relationship("Workflow", back_populates="executions")

class AgentTask(Base):
    __tablename__ = "agent_tasks"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    objective = Column(Text, nullable=False)
    status = Column(String(50), default="pending") # pending, planning, executing, verifying, completed, failed, paused, cancelled
    autonomy_level = Column(String(50), default="supervised") # assist, supervised, autonomous
    model_provider = Column(String(50), default="ollama")
    model_name = Column(String(100), default="llama3.2:latest")
    plan = Column(JSON, nullable=True, default=list)
    current_step_index = Column(Integer, default=0)
    steps_history = Column(JSON, nullable=True, default=list)
    attached_files = Column(JSON, nullable=True, default=list)
    artifacts = Column(JSON, nullable=True, default=list)
    final_summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    cron_expression = Column(String(100), nullable=True) # e.g. "0 9 * * *"
    interval_seconds = Column(Integer, nullable=True) # for interval-based runs
    schedule_type = Column(String(50), default="recurring") # recurring, one_time, interval
    one_time_run_at = Column(DateTime, nullable=True) # for one-off scheduled runs
    timezone = Column(String(100), default="UTC")
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workflow = relationship("Workflow", back_populates="schedules")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String(50), default="info") # info, success, warning, error
    category = Column(String(50), default="workflow") # workflow, schedule, agent, system
    resource_id = Column(String(100), nullable=True) # workflow_id or execution_id
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ToolConfig(Base):
    __tablename__ = "tool_configs"
    
    id = Column(String(100), primary_key=True) # e.g. "browser_playwright", "excel_analyzer"
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    risk_level = Column(String(50), default="low") # low, medium, high, critical
    requires_confirmation = Column(Boolean, default=False)
    config = Column(JSON, nullable=True, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorkspaceFile(Base):
    __tablename__ = "workspace_files"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, xlsx, csv, docx, json, etc.
    size_bytes = Column(Integer, nullable=False)
    metadata_info = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
