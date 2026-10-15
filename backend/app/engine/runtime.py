import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from app.schemas.workflow import WorkflowNode, WorkflowEdge, WorkflowResponse
from app.engine.dag_validator import DAGValidator, ExpressionEvaluator
from app.tools.registry import registry

class WorkflowRuntime:
    """Executes a validated workflow graph step-by-step with dependency resolution, logs and timeout handling."""
    
    def __init__(self, execution_id: str, nodes: List[WorkflowNode], edges: List[WorkflowEdge], initial_inputs: Optional[Dict[str, Any]] = None):
        self.execution_id = execution_id
        self.nodes = {n.id: n for n in nodes}
        self.edges = edges
        self.initial_inputs = initial_inputs or {}
        
        # State tracking
        self.node_states: Dict[str, Dict[str, Any]] = {}
        self.logs: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {
            "inputs": self.initial_inputs,
            "$node": {},
            "$json": self.initial_inputs
        }
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        self.log("Workflow execution was cancelled by user", level="WARNING")

    def log(self, message: str, node_id: Optional[str] = None, level: str = "INFO", data: Optional[Any] = None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "node_id": node_id,
            "message": message,
            "data": data
        }
        self.logs.append(entry)

    async def run(self) -> Dict[str, Any]:
        start_time = time.time()
        self.log(f"Starting workflow execution (ID: {self.execution_id})")

        # 1. Validate Graph
        validation = DAGValidator.validate(list(self.nodes.values()), self.edges)
        if not validation.is_valid:
            error_msgs = [e.message for e in validation.errors]
            self.log(f"DAG Validation failed: {', '.join(error_msgs)}", level="ERROR")
            return {
                "status": "failed",
                "error": "Validation failed: " + "; ".join(error_msgs),
                "node_states": self.node_states,
                "logs": self.logs,
                "outputs": {},
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        # 2. Execute topologically
        execution_order = validation.execution_order
        active_branches: Set[str] = set(self.nodes.keys()) # Tracks disabled branch paths in if-else
        final_outputs: Dict[str, Any] = {}

        for node_id in execution_order:
            if self._is_cancelled:
                return {
                    "status": "cancelled",
                    "error": "Execution cancelled by user",
                    "node_states": self.node_states,
                    "logs": self.logs,
                    "outputs": final_outputs,
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

            if node_id not in active_branches:
                self.node_states[node_id] = {"status": "skipped", "output": None}
                self.log(f"Skipping node '{node_id}' due to inactive condition branch", node_id=node_id)
                continue

            node = self.nodes[node_id]
            self.node_states[node_id] = {"status": "running", "output": None}
            self.log(f"Executing node '{node_id}' (Type: {node.type})", node_id=node_id)

            # Resolve parameters using expression evaluator
            resolved_params = {}
            for param_key, param_val in node.data.items():
                resolved_params[param_key] = ExpressionEvaluator.evaluate(param_val, self.context)

            # Look up tool from registry
            tool = registry.get_tool(node.type)
            if not tool:
                err_msg = f"Tool handler '{node.type}' not found in registry"
                self.node_states[node_id] = {"status": "failed", "error": err_msg}
                self.log(err_msg, node_id=node_id, level="ERROR")
                return {
                    "status": "failed",
                    "error": err_msg,
                    "node_states": self.node_states,
                    "logs": self.logs,
                    "outputs": final_outputs,
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

            # Execute with timeout protection
            try:
                node_start = time.time()
                timeout = getattr(tool.definition, "timeout_seconds", 60)
                output = await asyncio.wait_for(
                    tool.execute(resolved_params, context=self.context),
                    timeout=timeout
                )
                node_duration = int((time.time() - node_start) * 1000)
                
                self.node_states[node_id] = {
                    "status": "completed",
                    "output": output,
                    "duration_ms": node_duration
                }
                
                # Update runtime context
                self.context["$node"][node_id] = output
                self.context["$json"] = output
                final_outputs[node_id] = output
                
                self.log(f"Node '{node_id}' completed in {node_duration}ms", node_id=node_id, data=output)

                # Special condition branch pruning
                if node.type == "flow_condition":
                    branch_taken = output.get("branch", "true")
                    # Find downstream edges and deactivate unchosen handles
                    for edge in self.edges:
                        if edge.source == node_id:
                            handle = edge.sourceHandle or "true"
                            if handle != branch_taken:
                                # Recursively prune downstream nodes
                                self._prune_downstream(edge.target, active_branches)

            except asyncio.TimeoutError:
                err_msg = f"Node '{node_id}' timed out after {timeout} seconds"
                self.node_states[node_id] = {"status": "failed", "error": err_msg}
                self.log(err_msg, node_id=node_id, level="ERROR")
                return {
                    "status": "failed",
                    "error": err_msg,
                    "node_states": self.node_states,
                    "logs": self.logs,
                    "outputs": final_outputs,
                    "duration_ms": int((time.time() - start_time) * 1000)
                }
            except Exception as e:
                err_msg = f"Node '{node_id}' failed: {str(e)}"
                self.node_states[node_id] = {"status": "failed", "error": err_msg}
                self.log(err_msg, node_id=node_id, level="ERROR")
                return {
                    "status": "failed",
                    "error": err_msg,
                    "node_states": self.node_states,
                    "logs": self.logs,
                    "outputs": final_outputs,
                    "duration_ms": int((time.time() - start_time) * 1000)
                }

        total_duration = int((time.time() - start_time) * 1000)
        self.log(f"Workflow completed successfully in {total_duration}ms")
        return {
            "status": "completed",
            "node_states": self.node_states,
            "logs": self.logs,
            "outputs": final_outputs,
            "duration_ms": total_duration
        }

    def _prune_downstream(self, target_id: str, active_branches: Set[str]):
        if target_id in active_branches:
            active_branches.discard(target_id)
            for edge in self.edges:
                if edge.source == target_id:
                    self._prune_downstream(edge.target, active_branches)
