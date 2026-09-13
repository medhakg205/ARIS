// ============================================================
// ARIS — Settings View
// Backend URL, AI provider selection, serial port config,
// demo mode controls, connection diagnostics.
// ============================================================

import React, { useState, useEffect } from 'react';
import { Settings, RefreshCw, CheckCircle, AlertTriangle } from 'lucide-react';
import type { HealthStatus, BoardProfile, AIProviderInfo } from '../../types';
import { apiHealth, apiGetAIProviders, apiConnectionStatus, ARISApiError } from '../../services/api';
import { ErrorBanner } from '../common/ErrorBanner';

interface SettingsViewProps {
  health: HealthStatus | null;
  boards: BoardProfile[];
  selectedBoard: BoardProfile | null;
  onSelectBoard: (board: BoardProfile) => void;
  hardwareConnected: boolean;
  onConnect: (port: string, baud: number) => Promise<void>;
  onDisconnect: () => Promise<void>;
  isDemo: boolean;
  onStartDemo: () => void;
  onStopRun: () => void;
  backendOnline: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  health,
  boards,
  selectedBoard,
  onSelectBoard,
  hardwareConnected,
  onConnect,
  onDisconnect,
  isDemo,
  onStartDemo,
  onStopRun,
  backendOnline,
}) => {
  const [providers, setProviders] = useState<AIProviderInfo[]>([]);
  const [ports, setPorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState('');
  const [baudRate, setBaudRate] = useState(115200);
  const [error, setError] = useState<ARISApiError | null>(null);
  const [probeResult, setProbeResult] = useState<HealthStatus | null>(null);

  useEffect(() => {
    if (backendOnline) {
      apiGetAIProviders()
        .then((r) => setProviders(r.providers))
        .catch(() => {});
      apiConnectionStatus()
        .then((cs) => {
          setPorts(cs.available_ports || []);
          if (cs.port) setSelectedPort(cs.port);
        })
        .catch(() => {});
    }
  }, [backendOnline]);

  const handleProbe = async () => {
    try {
      const h = await apiHealth();
      setProbeResult(h);
      setError(null);
    } catch (e) {
      setError(e as ARISApiError);
      setProbeResult(null);
    }
  };

  const handleConnect = async () => {
    if (!selectedPort) return;
    try {
      await onConnect(selectedPort, baudRate);
      setError(null);
    } catch (e) {
      setError(e as ARISApiError);
    }
  };

  const handleRefreshPorts = async () => {
    try {
      const cs = await apiConnectionStatus();
      setPorts(cs.available_ports || []);
    } catch {}
  };

  return (
    <div className="flex flex-col h-full overflow-auto p-6 gap-6 max-w-4xl mx-auto w-full">
      <div className="flex items-center gap-2.5">
        <div className="p-2 rounded-xl bg-white/[0.04] text-slate-300">
          <Settings className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xl font-bold font-sans text-white tracking-tight">System Settings &amp; Hardware Discovery</h2>
          <p className="text-xs text-slate-400 font-sans">Manage serial link interfaces, neural synthesis keys, and target device profiles.</p>
        </div>
      </div>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      {/* Target Board Profile Section */}
      <Section label="Target Microcontroller Architecture">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-sans text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Zero-Config Auto-Detection: Memory &amp; register specifications auto-load on USB connection
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {boards.map((board) => (
            <button
              key={board.board_id}
              onClick={() => onSelectBoard(board)}
              className={`text-left p-4 rounded-2xl border transition-all duration-200 ${
                selectedBoard?.board_id === board.board_id
                  ? 'border-cyan-500/50 bg-cyan-500/10 shadow-lg shadow-cyan-500/5 ring-1 ring-cyan-500/30'
                  : 'border-white/[0.08] bg-[#0d111a]/60 hover:border-white/[0.16] hover:bg-[#131926]/70'
              }`}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-sans font-bold text-white">
                  {board.display_name}
                </p>
                {selectedBoard?.board_id === board.board_id && (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400" />
                )}
              </div>
              <p className="text-xs text-slate-400 font-sans mt-1">
                {board.mcu.toUpperCase()} · {board.architecture.toUpperCase()} · {board.clock_hz / 1e6} MHz
              </p>
              <div className="mt-3 pt-2 border-t border-white/[0.04] flex items-center justify-between text-[11px] font-mono text-slate-400">
                <span>SRAM: {board.sram_bytes / 1024}KB</span>
                <span>Flash: {board.flash_bytes / 1024}KB</span>
              </div>
            </button>
          ))}
        </div>
      </Section>

      {/* Backend & Hardware Link Section */}
      <Section label="Local Service &amp; Communication Bus">
        <div className="bg-[#0d111a]/80 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[11px] font-sans uppercase tracking-wider text-slate-400">REST API Gateway</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-mono text-slate-200">http://127.0.0.1:8765</span>
                <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400' : 'bg-rose-500'}`} />
              </div>
            </div>

            <div className="p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <span className="text-[11px] font-sans uppercase tracking-wider text-slate-400">WebSocket Socket</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs font-mono text-slate-200">ws://127.0.0.1:8765/ws/telemetry</span>
                <span className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-cyan-400' : 'bg-slate-600'}`} />
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleProbe}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.1] text-white rounded-full transition-colors shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Verify Link Health
            </button>
            {probeResult && (
              <div className="flex items-center gap-2 text-xs font-sans text-emerald-400">
                <CheckCircle className="w-4 h-4" />
                <span>v{probeResult.version} connected · {probeResult.subsystem}</span>
              </div>
            )}
          </div>
        </div>
      </Section>

      {/* Physical Hardware Serial Port Diagnostics */}
      <Section label="Physical Hardware Serial Interface">
        <div className="bg-[#0d111a]/80 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-sans text-slate-400 block mb-1.5">Detected COM / TTY Port</label>
              <div className="flex items-center gap-2">
                <select
                  value={selectedPort}
                  onChange={(e) => setSelectedPort(e.target.value)}
                  className="bg-white/[0.04] border border-white/[0.1] rounded-xl px-3 py-2 text-xs font-mono text-slate-200 outline-none flex-1 focus:border-cyan-500/50"
                >
                  <option value="" className="bg-[#0d111a]">Select Port…</option>
                  {ports.map((p) => (
                    <option key={p} value={p} className="bg-[#0d111a]">{p}</option>
                  ))}
                </select>
                <button
                  onClick={handleRefreshPorts}
                  className="text-xs font-mono text-slate-400 hover:text-white p-2 border border-white/[0.08] rounded-xl bg-white/[0.02]"
                  title="Rescan COM Ports"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs font-sans text-slate-400 block mb-1.5">Hardware Baud Rate</label>
              <select
                value={baudRate}
                onChange={(e) => setBaudRate(Number(e.target.value))}
                className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-3 py-2 text-xs font-mono text-slate-200 outline-none focus:border-cyan-500/50"
              >
                <option value={115200} className="bg-[#0d111a]">115200 baud (ARIS Default)</option>
                <option value={9600} className="bg-[#0d111a]">9600 baud</option>
              </select>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            {hardwareConnected ? (
              <button
                onClick={onDisconnect}
                className="px-4 py-2 text-xs font-semibold bg-rose-500/15 border border-rose-500/30 text-rose-400 rounded-full hover:bg-rose-500/25 transition-colors"
              >
                Disconnect Target
              </button>
            ) : (
              <button
                onClick={handleConnect}
                disabled={!selectedPort}
                className="px-4 py-2 text-xs font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 rounded-full hover:bg-emerald-500/25 transition-colors disabled:opacity-40"
              >
                Connect Target
              </button>
            )}
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${hardwareConnected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
              <span className={`text-xs font-sans font-medium ${hardwareConnected ? 'text-emerald-400' : 'text-slate-400'}`}>
                {hardwareConnected ? 'Physical Hardware Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </Section>

      {/* AI Providers */}
      <Section label="Neural Reasoning &amp; Synthesis Providers">
        <div className="bg-[#0d111a]/80 backdrop-blur-xl border border-white/[0.08] rounded-3xl p-5 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {providers.map((prov) => (
              <div
                key={prov.provider_id}
                className="flex items-center justify-between p-3.5 rounded-2xl bg-white/[0.02] border border-white/[0.04]"
              >
                <div className="flex items-center gap-2.5">
                  <div className={`w-2 h-2 rounded-full ${prov.available ? 'bg-emerald-400' : 'bg-slate-600'}`} />
                  <span className="text-xs font-medium text-slate-200 font-sans">{prov.display_name}</span>
                </div>
                <span className={`text-[10px] font-sans px-2.5 py-0.5 rounded-full border ${
                  prov.available
                    ? 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
                    : 'text-slate-500 border-white/[0.08]'
                }`}>
                  {prov.available ? 'Online' : 'Not Configured'}
                </span>
              </div>
            ))}
          </div>
          <p className="text-[11px] font-sans text-slate-400 mt-2">
            Deterministic AST rule synthesis operates locally with zero network dependency. Configure GEMINI_API_KEY for cloud model acceleration.
          </p>
        </div>
      </Section>
    </div>
  );
};

const Section: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children,
}) => (
  <div className="space-y-2">
    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-sans px-1">
      {label}
    </h3>
    {children}
  </div>
);
