import React from 'react';
import { 
  Activity, 
  Cpu, 
  Database, 
  Zap, 
  Clock, 
  ShieldAlert, 
  Radio, 
  Usb,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Play,
  Terminal,
  Layers,
  ArrowRight
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { TelemetryFrame, HardwareProfile } from '../../types';

interface TelemetryDashboardProps {
  telemetry: TelemetryFrame | null;
  telemetryHistory: TelemetryFrame[];
  boardDetail: HardwareProfile | null;
  connectedPort: string | null;
  serialPorts: any[];
  onRefreshPorts: () => void;
  onConnectPort: (port: string) => void;
  onDisconnectPort: () => void;
  onSwitchToCodeStudio: () => void;
}

export const TelemetryDashboard: React.FC<TelemetryDashboardProps> = ({
  telemetry,
  telemetryHistory,
  boardDetail,
  connectedPort,
  serialPorts,
  onRefreshPorts,
  onConnectPort,
  onDisconnectPort,
  onSwitchToCodeStudio
}) => {
  if (!boardDetail) return null;

  // 1. If NO physical hardware is connected, show the Physical Hardware Connection & Setup Guide
  if (!connectedPort || !telemetry) {
    return (
      <div className="p-8 max-w-5xl mx-auto space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
        {/* Hardware Awaiting Banner */}
        <div className="bg-[#101522] border-2 border-slate-800 rounded-3xl p-8 shadow-2xl text-center relative overflow-hidden">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-4 text-cyan-400 shadow-lg shadow-cyan-500/20">
            <Usb className="w-8 h-8" />
          </div>

          <h2 className="text-xl font-extrabold text-white tracking-wide">
            Awaiting Physical {boardDetail.name} Connection
          </h2>
          <p className="text-sm font-mono text-slate-400 max-w-xl mx-auto mt-2 leading-relaxed">
            Plug your Arduino microcontroller into your computer via USB, select the COM port below, and click Connect to stream real live telemetry.
          </p>

          {/* COM Port Selector & Connect Button */}
          <div className="mt-8 flex items-center justify-center gap-3 max-w-lg mx-auto bg-[#0a0d14] p-3 rounded-2xl border border-slate-800">
            <select
              id="port-select"
              className="flex-1 bg-transparent font-mono text-xs text-cyan-300 font-bold p-2 focus:outline-none cursor-pointer"
            >
              {serialPorts.length === 0 && (
                <option value="" className="bg-[#101522]">No COM Ports Found (Plug in USB)</option>
              )}
              {serialPorts.map((p) => (
                <option key={p.port} value={p.port} className="bg-[#101522]">
                  {p.port} — {p.desc}
                </option>
              ))}
            </select>

            <button
              onClick={onRefreshPorts}
              title="Refresh Ports"
              className="p-2.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 transition border border-slate-700"
            >
              <RefreshCw className="w-4 h-4" />
            </button>

            <button
              onClick={() => {
                const el = document.getElementById('port-select') as HTMLSelectElement;
                if (el && el.value) onConnectPort(el.value);
              }}
              disabled={serialPorts.length === 0}
              className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono text-xs font-bold rounded-xl transition shadow-lg shadow-cyan-600/30 disabled:opacity-40"
            >
              Connect Hardware
            </button>
          </div>
        </div>

        {/* 3-Step Setup Instructions */}
        <div className="grid grid-cols-3 gap-6">
          <div className="bg-[#101522] border border-slate-800 p-6 rounded-2xl shadow-xl space-y-3">
            <div className="w-7 h-7 rounded-lg bg-cyan-500/20 text-cyan-300 font-mono font-bold flex items-center justify-center text-xs">
              1
            </div>
            <h3 className="text-sm font-bold text-slate-200">Prepare Firmware</h3>
            <p className="text-xs text-slate-400 font-mono leading-relaxed">
              Open <span className="text-cyan-400 cursor-pointer underline" onClick={onSwitchToCodeStudio}>Code Studio</span>, write or paste your Arduino sketch, and click "Analyze AST".
            </p>
          </div>

          <div className="bg-[#101522] border border-slate-800 p-6 rounded-2xl shadow-xl space-y-3">
            <div className="w-7 h-7 rounded-lg bg-purple-500/20 text-purple-300 font-mono font-bold flex items-center justify-center text-xs">
              2
            </div>
            <h3 className="text-sm font-bold text-slate-200">Upload to Arduino</h3>
            <p className="text-xs text-slate-400 font-mono leading-relaxed">
              Copy the instrumented sketch into Arduino IDE and upload to your physical {boardDetail.name} over USB.
            </p>
          </div>

          <div className="bg-[#101522] border border-slate-800 p-6 rounded-2xl shadow-xl space-y-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-300 font-mono font-bold flex items-center justify-center text-xs">
              3
            </div>
            <h3 className="text-sm font-bold text-slate-200">Live Observability</h3>
            <p className="text-xs text-slate-400 font-mono leading-relaxed">
              Connect to your COM port above. Real CPU %, Stack watermark, and Loop latency will immediately stream live!
            </p>
          </div>
        </div>
      </div>
    );
  }

  // 2. When Physical Hardware is CONNECTED, display live physical telemetry
  const chartData = telemetryHistory.map((frame) => ({
    time: `${(frame.timestamp_ms / 1000).toFixed(1)}s`,
    cpu: frame.cpu_compensated_pct,
    loop_ms: Number((frame.loop_duration_us / 1000).toFixed(2)),
    power: frame.power_consumption_mw,
    sram_used: frame.used_sram_bytes + frame.stack_high_watermark_bytes
  }));

  const sramTotal = boardDetail.sram_bytes;
  const sramUsed = telemetry.used_sram_bytes + telemetry.stack_high_watermark_bytes;
  const sramPercent = Math.min(100, Math.round((sramUsed / sramTotal) * 100));
  const isStalled = telemetry.cpu_utilization_pct > 65;

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Live Physical Connection Banner */}
      <div className="flex items-center justify-between bg-[#101522] border border-emerald-500/40 p-4 rounded-2xl shadow-xl neon-border-green">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">
                Physical Hardware Streaming Active ({connectedPort})
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                115200 BAUD USB
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Receiving real-time execution telemetry directly from physical {boardDetail.name} ({boardDetail.mcu_model})
            </p>
          </div>
        </div>

        <button
          onClick={onDisconnectPort}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono font-bold transition border border-slate-700"
        >
          Disconnect USB
        </button>
      </div>

      {/* 4 Core Primary Telemetry Gauges */}
      <div className="grid grid-cols-4 gap-5">
        {/* 1. CPU Execution Load */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl relative overflow-hidden group hover:border-cyan-500/40 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Estimated CPU Load</span>
            <Cpu className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold font-mono ${isStalled ? 'text-amber-400' : 'text-cyan-400'}`}>
              {telemetry.cpu_compensated_pct.toFixed(1)}%
            </span>
            <span className="text-xs font-mono text-slate-500">
              (gross: {telemetry.cpu_utilization_pct.toFixed(1)}%)
            </span>
          </div>
          <div className="mt-3 w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
            <div 
              className={`h-full transition-all duration-300 ${isStalled ? 'bg-gradient-to-r from-amber-500 to-red-500' : 'bg-gradient-to-r from-cyan-500 to-blue-500'}`}
              style={{ width: `${Math.min(100, telemetry.cpu_compensated_pct)}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-3 flex items-center justify-between">
            <span>Observer Bias: -{telemetry.observer_overhead_pct.toFixed(2)}%</span>
            <span className="text-cyan-400">16MHz Clock</span>
          </p>
        </div>

        {/* 2. Dynamic SRAM Allocation */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl relative overflow-hidden group hover:border-blue-500/40 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">SRAM Consumption</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-blue-400">
              {sramUsed} <span className="text-lg font-normal text-slate-400">/ {sramTotal} B</span>
            </span>
            <span className="text-xs font-mono text-slate-400">({sramPercent}%)</span>
          </div>
          <div className="mt-3 w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${sramPercent}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-3 flex items-center justify-between">
            <span>Free SRAM: {telemetry.free_sram_bytes} Bytes</span>
            <span className="text-emerald-400">{((telemetry.free_sram_bytes / sramTotal) * 100).toFixed(0)}% Free</span>
          </p>
        </div>

        {/* 3. Stack High-Water Mark */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl relative overflow-hidden group hover:border-purple-500/40 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Stack Watermark Sentinel</span>
            <ShieldAlert className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-purple-400">
              {telemetry.stack_high_watermark_bytes} <span className="text-lg font-normal text-slate-400">Bytes</span>
            </span>
          </div>
          <div className="mt-3 w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-300"
              style={{ width: `${Math.min(100, (telemetry.stack_high_watermark_bytes / (sramTotal * 0.35)) * 100)}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-3 flex items-center justify-between">
            <span>RAM Pattern: 0x5A</span>
            <span className="text-purple-300">Safe Headroom</span>
          </p>
        </div>

        {/* 4. Loop Latency & Jitter */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl relative overflow-hidden group hover:border-emerald-500/40 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Loop Latency & Jitter</span>
            <Clock className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-extrabold font-mono text-emerald-400">
              {telemetry.loop_duration_us > 1000 ? `${(telemetry.loop_duration_us / 1000).toFixed(1)} ms` : `${telemetry.loop_duration_us} µs`}
            </span>
            <span className="text-xs font-mono text-slate-400">
              ({telemetry.loop_frequency_hz.toFixed(0)} Hz)
            </span>
          </div>
          <div className="mt-3 w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(5, (telemetry.loop_frequency_hz / 10000) * 100))}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-slate-400 mt-3 flex items-center justify-between">
            <span>Jitter: ±{telemetry.jitter_us} µs</span>
            <span className="text-emerald-300">{telemetry.power_consumption_mw} mW Power</span>
          </p>
        </div>
      </div>

      {/* Real-time Oscilloscope & Hardware Peripheral Matrix */}
      <div className="grid grid-cols-3 gap-6">
        {/* Oscilloscope Chart (2 cols) */}
        <div className="col-span-2 bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl oscilloscope-grid">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
                Real Hardware Execution Oscilloscope ({connectedPort})
              </h3>
            </div>
            <span className="text-[10px] font-mono text-cyan-400/80 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40">
              Sliding Window: 50 Frames (5.0s)
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00f0ff" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="loopGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="time" stroke="#64748b" fontSize={10} fontStyle="monospace" />
                <YAxis stroke="#64748b" fontSize={10} fontStyle="monospace" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0a0d14', borderColor: '#1e293b', borderRadius: '8px', fontSize: '11px', fontFamily: 'monospace' }}
                />
                <Area type="monotone" dataKey="cpu" name="CPU %" stroke="#00f0ff" strokeWidth={2} fillOpacity={1} fill="url(#cpuGrad)" />
                <Area type="monotone" dataKey="loop_ms" name="Loop Duration (ms)" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#loopGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hardware Peripheral & Power Breakdown (1 col) */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
                Physical Peripheral Activity
              </h3>
            </div>

            <div className="space-y-3.5">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0a0d14] border border-slate-800/80">
                <span className="text-xs font-mono text-slate-400">Timer0 Overflow ISR:</span>
                <span className="text-xs font-mono font-bold text-cyan-400">{telemetry.isr_frequency_hz} Hz</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0a0d14] border border-slate-800/80">
                <span className="text-xs font-mono text-slate-400">10-Bit ADC Conversions:</span>
                <span className="text-xs font-mono font-bold text-blue-400">{telemetry.adc_conversions_sec} conv/s</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0a0d14] border border-slate-800/80">
                <span className="text-xs font-mono text-slate-400">GPIO Port Toggles:</span>
                <span className="text-xs font-mono font-bold text-purple-400">{telemetry.gpio_toggles_sec} toggles/s</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0a0d14] border border-slate-800/80">
                <span className="text-xs font-mono text-slate-400">Active Current Draw:</span>
                <span className="text-xs font-mono font-bold text-amber-400">{telemetry.active_current_ma} mA</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#0a0d14] border border-slate-800/80">
                <span className="text-xs font-mono text-slate-400">Board Power Dissipation:</span>
                <span className="text-xs font-mono font-bold text-emerald-400">{telemetry.power_consumption_mw} mW</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 block mb-1">Raw Micro-Telemetry Frame ({connectedPort}):</span>
            <div className="bg-[#0a0d14] p-2 rounded border border-slate-800 text-[10px] font-mono text-slate-300 break-all select-all">
              {telemetry.raw_packet}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
