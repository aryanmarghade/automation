'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  Bot, 
  Send, 
  Paperclip, 
  Sparkles, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  FileText, 
  Download, 
  Play, 
  Pause,
  StopCircle,
  RotateCcw,
  SlidersHorizontal,
  ChevronRight,
  ShieldAlert,
  Loader2,
  Workflow,
  ArrowUpRight,
  Check,
  X,
  MessageSquare
} from 'lucide-react';
import { AgentService, FileService } from '@/services/api';

export default function AgentPage() {
  const router = useRouter();
  const [objective, setObjective] = useState('');
  const [autonomyLevel, setAutonomyLevel] = useState('supervised');
  const [selectedModel, setSelectedModel] = useState('llama3.2:latest');
  const [attachedFiles, setAttachedFiles] = useState<string[]>([]);
  const [workspaceFiles, setWorkspaceFiles] = useState<any[]>([]);

  // Execution states
  const [isPlanning, setIsPlanning] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentPlan, setCurrentPlan] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [approvalStep, setApprovalStep] = useState<any>(null);
  const [convertingWorkflow, setConvertingWorkflow] = useState(false);

  // Chat message history
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'agent' | 'system'; text: string; time: string }>>([
    {
      role: 'agent',
      text: 'Hello! I am your NexusFlow autonomous assistant. Describe an objective (e.g. analyze datasets, perform web research, inspect PDFs, or extract tables) and I will construct and execute a verified pipeline.',
      time: 'Ready'
    }
  ]);

  useEffect(() => {
    FileService.listFiles().then(setWorkspaceFiles).catch(() => {});
  }, []);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!objective.trim() || isPlanning || isExecuting) return;

    const userText = objective.trim();
    setChatMessages(prev => [...prev, {
      role: 'user',
      text: userText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);

    setIsPlanning(true);
    setCurrentPlan(null);
    setExecutionResult(null);

    try {
      const plan = await AgentService.plan(userText, attachedFiles, 'ollama', selectedModel);
      setCurrentPlan(plan);

      setChatMessages(prev => [...prev, {
        role: 'agent',
        text: `Formulated structured plan with ${plan.steps?.length || 0} steps. ${plan.plan_rationale || ''}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);

      if (autonomyLevel === 'autonomous') {
        await handleExecutePlan(plan, userText);
      }
    } catch (err: any) {
      setChatMessages(prev => [...prev, {
        role: 'system',
        text: `Planning error: ${err.message || 'Check backend connection'}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsPlanning(false);
    }
  };

  const handleExecutePlan = async (planToRun = currentPlan, currentObjective = objective) => {
    if (!planToRun) return;
    setIsExecuting(true);
    setIsPaused(false);

    try {
      const res = await AgentService.execute(currentObjective, planToRun, autonomyLevel, 'ollama', selectedModel);
      setActiveTaskId(res.id);
      setExecutionResult(res);

      setChatMessages(prev => [...prev, {
        role: 'agent',
        text: `Execution finished with status: ${res.status}. ${res.final_summary || ''}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch (e: any) {
      setChatMessages(prev => [...prev, {
        role: 'system',
        text: `Execution failed: ${e.message}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsExecuting(false);
    }
  };

  const handlePause = async () => {
    if (!activeTaskId) return;
    try {
      await AgentService.pauseTask(activeTaskId);
      setIsPaused(true);
    } catch (e) {}
  };

  const handleResume = async () => {
    if (!activeTaskId) return;
    try {
      await AgentService.resumeTask(activeTaskId);
      setIsPaused(false);
    } catch (e) {}
  };

  const handleCancel = async () => {
    if (!activeTaskId) return;
    try {
      await AgentService.cancelTask(activeTaskId);
      setIsExecuting(false);
      setIsPaused(false);
    } catch (e) {}
  };

  const handleConvertToWorkflow = async () => {
    if (!currentPlan) return;
    setConvertingWorkflow(true);
    try {
      const wf = await AgentService.convertToWorkflow(currentPlan, `Workflow: ${objective.slice(0, 30)}...`);
      router.push(`/builder?id=${wf.id}`);
    } catch (e: any) {
      alert(`Conversion failed: ${e.message}`);
    } finally {
      setConvertingWorkflow(false);
    }
  };

  const toggleFileAttach = (filename: string) => {
    setAttachedFiles(prev => 
      prev.includes(filename) ? prev.filter(f => f !== filename) : [...prev, filename]
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Bot className="w-5 h-5 text-indigo-400" />
            Autonomous AI Agent
          </h1>
          <p className="text-xs text-slate-400">Natural language goal planner with bounded tool chaining, verification, and visual DAG synthesis.</p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px] text-slate-500">Mode:</span>
            <select
              value={autonomyLevel}
              onChange={(e) => setAutonomyLevel(e.target.value)}
              className="bg-transparent text-indigo-400 font-medium focus:outline-none cursor-pointer"
            >
              <option value="supervised" className="bg-slate-900">Supervised (Approve)</option>
              <option value="autonomous" className="bg-slate-900">Autonomous (Direct)</option>
              <option value="assist" className="bg-slate-900">Assist (Strict Safety)</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-xs text-slate-300">
            <span className="text-[11px] text-slate-500">Model:</span>
            <span className="text-xs font-mono text-slate-300">{selectedModel}</span>
          </div>
        </div>
      </div>

      {/* Chat & Prompt Interface */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 shadow-sm space-y-4">
        {/* Chat History Stream */}
        <div className="space-y-3 max-h-56 overflow-y-auto pr-1 divide-y divide-slate-900">
          {chatMessages.map((msg, i) => (
            <div key={i} className="pt-2 flex items-start gap-3">
              <div className={`p-1.5 rounded-lg shrink-0 ${
                msg.role === 'user' ? 'bg-indigo-600/20 text-indigo-400' :
                msg.role === 'agent' ? 'bg-emerald-600/20 text-emerald-400' :
                'bg-red-600/20 text-red-400'
              }`}>
                {msg.role === 'user' ? <MessageSquare className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-slate-300 capitalize">{msg.role}</span>
                  <span className="text-[10px] text-slate-500 font-mono">{msg.time}</span>
                </div>
                <p className="text-xs text-slate-300 mt-0.5">{msg.text}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Input Bar */}
        <div className="space-y-3 pt-2 border-t border-slate-800/80">
          <textarea
            rows={2}
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="Describe your objective in natural language... (e.g. 'Analyze test_sales.csv, detect revenue anomalies, and generate a category breakdown chart')"
            className="w-full bg-slate-900/70 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 resize-none"
          />

          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                <Paperclip className="w-3.5 h-3.5" /> Attach Files:
              </span>
              {workspaceFiles.map(file => {
                const isSelected = attachedFiles.includes(file.name);
                return (
                  <button
                    key={file.name}
                    type="button"
                    onClick={() => toggleFileAttach(file.name)}
                    className={`text-[10px] px-2 py-0.5 rounded-md border transition-colors flex items-center gap-1 ${
                      isSelected
                        ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40 font-medium'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    {file.name}
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleSendMessage}
              disabled={isPlanning || isExecuting || !objective.trim()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all shrink-0"
            >
              {isPlanning ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Formulating Plan...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Plan & Execute
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Plan Preview & Execution Live Stream */}
      {currentPlan && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Plan Breakdown */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-200">Execution Plan</h2>
                <p className="text-[11px] text-slate-400 mt-0.5">{currentPlan.plan_rationale || 'Structured tool pipeline'}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleConvertToWorkflow}
                  disabled={convertingWorkflow}
                  className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  <Workflow className="w-3 h-3 text-purple-400" />
                  {convertingWorkflow ? 'Converting...' : 'Convert to Visual DAG'}
                </button>

                {!executionResult && (
                  <button
                    onClick={() => handleExecutePlan()}
                    disabled={isExecuting}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all"
                  >
                    {isExecuting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3 fill-current" />}
                    Confirm & Execute
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-2.5">
              {currentPlan.steps?.map((step: any, idx: number) => (
                <div key={step.step_id || idx} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] flex items-center justify-center border border-indigo-500/30 font-bold">
                        {idx + 1}
                      </span>
                      {step.tool_id}
                    </span>
                    <span className="text-[10px] text-slate-500 uppercase font-mono">{step.step_id}</span>
                  </div>
                  <p className="text-xs text-slate-300">{step.description}</p>
                  <div className="text-[11px] text-slate-500 bg-slate-950/80 p-2 rounded border border-slate-800/60 font-mono overflow-x-auto">
                    {JSON.stringify(step.parameters, null, 2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Results & Verification Timeline */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-sm font-semibold text-slate-200">Execution Results & Artifacts</h2>
              
              {isExecuting && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={isPaused ? handleResume : handlePause}
                    className="p-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
                  >
                    {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={handleCancel}
                    className="p-1.5 rounded bg-red-950/40 hover:bg-red-900/50 text-red-400 border border-red-800/40"
                  >
                    <StopCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {executionResult && (
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                  executionResult.status === 'completed'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                }`}>
                  {executionResult.status}
                </span>
              )}
            </div>

            {isExecuting && (
              <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-3">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                <p className="text-xs">Executing step-by-step tool loop...</p>
              </div>
            )}

            {executionResult && (
              <div className="space-y-4">
                {/* Final Summary */}
                <div className="p-3.5 rounded-lg bg-indigo-950/20 border border-indigo-800/30 text-xs text-indigo-300 flex items-start gap-2.5">
                  <CheckCircle className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="font-semibold text-indigo-200">Execution Summary</div>
                    <div className="mt-0.5">{executionResult.final_summary}</div>
                  </div>
                </div>

                {/* Generated Artifacts */}
                {executionResult.artifacts?.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-xs font-semibold text-slate-300">Generated Deliverables</h3>
                    <div className="grid grid-cols-1 gap-2">
                      {executionResult.artifacts.map((art: any, i: number) => (
                        <div key={i} className="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-emerald-400" />
                            <div>
                              <div className="text-xs font-medium text-slate-200">{art.filename}</div>
                              <div className="text-[10px] text-slate-500 capitalize">{art.type} Artifact</div>
                            </div>
                          </div>
                          <a
                            href={`http://127.0.0.1:8000/artifacts/${art.filename}`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded text-xs font-medium flex items-center gap-1 transition-colors"
                          >
                            <Download className="w-3 h-3" />
                            View File
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Step Outputs */}
                <div className="space-y-2">
                  <h3 className="text-xs font-semibold text-slate-300">Step Telemetry</h3>
                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {executionResult.steps_history?.map((sh: any, i: number) => (
                      <div key={i} className="p-2.5 rounded bg-slate-900/80 border border-slate-800 text-[11px] space-y-1">
                        <div className="flex items-center justify-between font-mono text-slate-400">
                          <span>{sh.step_id} ({sh.tool_id})</span>
                          <span className={sh.status === 'completed' ? 'text-emerald-400' : 'text-red-400'}>{sh.status}</span>
                        </div>
                        <pre className="text-slate-300 font-mono text-[10px] bg-slate-950 p-2 rounded overflow-x-auto">
                          {JSON.stringify(sh.output, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
