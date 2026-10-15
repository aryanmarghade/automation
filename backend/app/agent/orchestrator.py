import asyncio
import json
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.tools.registry import registry
from app.services.ai_provider import OllamaProvider, OpenAICompatibleProvider
from app.core.config import settings

PLANNER_SYSTEM_PROMPT = """You are the NexusFlow Autonomous Planning Engine.
Your job is to analyze the user's objective, evaluate available files and tools, and construct a concrete, executable multi-step JSON plan.

Available Tools:
{tools_doc}

Attached Files:
{attached_files}

You MUST output ONLY a valid JSON object with the following schema:
{{
  "objective": "Summarized objective",
  "plan_rationale": "Why these steps are selected",
  "requires_user_confirmation": false,
  "steps": [
    {{
      "step_id": "step_1",
      "tool_id": "tool_name_from_registry",
      "description": "Clear step intent",
      "parameters": {{ "param_key": "param_value" }},
      "expected_output": "What this step produces"
    }}
  ]
}}
Do NOT output markdown commentary outside the JSON block.
"""

RECOVERY_SYSTEM_PROMPT = """You are the NexusFlow Autonomous Recovery Engine.
A step in an execution plan failed. Analyze the failure and propose a single recovery action.

Failed Step: {step_id} (Tool: {tool_id})
Error Encountered: {error}
Original Parameters: {parameters}
Previous Step Context: {context}

Available Tools:
{tools_doc}

Output ONLY a valid JSON object with:
{{
  "decision": "retry_with_new_params" or "alternative_tool" or "fail",
  "rationale": "Brief explanation",
  "recovered_step": {{
    "step_id": "{step_id}_recovery",
    "tool_id": "valid_tool_id",
    "description": "Recovery action intent",
    "parameters": {{ "param_key": "param_value" }}
  }}
}}
"""

class AgentExecutionState:
    def __init__(self, task_id: str, plan: Dict[str, Any], autonomy_level: str = "supervised", max_iterations: int = 15, max_step_retries: int = 2):
        self.task_id = task_id
        self.plan = plan
        self.autonomy_level = autonomy_level
        self.max_iterations = max_iterations
        self.max_step_retries = max_step_retries
        self.current_step_index = 0
        self.status = "pending" # pending, running, paused, waiting_approval, completed, failed, cancelled
        self.steps_history: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self._is_cancelled = False
        self._is_paused = False
        self._resume_event = asyncio.Event()
        self._resume_event.set()

    def cancel(self):
        self._is_cancelled = True
        self.status = "cancelled"
        self._resume_event.set()

    def pause(self):
        self._is_paused = True
        self.status = "paused"
        self._resume_event.clear()

    def resume(self):
        self._is_paused = False
        self.status = "running"
        self._resume_event.set()

class AgentTaskManager:
    _tasks: Dict[str, AgentExecutionState] = {}

    @classmethod
    def register(cls, state: AgentExecutionState):
        cls._tasks[state.task_id] = state

    @classmethod
    def get(cls, task_id: str) -> Optional[AgentExecutionState]:
        return cls._tasks.get(task_id)

    @classmethod
    def remove(cls, task_id: str):
        cls._tasks.pop(task_id, None)

