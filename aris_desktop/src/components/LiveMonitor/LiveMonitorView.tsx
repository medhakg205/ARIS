// ============================================================
// ARIS — Live Monitor View
// Consumes /ws/telemetry/{run_id} — real-time telemetry display.
// Shows timeline charts, metric cards, runtime events, connection state.
// ============================================================

import React, { useMemo, useCallback } from 'react';
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
  onStartDemo?: () => void;
  onStopRun?: () => void;
  onNavigate?: (tab: string) => void;
}

const CHART_METRICS = [
  { key: 'loop_time', label: 'Loop Time (ms)', color: '#00878a', classification: 'MEASURED' as const },
  { key: 'cpu_load', label: 'CPU Load (%)', color: '#56d4dd', classification: 'ESTIMATED' as const },
  { key: 'sram_free', label: 'SRAM Free (B)', color: '#41b3a3', classification: 'MEASURED' as const },
  { key: 'interrupt_rate', label: 'IRQ Rate (Hz)', color: '#88a0b8', classification: 'DERIVED' as const },
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
  onStartDemo,
  onStopRun,
  onNavigate,
}) => {
  const seqCount = useMemo(() => {
    const s = latestSamples['loop_time'];
    return s?.sequence ?? 0;
  }, [latestSamples]);

  if (!activeRun) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-500">
        <Activity className="w-12 h-12 text-slate-700" />
        <p className="font-mono text-sm">
          {hardwareConnected ? 'Microcontroller detected and connected.' : 'No active telemetry run.'}
        </p>
        <div className="flex items-center gap-3">
          {hardwareConnected ? (
            <button
              onClick={onStartRun}
              className="px-4 py-2 text-xs font-mono bg-[#00878a] text-white rounded hover:bg-[#00979d] transition-colors"
            >
              Start Live Hardware Run
            </button>
          ) : (
            <>
              {onStartDemo && (
                <button
                  onClick={onStartDemo}
                  className="px-4 py-2 text-xs font-sans font-medium bg-[#00878a] text-white rounded hover:bg-[#00979d] transition-colors shadow-sm flex items-center gap-2"
                >
                  Start Virtual Arduino Demo
                </button>
              )}
              <div className="text-[11px] font-mono text-slate-500 bg-slate-900 border border-slate-800 px-3 py-2 rounded">
                Or plug Arduino via USB
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-3.5 sm:p-4 gap-3 max-w-7xl mx-auto w-full">
      {/* Realtime Telemetry Status Bar */}
      <div className="flex items-center justify-between gap-3 bg-[#1e232b] border border-white/[0.08] rounded-xl px-4 py-2.5 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {wsConnected ? (
              <>
                <div className="relative flex items-center justify-center">
                  <span className="w-2 h-2 rounded-full bg-[#00878a] shadow-sm shadow-[#00878a] animate-pulse" />
                </div>
                <span className="text-xs font-semibold text-slate-100 font-sans">Telemetry Stream Active</span>
              </>
            ) : (
              <>
                <div className="w-2 h-2 rounded-full bg-rose-400" />
                <span className="text-xs font-medium text-rose-400 font-sans">Connecting to Telemetry…</span>
              </>
            )}
          </div>

          <div className="w-px h-3.5 bg-white/[0.08]" />
          <span className="text-xs text-slate-400 font-sans">
            Session: <span className="font-mono text-slate-200 font-semibold">{activeRun.run_id}</span>
          </span>

          <div className="w-px h-3.5 bg-white/[0.08]" />
          <span className="text-[11px] px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-emerald-300 font-mono font-semibold">
            {activeRun.status}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">Frame #{seqCount}</span>
          {isDemo && (
            <span className="text-[10px] font-semibold px-2 py-0.5 border border-[#00878a]/40 bg-[#00878a]/15 text-teal-300 rounded-md font-mono">
              SYNTHETIC / DEMO
            </span>
          )}
          {onStopRun && activeRun.status === 'RUNNING' && (
            <button
              onClick={() => {
                onStopRun();
                if (onNavigate) onNavigate('analysis');
              }}
              className="px-3.5 py-1.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/40 text-xs font-mono font-semibold rounded-lg transition-all shadow-sm hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              Stop &amp; View Analysis →
            </button>
          )}
        </div>
      </div>

      {/* Primary Oscilloscope Real-Time Charts Grid (2x2) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      {CHART_METRICS.map(({ key, label, color, classification }) => {
          const history = telemetryHistory[key] || [];
          const baseTime = history.length > 0 ? history[0].timestamp_ms : 0;
          const chartData = history.slice(-80).map((s) => ({
            t: s.timestamp_ms,
            elapsed: Number(((s.timestamp_ms - baseTime) / 1000).toFixed(1)),
            v: s.value,
          }));
          const latest = latestSamples[key];

          return (
            <div key={key} className="bg-[#1e232b] border border-white/[0.08] hover:border-white/[0.14] rounded-xl p-3.5 shadow-sm flex flex-col justify-between transition-all">
              {/* Card Header Row */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-baseline gap-2.5">
                  <span className="text-xs font-sans font-semibold text-slate-400 tracking-wider uppercase">{label}</span>
                  {latest && (
                    <div className="flex items-baseline gap-1">
                      <span className="text-xl sm:text-2xl font-sans font-bold text-white tabular-nums tracking-tight">
                        {latest.value.toFixed(2)}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">{latest.unit}</span>
                    </div>
                  )}
                </div>
                <span className="text-[9.5px] font-sans font-semibold px-2 py-0.5 rounded-full border border-white/[0.08] bg-white/[0.04] text-slate-300 shrink-0">
                  {classification}
                </span>
              </div>

              {/* Waveform Chart */}
              <div className="h-28 sm:h-32 w-full pt-1">
                {chartData.length > 1 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData} margin={{ top: 5, right: 8, left: -20, bottom: 2 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.04)" />
                      <XAxis
                        dataKey="elapsed"
                        tick={{ fontSize: 9, fill: '#4a5568', fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(v: number) => `${v}s`}
                        interval="preserveStartEnd"
                        minTickGap={30}
                      />
                      <YAxis
                        width={40}
                        tick={{ fontSize: 9.5, fill: '#64748b', fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip
                        contentStyle={{
                          background: 'rgba(13, 17, 26, 0.95)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: 8,
                          fontFamily: 'monospace',
                          fontSize: 11,
                          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                        }}
                        labelFormatter={(val: number) => `T + ${val}s`}
                        formatter={(v: number) => [v.toFixed(3), label]}
                      />
                      <Line
                        type="monotone"
                        dataKey="v"
                        stroke={color}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-xs font-sans text-slate-500">
                    Awaiting telemetry packets…
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Secondary Hardware Activity Probes */}
      <div className="shrink-0 mt-0.5">
        <h3 className="text-[11px] font-sans font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Hardware Peripheral Probes
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
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
    </div>
  );
};
