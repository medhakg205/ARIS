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
        <p className="font-mono text-sm">
          {hardwareConnected ? 'Microcontroller detected and connected.' : 'Plug your Arduino via USB to stream real telemetry.'}
        </p>
        {hardwareConnected ? (
          <button
            onClick={onStartRun}
            className="px-4 py-2 text-xs font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded hover:bg-emerald-500/20 transition-colors"
          >
            Start Live Hardware Run
          </button>
        ) : (
          <div className="text-[11px] font-mono text-slate-500 bg-slate-900 border border-slate-800 px-4 py-2 rounded">
            Waiting for USB serial device…
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto p-4 sm:p-5 gap-3.5 max-w-7xl mx-auto w-full">
      {/* Realtime Telemetry Telemetry Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0d111a]/80 backdrop-blur-xl border border-white/[0.08] rounded-xl px-4 py-2.5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            {wsConnected ? (
              <>
                <div className="relative flex items-center justify-center">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <div className="absolute w-4 h-4 rounded-full bg-emerald-400/30 animate-ping pointer-events-none" />
                </div>
                <span className="text-xs font-semibold text-emerald-400 font-sans">Telemetry Stream Active</span>
              </>
            ) : (
              <>
                <div className="w-2.5 h-2.5 rounded-full bg-rose-400" />
                <span className="text-xs font-semibold text-rose-400 font-sans">Connecting to Telemetry…</span>
              </>
            )}
          </div>

          <div className="w-px h-4 bg-white/[0.08]" />
          <span className="text-xs text-slate-400 font-sans">
            Session: <span className="font-mono text-slate-200">{activeRun.run_id}</span>
          </span>

          <div className="w-px h-4 bg-white/[0.08]" />
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06] text-cyan-400 font-mono font-medium">
            {activeRun.status}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400">Frame #{seqCount}</span>
          {isDemo && (
            <span className="text-[10px] font-medium px-2 py-0.5 border border-amber-500/30 bg-amber-500/10 text-amber-400 rounded-full">
              SYNTHETIC / DEMO
            </span>
          )}
        </div>
      </div>

      {/* Primary Oscilloscope Real-Time Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CHART_METRICS.map(({ key, label, color, classification }) => {
          const history = telemetryHistory[key] || [];
          const chartData = history.slice(-80).map((s) => ({
            t: s.timestamp_ms,
            v: s.value,
          }));
          const latest = latestSamples[key];

          return (
            <div key={key} className="bg-[#0d111a]/80 backdrop-blur-xl border border-white/[0.08] hover:border-white/[0.16] transition-all duration-200 rounded-3xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-sans font-semibold text-slate-300 tracking-wider uppercase">{label}</span>
                <span className={`text-[10px] font-sans font-medium px-2 py-0.5 rounded-full border ${
                  classification === 'MEASURED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                  classification === 'ESTIMATED' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                  'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                }`}>
                  {classification}
                </span>
              </div>

              {latest && (
                <div className="flex items-baseline gap-1.5 mb-2">
                  <span className="text-3xl font-sans font-bold text-white tabular-nums tracking-tight">
                    {latest.value.toFixed(2)}
                  </span>
                  <span className="text-xs font-mono text-slate-400 font-medium">{latest.unit}</span>
                </div>
              )}

              <div className="h-36 pt-2">
                {chartData.length > 1 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.04)" />
                      <XAxis dataKey="t" hide />
                      <YAxis
                        width={35}
                        tick={{ fontSize: 10, fill: '#64748b', fontFamily: 'monospace' }}
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: 'rgba(13, 17, 26, 0.95)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          borderRadius: 12,
                          fontFamily: 'sans-serif',
                          fontSize: 12,
                          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.5)'
                        }}
                        labelFormatter={() => ''}
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
      <div>
        <h3 className="text-xs font-sans font-semibold text-slate-300 uppercase tracking-wider mb-3">
          Hardware Peripheral Probes
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
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
