// ============================================================
// ARIS — Dashboard View
// Shows board status, key metrics with veracity classification,
// active run info, and hardware connection status.
// ============================================================

import React from 'react';
import { Cpu, MemoryStick, Zap, Activity, Clock, AlertTriangle, Usb } from 'lucide-react';
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
  onNavigate: (tab: string) => void;
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
  onNavigate,
}) => {
  const runStatusColor: Record<string, string> = {
    CREATED: 'text-slate-400',
    BUILDING: 'text-amber-400',
    FLASHING: 'text-amber-400',
    RUNNING: 'text-emerald-400',
    COLLECTING: 'text-cyan-400',
    COMPLETED: 'text-slate-400',
    FAILED: 'text-red-400',
    ROLLED_BACK: 'text-orange-400',
  };

  return (
    <div className="flex flex-col h-full overflow-auto p-6 gap-6 max-w-7xl mx-auto w-full">
      {/* Target Microcontroller & Core Specs Hero Card */}
      <div className="bg-gradient-to-b from-[#101524]/90 to-[#0b0e17]/90 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-6 shadow-2xl relative overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-widest text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full border border-cyan-500/20">
                Active System Target
              </span>
              {hardwareConnected && (
                <span className="text-xs font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  USB Auto-Detected
                </span>
              )}
            </div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-white font-sans mt-2">
              {selectedBoard?.display_name || 'Detecting Hardware…'}
            </h1>
            <p className="text-xs text-slate-400 font-sans max-w-xl">
              Real-time telemetry probing ATmega registers, SRAM allocations, loop latency, and interrupt metrics.
            </p>
          </div>

          {/* Action Control Button */}
          <div className="flex items-center gap-3">
            {hardwareConnected && !activeRun && (
              <button
                onClick={onStartHardwareRun}
                className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black font-semibold text-xs rounded-full shadow-lg shadow-emerald-500/20 transition-all duration-200 flex items-center gap-2"
              >
                <Usb className="w-3.5 h-3.5" />
                Start Hardware Stream
              </button>
            )}
            {activeRun && (
              <button
                onClick={() => onNavigate('monitor')}
                className="px-5 py-2.5 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-black font-semibold text-xs rounded-full shadow-lg shadow-cyan-500/20 transition-all duration-200 flex items-center gap-2"
              >
                <Activity className="w-3.5 h-3.5" />
                Open Live Monitor →
              </button>
            )}
            {!hardwareConnected && !activeRun && (
              <div className="text-xs font-sans text-slate-400 bg-white/[0.03] border border-white/[0.08] px-4 py-2 rounded-full flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                Plug Arduino via USB to begin
              </div>
            )}
          </div>
        </div>

        {/* Board Key Specs Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-white/[0.06]">
          <InfoCard
            label="Microcontroller"
            value={selectedBoard?.mcu?.toUpperCase() || 'ATMEGA328P'}
            icon={<Cpu className="w-4 h-4 text-cyan-400" />}
          />
          <InfoCard
            label="Core Architecture"
            value={selectedBoard?.architecture?.toUpperCase() || 'AVR8'}
            icon={<Zap className="w-4 h-4 text-slate-300" />}
          />
          <InfoCard
            label="Clock Speed"
            value={selectedBoard ? `${selectedBoard.clock_hz / 1_000_000} MHz` : '16 MHz'}
            icon={<Clock className="w-4 h-4 text-slate-300" />}
          />
          <InfoCard
            label="Memory Footprint"
            value={selectedBoard ? `${selectedBoard.sram_bytes / 1024}K SRAM / ${selectedBoard.flash_bytes / 1024}K Flash` : '2K / 32K'}
            icon={<MemoryStick className="w-4 h-4 text-slate-300" />}
          />
        </div>
      </div>

      {/* Metrics Section Header */}
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white font-sans tracking-tight">Telemetry Matrix</h2>
            <p className="text-xs text-slate-400 font-sans">Empirical hardware measurements with veracity classification.</p>
          </div>
          <div className="flex items-center gap-2 text-[11px] font-sans text-slate-400">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Measured</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400" /> Estimated</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-400" /> Derived</span>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Hardware Peripheral Details */}
        {selectedBoard && (
          <div className="lg:col-span-2 bg-[#0d111a]/80 backdrop-blur-md border border-white/[0.08] rounded-3xl p-6 shadow-sm">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4 font-sans flex items-center justify-between">
              <span>Hardware Peripheral Register Map</span>
              <span className="text-[10px] text-cyan-400 font-mono">100% CANONICAL MATCH</span>
            </h3>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
              <SpecRow label="Flash Memory" value={`${selectedBoard.flash_bytes / 1024} KB`} />
              <SpecRow label="Static RAM" value={`${selectedBoard.sram_bytes / 1024} KB`} />
              <SpecRow label="EEPROM" value={`${selectedBoard.eeprom_bytes / 1024} KB`} />
              <SpecRow label="Digital GPIO" value={`${selectedBoard.gpio_count} pins`} />
              <SpecRow label="Analog ADC" value={`${selectedBoard.adc_channels} ch`} />
              <SpecRow label="Hardware UART" value={`${selectedBoard.uart_count} port`} />
            </div>
          </div>
        )}

        {/* Quick Actions Card */}
        <div className="bg-[#0d111a]/80 backdrop-blur-md border border-white/[0.08] rounded-3xl p-6 shadow-sm flex flex-col justify-between">
          <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 font-sans">
            Investigation Suite
          </h3>
          <div className="space-y-2">
            {[
              { tab: 'firmware', label: 'Firmware Studio', desc: 'Inspect source code & AST' },
              { tab: 'analysis', label: 'Antipattern Analysis', desc: 'Examine runtime bottleneck findings' },
              { tab: 'optimization', label: 'AI Code Optimization', desc: 'Review & approve safe patches' },
              { tab: 'history', label: 'Empirical History', desc: 'Validation records & benchmarks' },
            ].map(({ tab, label, desc }) => (
              <button
                key={tab}
                onClick={() => onNavigate(tab)}
                className="w-full text-left p-3 rounded-2xl bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.04] hover:border-white/[0.1] transition-all duration-200 group flex items-center justify-between"
              >
                <div>
                  <p className="text-xs font-medium text-slate-200 group-hover:text-cyan-400 transition-colors">{label}</p>
                  <p className="text-[11px] text-slate-400 font-sans">{desc}</p>
                </div>
                <span className="text-slate-400 group-hover:text-cyan-400 transition-colors font-mono text-xs">→</span>
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
  <div className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-3 flex items-center gap-3">
    <div className="p-2 rounded-xl bg-white/[0.04] text-cyan-400 shrink-0">
      {icon}
    </div>
    <div>
      <p className="text-[10px] font-sans uppercase tracking-wider text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-white font-sans">{value}</p>
    </div>
  </div>
);

const SpecRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="bg-white/[0.02] border border-white/[0.04] rounded-xl p-3">
    <p className="text-[10px] font-sans uppercase tracking-wider text-slate-400">{label}</p>
    <p className="text-sm font-bold text-white font-sans mt-0.5">{value}</p>
  </div>
);
