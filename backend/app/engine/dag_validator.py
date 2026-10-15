import re
from typing import Dict, Any, List, Set
from collections import defaultdict, deque
from app.schemas.workflow import WorkflowNode, WorkflowEdge, WorkflowValidationResponse, ValidationError

class ExpressionEvaluator:
    """
    Safely resolves expressions like {{ $node["trigger"].data.value }} or {{ $json.records[0].name }}
    WITHOUT using eval() or exec().
    """
    @staticmethod
    def evaluate(expression_str: Any, context: Dict[str, Any]) -> Any:
        if not isinstance(expression_str, str):
            return expression_str
        
        # Check if it is a template variable {{ ... }}
        pattern = r"\{\{\s*(.*?)\s*\}\}"
        matches = re.findall(pattern, expression_str)
        
        if not matches:
            return expression_str
        
        # If the string is purely one variable e.g. "{{ $node.a.data }}"
        if len(matches) == 1 and expression_str.strip() == f"{{{{{matches[0]}}}}}":
            return ExpressionEvaluator._resolve_path(matches[0].strip(), context)
        
        # Otherwise substitute inside the string
        result = expression_str
        for match in matches:
            val = ExpressionEvaluator._resolve_path(match.strip(), context)
            result = result.replace(f"{{{{{match}}}}}", str(val) if val is not None else "")
        return result

    @staticmethod
    def _resolve_path(path: str, context: Dict[str, Any]) -> Any:
        try:
            # Handle special aliases
            # e.g., $node["node_id"].output or $nodes.node_id.output or $json.key
            normalized = path.replace("['", ".").replace("']", ".").replace('["', ".").replace('"]', ".")
            tokens = [t for t in normalized.split(".") if t]
            
            curr = context
            for token in tokens:
                if isinstance(curr, dict):
                    curr = curr.get(token)
                elif isinstance(curr, list):
                    idx = int(token)
                    curr = curr[idx] if 0 <= idx < len(curr) else None
                else:
                    return None
            return curr
        except Exception:
            return None

class DAGValidator:
    """Validates workflow graph connectivity, detects cycles, and generates execution order (Topological Sort)."""
    
    @staticmethod
    def validate(nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> WorkflowValidationResponse:
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        
        if not nodes:
            return WorkflowValidationResponse(
                is_valid=True,
                errors=[],
                warnings=[ValidationError(message="Workflow contains no nodes", severity="warning")],
                execution_order=[]
            )
        
        node_ids = {node.id for node in nodes}
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source not in node_ids:
                errors.append(ValidationError(
                    node_id=edge.source,
                    message=f"Edge source '{edge.source}' does not exist in nodes"
                ))
            if edge.target not in node_ids:
                errors.append(ValidationError(
                    node_id=edge.target,
                    message=f"Edge target '{edge.target}' does not exist in nodes"
                ))
            
            if edge.source in node_ids and edge.target in node_ids:
                adj[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # Check for trigger / start node
        trigger_nodes = [n for n in nodes if n.type in ("trigger_manual", "trigger_schedule", "trigger_webhook", "trigger_file_watch") or in_degree[n.id] == 0]
        if not trigger_nodes:
            errors.append(ValidationError(message="Workflow has no starting/trigger node."))

        # Cycle Detection via Kahn's Algorithm
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        execution_order = []
        
        while queue:
            curr = queue.popleft()
            execution_order.append(curr)
            
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        if len(execution_order) != len(nodes):
            unresolved = set(node_ids) - set(execution_order)
            errors.append(ValidationError(
                message=f"Cycle detected in workflow graph involving nodes: {', '.join(unresolved)}"
            ))
            
        return WorkflowValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            execution_order=execution_order if len(errors) == 0 else []
        )
