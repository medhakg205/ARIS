// ============================================================
// ARIS — Live Monitor View
// Consumes /ws/telemetry/{run_id} — real-time telemetry display.
// Shows timeline charts, metric cards, runtime events, connection state.
// ============================================================

import React, { useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { Wifi, WifiOff, Activity } from 'lucide-react';
import { MetricBadge } from '../common/MetricBadge';
import type { TelemetrySample, RunRecord } from '../../types';

interface LiveMonitorViewProps {
  activeRun: RunRecord | null;
  wsConnected: boolean;
  isDemo: boolean;
  latestSamples: Record<string, TelemetrySample>;
  telemetryHistory: Record<string, TelemetrySample[]>;
  hardwareConnected: boolean;
  onStartRun: () => void;
}

const CHART_METRICS = [
  { key: 'loop_time', label: 'Loop Time (ms)', color: '#22d3ee', classification: 'MEASURED' as const },
  { key: 'cpu_load', label: 'CPU Load (%)', color: '#f59e0b', classification: 'ESTIMATED' as const },
  { key: 'sram_free', label: 'SRAM Free (B)', color: '#10b981', classification: 'MEASURED' as const },
  { key: 'interrupt_rate', label: 'IRQ Rate (Hz)', color: '#8b5cf6', classification: 'DERIVED' as const },
];

const LIVE_METRICS = [
  { key: 'loop_jitter', label: 'Jitter', unit: 'ms', classification: 'DERIVED' as const },
  { key: 'stack_used', label: 'Stack', unit: 'B', classification: 'DERIVED' as const },
  { key: 'gpio_activity', label: 'GPIO', unit: 'ev', classification: 'MEASURED' as const },
  { key: 'uart_activity', label: 'UART', unit: 'B', classification: 'MEASURED' as const },
  { key: 'adc_activity', label: 'ADC', unit: 'conv', classification: 'MEASURED' as const },
  { key: 'instrumentation_overhead', label: 'Probe OH', unit: 'µs', classification: 'MEASURED' as const },
];

export const LiveMonitorView: React.FC<LiveMonitorViewProps> = ({
  activeRun,
  wsConnected,
  isDemo,
  latestSamples,
  telemetryHistory,
  hardwareConnected,
  onStartRun,
}) => {
  const seqCount = useMemo(() => {
    const s = latestSamples['loop_time'];
    return s?.sequence ?? 0;
  }, [latestSamples]);

  if (!activeRun) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-500">
        <Activity className="w-12 h-12 text-slate-700" />
        <p className="font-mono text-sm">No active run. Start a run to begin live monitoring.</p>
        <button
          onClick={onStartRun}
          className="px-4 py-2 text-xs font-mono bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded hover:bg-cyan-500/20 transition-colors"
        >
          Start Demo Run
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto p-4 gap-4">
      {/* Connection Status Bar */}
      <div className="flex items-center gap-4 bg-slate-900/60 border border-slate-800 rounded px-4 py-2">
        {wsConnected ? (
          <><Wifi className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-mono text-emerald-400">WebSocket Live</span></>
        ) : (
          <><WifiOff className="w-4 h-4 text-red-400" />
          <span className="text-xs font-mono text-red-400">WebSocket Disconnected — Reconnecting…</span></>
        )}
        <div className="w-px h-4 bg-slate-800" />
        <span className="text-xs font-mono text-slate-500">Run: {activeRun.run_id}</span>
        <div className="w-px h-4 bg-slate-800" />
        <span className={`text-xs font-mono ${activeRun.status === 'RUNNING' || activeRun.status === 'COLLECTING' ? 'text-emerald-400' : 'text-slate-400'}`}>
          {activeRun.status}
        </span>
        <div className="flex-1" />
        <span className="text-[10px] font-mono text-slate-500">seq #{seqCount}</span>
        {isDemo && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 border border-amber-500/40 bg-amber-500/10 text-amber-400 rounded">
            SIMULATED
          </span>
        )}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CHART_METRICS.map(({ key, label, color, classification }) => {
          const history = telemetryHistory[key] || [];
          const chartData = history.slice(-80).map((s) => ({
            t: s.timestamp_ms,
            v: s.value,
          }));
          const latest = latestSamples[key];

          return (
            <div key={key} className="bg-slate-900/60 border border-slate-800 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">{label}</span>
                <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${
                  classification === 'MEASURED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                  classification === 'ESTIMATED' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                  'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                }`}>
                  {classification}
                </span>
              </div>
              {latest && (
                <div className="text-2xl font-mono font-bold tabular-nums mb-2" style={{ color }}>
                  {latest.value.toFixed(2)}
                  <span className="text-sm font-normal text-slate-500 ml-1">{latest.unit}</span>
                </div>
              )}
              <div className="h-32">
                {chartData.length > 1 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="2 4" stroke="#1e2740" />
                      <XAxis dataKey="t" hide />
                      <YAxis
                        width={40}
                        tick={{ fontSize: 9, fill: '#475569', fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{ background: '#0d121f', border: '1px solid #1e2740', borderRadius: 4, fontFamily: 'monospace', fontSize: 11 }}
                        labelFormatter={() => ''}
                        formatter={(v: number) => [v.toFixed(3), label]}
                      />
                      <Line
                        type="monotone"
                        dataKey="v"
                        stroke={color}
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-[10px] font-mono text-slate-600">
                    Waiting for data…
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Secondary Metric Cards */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {LIVE_METRICS.map(({ key, label, unit, classification }) => {
          const s = latestSamples[key];
          return (
            <MetricBadge
              key={key}
              label={label}
              value={s ? s.value : '—'}
              unit={s?.unit || unit}
              classification={s?.classification || classification}
              confidence={s?.confidence}
            />
          );
        })}
      </div>
    </div>
  );
};
