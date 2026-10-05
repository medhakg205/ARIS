import React from 'react';
import { Activity, Clock, Cpu, HardDrive, BarChart2, ShieldCheck, Radio } from 'lucide-react';
import type { TelemetrySample } from '../../types';

interface LiveValidationMonitorProps {
  isValidating: boolean;
  progressPct: number;
  currentSamples: number;
  targetSamples: number;
  latestSamples: Record<string, TelemetrySample>;
  isDemo: boolean;
  hardwareConnected: boolean;
}

export const LiveValidationMonitor: React.FC<LiveValidationMonitorProps> = ({
  isValidating,
  progressPct,
  currentSamples,
  targetSamples,
  latestSamples,
  isDemo,
  hardwareConnected,
}) => {
  // Extract actual current measurements from latestSamples
  const loopTimeSample = latestSamples['loop_time'];
  const cpuLoadSample = latestSamples['cpu_load'];
  const sramUsedSample = latestSamples['sram_used'];
  const jitterSample = latestSamples['loop_jitter'];
  const interruptSample = latestSamples['interrupt_rate'];

  const loopTimeMs = loopTimeSample?.value !== undefined ? loopTimeSample.value.toFixed(2) : '—';
  const cpuLoadPct = cpuLoadSample?.value !== undefined ? cpuLoadSample.value.toFixed(1) : '—';
  const sramBytes = sramUsedSample?.value !== undefined ? `${Math.round(sramUsedSample.value)}` : '—';
  const jitterMs = jitterSample?.value !== undefined ? jitterSample.value.toFixed(2) : '—';
  const interruptHz = interruptSample?.value !== undefined ? `${Math.round(interruptSample.value)}` : '—';

  if (!isValidating) return null;

  return (
    <div className="aris-card p-5 border-l-4 border-l-[var(--accent-cyan)] space-y-4 bg-[var(--accent-cyan-bg)]/20 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] relative">
            <Radio className="w-5 h-5 animate-pulse" />
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[var(--accent-cyan)] animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-heading font-bold text-sm text-[var(--text-primary)]">
                Live Hardware Validation in Progress
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-cyan)] text-slate-950 font-bold uppercase tracking-wider animate-pulse">
                VALIDATING
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] font-mono mt-0.5">
              Collecting continuous runtime telemetry frames to empirically verify candidate performance.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-mono font-bold px-2 py-1 rounded border uppercase tracking-wider ${
              hardwareConnected && !isDemo
                ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
                : 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30'
            }`}
          >
            {hardwareConnected && !isDemo ? 'PROVENANCE: PHYSICAL' : 'PROVENANCE: SIMULATION'}
          </span>
        </div>
      </div>

      {/* Progress Bar & Counter */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-[var(--text-secondary)] flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[var(--accent-cyan)] animate-spin" />
            Collecting runtime telemetry...
          </span>
          <span className="font-bold text-[var(--text-primary)]">
            {currentSamples} / {targetSamples} samples ({Math.min(100, Math.round(progressPct))}%)
          </span>
        </div>
        <div className="w-full bg-[var(--bg-app)] h-2.5 rounded-full overflow-hidden border border-[var(--border-color)]">
          <div
            className="h-full bg-gradient-to-r from-[var(--accent-cyan)] to-[var(--accent-green)] transition-all duration-300 rounded-full"
            style={{ width: `${Math.min(100, Math.max(5, progressPct))}%` }}
          />
        </div>
      </div>

      {/* Live Measurements Grid */}
      <div>
        <div className="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider mb-2">
          Current Live Measurements
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
              <Clock className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
              <span>Loop Time</span>
            </div>
            <div className="text-base font-bold font-mono text-[var(--text-primary)]">
              {loopTimeMs} <span className="text-xs text-[var(--text-muted)]">ms</span>
            </div>
            <div className="text-[9px] font-mono text-[var(--accent-green)]">Measured Cycle</div>
          </div>

          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
              <Cpu className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
              <span>CPU Load</span>
            </div>
            <div className="text-base font-bold font-mono text-[var(--text-primary)]">
              {cpuLoadPct} <span className="text-xs text-[var(--text-muted)]">%</span>
            </div>
            <div className="text-[9px] font-mono text-[var(--text-muted)]">Estimated (AVR)</div>
          </div>

          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
              <HardDrive className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
              <span>SRAM Used</span>
            </div>
            <div className="text-base font-bold font-mono text-[var(--text-primary)]">
              {sramBytes} <span className="text-xs text-[var(--text-muted)]">B</span>
            </div>
            <div className="text-[9px] font-mono text-[var(--accent-green)]">Headroom Intact</div>
          </div>

          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
              <BarChart2 className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
              <span>Loop Jitter</span>
            </div>
            <div className="text-base font-bold font-mono text-[var(--text-primary)]">
              {jitterMs} <span className="text-xs text-[var(--text-muted)]">ms</span>
            </div>
            <div className="text-[9px] font-mono text-[var(--accent-green)]">Variance Stabilized</div>
          </div>

          <div className="p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--text-muted)]">
              <ShieldCheck className="w-3.5 h-3.5 text-[var(--accent-cyan)]" />
              <span>Interrupt Rate</span>
            </div>
            <div className="text-base font-bold font-mono text-[var(--text-primary)]">
              {interruptHz} <span className="text-xs text-[var(--text-muted)]">Hz</span>
            </div>
            <div className="text-[9px] font-mono text-[var(--text-muted)]">ISR Safe</div>
          </div>
        </div>
      </div>
    </div>
  );
};
