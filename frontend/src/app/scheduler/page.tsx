'use client';

import React, { useState, useEffect } from 'react';
import { 
  CalendarClock, 
  Play, 
  Pause, 
  Trash2, 
  Plus, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  RefreshCw,
  Workflow,
  Globe
} from 'lucide-react';
import { ScheduleService, WorkflowService } from '@/services/api';

export default function SchedulerPage() {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form states
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [scheduleName, setScheduleName] = useState('');
  const [scheduleType, setScheduleType] = useState('interval'); // interval, cron
  const [intervalSeconds, setIntervalSeconds] = useState(3600);
  const [cronExpr, setCronExpr] = useState('0 9 * * *');
  const [timezone, setTimezone] = useState('UTC');

  const loadData = async () => {
    try {
      const [scheds, wfs] = await Promise.all([
        ScheduleService.list(),
        WorkflowService.list()
      ]);
      setSchedules(scheds);
      setWorkflows(wfs);
      if (wfs.length > 0 && !selectedWorkflowId) {
        setSelectedWorkflowId(wfs[0].id);
      }
    } catch (e) {}
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedWorkflowId) return;
    setLoading(true);

    try {
      await ScheduleService.create({
        workflow_id: selectedWorkflowId,
        name: scheduleName || `Schedule for ${workflows.find(w => w.id === selectedWorkflowId)?.name}`,
        schedule_type: scheduleType,
        interval_seconds: scheduleType === 'interval' ? Number(intervalSeconds) : null,
        cron_expression: scheduleType === 'cron' ? cronExpr : null,
        timezone: timezone,
        is_active: true
      });
      setShowModal(false);
      setScheduleName('');
      await loadData();
    } catch (err: any) {
      alert(`Failed to create schedule: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (sched: any) => {
    try {
      if (sched.is_active) {
        await ScheduleService.pause(sched.id);
      } else {
        await ScheduleService.resume(sched.id);
      }
      await loadData();
    } catch (e: any) {
      alert(`Toggle failed: ${e.message}`);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this schedule?')) {
      await ScheduleService.delete(id);
      await loadData();
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-indigo-400" />
            Workflow Scheduler & Background Jobs
          </h1>
          <p className="text-xs text-slate-400">Independent background execution engine with interval triggers, cron schedules, and persistent history.</p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-600/20 flex items-center gap-2 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create New Schedule
        </button>
      </div>

      {/* Schedules List */}
      {schedules.length === 0 ? (
        <div className="py-16 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
          No automated schedules configured. Click &quot;Create New Schedule&quot; to set up recurring background tasks.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {schedules.map((sched) => {
            const wf = workflows.find(w => w.id === sched.workflow_id);
            return (
              <div key={sched.id} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200 truncate">{sched.name}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-mono font-bold ${
                      sched.is_active ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}>
                      {sched.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <Workflow className="w-3.5 h-3.5 text-purple-400" />
                    <span className="truncate">{wf ? wf.name : `Workflow: ${sched.workflow_id}`}</span>
                  </div>

                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800/80 text-[10px] font-mono text-slate-300 space-y-1">
                    <div>Type: <span className="text-indigo-400">{sched.schedule_type}</span></div>
                    {sched.interval_seconds && <div>Every: <span className="text-indigo-400">{sched.interval_seconds}s ({(sched.interval_seconds / 60).toFixed(0)}m)</span></div>}
                    {sched.cron_expression && <div>Cron: <span className="text-indigo-400">{sched.cron_expression}</span></div>}
                    <div>Timezone: <span className="text-slate-400">{sched.timezone || 'UTC'}</span></div>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                  <button
                    onClick={() => handleToggleActive(sched)}
                    className={`px-2.5 py-1 rounded text-xs font-medium flex items-center gap-1 transition-colors ${
                      sched.is_active ? 'bg-slate-900 hover:bg-slate-800 text-amber-400' : 'bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-400 border border-emerald-800/30'
                    }`}
                  >
                    {sched.is_active ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                    {sched.is_active ? 'Pause' : 'Resume'}
                  </button>

                  <button
                    onClick={() => handleDelete(sched.id)}
                    className="text-slate-500 hover:text-red-400 p-1 rounded transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Schedule Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold text-white">Create Automated Schedule</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-slate-300">✕</button>
            </div>

            <form onSubmit={handleCreateSchedule} className="space-y-3">
              <div>
                <label className="text-[11px] text-slate-400">Schedule Name</label>
                <input
                  type="text"
                  value={scheduleName}
                  onChange={(e) => setScheduleName(e.target.value)}
                  placeholder="e.g. 'Daily Morning ETL Report'"
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400">Select Target Workflow</label>
                <select
                  value={selectedWorkflowId}
                  onChange={(e) => setSelectedWorkflowId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 focus:outline-none"
                >
                  {workflows.map(w => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[11px] text-slate-400">Schedule Frequency Type</label>
                <select
                  value={scheduleType}
                  onChange={(e) => setScheduleType(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 focus:outline-none"
                >
                  <option value="interval">Recurring Interval (Seconds/Minutes)</option>
                  <option value="cron">Cron Expression (e.g. 0 9 * * *)</option>
                </select>
              </div>

              {scheduleType === 'interval' ? (
                <div>
                  <label className="text-[11px] text-slate-400">Interval in Seconds</label>
                  <input
                    type="number"
                    value={intervalSeconds}
                    onChange={(e) => setIntervalSeconds(Number(e.target.value))}
                    min={10}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 font-mono focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5">3600 = 1 hour, 86400 = 1 day</span>
                </div>
              ) : (
                <div>
                  <label className="text-[11px] text-slate-400">Cron Expression (5-part)</label>
                  <input
                    type="text"
                    value={cronExpr}
                    onChange={(e) => setCronExpr(e.target.value)}
                    placeholder="0 9 * * *"
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 mt-1 font-mono focus:outline-none"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5">Format: minute hour day month day-of-week</span>
                </div>
              )}

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold shadow-sm transition-all"
                >
                  {loading ? 'Creating...' : 'Save Schedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
