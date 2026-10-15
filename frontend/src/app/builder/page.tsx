'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  Connection,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Play, 
  Save, 
  Plus, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw,
  Trash2,
  Settings,
  HelpCircle,
  Database,
  Globe,
  Sliders,
  Terminal,
  FileSpreadsheet,
  FileText
} from 'lucide-react';
import { WorkflowService, ToolService } from '@/services/api';

// Custom Canvas Node Component
function AutomationNode({ data, id, isSelected }: any) {
  const getIcon = () => {
    switch (data.type) {
      case 'trigger_manual': return <Play className="w-4 h-4 text-emerald-400" />;
      case 'excel_tabular_analyzer': return <FileSpreadsheet className="w-4 h-4 text-emerald-400" />;
      case 'pdf_document_analyzer': return <FileText className="w-4 h-4 text-blue-400" />;
      case 'browser_playwright': return <Globe className="w-4 h-4 text-purple-400" />;
      case 'flow_condition': return <Sliders className="w-4 h-4 text-amber-400" />;
      case 'http_request': return <Database className="w-4 h-4 text-sky-400" />;
      default: return <Terminal className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className={`px-4 py-3 shadow-md rounded-xl bg-slate-950 border transition-all min-w-[200px] ${
      isSelected ? 'border-indigo-500 ring-2 ring-indigo-500/20' : 'border-slate-800 hover:border-slate-700'
    }`}>
      {data.type !== 'trigger_manual' && (
        <Handle type="target" position={Position.Top} className="w-3 h-3 bg-indigo-500 border-2 border-slate-900" />
      )}
      <div className="flex items-center space-x-2.5">
        <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800">
          {getIcon()}
        </div>
        <div className="flex-1 overflow-hidden">
          <div className="text-xs font-semibold text-slate-200 truncate">{data.label || data.name}</div>
          <div className="text-[10px] text-slate-500 font-mono truncate">{id}</div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-indigo-500 border-2 border-slate-900" />
    </div>
  );
}

const nodeTypes = {
  custom: AutomationNode,
};

export default function BuilderPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([
    {
      id: 'trigger_1',
      type: 'custom',
      position: { x: 250, y: 50 },
      data: { label: 'Manual Trigger', type: 'trigger_manual', payload: {} },
    },
    {
      id: 'excel_1',
      type: 'custom',
      position: { x: 250, y: 180 },
      data: { label: 'Analyze Spreadsheet', type: 'excel_tabular_analyzer', file_path: 'test_sales.csv', operation: 'inspect' },
    },
  ]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([
    { id: 'e1-2', source: 'trigger_1', target: 'excel_1' },
  ]);

  const [availableTools, setAvailableTools] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [workflowName, setWorkflowName] = useState('My Automation Workflow');
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<any>(null);
  const [validation, setValidation] = useState<any>(null);

  useEffect(() => {
    ToolService.list().then(setAvailableTools).catch(() => {});
  }, []);

  const onConnect = useCallback((params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const onNodeClick = (_: any, node: any) => {
    setSelectedNode(node);
  };

  const handleAddNode = (tool: any) => {
    const newNodeId = `${tool.id}_${Date.now().toString().slice(-4)}`;
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: 250 + Math.random() * 50, y: 280 + Math.random() * 50 },
      data: {
        label: tool.name,
        type: tool.id,
        ...tool.parameters.reduce((acc: any, p: any) => ({ ...acc, [p.name]: p.default || '' }), {}),
      },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  const handleSaveWorkflow = async () => {
    try {
      const payload = {
        name: workflowName,
        nodes: nodes.map(n => ({ id: n.id, type: String((n.data as any)?.type || n.type || 'custom'), position: n.position, data: n.data as Record<string, any> })),
        edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target })),
        is_active: true,
      };
      await WorkflowService.create(payload);
      alert('Workflow saved successfully to SQLite library!');
    } catch (e: any) {
      alert(`Save failed: ${e.message}`);
    }
  };

  const handleValidateAndRun = async () => {
    setIsRunning(true);
    setRunResult(null);

    try {
      const formattedNodes = nodes.map(n => ({ id: n.id, type: String((n.data as any)?.type || n.type || 'custom'), position: n.position, data: n.data as Record<string, any> }));
      const formattedEdges = edges.map(e => ({ id: e.id, source: e.source, target: e.target }));

      // 1. Validate DAG
      const val = await WorkflowService.validate({ nodes: formattedNodes, edges: formattedEdges });
      setValidation(val);

      if (!val.is_valid) {
        alert('Validation errors detected in workflow!');
        return;
      }

      // 2. Save temporary or active workflow and run
      const wf = await WorkflowService.create({
        name: workflowName,
        nodes: formattedNodes,
        edges: formattedEdges,
      });

      const res = await WorkflowService.run(wf.id);
      setRunResult(res);
    } catch (e: any) {
      alert(`Run error: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden bg-slate-950">
      {/* Node Palette Sidebar */}
      <div className="w-72 bg-slate-950 border-r border-slate-800 flex flex-col h-full z-10 select-none">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">Available Nodes</h2>
          <p className="text-[11px] text-slate-500 mt-0.5">Click any tool to place on canvas</p>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {availableTools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => handleAddNode(tool)}
              className="w-full text-left p-2.5 rounded-lg bg-slate-900/70 hover:bg-slate-900 border border-slate-800/80 hover:border-indigo-500/40 transition-all group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300">{tool.name}</span>
                <Plus className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400" />
              </div>
              <p className="text-[10px] text-slate-400 line-clamp-2 mt-1">{tool.description}</p>
              <div className="mt-1.5 flex items-center gap-1.5">
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono">{tool.category}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col h-full relative">
        {/* Canvas Toolbar */}
        <div className="h-14 bg-slate-950/80 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="bg-transparent font-semibold text-sm text-slate-200 focus:outline-none focus:border-b border-indigo-500"
            />
            {validation && (
              <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                validation.is_valid ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
              }`}>
                {validation.is_valid ? 'DAG Valid' : 'Invalid Graph'}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveWorkflow}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors border border-slate-700"
            >
              <Save className="w-3.5 h-3.5" />
              Save Workflow
            </button>
            <button
              onClick={handleValidateAndRun}
              disabled={isRunning}
              className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {isRunning ? 'Running...' : 'Execute DAG'}
            </button>
          </div>
        </div>

        {/* React Flow Area */}
        <div className="flex-1 w-full h-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background color="#1e293b" gap={16} />
            <Controls />
            <MiniMap style={{ background: '#020617', borderRadius: '8px' }} />
          </ReactFlow>
        </div>

        {/* Node Configuration Inspector Drawer */}
        {selectedNode && (
          <div className="absolute right-4 top-16 w-80 bg-slate-950/95 backdrop-blur border border-slate-800 rounded-xl p-4 shadow-xl z-20 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-slate-200">Node Inspector</span>
              <button onClick={() => setSelectedNode(null)} className="text-slate-500 hover:text-slate-300 text-xs">✕</button>
            </div>
            <div>
              <label className="text-[11px] text-slate-400">Node ID</label>
              <div className="text-xs font-mono text-indigo-400">{selectedNode.id}</div>
            </div>
            <div>
              <label className="text-[11px] text-slate-400">Tool Type</label>
              <div className="text-xs font-medium text-slate-300">{selectedNode.data?.type}</div>
            </div>
            <div className="space-y-2 pt-2">
              <label className="text-[11px] text-slate-400">Parameters (JSON / Values)</label>
              {Object.keys(selectedNode.data || {})
                .filter(k => k !== 'label' && k !== 'type')
                .map((key) => (
                  <div key={key}>
                    <span className="text-[10px] text-slate-500 capitalize">{key}</span>
                    <input
                      type="text"
                      value={selectedNode.data[key] || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setNodes(nds => nds.map(n => n.id === selectedNode.id ? { ...n, data: { ...n.data, [key]: val } } : n));
                        setSelectedNode((prev: any) => ({ ...prev, data: { ...prev.data, [key]: val } }));
                      }}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 mt-0.5 font-mono"
                    />
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
