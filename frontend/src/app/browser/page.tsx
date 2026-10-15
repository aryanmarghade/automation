'use client';

import React, { useState } from 'react';
import { 
  Globe, 
  Search, 
  Play, 
  ExternalLink, 
  Camera, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Download,
  Loader2,
  ShieldCheck,
  Compass
} from 'lucide-react';
import { ToolService } from '@/services/api';

export default function BrowserPage() {
  const [activeTab, setActiveTab] = useState<'research' | 'navigate'>('research');
  const [query, setQuery] = useState('');
  const [url, setUrl] = useState('https://news.ycombinator.com');
  const [selector, setSelector] = useState('');
  const [fillText, setFillText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleRunAction = async (action: string) => {
    setLoading(true);
    setResult(null);
    try {
      const payload: any = { action };
      if (action === 'research_topic' || action === 'search_web') {
        payload.query = query;
      } else {
        payload.url = url;
        if (selector) payload.selector = selector;
        if (fillText) payload.fill_text = fillText;
      }

      const res = await ToolService.test('browser_playwright', payload);
      setResult(res);
    } catch (e: any) {
      setResult({ error: e.message, is_success: false });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-400" />
            Browser & Web Research Engine
          </h1>
          <p className="text-xs text-slate-400">Playwright-managed isolated Chromium browser with screenshot capture, navigation, and web research.</p>
        </div>

        <div className="flex items-center gap-2 text-xs bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Profile: Isolated Chromium Session</span>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div className="flex border-b border-slate-800 gap-6">
        <button
          onClick={() => setActiveTab('research')}
          className={`pb-2.5 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
            activeTab === 'research' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-300'
          }`}
        >
          <Search className="w-3.5 h-3.5" />
          Autonomous Web Research
        </button>
        <button
          onClick={() => setActiveTab('navigate')}
          className={`pb-2.5 text-xs font-semibold flex items-center gap-2 transition-all border-b-2 ${
            activeTab === 'navigate' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-300'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          Browser Navigation & Interaction
        </button>
      </div>

      {/* Control Panel */}
      <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        {activeTab === 'research' ? (
          <div className="space-y-3">
            <label className="text-xs font-medium text-slate-300">Research Topic or Query</label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g. 'Latest developments in local AI agent frameworks'"
                className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
              />
              <button
                onClick={() => handleRunAction('research_topic')}
                disabled={loading || !query.trim()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all shrink-0"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                Run Web Research
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-slate-400">Target URL</label>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 font-mono"
                />
              </div>
              <div>
                <label className="text-[11px] text-slate-400">Element Selector (Optional)</label>
                <input
                  type="text"
                  value={selector}
                  onChange={(e) => setSelector(e.target.value)}
                  placeholder="e.g. 'button.submit' or 'input#name'"
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 font-mono"
                />
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={() => handleRunAction('navigate_and_extract')}
                disabled={loading}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Play className="w-3 h-3 fill-current" />
                Navigate & Extract
              </button>

              <button
                onClick={() => handleRunAction('screenshot')}
                disabled={loading}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Camera className="w-3.5 h-3.5 text-purple-400" />
                Capture Full Screenshot
              </button>

              <button
                onClick={() => handleRunAction('click_and_fill')}
                disabled={loading || !selector}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                Click & Fill Form
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results Telemetry Panel */}
      {result && (
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-sm font-semibold text-slate-200">Execution Output</h2>
            <span className={`text-[11px] px-2 py-0.5 rounded font-mono ${
              result.is_success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
            }`}>
              {result.is_success ? 'Success' : 'Error'}
            </span>
          </div>

          {result.screenshot_file && (
            <div className="space-y-2">
              <span className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                <Camera className="w-3.5 h-3.5 text-purple-400" />
                Captured Page Screenshot:
              </span>
              <div className="rounded-lg overflow-hidden border border-slate-800 bg-black/40 max-h-80 flex items-center justify-center">
                <img
                  src={`http://127.0.0.1:8000/artifacts/${result.screenshot_file}`}
                  alt="Browser Screenshot"
                  className="max-h-80 w-auto object-contain"
                />
              </div>
            </div>
          )}

          {result.sources_consulted && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-slate-300">Verified Sources & Citations</h3>
              <div className="space-y-2">
                {result.sources_consulted.map((s: any, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-indigo-300">{s.source_title}</span>
                      <a href={s.source_url} target="_blank" rel="noreferrer" className="text-[10px] text-slate-500 hover:text-indigo-400 flex items-center gap-1">
                        Open Link <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <p className="text-[11px] text-slate-400">{s.evidence_snippet}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.text_preview && (
            <div className="space-y-1">
              <span className="text-xs font-medium text-slate-400">Visible Page Text Preview ({result.character_length} characters)</span>
              <pre className="text-[11px] font-mono bg-slate-900 p-3 rounded-lg border border-slate-800 text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                {result.text_preview}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
