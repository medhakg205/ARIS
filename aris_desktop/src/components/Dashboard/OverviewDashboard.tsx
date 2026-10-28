// ============================================================
// ARIS — Overview Dashboard (v3.0.0)
// Authentic First-Launch Empty State + 5 Core Questions when Active:
// 1. What is connected?
// 2. What firmware am I analyzing?
// 3. What is ARIS doing?
// 4. What did ARIS find?
// 5. What can I improve?
// ============================================================

import React from 'react';
import {
  Cpu,
  Activity,
  HardDrive,
  Clock,
  Zap,
  FlaskConical,
  Play,
  Square,
  FileCode2,
  TrendingDown,
  AlertTriangle,
  RotateCw,
  CheckCircle2,
  ArrowRight,
  Usb,
  Search,
} from 'lucide-react';
import {
  BoardProfile,
  RunRecord,
  TelemetrySample,
  HealthStatus,
  FirmwareRecord,
  IDESketchInfo,
  FindingRecord,
  OptimizationCandidate,
} from '../../types';
import { ArisLogo } from '../common/ArisLogo';

interface OverviewDashboardProps {
  health: HealthStatus | null;
  selectedBoard: BoardProfile | null;
  activeRun: RunRecord | null;
  activeFirmware: FirmwareRecord | null;
  activeIDESketch: IDESketchInfo | null;
  hardwareConnected: boolean;
  isDemo: boolean;
  latestSamples: Record<string, TelemetrySample>;
  backendOnline: boolean;
  findings?: FindingRecord[];
  optimizations?: OptimizationCandidate[];
  onStartDemo: (boardId?: string, projectId?: string) => Promise<void>;
  onStartHardwareRun: () => Promise<void>;
  onStopRun: () => Promise<void>;
  onNavigate: (tab: string) => void;
  onOpenInfo: () => void;
  connectedPort?: string;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({
  health,
  selectedBoard,
  activeRun,
  activeFirmware,
  activeIDESketch,
  hardwareConnected,
  isDemo,
  latestSamples,
  backendOnline,
  findings = [],
  optimizations = [],
  onStartDemo,
  onStartHardwareRun,
  onStopRun,
  onNavigate,
  onOpenInfo,
  connectedPort,
}) => {
  const isRunning = activeRun?.status === 'RUNNING' || activeRun?.status === 'COLLECTING';
  const hasHardware = hardwareConnected && selectedBoard !== null;
  const isActive = hasHardware || isDemo || isRunning;

  // Real measured telemetry values (no fake hardcoded numbers!)
  const loopTimeSample = latestSamples['loop_time'] || latestSamples['loop_time_us'];
  const cpuLoadSample = latestSamples['cpu_load'] || latestSamples['cpu_load_pct'];
  const sramSample = latestSamples['sram_used'] || latestSamples['sram_used_bytes'];

  const loopTime = loopTimeSample?.value !== undefined
    ? loopTimeSample.value > 100
      ? (loopTimeSample.value / 1000).toFixed(2)
      : loopTimeSample.value.toFixed(2)
    : null;

  const cpuLoad = cpuLoadSample?.value !== undefined
    ? cpuLoadSample.value.toFixed(1)
    : null;

  const sramUsed = sramSample?.value !== undefined
    ? Math.round(sramSample.value)
    : null;

  const maxSram = selectedBoard?.sram_bytes || (selectedBoard ? (selectedBoard.architecture === 'avr8' ? 2048 : 32768) : null);
  const maxFlash = selectedBoard?.flash_bytes || (selectedBoard ? 32768 : null);

  // Active firmware details
  const currentSketchName = activeIDESketch?.name || activeFirmware?.name || null;

  // ============================================================
  // SCENARIO 1: FIRST-LAUNCH / NO HARDWARE CONNECTED / NO DEMO
  // ============================================================
  if (!isActive) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 select-none bg-[var(--bg-app)]">
        <div className="max-w-lg w-full flex flex-col items-center text-center space-y-7 aris-card p-8 sm:p-10 shadow-sm">
          {/* Logo & Headline */}
          <div className="flex flex-col items-center space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-center shadow-sm">
              <ArisLogo size={36} glow={false} />
            </div>
            <div className="space-y-1">
              <h2 className="text-2xl font-heading font-extrabold tracking-tight text-[var(--text-primary)]">
                ARIS Studio
              </h2>
              <p className="text-xs font-sans text-[var(--text-muted)]">
                Adaptive Runtime Intelligence System for Arduino & AVR
              </p>
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2 max-w-sm">
            <div className="text-sm font-semibold text-[var(--text-secondary)] font-sans">
              Hardware Standby
            </div>
            <p className="text-xs text-[var(--text-muted)] leading-relaxed font-sans">
              Connect your Arduino board via USB to stream real-time loop telemetry, detect blocking code, and safely optimize local sketch files.
            </p>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 w-full justify-center pt-1">
            <button
              onClick={() => onNavigate('devices')}
              className="aris-btn-secondary w-full sm:w-auto"
            >
              <Usb size={14} className="text-[var(--accent-cyan)]" />
              <span>Connect Hardware</span>
            </button>

            <button
              onClick={() => onStartDemo('arduino_uno', 'led_blink')}
              className="aris-btn-primary w-full sm:w-auto"
            >
              <Play size={14} />
              <span>Launch Simulation</span>
            </button>
          </div>

          {/* Minimal 3-Step Guidance (Google Home Simplicity) */}
          <div className="w-full pt-5 border-t border-[var(--border-color)] grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
            <div className="p-3 rounded-lg bg-[var(--bg-surface)]/60 border border-[var(--border-color)]">
              <div className="text-[10px] font-mono font-bold text-[var(--accent-cyan)] uppercase">1. Hardware</div>
              <div className="text-xs font-sans font-medium text-[var(--text-secondary)] mt-1">
                Auto-detects Uno, Nano, Mega on USB
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-surface)]/60 border border-[var(--border-color)]">
              <div className="text-[10px] font-mono font-bold text-[var(--accent-cyan)] uppercase">2. Firmware</div>
              <div className="text-xs font-sans font-medium text-[var(--text-secondary)] mt-1">
                Syncs local Arduino .ino directly
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-surface)]/60 border border-[var(--border-color)]">
              <div className="text-[10px] font-mono font-bold text-[var(--accent-cyan)] uppercase">3. Optimize</div>
              <div className="text-xs font-sans font-medium text-[var(--text-secondary)] mt-1">
                Validated closed-loop improvements
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ============================================================
  // SCENARIO 2: ACTIVE (HARDWARE CONNECTED OR SIMULATION ACTIVE)
  // ============================================================
  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 lg:p-8 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. Header Bar: Status & Primary Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-heading font-extrabold text-[var(--text-primary)]">
              Dashboard
            </h1>
            <span
              className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                isDemo
                  ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30'
                  : 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
              }`}
            >
              {isDemo ? 'SIMULATION ACTIVE' : 'PHYSICAL HARDWARE'}
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-1 font-sans">
            {selectedBoard?.display_name || 'Arduino Target'} · {selectedBoard?.mcu?.toUpperCase() || 'AVR'} ·{' '}
            {connectedPort ? `${connectedPort} (115200 baud)` : isDemo ? 'Virtual UART Bus' : 'Connected'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isRunning ? (
            <button
              onClick={onStopRun}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/30 hover:opacity-90 text-xs font-sans font-semibold shadow-sm transition-opacity"
            >
              <Square size={13} />
              <span>Stop Session</span>
            </button>
          ) : hasHardware ? (
            <button
              onClick={onStartHardwareRun}
              className="aris-btn-primary"
            >
              <Play size={13} />
              <span>Capture Telemetry</span>
            </button>
          ) : (
            <button
              onClick={onStopRun}
              className="aris-btn-secondary"
            >
              <span>Exit Simulation</span>
            </button>
          )}

          <button
            onClick={() => onNavigate('firmware')}
            className="aris-btn-secondary"
          >
            <FileCode2 size={13} className="text-[var(--accent-cyan)]" />
            <span>View Firmware</span>
          </button>
        </div>
      </div>

      {/* 2. Top Status Grid: The 4 Core Product Dimensions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Dimension 1: Target Hardware */}
        <div
          onClick={() => onNavigate('devices')}
          className="aris-card p-4 space-y-2 cursor-pointer aris-card-hover"
        >
          <div className="flex items-center justify-between text-xs font-sans font-medium text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5">
              <Cpu size={14} className="text-[var(--accent-cyan)]" />
              <span>Target Hardware</span>
            </span>
            <span
              className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold border ${
                selectedBoard?.confidence === 'CONFIRMED'
                  ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
                  : selectedBoard?.confidence === 'MISMATCH'
                  ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] border-[var(--accent-red)]/30'
                  : 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30'
              }`}
            >
              {selectedBoard?.confidence || (hasHardware ? 'HIGH' : 'SIMULATION')}
            </span>
          </div>
          <div className="font-heading font-bold text-sm text-[var(--text-primary)] truncate">
            {selectedBoard?.display_name || 'Arduino Target'}
          </div>
          <div className="text-[11px] font-mono text-[var(--text-muted)] flex justify-between">
            <span>{selectedBoard?.mcu ? selectedBoard.mcu.toUpperCase() : (selectedBoard?.architecture?.toUpperCase() || 'UNKNOWN')}</span>
            <span>{selectedBoard?.clock_hz ? `${(selectedBoard.clock_hz / 1e6).toFixed(0)} MHz` : '—'}</span>
          </div>
        </div>

        {/* Dimension 2: Firmware Sketch */}
        <div
          onClick={() => onNavigate('firmware')}
          className="aris-card p-4 space-y-2 cursor-pointer aris-card-hover"
        >
          <div className="flex items-center justify-between text-xs font-sans font-medium text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5">
              <FileCode2 size={14} className="text-[var(--accent-green)]" />
              <span>Firmware Sketch</span>
            </span>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {activeIDESketch ? 'Arduino IDE' : 'Source'}
            </span>
          </div>
          <div className="font-heading font-bold text-sm text-[var(--text-primary)] truncate">
            {currentSketchName || 'No sketch selected'}
          </div>
          <div className="text-[11px] font-mono text-[var(--text-muted)] flex justify-between">
            <span>FQBN: {selectedBoard?.fqbn || '—'}</span>
            <span>{activeFirmware?.source_code ? `${activeFirmware.source_code.split('\n').length} lines` : '—'}</span>
          </div>
        </div>

        {/* Dimension 3: Telemetry Stream */}
        <div
          onClick={() => onNavigate('telemetry')}
          className="aris-card p-4 space-y-2 cursor-pointer aris-card-hover"
        >
          <div className="flex items-center justify-between text-xs font-sans font-medium text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5">
              <Activity size={14} className="text-[var(--accent-amber)]" />
              <span>Telemetry Stream</span>
            </span>
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {isRunning ? 'STREAMING' : 'READY'}
            </span>
          </div>
          <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
            {isRunning ? 'Collecting Live Frames' : loopTime ? 'Baseline Measured' : 'Ready to Measure'}
          </div>
          <div className="text-[11px] font-mono text-[var(--text-muted)] flex justify-between">
            <span>{isDemo ? 'Simulation Stream' : 'UART Physical Bus'}</span>
            <span>{Object.keys(latestSamples).length} metrics</span>
          </div>
        </div>

        {/* Dimension 4: Findings & Optimizations */}
        <div
          onClick={() => onNavigate('analysis')}
          className="aris-card p-4 space-y-2 cursor-pointer aris-card-hover"
        >
          <div className="flex items-center justify-between text-xs font-sans font-medium text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5">
              <Zap size={14} className="text-[var(--accent-purple)]" />
              <span>Analysis & Advice</span>
            </span>
            {findings.length > 0 && (
              <span className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-bold">
                {findings.length} ISSUES
              </span>
            )}
          </div>
          <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
            {findings.length > 0 ? `${findings.length} Bottlenecks Found` : 'No Issues Detected'}
          </div>
          <div className="text-[11px] font-mono text-[var(--text-muted)] flex justify-between">
            <span>{optimizations.length} recommendations</span>
            <span className="text-[var(--accent-cyan)] font-semibold">Inspect →</span>
          </div>
        </div>
      </div>

      {/* 3. Essential Runtime Metrics (Loop Time, CPU, SRAM) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-sans font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Key Measurements
          </span>
          <span className="text-xs font-sans text-[var(--text-muted)]">
            Source: <span className="font-mono text-[var(--text-secondary)]">{isDemo ? 'Simulation' : 'Physical Hardware'}</span>
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Metric 1: Loop Time */}
          <div className="aris-card p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-sans font-semibold text-[var(--text-secondary)] flex items-center gap-2">
                Loop Execution Time
                <span className="text-[8px] font-mono px-1.5 py-0.2 rounded-full bg-[var(--bg-surface)] text-[var(--accent-green)] border border-[var(--border-color)] font-bold">MEASURED</span>
              </span>
              <Clock size={14} className="text-[var(--text-muted)]" />
            </div>
            <div className="flex items-baseline gap-2 pt-1">
              <span className="text-3xl font-heading font-extrabold text-[var(--text-primary)] tabular-nums">
                {loopTime ? `${loopTime}` : '—'}
              </span>
              {loopTime && <span className="text-xs font-mono text-[var(--text-muted)]">ms</span>}
            </div>
            <div className="text-xs font-sans text-[var(--text-muted)]">
              {loopTime ? 'Iteration period between loop() cycles' : 'Run telemetry to measure'}
            </div>
          </div>

          {/* Metric 2: CPU Load */}
          <div className="aris-card p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-sans font-semibold text-[var(--text-secondary)] flex items-center gap-2">
                CPU Duty Cycle
                <span className="text-[8px] font-mono px-1.5 py-0.2 rounded-full bg-[var(--bg-surface)] text-[var(--accent-cyan)] border border-[var(--border-color)] font-bold">ESTIMATED</span>
              </span>
              <Cpu size={14} className="text-[var(--text-muted)]" />
            </div>
            <div className="flex items-baseline gap-2 pt-1">
              <span className="text-3xl font-heading font-extrabold text-[var(--text-primary)] tabular-nums">
                {cpuLoad ? `${cpuLoad}%` : '—'}
              </span>
            </div>
            <div className="text-xs font-sans text-[var(--text-muted)]">
              {cpuLoad ? 'Estimated non-idle processor cycle load' : 'Run telemetry to measure'}
            </div>
          </div>

          {/* Metric 3: SRAM Utilization */}
          <div className="aris-card p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-sans font-semibold text-[var(--text-secondary)] flex items-center gap-2">
                Static RAM (SRAM)
                <span className="text-[8px] font-mono px-1.5 py-0.2 rounded-full bg-[var(--bg-surface)] text-[var(--accent-purple)] border border-[var(--border-color)] font-bold">DERIVED</span>
              </span>
              <HardDrive size={14} className="text-[var(--text-muted)]" />
            </div>
            <div className="flex items-baseline gap-2 pt-1">
              <span className="text-3xl font-heading font-extrabold text-[var(--text-primary)] tabular-nums">
                {sramUsed !== null ? `${sramUsed}` : '—'}
              </span>
              <span className="text-xs font-mono text-[var(--text-muted)]">/ {maxSram ? `${maxSram} B` : '—'}</span>
            </div>
            <div className="text-xs font-sans text-[var(--text-muted)]">
              {sramUsed !== null && maxSram !== null ? `${maxSram - sramUsed} bytes free headroom` : 'Static global allocation'}
            </div>
          </div>
        </div>
      </div>

      {/* 4. Analysis & Recommended Optimizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Findings */}
        <div className="aris-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-3">
            <div className="flex items-center gap-2">
              <Search size={15} className="text-[var(--accent-amber)]" />
              <span className="font-heading font-bold text-sm text-[var(--text-primary)]">
                Analysis Findings
              </span>
            </div>
            <button
              onClick={() => onNavigate('analysis')}
              className="text-xs font-sans font-semibold text-[var(--accent-cyan)] hover:underline"
            >
              View All ({findings.length}) →
            </button>
          </div>

          {findings.length === 0 ? (
            <div className="py-8 text-center text-xs font-sans text-[var(--text-muted)]">
              No firmware bottlenecks found. Run static analysis or telemetry to inspect code.
            </div>
          ) : (
            <div className="space-y-2.5">
              {findings.slice(0, 3).map((f) => (
                <div
                  key={f.finding_id}
                  onClick={() => onNavigate('analysis')}
                  className="p-3.5 rounded-xl bg-[var(--bg-surface)]/70 border border-[var(--border-color)] hover:border-[var(--border-hover)] cursor-pointer transition-all space-y-1.5 shadow-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-sans font-semibold text-xs text-[var(--text-primary)]">
                      {f.title}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        f.severity === 'CRITICAL' || f.severity === 'HIGH'
                          ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)]'
                          : f.severity === 'MEDIUM'
                          ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)]'
                          : 'bg-[var(--bg-card)] text-[var(--text-muted)]'
                      }`}
                    >
                      {f.severity}
                    </span>
                  </div>
                  <div className="text-[11px] font-mono text-[var(--text-muted)]">
                    {f.source_file}:{f.source_line}
                  </div>
                  <p className="text-xs font-sans text-[var(--text-secondary)] line-clamp-1">
                    {f.recommended_action}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Recommended Optimizations */}
        <div className="aris-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-3">
            <div className="flex items-center gap-2">
              <Zap size={15} className="text-[var(--accent-cyan)]" />
              <span className="font-heading font-bold text-sm text-[var(--text-primary)]">
                Recommended Optimizations
              </span>
            </div>
            <button
              onClick={() => onNavigate('optimize')}
              className="text-xs font-sans font-semibold text-[var(--accent-cyan)] hover:underline"
            >
              Open Optimizer ({optimizations.length}) →
            </button>
          </div>

          {optimizations.length === 0 ? (
            <div className="py-8 text-center text-xs font-sans text-[var(--text-muted)]">
              No optimizations generated yet. Once findings are identified, ARIS recommends non-blocking improvements.
            </div>
          ) : (
            <div className="space-y-2.5">
              {optimizations.slice(0, 3).map((opt) => (
                <div
                  key={opt.optimization_id}
                  onClick={() => onNavigate('optimize')}
                  className="p-3.5 rounded-xl bg-[var(--bg-surface)]/70 border border-[var(--border-color)] hover:border-[var(--accent-cyan)]/40 cursor-pointer transition-all space-y-1.5 shadow-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-sans font-semibold text-xs text-[var(--text-primary)]">
                      {opt.title}
                    </span>
                    <span className="text-[10px] font-mono text-[var(--accent-green)] font-bold bg-[var(--accent-green-bg)] px-2 py-0.5 rounded-full">
                      {(opt.expected_effect as any)?.latency_delta_ms !== undefined
                        ? `${(opt.expected_effect as any).latency_delta_ms} ms latency`
                        : (opt.expected_effect as any)?.loop_time_delta_ms !== undefined
                        ? `${(opt.expected_effect as any).loop_time_delta_ms} ms latency`
                        : 'Predicted improvement'}
                    </span>
                  </div>
                  <p className="text-xs font-sans text-[var(--text-muted)] line-clamp-1">
                    {opt.reason}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
