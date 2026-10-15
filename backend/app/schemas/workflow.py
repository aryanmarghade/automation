from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Node & Edge Models
class NodePosition(BaseModel):
    x: float
    y: float

class WorkflowNode(BaseModel):
    id: str
    type: str
    position: NodePosition
    data: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    label: Optional[str] = None

# Workflow Schemas
class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    viewport: Optional[Dict[str, Any]] = None
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    viewport: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

class WorkflowResponse(WorkflowBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Execution Schemas
class ExecutionRequest(BaseModel):
    workflow_id: Optional[str] = None
    nodes: Optional[List[WorkflowNode]] = None
    edges: Optional[List[WorkflowEdge]] = None
    trigger_type: str = "manual"
    inputs: Dict[str, Any] = Field(default_factory=dict)

class ExecutionResponse(BaseModel):
    id: str
    workflow_id: Optional[str] = None
    mode: str
    status: str
    trigger_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    error: Optional[str] = None
    node_states: Dict[str, Any]
    logs: List[Dict[str, Any]]
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    class Config:
        from_attributes = True

# Validation Schemas
class WorkflowValidationRequest(BaseModel):
    name: Optional[str] = "Validation"
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)

class ValidationError(BaseModel):
    node_id: Optional[str] = None
    message: str
    severity: str = "error" # "error", "warning"

class WorkflowValidationResponse(BaseModel):
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[ValidationError]
    execution_order: List[str]
