'use client';

import React, { useState, useEffect } from 'react';
import { Wrench, Shield, CheckCircle, Terminal, Play, Loader2 } from 'lucide-react';
import { ToolService } from '@/services/api';

export default function ToolsPage() {
  const [tools, setTools] = useState<any[]>([]);
  const [testingToolId, setTestingToolId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => {
    ToolService.list().then(setTools).catch(() => {});
  }, []);

  const handleTest = async (toolId: string) => {
    setTestingToolId(toolId);
    setTestResult(null);
    try {
      const res = await ToolService.test(toolId, {});
      setTestResult({ toolId, data: res });
    } catch (e: any) {
      setTestResult({ toolId, error: e.message });
    } finally {
      setTestingToolId(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Wrench className="w-5 h-5 text-indigo-400" />
          Dynamic Tool Registry
        </h1>
        <p className="text-xs text-slate-400">Validated operational capabilities exposed safely to the visual DAG canvas and ReAct agent planner.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {tools.map((tool) => (
          <div key={tool.id} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-200">{tool.name}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-bold ${
                  tool.risk_level === 'low' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                  tool.risk_level === 'medium' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                  'bg-red-500/10 text-red-400 border border-red-500/20'
                }`}>
                  Risk: {tool.risk_level}
                </span>
              </div>
              <p className="text-xs text-slate-400">{tool.description}</p>
              <div className="text-[11px] text-slate-500 font-mono">ID: {tool.id} • Category: {tool.category}</div>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
              <span className="text-[11px] text-slate-400">{tool.parameters?.length || 0} Configurable Params</span>
              <button
                onClick={() => handleTest(tool.id)}
                disabled={testingToolId === tool.id}
                className="px-3 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-xs font-medium text-indigo-300 flex items-center gap-1.5 transition-colors"
              >
                {testingToolId === tool.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                Run Health Test
              </button>
            </div>

            {testResult?.toolId === tool.id && (
              <div className="mt-2 p-2 rounded bg-slate-900 text-[10px] font-mono text-slate-300 overflow-x-auto border border-slate-800">
                {JSON.stringify(testResult.data || testResult.error, null, 2)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
