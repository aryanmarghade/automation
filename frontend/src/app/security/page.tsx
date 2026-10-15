'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Lock, 
  AlertTriangle, 
  CheckCircle, 
  Terminal, 
  Globe, 
  FolderGit2, 
  AppWindow,
  Cpu
} from 'lucide-react';
import { ToolService } from '@/services/api';

export default function SecurityPage() {
  const [tools, setTools] = useState<any[]>([]);

  useEffect(() => {
    ToolService.list().then(setTools).catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-5xl mx-auto w-full space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Security Boundaries & Permissions
          </h1>
          <p className="text-xs text-slate-400">Strict process allowlists, SSRF metadata filtering, and filesystem sandboxing enforcement.</p>
        </div>

        <div className="flex items-center gap-2 text-xs bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg text-emerald-400 font-medium">
          <CheckCircle className="w-4 h-4" />
          <span>Local Security Policy Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Desktop Whitelist Card */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
            <AppWindow className="w-4 h-4 text-indigo-400" />
            Windows Desktop Process Allowlist
          </div>
          <p className="text-xs text-slate-400">
            Desktop UI automation operates strictly on an explicit whitelist. Arbitrary command shells (e.g. <code>cmd.exe</code>, <code>powershell.exe</code>) are prohibited.
          </p>
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono space-y-1 text-slate-300">
            <div className="text-emerald-400">✓ notepad.exe (Text editing)</div>
            <div className="text-emerald-400">✓ calc.exe (Windows Calculator)</div>
            <div className="text-emerald-400">✓ explorer.exe (File Manager)</div>
            <div className="text-emerald-400">✓ mspaint.exe (Paint)</div>
            <div className="text-red-400 line-through">✗ cmd.exe (Blocked)</div>
          </div>
        </div>

        {/* Browser SSRF Protection Card */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
            <Globe className="w-4 h-4 text-blue-400" />
            Browser SSRF & Sandbox Protection
          </div>
          <p className="text-xs text-slate-400">
            Playwright browser sessions are sandboxed against malicious requests and link-local metadata exfiltration.
          </p>
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono space-y-1 text-slate-300">
            <div className="text-emerald-400">✓ Strict http/https protocol enforcement</div>
            <div className="text-emerald-400">✓ Workspace sandbox for local file preview</div>
            <div className="text-red-400">✗ 169.254.169.254 (Cloud metadata blocked)</div>
            <div className="text-red-400">✗ Arbitrary filesystem traversal blocked</div>
          </div>
        </div>

        {/* Filesystem Sandbox */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
            <FolderGit2 className="w-4 h-4 text-amber-400" />
            Workspace Storage Boundary
          </div>
          <p className="text-xs text-slate-400">
            All analytical files, generated Excel sheets, CSV summaries, and screenshots are restricted to the local workspace folder.
          </p>
          <div className="p-3 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300">
            Sandbox Root: <span className="text-indigo-300">D:\projects\Automation\workspace</span>
          </div>
        </div>

        {/* Dynamic Risk Gating */}
        <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
            <Lock className="w-4 h-4 text-purple-400" />
            Tool Risk Classification
          </div>
          <p className="text-xs text-slate-400">
            Total of {tools.length} operational capabilities actively monitored with risk classification.
          </p>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">
            <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-medium">
              Low Risk
            </div>
            <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-medium">
              Medium Risk
            </div>
            <div className="p-2 rounded bg-red-500/10 border border-red-500/20 text-red-400 font-medium">
              High Risk
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