class AgentOrchestrator:
    def __init__(self, model_provider: str = "ollama", model_name: Optional[str] = None, api_key: str = "", api_base: Optional[str] = None):
        self.model_provider = model_provider
        self.model_name = model_name or settings.DEFAULT_OLLAMA_MODEL
        if model_provider == "ollama":
            self.provider = OllamaProvider()
        else:
            self.provider = OpenAICompatibleProvider(api_key=api_key, base_url=api_base)

    async def create_plan(self, objective: str, attached_files: List[str] = None) -> Dict[str, Any]:
        attached_files = attached_files or []
        tools = registry.list_tools()
        tools_doc = "\n".join([f"- {t.id}: {t.name} ({t.category.value}) - {t.description}" for t in tools])

        prompt = PLANNER_SYSTEM_PROMPT.format(
            tools_doc=tools_doc,
            attached_files=", ".join(attached_files) if attached_files else "None"
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Objective: {objective}"}
        ]

        res = await self.provider.chat_completion(messages, model=self.model_name, temperature=0.1)
        raw_content = res.get("content", "").strip()

        if not raw_content or "{" not in raw_content:
            return self._fallback_deterministic_plan(objective, attached_files)

        try:
            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                plan_json = json.loads(json_match.group(0))
                # Validate plan schema
                if "steps" in plan_json and isinstance(plan_json["steps"], list):
                    # Filter/validate tools in plan
                    valid_steps = []
                    for s in plan_json["steps"]:
                        if registry.get_tool(s.get("tool_id")):
                            valid_steps.append(s)
                    if valid_steps:
                        plan_json["steps"] = valid_steps
                        return plan_json
            return self._fallback_deterministic_plan(objective, attached_files)
        except Exception:
            return self._fallback_deterministic_plan(objective, attached_files)

    def _fallback_deterministic_plan(self, objective: str, attached_files: List[str]) -> Dict[str, Any]:
        lower_obj = objective.lower()
        steps = []
        
        if any(w in lower_obj for w in ["excel", "spreadsheet", "xlsx", "csv", "table", "sales", "finance", "revenue"]):
            target_file = attached_files[0] if attached_files else "sample_data.csv"
            steps.append({
                "step_id": "step_1",
                "tool_id": "excel_tabular_analyzer",
                "description": f"Inspect dataset structure for {target_file}",
                "parameters": {"file_path": target_file, "operation": "inspect"},
                "expected_output": "Dataset dimensions, columns and dtypes"
            })
            steps.append({
                "step_id": "step_2",
                "tool_id": "excel_tabular_analyzer",
                "description": "Calculate statistical summary and detect anomalies",
                "parameters": {"file_path": target_file, "operation": "summary_stats"},
                "expected_output": "Metrics and distribution statistics"
            })
            if any(w in lower_obj for w in ["chart", "plot", "visual", "graph"]):
                steps.append({
                    "step_id": "step_3",
                    "tool_id": "excel_tabular_analyzer",
                    "description": "Generate visual chart report",
                    "parameters": {"file_path": target_file, "operation": "generate_chart", "chart_type": "bar", "x_col": "Category", "y_col": "Revenue", "chart_title": "Data Breakdown"},
                    "expected_output": "Rendered PNG chart file"
                })

        elif any(w in lower_obj for w in ["pdf", "document", "contract", "paper", "report"]):
            target_file = attached_files[0] if attached_files else "sample_doc.pdf"
            steps.append({
                "step_id": "step_1",
                "tool_id": "pdf_document_analyzer",
                "description": f"Inspect PDF metadata and page count for {target_file}",
                "parameters": {"file_path": target_file, "operation": "inspect"},
                "expected_output": "Page count and document properties"
            })
            steps.append({
                "step_id": "step_2",
                "tool_id": "pdf_document_analyzer",
                "description": "Extract content and search relevant citations",
                "parameters": {"file_path": target_file, "operation": "extract_pages", "page_start": 1, "page_end": 5},
                "expected_output": "Extracted pages with citations"
            })

        elif any(w in lower_obj for w in ["research", "search", "web", "browser", "find online", "scrape"]):
            steps.append({
                "step_id": "step_1",
                "tool_id": "browser_playwright",
                "description": f"Perform verified web research on: {objective}",
                "parameters": {"action": "search_web", "query": objective},
                "expected_output": "Search citations and verified sources"
            })

        else:
            steps.append({
                "step_id": "step_1",
                "tool_id": "windows_desktop_automation",
                "description": "Query system environment and diagnostics",
                "parameters": {"action": "get_system_info"},
                "expected_output": "Host system metrics"
            })

        return {
            "objective": objective,
            "plan_rationale": "Deterministic execution plan matching keyword and file targets.",
            "requires_user_confirmation": False,
            "steps": steps
        }

    async def execute_task_stream(self, state: AgentExecutionState) -> AsyncGenerator[Dict[str, Any], None]:
        """Executes the agent loop with live SSE streaming events, inspection, and recovery."""
        state.status = "running"
        yield {"type": "status", "status": "running", "message": "Agent execution loop started"}

        steps = list(state.plan.get("steps", []))
        step_idx = 0
        iteration_count = 0

        while step_idx < len(steps):
            if state._is_cancelled:
                state.status = "cancelled"
                yield {"type": "status", "status": "cancelled", "message": "Task cancelled by user"}
                return

            if state._is_paused:
                yield {"type": "status", "status": "paused", "message": "Task paused by user"}
                await state._resume_event.wait()
                if state._is_cancelled:
                    return
                yield {"type": "status", "status": "running", "message": "Task resumed"}

            iteration_count += 1
            if iteration_count > state.max_iterations:
                state.status = "failed"
                yield {"type": "error", "message": f"Execution halted: Exceeded maximum allowed iterations ({state.max_iterations})"}
                return

            step = steps[step_idx]
            step_id = step.get("step_id")
            tool_id = step.get("tool_id")
            params = step.get("parameters", {})
            description = step.get("description", "")

            tool = registry.get_tool(tool_id)
            if not tool:
                err_msg = f"Tool '{tool_id}' not found in registry"
                state.steps_history.append({"step_id": step_id, "status": "failed", "error": err_msg})
                yield {"type": "step_failed", "step_id": step_id, "error": err_msg}
                state.status = "failed"
                return

            # Autonomy / Approval Gate
            if state.autonomy_level == "assist" or (state.autonomy_level == "supervised" and tool.definition.risk_level in ["high", "critical"]):
                state.status = "waiting_approval"
                yield {
                    "type": "waiting_approval",
                    "step_id": step_id,
                    "tool_id": tool_id,
                    "description": description,
                    "risk_level": tool.definition.risk_level.value,
                    "parameters": params
                }
                # Wait for user approval via event
                state._resume_event.clear()
                await state._resume_event.wait()
                if state._is_cancelled:
                    return

            yield {
                "type": "step_start",
                "step_index": step_idx + 1,
                "total_steps": len(steps),
                "step_id": step_id,
                "tool_id": tool_id,
                "description": description
            }

            # Execute with bounded retries and recovery
            step_success = False
            retries = 0
            last_error = None

            while retries <= state.max_step_retries and not step_success:
                try:
                    start_t = time.time()
                    # Resolve context references if any
                    timeout = getattr(tool.definition, "timeout_seconds", 60)
                    out = await asyncio.wait_for(tool.execute(params, context=state.context), timeout=timeout)
                    duration_ms = int((time.time() - start_t) * 1000)

                    # Inspect output for error flags
                    if isinstance(out, dict) and ("error" in out or out.get("is_success") is False):
                        raise RuntimeError(out.get("error", "Tool execution returned error state"))

                    step_success = True
                    state.context[step_id] = out
                    state.steps_history.append({
                        "step_id": step_id,
                        "tool_id": tool_id,
                        "status": "completed",
                        "output": out,
                        "duration_ms": duration_ms
                    })

                    # Track artifacts
                    if isinstance(out, dict):
                        if "chart_file" in out:
                            art = {"type": "chart", "filename": out["chart_file"], "path": out["chart_path"]}
                            state.artifacts.append(art)
                            yield {"type": "artifact_generated", "artifact": art}
                        if "exported_file" in out:
                            art = {"type": "spreadsheet", "filename": out["exported_file"], "path": out["exported_path"]}
                            state.artifacts.append(art)
                            yield {"type": "artifact_generated", "artifact": art}

                    yield {
                        "type": "step_completed",
                        "step_id": step_id,
                        "tool_id": tool_id,
                        "output": out,
                        "duration_ms": duration_ms
                    }

                except Exception as e:
                    last_error = str(e)
                    retries += 1
                    yield {
                        "type": "step_retry",
                        "step_id": step_id,
                        "retry_count": retries,
                        "max_retries": state.max_step_retries,
                        "error": last_error
                    }

            if not step_success:
                # Attempt autonomous recovery
                recovery = await self._attempt_recovery(step, last_error, state.context)
                if recovery and recovery.get("decision") in ["retry_with_new_params", "alternative_tool"] and "recovered_step" in recovery:
                    yield {
                        "type": "recovery_proposed",
                        "step_id": step_id,
                        "rationale": recovery.get("rationale"),
                        "recovered_step": recovery["recovered_step"]
                    }
                    # Insert recovered step
                    steps.insert(step_idx + 1, recovery["recovered_step"])
                else:
                    state.steps_history.append({
                        "step_id": step_id,
                        "tool_id": tool_id,
                        "status": "failed",
                        "error": last_error
                    })
                    state.status = "failed"
                    yield {"type": "step_failed", "step_id": step_id, "error": last_error}
                    return

            step_idx += 1

        state.status = "completed"
        final_summary = f"Successfully executed all {len(steps)} pipeline steps. Generated {len(state.artifacts)} verified deliverables."
        yield {
            "type": "completed",
            "status": "completed",
            "final_summary": final_summary,
            "artifacts": state.artifacts,
            "steps_history": state.steps_history
        }

    async def _attempt_recovery(self, failed_step: Dict[str, Any], error_str: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Invokes the recovery engine to propose alternative parameters or substitute tools."""
        try:
            tools = registry.list_tools()
            tools_doc = "\n".join([f"- {t.id}: {t.name} - {t.description}" for t in tools])
            prompt = RECOVERY_SYSTEM_PROMPT.format(
                step_id=failed_step.get("step_id"),
                tool_id=failed_step.get("tool_id"),
                error=error_str,
                parameters=json.dumps(failed_step.get("parameters", {})),
                context=json.dumps({k: v for k, v in list(context.items())[:3]}),
                tools_doc=tools_doc
            )
            res = await self.provider.chat_completion([{"role": "user", "content": prompt}], model=self.model_name, temperature=0.1)
            raw = res.get("content", "").strip()
            import re
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
        return None

    @staticmethod
    def plan_to_visual_workflow(plan: Dict[str, Any], workflow_name: str = "Agent Generated Workflow") -> Dict[str, Any]:
        """Converts an agent execution plan into an editable visual workflow DAG."""
        steps = plan.get("steps", [])
        nodes = []
        edges = []

        # 1. Add Start / Trigger node
        trigger_id = "agent_trigger_start"
        nodes.append({
            "id": trigger_id,
            "type": "trigger_manual",
            "position": {"x": 250, "y": 50},
            "data": {"label": "Manual Trigger", "type": "trigger_manual", "payload": {}}
        })

        prev_id = trigger_id
        for i, step in enumerate(steps):
            node_id = f"node_{step.get('tool_id')}_{i+1}"
            tool = registry.get_tool(step.get("tool_id"))
            tool_name = tool.definition.name if tool else step.get("tool_id")

            nodes.append({
                "id": node_id,
                "type": step.get("tool_id"),
                "position": {"x": 250, "y": 150 + (i * 120)},
                "data": {
                    "label": tool_name,
                    "type": step.get("tool_id"),
                    **step.get("parameters", {})
                }
            })

            edges.append({
                "id": f"e_{prev_id}_{node_id}",
                "source": prev_id,
                "target": node_id
            })
            prev_id = node_id

        return {
            "name": workflow_name,
            "description": f"Generated from objective: {plan.get('objective', '')}",
            "nodes": nodes,
            "edges": edges,
            "is_active": True,
            "tags": ["agent-generated"]
        }
