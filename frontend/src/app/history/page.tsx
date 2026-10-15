'use client';

import React, { useState, useEffect } from 'react';
import { 
  History, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Terminal, 
  ChevronRight, 
  RotateCcw,
  Download,
  Filter,
  RefreshCw,
  FileText
} from 'lucide-react';
import { ExecutionService } from '@/services/api';

export default function HistoryPage() {
  const [executions, setExecutions] = useState<any[]>([]);
  const [selectedExec, setSelectedExec] = useState<any>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [retrying, setRetrying] = useState(false);

  const loadExecutions = async () => {
    try {
      const data = await ExecutionService.list();
      setExecutions(data);
      if (data.length > 0 && !selectedExec) {
        setSelectedExec(data[0]);
      }
    } catch (e) {}
  };

  useEffect(() => {
    loadExecutions();
  }, []);

  const handleRetry = async (execId: string) => {
    setRetrying(true);
    try {
      const newExec = await ExecutionService.retry(execId);
      await loadExecutions();
      setSelectedExec(newExec);
    } catch (e: any) {
      alert(`Retry failed: ${e.message}`);
    } finally {
      setRetrying(false);
    }
  };

  const filteredExecutions = executions.filter(e => {
    if (filterStatus === 'all') return true;
    return e.status === filterStatus;
  });

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Execution History & Monitoring
          </h1>
          <p className="text-xs text-slate-400">Audit logs, step-by-step node telemetry, generated artifacts, and safe retries.</p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-500">Status:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-transparent text-indigo-400 font-medium focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Runs</option>
              <option value="completed" className="bg-slate-900">Completed</option>
              <option value="failed" className="bg-slate-900">Failed</option>
              <option value="running" className="bg-slate-900">Running</option>
            </select>
          </div>

          <button
            onClick={loadExecutions}
            className="p-1.5 rounded-lg bg-slate-950 hover:bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Executions List */}
        <div className="lg:col-span-2 space-y-2.5">
          {filteredExecutions.length === 0 ? (
            <div className="py-16 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No executions found matching filter criteria.
            </div>
          ) : (
            filteredExecutions.map((exec) => {
              const isSelected = selectedExec?.id === exec.id;
              return (
                <div
                  key={exec.id}
                  onClick={() => setSelectedExec(exec)}
                  className={`p-4 rounded-xl bg-slate-950 border transition-all cursor-pointer flex items-center justify-between ${
                    isSelected ? 'border-indigo-500 ring-1 ring-indigo-500/30' : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold uppercase ${
                        exec.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                        exec.status === 'running' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                        'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}>
                        {exec.status}
                      </span>
                      <span className="text-xs font-mono text-slate-200">Execution: {exec.id.slice(0, 8)}...</span>
                      {exec.retry_count > 0 && (
                        <span className="text-[10px] px-1.5 rounded bg-slate-800 text-slate-400 font-mono">Retry #{exec.retry_count}</span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Trigger: <span className="capitalize text-slate-400 font-medium">{exec.trigger_type}</span> • Duration: {exec.duration_ms || 0}ms
                    </div>
                  </div>

                  <div className="text-right text-xs text-slate-400 font-mono flex items-center gap-2">
                    <span>{new Date(exec.started_at).toLocaleTimeString()}</span>
                    <ChevronRight className={`w-4 h-4 text-slate-500 transition-transform ${isSelected ? 'rotate-90 text-indigo-400' : ''}`} />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Execution Inspector Drawer */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h2 className="text-sm font-semibold text-slate-200">Execution Telemetry</h2>
            {selectedExec && (
              <button
                onClick={() => handleRetry(selectedExec.id)}
                disabled={retrying}
                className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded text-xs font-medium flex items-center gap-1 transition-colors"
              >
                <RotateCcw className="w-3 h-3 text-indigo-400" />
                {retrying ? 'Retrying...' : 'Safe Retry'}
              </button>
            )}
          </div>

          {selectedExec ? (
            <div className="space-y-3.5">
              <div>
                <span className="text-[10px] text-slate-500 uppercase font-mono">Execution ID</span>
                <div className="text-xs font-mono text-indigo-400 mt-0.5">{selectedExec.id}</div>
              </div>

              {selectedExec.error && (
                <div className="p-2.5 rounded bg-red-950/30 border border-red-800/40 text-xs text-red-300 space-y-1">
                  <div className="font-semibold text-red-200">Error Details:</div>
                  <div className="font-mono text-[11px]">{selectedExec.error}</div>
                </div>
              )}

              <div>
                <span className="text-[10px] text-slate-500 uppercase font-mono">Node States & Outputs</span>
                <pre className="text-[10px] font-mono bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-slate-300 overflow-x-auto max-h-48 mt-1">
                  {JSON.stringify(selectedExec.node_states || selectedExec.outputs, null, 2)}
                </pre>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase font-mono">Telemetry Log Stream ({selectedExec.logs?.length || 0} entries)</span>
                <div className="space-y-1 max-h-48 overflow-y-auto pr-1 mt-1">
                  {selectedExec.logs?.map((l: any, i: number) => (
                    <div key={i} className="text-[10px] font-mono text-slate-400 bg-slate-900/80 p-1.5 rounded border border-slate-800/40 flex items-start gap-1.5">
                      <span className="text-slate-500 shrink-0">[{l.level}]</span>
                      <span className="text-slate-300">{l.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              Select an execution to inspect logs and telemetry.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
