'use client';

import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Server, 
  Sparkles, 
  CheckCircle, 
  AlertCircle, 
  Sliders, 
  Key, 
  ShieldCheck, 
  Save, 
  RefreshCw,
  Zap
} from 'lucide-react';

export default function SettingsPage() {
  const [provider, setProvider] = useState('ollama');
  const [model, setModel] = useState('llama3.2:latest');
  const [ollamaUrl, setOllamaUrl] = useState('http://127.0.0.1:11434');
  const [temperature, setTemperature] = useState(0.2);
  const [maxSteps, setMaxSteps] = useState(10);
  const [isSaved, setIsSaved] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    // Check local Ollama health
    fetch('http://127.0.0.1:11434/api/tags')
      .then(res => {
        if (res.ok) setOllamaStatus('online');
        else setOllamaStatus('offline');
      })
      .catch(() => setOllamaStatus('offline'));
  }, [ollamaUrl]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-5 h-5 text-indigo-400" />
            AI Providers & Model Configuration
          </h1>
          <p className="text-xs text-slate-400">Configure local Ollama LLM endpoints, autonomous agent parameters, and cloud provider keys.</p>
        </div>

        <div className="flex items-center gap-2 text-xs bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <Server className="w-4 h-4 text-indigo-400" />
          <span>Engine: Local-First Runtime</span>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Ollama Connection Card */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-semibold text-slate-200">Local Ollama Service</h2>
            </div>
            <div className="flex items-center gap-1.5 text-xs">
              {ollamaStatus === 'online' ? (
                <span className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-mono">
                  <CheckCircle className="w-3 h-3" /> Online (11434)
                </span>
              ) : (
                <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 font-mono">
                  <AlertCircle className="w-3 h-3" /> Fallback Planner Active
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Ollama Endpoint URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={e => setOllamaUrl(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-medium">Primary Active Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="llama3.2:latest">llama3.2:latest (General ReAct Agent)</option>
                <option value="qwen2.5-coder:7b">qwen2.5-coder:7b (Workflow Code & Logic)</option>
                <option value="mistral:latest">mistral:latest (Document Analysis)</option>
                <option value="deepseek-r1:latest">deepseek-r1:latest (Deep Reasoning)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Agent Inference Parameters */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-slate-200">ReAct Autonomous Loop Settings</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="space-y-2">
              <div className="flex justify-between text-slate-300">
                <label className="font-medium">Model Temperature</label>
                <span className="font-mono text-indigo-400">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={e => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <p className="text-[11px] text-slate-500">Lower values produce deterministic tool calls; higher values increase exploratory planning.</p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-slate-300">
                <label className="font-medium">Max Agent Iteration Steps</label>
                <span className="font-mono text-indigo-400">{maxSteps} steps</span>
              </div>
              <input
                type="range"
                min="3"
                max="25"
                step="1"
                value={maxSteps}
                onChange={e => setMaxSteps(parseInt(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <p className="text-[11px] text-slate-500">Guards against runaway loops by terminating after max verification attempts.</p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex items-center justify-between pt-2">
          {isSaved ? (
            <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
              <CheckCircle className="w-4 h-4" /> Settings updated successfully
            </span>
          ) : <div />}

          <button
            type="submit"
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Save className="w-4 h-4" />
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}
