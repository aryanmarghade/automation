import asyncio
import json
import httpx
from typing import Dict, Any
from app.tools.registry import BaseTool, ToolDefinition, ToolCategory, ToolParameter, RiskLevel, registry

class ManualTriggerTool(BaseTool):
    def __init__(self):
        super().__init__(ToolDefinition(
            id="trigger_manual",
            name="Manual Trigger",
            description="Entrypoint for manual workflow execution with optional payload.",
            category=ToolCategory.TRIGGERS,
            risk_level=RiskLevel.LOW,
            parameters=[
                ToolParameter(name="payload", type="object", description="Initial key-value JSON input data", required=False, default={})
            ]
        ))

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = params.get("payload", {})
        return {"status": "triggered", "data": payload}

class DataTransformTool(BaseTool):
    def __init__(self):
        super().__init__(ToolDefinition(
            id="data_transform",
            name="Data Transform",
            description="Transforms, maps, or extracts keys from intermediate data using safe rules.",
            category=ToolCategory.TRANSFORM,
            risk_level=RiskLevel.LOW,
            parameters=[
                ToolParameter(name="input_data", type="object", description="The data to transform", required=True),
                ToolParameter(name="operation", type="string", description="Operation to perform: 'pick_keys', 'json_parse', 'json_stringify', 'merge'", required=True, options=["pick_keys", "json_parse", "json_stringify", "merge"]),
                ToolParameter(name="keys", type="string", description="Comma-separated list of keys to pick or merge", required=False, default="")
            ]
        ))

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        input_data = params.get("input_data")
        op = params.get("operation", "pick_keys")
        
        if op == "json_parse" and isinstance(input_data, str):
            try:
                return {"result": json.loads(input_data)}
            except Exception as e:
                return {"error": f"Failed to parse JSON: {str(e)}"}
        elif op == "json_stringify":
            return {"result": json.dumps(input_data)}
        elif op == "pick_keys" and isinstance(input_data, dict):
            keys = [k.strip() for k in params.get("keys", "").split(",") if k.strip()]
            picked = {k: input_data.get(k) for k in keys if k in input_data}
            return {"result": picked}
        elif op == "merge" and isinstance(input_data, dict):
            return {"result": input_data}
        return {"result": input_data}

class ConditionTool(BaseTool):
    def __init__(self):
        super().__init__(ToolDefinition(
            id="flow_condition",
            name="If-Else Condition",
            description="Evaluates a condition comparing two values and routes execution down True or False branches.",
            category=ToolCategory.TRANSFORM,
            risk_level=RiskLevel.LOW,
            parameters=[
                ToolParameter(name="value1", type="string", description="Left-hand value or variable", required=True),
                ToolParameter(name="operator", type="string", description="Comparison operator", required=True, options=["equals", "not_equals", "contains", "greater_than", "less_than", "is_empty", "is_not_empty"]),
                ToolParameter(name="value2", type="string", description="Right-hand value", required=False, default="")
            ]
        ))

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        v1 = params.get("value1")
        v2 = params.get("value2", "")
        op = params.get("operator", "equals")
        
        matched = False
        if op == "equals":
            matched = str(v1) == str(v2)
        elif op == "not_equals":
            matched = str(v1) != str(v2)
        elif op == "contains":
            matched = str(v2) in str(v1)
        elif op == "greater_than":
            try:
                matched = float(v1) > float(v2)
            except Exception:
                matched = str(v1) > str(v2)
        elif op == "less_than":
            try:
                matched = float(v1) < float(v2)
            except Exception:
                matched = str(v1) < str(v2)
        elif op == "is_empty":
            matched = v1 is None or v1 == "" or v1 == [] or v1 == {}
        elif op == "is_not_empty":
            matched = v1 is not None and v1 != "" and v1 != [] and v1 != {}
            
        return {
            "result": matched,
            "branch": "true" if matched else "false",
            "evaluated": {"value1": v1, "operator": op, "value2": v2}
        }

class HttpRequestTool(BaseTool):
    def __init__(self):
        super().__init__(ToolDefinition(
            id="http_request",
            name="HTTP Request",
            description="Makes an outbound HTTP request (GET, POST, PUT, DELETE) to a specified API.",
            category=ToolCategory.HTTP,
            risk_level=RiskLevel.MEDIUM,
            parameters=[
                ToolParameter(name="url", type="string", description="Target URL endpoint", required=True),
                ToolParameter(name="method", type="string", description="HTTP Method", required=True, default="GET", options=["GET", "POST", "PUT", "DELETE", "PATCH"]),
                ToolParameter(name="headers", type="object", description="Optional JSON headers dictionary", required=False, default={}),
                ToolParameter(name="body", type="object", description="Optional JSON request body for POST/PUT", required=False, default={})
            ],
            timeout_seconds=30
        ))

    async def execute(self, params: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        url = params.get("url")
        method = params.get("method", "GET").upper()
        headers = params.get("headers") or {}
        body = params.get("body") or {}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    res = await client.get(url, headers=headers)
                elif method == "POST":
                    res = await client.post(url, headers=headers, json=body)
                elif method == "PUT":
                    res = await client.put(url, headers=headers, json=body)
                elif method == "DELETE":
                    res = await client.delete(url, headers=headers)
                else:
                    return {"error": f"Unsupported HTTP method: {method}"}
                
                try:
                    res_json = res.json()
                except Exception:
                    res_json = None
                    
                return {
                    "status_code": res.status_code,
                    "is_success": res.is_success,
                    "data": res_json if res_json is not None else res.text,
                    "headers": dict(res.headers)
                }
            except Exception as e:
                return {"error": str(e), "is_success": False}

def register_core_tools():
    registry.register(ManualTriggerTool())
    registry.register(DataTransformTool())
    registry.register(ConditionTool())
    registry.register(HttpRequestTool())
