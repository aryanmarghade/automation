'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Library, Play, Trash2, Edit3, ArrowRight } from 'lucide-react';
import { WorkflowService } from '@/services/api';

export default function LibraryPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);

  const loadWorkflows = async () => {
    try {
      const data = await WorkflowService.list();
      setWorkflows(data);
    } catch (e) {}
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  const handleDelete = async (id: string) => {
    if (confirm('Delete this workflow?')) {
      await WorkflowService.delete(id);
      await loadWorkflows();
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Library className="w-5 h-5 text-indigo-400" />
            Workflow Library
          </h1>
          <p className="text-xs text-slate-400">Persisted reusable automation DAGs saved in local SQLite storage.</p>
        </div>

        <Link
          href="/builder"
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all"
        >
          Create New DAG
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {workflows.map((wf) => (
          <div key={wf.id} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 flex flex-col justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">{wf.name}</h3>
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{wf.description || 'No description provided.'}</p>
              <div className="mt-3 text-[11px] text-slate-500">
                {wf.nodes?.length || 0} Nodes • {wf.edges?.length || 0} Edges
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
              <button
                onClick={() => handleDelete(wf.id)}
                className="text-slate-500 hover:text-red-400 p-1 rounded transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>

              <Link
                href={`/builder?id=${wf.id}`}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-medium text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                Open in Canvas
                <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
