'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Bot, 
  Workflow, 
  CheckCircle2, 
  Clock, 
  Play, 
  FolderGit2, 
  Cpu, 
  ArrowUpRight,
  HardDrive,
  Activity
} from 'lucide-react';
import { WorkflowService, ExecutionService, FileService } from '@/services/api';

export default function DashboardPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [executions, setExecutions] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [wfs, execs, fls] = await Promise.all([
          WorkflowService.list().catch(() => []),
          ExecutionService.list().catch(() => []),
          FileService.listFiles().catch(() => []),
        ]);
        setWorkflows(wfs);
        setExecutions(execs);
        setFiles(fls);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">NexusFlow Control Center</h1>
          <p className="text-xs text-slate-400 mt-1">Autonomous orchestration, visual DAG builder, and system automation runtime</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/agent"
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Bot className="w-4 h-4" />
            Launch AI Agent Task
          </Link>
          <Link
            href="/builder"
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition-all"
          >
            <Workflow className="w-4 h-4 text-purple-400" />
            New Visual Workflow
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Workflows Saved</span>
            <Workflow className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white">{workflows.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Ready for execution</div>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Total Executions</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">{executions.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">Local runs recorded</div>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Workspace Files</span>
            <FolderGit2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{files.length}</div>
          <div className="text-[11px] text-slate-500 mt-1">PDFs, Excel & Data artifacts</div>
        </div>

        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">System Status</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1.5 mt-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            Active & Ready
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Ollama / Local Inference</div>
        </div>
      </div>

      {/* Quick Launch & Recent Executions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Workflows */}
        <div className="lg:col-span-2 p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">Active Workflows</h2>
            <Link href="/library" className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
              View All <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {workflows.length === 0 ? (
            <div className="py-10 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-lg">
              No saved workflows yet. Create your first visual DAG in the canvas editor.
            </div>
          ) : (
            <div className="divide-y divide-slate-800/80">
              {workflows.slice(0, 5).map((wf) => (
                <div key={wf.id} className="py-3 flex items-center justify-between">
                  <div>
                    <h3 className="text-xs font-semibold text-slate-200">{wf.name}</h3>
                    <p className="text-[11px] text-slate-500">{wf.nodes?.length || 0} nodes • Updated {new Date(wf.updated_at).toLocaleDateString()}</p>
                  </div>
                  <Link
                    href={`/builder?id=${wf.id}`}
                    className="px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors flex items-center gap-1.5"
                  >
                    <Play className="w-3 h-3 text-emerald-400 fill-emerald-400" />
                    Open Canvas
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Capabilities */}
        <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200">Platform Capabilities</h2>
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-3">
              <Bot className="w-4 h-4 text-indigo-400 mt-0.5" />
              <div>
                <h4 className="text-xs font-medium text-slate-200">Autonomous ReAct Loop</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Understands objectives, formulates bounded multi-step plans and handles recoverable errors.</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-3">
              <Workflow className="w-4 h-4 text-purple-400 mt-0.5" />
              <div>
                <h4 className="text-xs font-medium text-slate-200">Node-based Visual DAG</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">Topological dependency executor with condition branches, expressions, and retries.</p>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start gap-3">
              <FolderGit2 className="w-4 h-4 text-emerald-400 mt-0.5" />
              <div>
                <h4 className="text-xs font-medium text-slate-200">Data Intelligence & Reports</h4>
                <p className="text-[11px] text-slate-400 mt-0.5">PDF citations, DuckDB SQL analysis on spreadsheets, and chart generation.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
