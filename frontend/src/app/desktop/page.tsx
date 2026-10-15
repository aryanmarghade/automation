'use client';

import React, { useState, useEffect } from 'react';
import { 
  AppWindow, 
  Terminal, 
  Play, 
  Camera, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Layers, 
  Cpu, 
  ShieldCheck, 
  RefreshCw,
  Eye,
  Keyboard,
  MousePointer
} from 'lucide-react';
import { ToolService } from '@/services/api';

export default function DesktopPage() {
  const [windows, setWindows] = useState<any[]>([]);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [selectedWindow, setSelectedWindow] = useState<string>('');
  const [appName, setAppName] = useState('notepad.exe');
  const [textToType, setTextToType] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionResult, setActionResult] = useState<any>(null);
  const [windowControls, setWindowControls] = useState<any[]>([]);

  const fetchSystemData = async () => {
    try {
      const [winRes, sysRes] = await Promise.all([
        ToolService.test('windows_desktop_automation', { action: 'list_open_windows' }),
        ToolService.test('windows_desktop_automation', { action: 'get_system_info' })
      ]);
      if (winRes?.windows) setWindows(winRes.windows);
      if (sysRes) setSystemInfo(sysRes);
    } catch (e) {}
  };

  useEffect(() => {
    fetchSystemData();
  }, []);

  const handleRunAction = async (action: string, extraParams = {}) => {
    setLoading(true);
    setActionResult(null);
    try {
      const payload: any = {
        action,
        app_name: appName,
        window_title: selectedWindow,
        text_to_type: textToType,
        ...extraParams
      };
      const res = await ToolService.test('windows_desktop_automation', payload);
      setActionResult(res);

      if (action === 'inspect_window_controls' && res.controls) {
        setWindowControls(res.controls);
      }
      await fetchSystemData();
    } catch (e: any) {
      setActionResult({ error: e.message, is_success: false });
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
            <AppWindow className="w-5 h-5 text-indigo-400" />
            Windows Desktop Automation Control Panel
          </h1>
          <p className="text-xs text-slate-400">Native Windows UIAutomation & pywinauto agent controller with accessible tree inspection.</p>
        </div>

        <div className="flex items-center gap-2 text-xs bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Security: Approved Process Whitelist Enforced</span>
        </div>
      </div>

      {/* System Metrics Banner */}
      {systemInfo && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Operating System</span>
            <div className="text-xs font-semibold text-slate-200 mt-0.5">{systemInfo.os} {systemInfo.release}</div>
          </div>
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Logical CPUs</span>
            <div className="text-xs font-semibold text-slate-200 mt-0.5">{systemInfo.cpu_count} Cores</div>
          </div>
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase font-mono">System Memory</span>
            <div className="text-xs font-semibold text-slate-200 mt-0.5">{systemInfo.ram_available_gb} GB / {systemInfo.ram_total_gb} GB Free</div>
          </div>
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
            <span className="text-[10px] text-slate-500 uppercase font-mono">CPU Utilization</span>
            <div className="text-xs font-semibold text-emerald-400 mt-0.5">{systemInfo.cpu_percent}% Active</div>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: App Launcher & Controls */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
          <h2 className="text-sm font-semibold text-slate-200">Application Operations</h2>

          <div className="space-y-3">
            <div>
              <label className="text-[11px] text-slate-400">Launch Approved Application</label>
              <div className="flex items-center gap-2 mt-1">
                <select
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                  className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono flex-1 focus:outline-none"
                >
                  <option value="notepad.exe">notepad.exe (Text Editor)</option>
                  <option value="calc.exe">calc.exe (Calculator)</option>
                  <option value="explorer.exe">explorer.exe (File Explorer)</option>
                  <option value="mspaint.exe">mspaint.exe (Paint)</option>
                </select>
                <button
                  onClick={() => handleRunAction('launch_app')}
                  disabled={loading}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition-colors flex items-center gap-1"
                >
                  <Play className="w-3 h-3 fill-current" />
                  Launch
                </button>
              </div>
            </div>

            <div>
              <label className="text-[11px] text-slate-400">Target Window Title</label>
              <input
                type="text"
                value={selectedWindow}
                onChange={(e) => setSelectedWindow(e.target.value)}
                placeholder="e.g. 'Notepad' or 'Calculator'"
                className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 font-mono"
              />
            </div>

            <div>
              <label className="text-[11px] text-slate-400">Keyboard Input (Text to Type)</label>
              <textarea
                rows={2}
                value={textToType}
                onChange={(e) => setTextToType(e.target.value)}
                placeholder="Enter text to type into the focused window..."
                className="w-full bg-slate-900 border border-slate-800 rounded p-2 text-xs text-slate-200 mt-1 resize-none"
              />
            </div>

            <div className="flex items-center gap-2 pt-2 flex-wrap">
              <button
                onClick={() => handleRunAction('type_text')}
                disabled={loading || !textToType}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Keyboard className="w-3.5 h-3.5 text-indigo-400" />
                Send Keys
              </button>

              <button
                onClick={() => handleRunAction('inspect_window_controls')}
                disabled={loading || !selectedWindow}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Eye className="w-3.5 h-3.5 text-blue-400" />
                Inspect Controls
              </button>

              <button
                onClick={() => handleRunAction('capture_screenshot')}
                disabled={loading}
                className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 rounded text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Camera className="w-3.5 h-3.5 text-purple-400" />
                Screenshot
              </button>
            </div>
          </div>
        </div>

        {/* Center/Right: Open Windows & Accessible Controls Inspector */}
        <div className="lg:col-span-2 space-y-4">
          {/* Active Windows List */}
          <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
              <h2 className="text-sm font-semibold text-slate-200">Detected Desktop Windows ({windows.length})</h2>
              <button onClick={fetchSystemData} className="text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1">
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
              {windows.map((win, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedWindow(win.title)}
                  className={`text-left p-2.5 rounded-lg border text-xs transition-all ${
                    selectedWindow === win.title
                      ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/50'
                      : 'bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold truncate">{win.title}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">Class: {win.class_name || 'Generic'}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Action Result & Control Telemetry */}
          {actionResult && (
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-200">Execution Result</h3>
                <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
                  actionResult.is_success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {actionResult.is_success ? 'Success' : 'Error'}
                </span>
              </div>

              {actionResult.screenshot_file && (
                <div className="rounded-lg overflow-hidden border border-slate-800 bg-black/40 max-h-72 flex items-center justify-center">
                  <img
                    src={`http://127.0.0.1:8000/artifacts/${actionResult.screenshot_file}`}
                    alt="Desktop Screenshot"
                    className="max-h-72 w-auto object-contain"
                  />
                </div>
              )}

              <pre className="text-[10px] font-mono bg-slate-900 p-2.5 rounded border border-slate-800 text-slate-300 overflow-x-auto max-h-36">
                {JSON.stringify(actionResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
