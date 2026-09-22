// ============================================================
// ARIS — Dashboard View
// Shows board status, key metrics with veracity classification,
// active run info, and hardware connection status.
// ============================================================

import React from 'react';
import { Cpu, MemoryStick, Zap, Activity, Clock, Usb, HelpCircle } from 'lucide-react';
import { MetricBadge } from '../common/MetricBadge';
import type { BoardProfile, RunRecord, TelemetrySample, HealthStatus } from '../../types';

interface DashboardViewProps {
  health: HealthStatus | null;
  selectedBoard: BoardProfile | null;
  activeRun: RunRecord | null;
  hardwareConnected: boolean;
  isDemo: boolean;
  latestSamples: Record<string, TelemetrySample>;
  backendOnline: boolean;
  onStartDemo: () => void;
  onStartHardwareRun?: () => void;
  onStopRun?: () => void;
  onNavigate: (tab: string) => void;
  onOpenInfo: () => void;
}

const DASH_METRICS = [
  { key: 'cpu_load', label: 'CPU Load', unit: '%', classification: 'ESTIMATED' as const },
  { key: 'loop_time', label: 'Loop Time', unit: 'ms', classification: 'MEASURED' as const },
  { key: 'loop_frequency', label: 'Loop Freq', unit: 'Hz', classification: 'DERIVED' as const },
  { key: 'loop_jitter', label: 'Loop Jitter', unit: 'ms', classification: 'DERIVED' as const },
  { key: 'sram_used', label: 'SRAM Used', unit: 'B', classification: 'DERIVED' as const },
  { key: 'sram_free', label: 'SRAM Free', unit: 'B', classification: 'MEASURED' as const },
  { key: 'stack_used', label: 'Stack Used', unit: 'B', classification: 'DERIVED' as const },
  { key: 'interrupt_rate', label: 'IRQ Rate', unit: 'Hz', classification: 'DERIVED' as const },
];

