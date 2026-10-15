import pytest
import asyncio
from app.schemas.workflow import WorkflowNode, WorkflowEdge, NodePosition
from app.engine.dag_validator import DAGValidator, ExpressionEvaluator
from app.engine.runtime import WorkflowRuntime
from app.tools.core_tools import register_core_tools
from app.tools.registry import registry

register_core_tools()

@pytest.mark.asyncio
async def test_dag_validation_and_execution():
    # Construct a 3-node DAG: Trigger -> Transform -> Condition
    nodes = [
        WorkflowNode(id="node_1", type="trigger_manual", position=NodePosition(x=0, y=0), data={"payload": {"amount": 150}}),
        WorkflowNode(id="node_2", type="data_transform", position=NodePosition(x=200, y=0), data={"input_data": "{{ $node.node_1.data }}", "operation": "pick_keys", "keys": "amount"}),
        WorkflowNode(id="node_3", type="flow_condition", position=NodePosition(x=400, y=0), data={"value1": "{{ $node.node_2.result.amount }}", "operator": "greater_than", "value2": "100"})
    ]
    edges = [
        WorkflowEdge(id="e1-2", source="node_1", target="node_2"),
        WorkflowEdge(id="e2-3", source="node_2", target="node_3")
    ]

    # Validate DAG
    val = DAGValidator.validate(nodes, edges)
    assert val.is_valid is True
    assert val.execution_order == ["node_1", "node_2", "node_3"]

    # Execute runtime
    runtime = WorkflowRuntime(execution_id="test_exec_1", nodes=nodes, edges=edges)
    res = await runtime.run()

    assert res["status"] == "completed"
    assert res["node_states"]["node_3"]["output"]["result"] is True
    assert res["node_states"]["node_3"]["output"]["branch"] == "true"

@pytest.mark.asyncio
async def test_cycle_detection():
    # Cyclic DAG: node_1 -> node_2 -> node_1
    nodes = [
        WorkflowNode(id="n1", type="trigger_manual", position=NodePosition(x=0, y=0), data={}),
        WorkflowNode(id="n2", type="data_transform", position=NodePosition(x=100, y=0), data={})
    ]
    edges = [
        WorkflowEdge(id="e1", source="n1", target="n2"),
        WorkflowEdge(id="e2", source="n2", target="n1")
    ]
    val = DAGValidator.validate(nodes, edges)
    assert val.is_valid is False
    assert any("Cycle detected" in err.message for err in val.errors)
