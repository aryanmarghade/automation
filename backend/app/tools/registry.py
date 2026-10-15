from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import inspect
import asyncio

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ToolCategory(str, Enum):
    AI = "AI & Reasoning"
    DOCUMENTS = "Files & Documents"
    TABULAR = "Spreadsheets & Tabular Data"
    BROWSER = "Browser Automation"
    SEARCH = "Search & Research"
    TRANSFORM = "Data Transformation"
    HTTP = "HTTP & APIs"
    WINDOWS = "Windows Automation"
    TRIGGERS = "Triggers & Scheduling"
    OUTPUT = "Outputs & Reports"

class ToolParameter(BaseModel):
    name: str
    type: str # string, number, boolean, object, array, file
    description: str
    required: bool = True
    default: Optional[Any] = None
    options: Optional[List[str]] = None

class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    category: ToolCategory
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    parameters: List[ToolParameter] = Field(default_factory=list)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 60

class BaseTool:
    def __init__(self, definition: ToolDefinition):
        self.definition = definition

    async def execute(self, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError("Tool execution must be implemented by subclasses")

    async def test(self) -> Dict[str, Any]:
        return {"status": "healthy", "message": f"Tool {self.definition.name} is ready"}

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.definition.id] = tool

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    def get_tools_by_category(self, category: ToolCategory) -> List[ToolDefinition]:
        return [tool.definition for tool in self._tools.values() if tool.definition.category == category]

    def export_for_agent(self) -> List[Dict[str, Any]]:
        """Returns JSON schema formatted for LLM function/tool calling."""
        agent_tools = []
        for tool in self._tools.values():
            d = tool.definition
            properties = {}
            required = []
            for p in d.parameters:
                properties[p.name] = {
                    "type": p.type,
                    "description": p.description
                }
                if p.options:
                    properties[p.name]["enum"] = p.options
                if p.required:
                    required.append(p.name)

            agent_tools.append({
                "type": "function",
                "function": {
                    "name": d.id,
                    "description": f"[{d.category.value}] {d.description} (Risk: {d.risk_level.value})",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return agent_tools

registry = ToolRegistry()
