// ============================================================
// ARIS — Dashboard View
// Shows board status, key metrics with veracity classification,
// active run info, and hardware connection status.
// ============================================================

import React from 'react';
import { Cpu, MemoryStick, Zap, Activity, Clock, AlertTriangle } from 'lucide-react';
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
    <div className="flex flex-col h-full overflow-auto p-4 gap-4">
      {/* Board Info Strip */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <InfoCard
          label="Board"
          value={selectedBoard?.display_name || '—'}
          icon={<Cpu className="w-4 h-4 text-cyan-400" />}
        />
        <InfoCard
          label="MCU"
          value={selectedBoard?.mcu?.toUpperCase() || '—'}
          icon={<Cpu className="w-4 h-4 text-slate-400" />}
        />
        <InfoCard
          label="Architecture"
          value={selectedBoard?.architecture?.toUpperCase() || '—'}
          icon={<Zap className="w-4 h-4 text-slate-400" />}
        />
        <InfoCard
          label="Clock"
          value={selectedBoard ? `${selectedBoard.clock_hz / 1_000_000} MHz` : '—'}
          icon={<Clock className="w-4 h-4 text-slate-400" />}
        />
      </div>

      {/* Connection + Run Status */}
      <div className="flex items-center gap-4 bg-slate-900/60 border border-slate-800 rounded p-3">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${hardwareConnected ? 'bg-emerald-400' : isDemo ? 'bg-amber-400' : 'bg-slate-600'}`} />
          <span className="text-xs font-mono text-slate-400">
            Hardware: {hardwareConnected ? 'Connected' : isDemo ? 'Demo / Simulated' : 'Disconnected'}
          </span>
        </div>
        <div className="w-px h-4 bg-slate-800" />
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-500">Run:</span>
          <span className={`text-xs font-mono font-semibold ${activeRun ? runStatusColor[activeRun.status] : 'text-slate-600'}`}>
            {activeRun ? `${activeRun.run_id} — ${activeRun.status}` : 'No Active Run'}
          </span>
        </div>
        {!backendOnline && (
          <>
            <div className="w-px h-4 bg-slate-800" />
            <div className="flex items-center gap-1.5 text-red-400">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span className="text-xs font-mono">Backend Offline</span>
            </div>
          </>
        )}
        <div className="flex-1" />
        {!activeRun && backendOnline && (
          <button
            onClick={onStartDemo}
            className="px-3 py-1 text-xs font-mono bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded hover:bg-amber-500/20 transition-colors"
          >
            Start Demo Run
          </button>
        )}
        {activeRun && (
          <button
            onClick={() => onNavigate('monitor')}
            className="px-3 py-1 text-xs font-mono bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded hover:bg-cyan-500/20 transition-colors"
          >
            Live Monitor →
          </button>
        )}
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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

      {/* Board Specs */}
      {selectedBoard && (
        <div className="bg-slate-900/60 border border-slate-800 rounded p-4">
          <h3 className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-3">
            Hardware Specification
          </h3>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            <SpecRow label="Flash" value={`${selectedBoard.flash_bytes / 1024} KB`} />
            <SpecRow label="SRAM" value={`${selectedBoard.sram_bytes / 1024} KB`} />
            <SpecRow label="EEPROM" value={`${selectedBoard.eeprom_bytes / 1024} KB`} />
            <SpecRow label="GPIO" value={`${selectedBoard.gpio_count} pins`} />
            <SpecRow label="ADC" value={`${selectedBoard.adc_channels} ch`} />
            <SpecRow label="UART" value={`${selectedBoard.uart_count} port${selectedBoard.uart_count !== 1 ? 's' : ''}`} />
          </div>
        </div>
      )}

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { tab: 'firmware', label: 'Upload Firmware', desc: 'Load .ino sketch' },
          { tab: 'analysis', label: 'View Findings', desc: `${(latestSamples as Record<string, unknown>).__findingCount || 0} findings` },
          { tab: 'optimization', label: 'Optimizations', desc: 'Review candidates' },
          { tab: 'history', label: 'History', desc: 'Past experiments' },
        ].map(({ tab, label, desc }) => (
          <button
            key={tab}
            onClick={() => onNavigate(tab)}
            className="bg-slate-900/40 border border-slate-800 rounded p-3 text-left hover:border-slate-700 hover:bg-slate-900/60 transition-colors group"
          >
            <p className="text-xs font-mono text-slate-300 group-hover:text-slate-100 transition-colors">{label}</p>
            <p className="text-[10px] font-mono text-slate-500 mt-0.5">{desc}</p>
          </button>
        ))}
      </div>
    </div>
  );
};

const InfoCard: React.FC<{ label: string; value: string; icon: React.ReactNode }> = ({
  label, value, icon,
}) => (
  <div className="bg-slate-900/60 border border-slate-800 rounded p-3 flex items-center gap-3">
    {icon}
    <div>
      <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">{label}</p>
      <p className="text-sm font-mono text-slate-100 font-semibold">{value}</p>
    </div>
  </div>
);

const SpecRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-[9px] font-mono text-slate-500 uppercase tracking-wider">{label}</p>
    <p className="text-xs font-mono text-slate-300">{value}</p>
  </div>
);