export const DashboardView: React.FC<DashboardViewProps> = ({
  health,
  selectedBoard,
  activeRun,
  hardwareConnected,
  isDemo,
  latestSamples,
  backendOnline,
  onStartDemo,
  onStartHardwareRun,
  onStopRun,
  onNavigate,
  onOpenInfo,
}) => {
  const runStatusColor: Record<string, string> = {
    CREATED: 'text-slate-400',
    BUILDING: 'text-amber-400',
    FLASHING: 'text-amber-400',
    RUNNING: 'text-emerald-400',
    COLLECTING: 'text-blue-400',
    COMPLETED: 'text-slate-400',
    FAILED: 'text-red-400',
    ROLLED_BACK: 'text-orange-400',
  };

  return (
    <div className="flex flex-col h-full overflow-auto p-4 sm:p-5 gap-3.5 max-w-7xl mx-auto w-full">
      {/* Target Microcontroller & Core Specs Hero Card */}
      <div className="bg-[#1a1e26] border border-white/[0.08] rounded-xl p-4 sm:p-5 shadow-sm relative overflow-hidden shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.08]">
                {hardwareConnected ? 'Active Physical Target' : (isDemo || activeRun?.is_demo) ? 'Simulated Target' : 'Hardware Target'}
              </span>
              {hardwareConnected && selectedBoard ? (
                <span className="text-[10px] font-medium text-emerald-300 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/25 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50 animate-pulse" />
                  USB Connected
                </span>
              ) : isDemo || activeRun?.is_demo ? (
                <span className="text-[10px] font-medium text-teal-300 bg-[#00878a]/15 px-2.5 py-0.5 rounded border border-[#00878a]/30 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00878a] shadow-sm shadow-[#00878a]/50 animate-pulse" />
                  Virtual MCU Demo (Synthetic)
                </span>
              ) : (
                <span className="text-[10px] font-medium text-amber-300/80 bg-amber-500/10 px-2.5 py-0.5 rounded border border-amber-500/20 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  Standby · No USB Device
                </span>
              )}
              <button
                onClick={onOpenInfo}
                className="text-[10px] font-medium text-slate-300 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] px-2.5 py-0.5 rounded border border-white/[0.08] flex items-center gap-1.5 transition-colors"
                title="System Architecture & Telemetry Guide"
              >
                <HelpCircle className="w-3 h-3 text-slate-400" />
                <span>System Guide (i)</span>
              </button>
            </div>
            <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-slate-100 font-samsung leading-tight">
              {hardwareConnected && selectedBoard
                ? selectedBoard.display_name
                : (isDemo || activeRun?.is_demo) && selectedBoard
                ? `${selectedBoard.display_name} (Virtual MCU Simulation)`
                : selectedBoard
                ? `${selectedBoard.display_name} (Ready)`
                : 'Arduino Uno (Ready)'}
            </h1>
            <p className="text-xs text-slate-400 max-w-2xl leading-normal mt-1 font-sans">
              {hardwareConnected && selectedBoard
                ? `Streaming physical telemetry probing ${selectedBoard.mcu?.toUpperCase()} registers, SRAM allocations, loop latency, and interrupt metrics.`
                : isDemo || activeRun?.is_demo
                ? `Simulating physical ATmega328P execution cycle. Streaming synthetic loop timing, SRAM footprint, CPU load, and embedded antipattern telemetry.`
                : 'Connect your Arduino (Uno, Nano, or Mega) via USB to auto-detect hardware, or start the Virtual Arduino Demo below to test real-time monitoring and AI optimizations without hardware.'}
            </p>
          </div>

          {/* Action Control Button Area */}
          <div className="flex items-center gap-2.5 shrink-0 mt-2 sm:mt-0">
            {hardwareConnected && !activeRun && (
              <button
                onClick={onStartHardwareRun}
                className="px-4 py-2 bg-[#00878a] hover:bg-[#00979d] text-white font-medium text-xs rounded transition-colors flex items-center gap-2 shadow-sm"
              >
                <Usb className="w-3.5 h-3.5" />
                Start Hardware Stream
              </button>
            )}
            {activeRun && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => onNavigate('monitor')}
                  className="px-4 py-2 bg-[#00878a] hover:bg-[#00979d] text-white font-medium text-xs rounded transition-colors flex items-center gap-2 shadow-sm"
                >
                  <Activity className="w-3.5 h-3.5" />
                  Open Live Monitor →
                </button>
                {onStopRun && (
                  <button
                    onClick={onStopRun}
                    className="px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 font-medium text-xs rounded transition-colors"
                  >
                    Stop Stream
                  </button>
                )}
              </div>
            )}
            {!hardwareConnected && !activeRun && (
              <button
                onClick={onStartDemo}
                className="px-4 py-2 bg-[#00878a] hover:bg-[#00979d] text-white font-medium text-xs rounded transition-all flex items-center gap-2 shadow-sm ring-1 ring-[#00878a]/50 hover:ring-[#00878a]"
                title="Simulates an ATmega328P with live telemetry, CPU load, and AI optimization"
              >
                <Zap className="w-3.5 h-3.5 text-amber-300" />
                Start Virtual Arduino Demo
              </button>
            )}
          </div>
        </div>

        {/* Board Key Specs Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3.5 pt-3 border-t border-white/[0.06]">
          <InfoCard
            label="Microcontroller"
            value={selectedBoard ? (selectedBoard.mcu?.toUpperCase() || 'ATMEGA328P') : 'ATMEGA328P'}
            icon={<Cpu className="w-3.5 h-3.5 text-slate-400" />}
          />
          <InfoCard
            label="Architecture"
            value={selectedBoard ? (selectedBoard.architecture?.toUpperCase() || 'AVR8') : 'AVR8'}
            icon={<Zap className="w-3.5 h-3.5 text-slate-400" />}
          />
          <InfoCard
            label="Clock Speed"
            value={selectedBoard ? `${selectedBoard.clock_hz / 1_000_000} MHz` : '16 MHz'}
            icon={<Clock className="w-3.5 h-3.5 text-slate-400" />}
          />
          <InfoCard
            label="Memory Footprint"
            value={selectedBoard ? `${selectedBoard.sram_bytes / 1024}K / ${selectedBoard.flash_bytes / 1024}K Flash` : '2K / 32K Flash'}
            icon={<MemoryStick className="w-3.5 h-3.5 text-slate-400" />}
          />
        </div>
      </div>

      {/* Metrics Section Header */}
      <div className="shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-200 font-samsung tracking-tight">Telemetry Matrix</h2>
            <p className="text-[11px] text-slate-400 font-sans leading-normal">Empirical hardware measurements with veracity classification.</p>
          </div>
          <div className="flex items-center gap-3 text-[10.5px] font-sans text-slate-400">
            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" /> Measured</span>
            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" /> Estimated</span>
            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" /> Derived</span>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 sm:gap-3 mt-2.5">
          {DASH_METRICS.map(({ key, label, unit, classification }) => {
            const sample = latestSamples[key];
            return (
              <MetricBadge
                key={key}
                label={label}
                value={sample ? sample.value : '—'}
                unit={sample ? (sample.unit || unit) : unit}
                classification={sample ? sample.classification : classification}
                confidence={sample?.confidence}
              />
            );
          })}
        </div>
      </div>

      {/* Hardware Specifications & Quick Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5 shrink-0">
        {/* Hardware Peripheral Details */}
        <div className="lg:col-span-2 bg-[#1a1e26] border border-white/[0.08] rounded-xl p-3.5 sm:p-4 shadow-sm">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2.5 font-sans flex items-center justify-between">
            <span>Hardware Peripheral Register Map</span>
            <span className={`text-[10px] px-2 py-0.5 rounded border font-mono ${
              hardwareConnected && selectedBoard
                ? 'text-[#00878a] bg-[#00878a]/10 border-[#00878a]/20'
                : 'text-slate-400 bg-white/[0.04] border-white/[0.08]'
            }`}>
              {hardwareConnected && selectedBoard ? 'CANONICAL MATCH' : 'STANDBY · AWAITING USB'}
            </span>
          </h3>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            <SpecRow label="Flash Memory" value={hardwareConnected && selectedBoard ? `${selectedBoard.flash_bytes / 1024} KB` : '—'} />
            <SpecRow label="Static RAM" value={hardwareConnected && selectedBoard ? `${selectedBoard.sram_bytes / 1024} KB` : '—'} />
            <SpecRow label="EEPROM" value={hardwareConnected && selectedBoard ? `${selectedBoard.eeprom_bytes / 1024} KB` : '—'} />
            <SpecRow label="Digital GPIO" value={hardwareConnected && selectedBoard ? `${selectedBoard.gpio_count} pins` : '—'} />
            <SpecRow label="Analog ADC" value={hardwareConnected && selectedBoard ? `${selectedBoard.adc_channels} ch` : '—'} />
            <SpecRow label="Hardware UART" value={hardwareConnected && selectedBoard ? `${selectedBoard.uart_count} port` : '—'} />
          </div>
        </div>

        {/* Quick Actions Card */}
        <div className="bg-[#1a1e26] border border-white/[0.08] rounded-xl p-3.5 sm:p-4 shadow-sm flex flex-col justify-between">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-sans">
            Investigation Suite
          </h3>
          <div className="space-y-1.5">
            {[
              { tab: 'firmware', label: 'Firmware Studio', desc: 'Inspect source code & AST' },
              { tab: 'analysis', label: 'Antipattern Analysis', desc: 'Examine runtime bottleneck findings' },
              { tab: 'optimization', label: 'AI Code Optimization', desc: 'Review & approve safe patches' },
              { tab: 'history', label: 'Empirical History', desc: 'Validation records & benchmarks' },
            ].map(({ tab, label, desc }) => (
              <button
                key={tab}
                onClick={() => onNavigate(tab)}
                className="w-full text-left px-2.5 py-1.5 rounded-lg bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] hover:border-white/[0.08] transition-colors group flex items-center justify-between"
              >
                <div>
                  <p className="text-xs font-medium text-slate-200 group-hover:text-[#00878a] transition-colors">{label}</p>
                  <p className="text-[10px] text-slate-400 font-sans">{desc}</p>
                </div>
                <span className="text-slate-500 group-hover:text-[#00878a] transition-colors font-mono text-xs">→</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const InfoCard: React.FC<{ label: string; value: string; icon: React.ReactNode }> = ({
  label, value, icon,
}) => (
  <div className="bg-white/[0.02] border border-white/[0.05] rounded-lg p-2.5 flex items-center gap-2.5">
    <div className="p-1 rounded bg-white/[0.04] text-slate-400 shrink-0">
      {icon}
    </div>
    <div>
      <p className="text-[9.5px] font-sans uppercase tracking-wider text-slate-400">{label}</p>
      <p className="text-xs sm:text-sm font-medium text-slate-200 font-mono">{value}</p>
    </div>
  </div>
);

const SpecRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="bg-white/[0.02] border border-white/[0.04] rounded p-2">
    <p className="text-[9.5px] font-sans uppercase tracking-wider text-slate-400">{label}</p>
    <p className="text-xs sm:text-sm font-semibold text-slate-200 font-mono mt-0.5">{value}</p>
  </div>
);

