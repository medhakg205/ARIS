// ============================================================
// ARIS — Telemetry Lab (v3.0.0)
// Simple, Trustworthy Observability:
// Empty state when offline, 2 Primary Charts + Metrics Cards when active,
// Table with explicit Hardware vs Simulation provenance.
// ============================================================

import React, { useState, useMemo } from 'react';
import {
  Activity,
  Play,
  Square,
  Pause,
  Download,
  Filter,
  Clock,
  Layers,
  Zap,
  Cpu,
  BarChart2,
  ChevronDown,
  Usb,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { RunRecord, TelemetrySample } from '../../types';

interface TelemetryLabProps {
  activeRun: RunRecord | null;
  wsConnected: boolean;
  isDemo: boolean;
  latestSamples: Record<string, TelemetrySample>;
  telemetryHistory: TelemetrySample[];
  hardwareConnected: boolean;
  onStartRun: () => Promise<void>;
  onStartDemo: () => Promise<void>;
  onStopRun: () => Promise<void>;
  onNavigate: (tab: string) => void;
}

type TimeRange = '10s' | '30s' | '1m' | 'all';

export const TelemetryLab: React.FC<TelemetryLabProps> = ({
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
  const [isPaused, setIsPaused] = useState(false);
  const [timeRange, setTimeRange] = useState<TimeRange>('30s');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isRunning = activeRun?.status === 'RUNNING' || activeRun?.status === 'COLLECTING';
  const hasData = telemetryHistory.length > 0;

  // Process historical samples for charting
  const chartData = useMemo(() => {
    if (!telemetryHistory.length) return [];

    const timeWindowSec =
      timeRange === '10s' ? 10 : timeRange === '30s' ? 30 : timeRange === '1m' ? 60 : Infinity;

    const maxTs = telemetryHistory[telemetryHistory.length - 1]?.timestamp_ms || 0;
    const minTs = maxTs - timeWindowSec * 1000;

    const filtered =
      timeWindowSec === Infinity
        ? telemetryHistory
        : telemetryHistory.filter((s) => s.timestamp_ms >= minTs);

    const grouped: Record<number, Record<string, number | string>> = {};
    const firstTs = filtered[0]?.timestamp_ms || 0;

    filtered.forEach((sample) => {
      const bucket = Math.floor((sample.timestamp_ms - firstTs) / 250) * 250;
      if (!grouped[bucket]) {
        grouped[bucket] = {
          elapsed_sec: (bucket / 1000).toFixed(1),
          timestamp_ms: sample.timestamp_ms,
        };
      }
      grouped[bucket][sample.metric] = sample.value;
    });

    return Object.values(grouped).sort(
      (a, b) => Number(a.timestamp_ms) - Number(b.timestamp_ms)
    );
  }, [telemetryHistory, timeRange]);

  // Real measurements from latest samples (no fake fallbacks!)
  const loopSample = latestSamples['loop_time'] || latestSamples['loop_time_us'];
  const cpuSample = latestSamples['cpu_load'] || latestSamples['cpu_load_pct'];
  const sramSample = latestSamples['sram_used'] || latestSamples['sram_used_bytes'];
  const sramFreeSample = latestSamples['sram_free'] || latestSamples['sram_free_bytes'];
  const stackSample = latestSamples['stack_used'] || latestSamples['stack_bytes'];
  const stackHwmSample = latestSamples['stack_high_water_mark'] || latestSamples['stack_hwm'];
  const jitterSample = latestSamples['loop_jitter'] || latestSamples['jitter_us'];
  const isrSample = latestSamples['interrupt_rate'] || latestSamples['isr_count'];

  const loopTimeStr = loopSample?.value !== undefined
    ? (loopSample.unit === 'us' ? (loopSample.value / 1000).toFixed(2) : loopSample.value.toFixed(2))
    : '—';
  const cpuLoadStr = cpuSample?.value !== undefined ? cpuSample.value.toFixed(1) : '—';
  const sramStr = sramSample?.value !== undefined ? `${Math.round(sramSample.value)}` : '—';
  const sramFreeStr = sramFreeSample?.value !== undefined ? `${Math.round(sramFreeSample.value)}` : '—';
  const stackStr = stackSample?.value !== undefined ? `${Math.round(stackSample.value)}` : '—';
  const stackHwmStr = stackHwmSample?.value !== undefined ? `${Math.round(stackHwmSample.value)}` : '—';
  const jitterStr = jitterSample?.value !== undefined
    ? (jitterSample.unit === 'us' ? (jitterSample.value / 1000).toFixed(2) : jitterSample.value.toFixed(2))
    : '—';
  const isrStr = isrSample?.value !== undefined ? `${Math.round(isrSample.value)}` : '—';

  // Export CSV
  const exportCSV = () => {
    if (!telemetryHistory.length) return;
    const headers = ['Timestamp_ms', 'Metric', 'Value', 'Source'];
    const rows = telemetryHistory.slice(-500).map((s) => [
      s.timestamp_ms,
      s.metric,
      s.value,
      s.is_demo ? 'SIMULATION' : 'HARDWARE',
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `aris_telemetry_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ============================================================
  // EMPTY STATE: NO ACTIVE RUN & NO TELEMETRY DATA
  // ============================================================
  if (!isRunning && !hasData) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 select-none bg-[var(--bg-app)]">
        <div className="max-w-md w-full flex flex-col items-center text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-center text-[var(--accent-cyan)] shadow-sm">
            <Activity size={24} />
          </div>

          <div className="space-y-1">
            <h2 className="text-lg font-heading font-bold text-[var(--text-primary)]">
              Telemetry Standby
            </h2>
            <p className="text-xs text-[var(--text-muted)] font-sans leading-relaxed">
              No live telemetry stream detected. Connect Arduino hardware or launch simulation mode to inspect runtime performance.
            </p>
          </div>

          <div className="flex items-center gap-2.5 pt-2">
            <button
              onClick={() => onNavigate('devices')}
              className="aris-btn-secondary flex items-center gap-2 text-xs"
            >
              <Usb size={14} className="text-[var(--accent-cyan)]" />
              <span>Connect Hardware</span>
            </button>

            <button
              onClick={onStartDemo}
              className="aris-btn-primary flex items-center gap-2 text-xs"
            >
              <Play size={14} />
              <span>Start Simulation</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // ACTIVE TELEMETRY VIEW
  // ============================================================
  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-heading font-extrabold text-[var(--text-primary)]">
              Telemetry
            </h1>
            <span
              className={`inline-flex items-center gap-1.5 text-[10px] font-mono px-2.5 py-0.5 rounded-full font-semibold border ${
                isDemo
                  ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30'
                  : hardwareConnected
                  ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
                  : 'bg-[var(--bg-surface)] text-[var(--text-muted)] border-[var(--border-color)]'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${
                isDemo ? 'bg-[var(--accent-amber)]' : hardwareConnected ? 'bg-[var(--accent-green)]' : 'bg-[var(--text-muted)]'
              }`} />
              {isDemo ? 'SIMULATION' : hardwareConnected ? 'PHYSICAL HARDWARE' : 'OFFLINE'}
            </span>
            {activeRun && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-color)] font-medium">
                {activeRun.run_id}
              </span>
            )}
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-1 font-sans">
            {isRunning ? 'Capturing live telemetry frames over serial interface' : 'Capture session completed'}
            {telemetryHistory.length > 0 && ` · ${telemetryHistory.length.toLocaleString()} frames ingested`}
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {/* Time range segmented control */}
          <div className="flex items-center rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] p-0.5 text-xs font-mono">
            {(['10s', '30s', '1m', 'all'] as TimeRange[]).map((tr) => (
              <button
                key={tr}
                onClick={() => setTimeRange(tr)}
                className={`px-2.5 py-1 rounded-md text-xs transition-colors ${
                  timeRange === tr
                    ? 'bg-[var(--bg-card)] text-[var(--text-primary)] font-semibold shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`}
              >
                {tr.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Export CSV */}
          <button
            onClick={exportCSV}
            title="Export CSV"
            className="aris-btn-secondary flex items-center gap-1.5 text-xs"
          >
            <Download size={13} />
            <span>Export CSV</span>
          </button>

          {/* Start / Stop Toggle */}
          {isRunning ? (
            <button
              onClick={onStopRun}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/30 text-xs font-semibold hover:opacity-90 transition-opacity"
            >
              <Square size={13} />
              <span>Stop Stream</span>
            </button>
          ) : (
            <button
              onClick={hardwareConnected ? onStartRun : onStartDemo}
              className="aris-btn-primary flex items-center gap-1.5 text-xs"
            >
              <Play size={13} />
              <span>{hardwareConnected ? 'Start Capture' : 'Start Simulation'}</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Key Metrics Row (Loop Time, CPU, SRAM, Stack, Jitter, Interrupts) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>Loop Time</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30">MEASURED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {loopTimeStr} {loopTimeStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">ms</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">Iteration period</div>
        </div>

        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>CPU Load</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30">ESTIMATED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {cpuLoadStr} {cpuLoadStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">%</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">Active duty cycle</div>
        </div>

        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>SRAM Alloc</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--accent-purple-bg)] text-[var(--accent-purple)] border border-[var(--accent-purple)]/30">DERIVED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {sramStr} {sramStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">B</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">
            {sramFreeStr !== '—' ? `${sramFreeStr} B free` : 'Static memory'}
          </div>
        </div>

        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>Stack Usage</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30">DERIVED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {stackStr} {stackStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">B</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">
            {stackHwmStr !== '—' ? `HWM: ${stackHwmStr} B` : 'Current depth'}
          </div>
        </div>

        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>Jitter</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-color)]">DERIVED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {jitterStr} {jitterStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">ms</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">Cycle variance</div>
        </div>

        <div className="aris-card p-3.5 space-y-1">
          <div className="text-xs font-sans font-medium text-[var(--text-secondary)] flex items-center justify-between">
            <span>Interrupts</span>
            <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30">DERIVED</span>
          </div>
          <div className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
            {isrStr} {isrStr !== '—' && <span className="text-xs font-mono font-normal text-[var(--text-muted)]">Hz</span>}
          </div>
          <div className="text-[11px] font-sans text-[var(--text-muted)]">ISR frequency</div>
        </div>
      </div>

      {/* 3. Primary Charts: Loop Time Latency & CPU Load */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Loop Time Chart */}
        <div className="aris-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-sans font-semibold text-[var(--text-primary)]">
                Loop Execution Latency
              </span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--accent-green-bg)] text-[var(--accent-green)]">
                MEASURED
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-[var(--accent-green)]">
              {loopTimeStr} ms
            </span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                <XAxis dataKey="elapsed_sec" stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="s" />
                <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} domain={['auto', 'auto']} unit="ms" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-card)',
                    borderColor: 'var(--border-color)',
                    fontSize: '11px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="loop_time"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CPU Load Chart */}
        <div className="aris-card p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-2.5">
            <div className="flex items-center gap-2">
              <span className="text-xs font-sans font-semibold text-[var(--text-primary)]">
                CPU Duty Cycle
              </span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]">
                ESTIMATED
              </span>
            </div>
            <span className="text-xs font-mono font-bold text-[var(--accent-cyan)]">
              {cpuLoadStr}%
            </span>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                <XAxis dataKey="elapsed_sec" stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="s" />
                <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} domain={[0, 100]} unit="%" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-card)',
                    borderColor: 'var(--border-color)',
                    fontSize: '11px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="cpu_load"
                  stroke="#00b4d8"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 4. Collapsible Advanced Channels (SRAM & Interrupts) */}
      <div className="space-y-2">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs font-sans font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] flex items-center gap-1.5 transition-colors"
        >
          <span>{showAdvanced ? 'Hide Advanced Telemetry Channels' : 'Show Advanced Telemetry Channels (SRAM, Interrupts)'}</span>
          <ChevronDown size={13} className={showAdvanced ? 'rotate-180 transition-transform' : 'transition-transform'} />
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-1">
            {/* SRAM Chart */}
            <div className="aris-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-sans font-semibold text-[var(--text-primary)]">
                    SRAM Allocation
                  </span>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--accent-purple-bg)] text-[var(--accent-purple)]">
                    DERIVED
                  </span>
                </div>
                <span className="text-xs font-mono font-bold text-[var(--accent-purple)]">
                  {sramStr} B
                </span>
              </div>
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                    <XAxis dataKey="elapsed_sec" stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="s" />
                    <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="B" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--bg-card)',
                        borderColor: 'var(--border-color)',
                        fontSize: '11px',
                        borderRadius: '8px',
                      }}
                    />
                    <Line type="monotone" dataKey="sram_used" stroke="#a855f7" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Interrupts Chart */}
            <div className="aris-card p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-sans font-semibold text-[var(--text-primary)]">
                    Interrupt Frequency
                  </span>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--accent-amber-bg)] text-[var(--accent-amber)]">
                    DERIVED
                  </span>
                </div>
                <span className="text-xs font-mono font-bold text-[var(--accent-amber)]">
                  {isrStr} Hz
                </span>
              </div>
              <div className="h-40 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.08)" />
                    <XAxis dataKey="elapsed_sec" stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="s" />
                    <YAxis stroke="var(--text-muted)" tick={{ fontSize: 10 }} unit="Hz" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'var(--bg-card)',
                        borderColor: 'var(--border-color)',
                        fontSize: '11px',
                        borderRadius: '8px',
                      }}
                    />
                    <Line type="monotone" dataKey="interrupt_rate" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 5. Recent Telemetry Samples Table with Explicit Source */}
      <div className="aris-card p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-3">
          <span className="font-heading font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">
            Recent Telemetry Frames ({telemetryHistory.length.toLocaleString()})
          </span>
          <span className="text-xs font-sans text-[var(--text-muted)]">
            Showing last 10 samples
          </span>
        </div>

        <div className="overflow-x-auto border border-[var(--border-color)] rounded-lg">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[var(--bg-surface)] text-[var(--text-muted)] border-b border-[var(--border-color)]">
              <tr>
                <th className="p-2.5 font-medium">Timestamp</th>
                <th className="p-2.5 font-medium">Metric</th>
                <th className="p-2.5 text-right font-medium">Value</th>
                <th className="p-2.5 font-medium">Unit</th>
                <th className="p-2.5 text-center font-medium">Provenance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {telemetryHistory.slice(-10).reverse().map((s, idx) => (
                <tr key={idx} className="hover:bg-[var(--bg-surface)] transition-colors">
                  <td className="p-2.5 text-[var(--text-muted)]">{s.timestamp_ms} ms</td>
                  <td className="p-2.5 text-[var(--text-primary)] font-semibold">{s.metric}</td>
                  <td className="p-2.5 text-right font-bold text-[var(--accent-cyan)]">{s.value.toFixed(2)}</td>
                  <td className="p-2.5 text-[var(--text-muted)]">{s.unit}</td>
                  <td className="p-2.5 text-center">
                    <span
                      className={`inline-flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        s.is_demo
                          ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)]'
                          : 'bg-[var(--accent-green-bg)] text-[var(--accent-green)]'
                      }`}
                    >
                      <span className={`w-1 h-1 rounded-full ${s.is_demo ? 'bg-[var(--accent-amber)]' : 'bg-[var(--accent-green)]'}`} />
                      {s.is_demo ? 'Simulation' : 'Physical'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
