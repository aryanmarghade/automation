'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Bot, 
  Workflow, 
  Library, 
  FolderGit2, 
  Globe, 
  Cpu, 
  Wrench, 
  History, 
  CalendarClock, 
  ShieldCheck, 
  Sliders,
  TerminalSquare
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: Sliders },
  { href: '/agent', label: 'AI Agent Execution', icon: Bot },
  { href: '/builder', label: 'Workflow Canvas', icon: Workflow },
  { href: '/library', label: 'Workflow Library', icon: Library },
  { href: '/files', label: 'File Workspace', icon: FolderGit2 },
  { href: '/tools', label: 'Tool Registry', icon: Wrench },
  { href: '/browser', label: 'Browser & Search', icon: Globe },
  { href: '/desktop', label: 'Windows Desktop', icon: Sliders },
  { href: '/history', label: 'Execution History', icon: History },
  { href: '/scheduler', label: 'Scheduler', icon: CalendarClock },
  { href: '/settings', label: 'AI Providers & Models', icon: Cpu },
  { href: '/security', label: 'Security & Permissions', icon: ShieldCheck },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen select-none shrink-0">
      <div className="p-4 border-b border-slate-800 flex items-center space-x-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <TerminalSquare className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-sm tracking-wide text-slate-100 flex items-center gap-1.5">
            NexusFlow AI
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Local</span>
          </h1>
          <p className="text-[11px] text-slate-400">Autonomous Workflow OS</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-[11px] text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Core: 127.0.0.1:8000</span>
        </div>
        <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">v1.0.0</span>
      </div>
    </aside>
  );
}
