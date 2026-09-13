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
    <div className="flex flex-col h-full overflow-auto p-4 gap-6 max-w-3xl">
      <h2 className="text-sm font-mono font-semibold text-slate-200 flex items-center gap-2">
        <Settings className="w-4 h-4 text-slate-400" />
        Settings
      </h2>

      {error && <ErrorBanner error={error} onDismiss={() => setError(null)} />}

      {/* Backend Connection */}
      <Section label="Backend Connection">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400 w-24">API Base:</span>
            <span className="text-xs font-mono text-slate-300">http://127.0.0.1:8765</span>
            <div className={`w-2 h-2 rounded-full ${backendOnline ? 'bg-emerald-400' : 'bg-red-400'}`} />
            <span className={`text-[10px] font-mono ${backendOnline ? 'text-emerald-400' : 'text-red-400'}`}>
              {backendOnline ? 'Online' : 'Offline'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400 w-24">WebSocket:</span>
            <span className="text-xs font-mono text-slate-300">ws://127.0.0.1:8765/ws/telemetry/&#123;run_id&#125;</span>
          </div>
          <button
            onClick={handleProbe}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-slate-800 border border-slate-700 text-slate-300 rounded hover:bg-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Probe Backend
          </button>
          {probeResult && (
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400">
              <CheckCircle className="w-3.5 h-3.5" />
              v{probeResult.version} · {probeResult.subsystem} · Database: {probeResult.database}
            </div>
          )}
        </div>
      </Section>

      {/* Board Selection */}
      <Section label="Target Board Profile">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
            Auto-Detect Active: Board and memory limits auto-configure on USB plug-in
          </span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {boards.map((board) => (
            <button
              key={board.board_id}
              onClick={() => onSelectBoard(board)}
              className={`text-left p-3 rounded border transition-all ${
                selectedBoard?.board_id === board.board_id
                  ? 'border-cyan-500/50 bg-cyan-500/5 ring-1 ring-cyan-500/30'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <p className="text-xs font-mono font-semibold text-slate-200">
                {board.display_name}
              </p>
              <p className="text-[10px] font-mono text-slate-500 mt-0.5">
                {board.mcu.toUpperCase()} · {board.architecture.toUpperCase()} · {board.clock_hz / 1e6} MHz
              </p>
              <p className="text-[10px] font-mono text-slate-500">
                Flash: {board.flash_bytes / 1024}KB · SRAM: {board.sram_bytes / 1024}KB
              </p>
            </button>
          ))}
        </div>
      </Section>

      {/* Serial Port */}
      <Section label="Hardware Serial Port">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <select
              value={selectedPort}
              onChange={(e) => setSelectedPort(e.target.value)}
              className="bg-slate-800/50 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-300 outline-none flex-1"
            >
              <option value="">Select port…</option>
              {ports.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
            <button
              onClick={handleRefreshPorts}
              className="text-xs font-mono text-slate-500 hover:text-slate-300 p-1.5 border border-slate-800 rounded"
              title="Refresh ports"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400 w-24">Baud Rate:</span>
            <select
              value={baudRate}
              onChange={(e) => setBaudRate(Number(e.target.value))}
              className="bg-slate-800/50 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-slate-300 outline-none"
            >
              <option value={9600}>9600</option>
              <option value={115200}>115200</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            {hardwareConnected ? (
              <button
                onClick={onDisconnect}
                className="px-3 py-1.5 text-xs font-mono bg-red-500/10 border border-red-500/40 text-red-400 rounded hover:bg-red-500/20 transition-colors"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={handleConnect}
                disabled={!selectedPort}
                className="px-3 py-1.5 text-xs font-mono bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 rounded hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
              >
                Connect
              </button>
            )}
            <div className={`w-2 h-2 rounded-full ${hardwareConnected ? 'bg-emerald-400' : 'bg-slate-600'}`} />
            <span className={`text-xs font-mono ${hardwareConnected ? 'text-emerald-400' : 'text-slate-500'}`}>
              {hardwareConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </Section>

      {/* AI Providers */}
      <Section label="AI Optimization Providers">
        <div className="space-y-2">
          {providers.length === 0 && (
            <p className="text-xs font-mono text-slate-500">Loading providers…</p>
          )}
          {providers.map((prov) => (
            <div
              key={prov.provider_id}
              className="flex items-center gap-3 bg-slate-900/40 border border-slate-800 rounded px-3 py-2"
            >
              <div className={`w-2 h-2 rounded-full ${prov.available ? 'bg-emerald-400' : 'bg-slate-600'}`} />
              <span className="text-xs font-mono text-slate-300 flex-1">{prov.display_name}</span>
              <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                prov.available
                  ? 'text-emerald-400 border-emerald-500/30'
                  : 'text-slate-500 border-slate-700'
              }`}>
                {prov.available ? 'Available' : 'Unavailable'}
              </span>
            </div>
          ))}
          <p className="text-[10px] font-mono text-slate-600 mt-2">
            Set GEMINI_API_KEY or OPENAI_API_KEY environment variables. The deterministic Rule Synthesizer is always available.
          </p>
        </div>
      </Section>

      {/* Demo Mode */}
      <Section label="Simulation &amp; Demo Mode">
        <div className="flex items-center gap-3">
          {isDemo ? (
            <button
              onClick={onStopRun}
              className="px-3 py-1.5 text-xs font-mono bg-amber-500/10 border border-amber-500/40 text-amber-400 rounded hover:bg-amber-500/20 transition-colors"
            >
              Stop Demo
            </button>
          ) : (
            <button
              onClick={onStartDemo}
              className="px-3 py-1.5 text-xs font-mono bg-amber-500/10 border border-amber-500/40 text-amber-400 rounded hover:bg-amber-500/20 transition-colors"
            >
              Start Demo Run (Simulated Hardware)
            </button>
          )}
          {isDemo && (
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-xs font-mono text-amber-400">DEMO MODE ACTIVE — Synthetic Telemetry</span>
            </div>
          )}
        </div>
        <p className="text-[10px] font-mono text-slate-600 mt-2">
          Demo mode uses the backend hardware simulator. Telemetry is clearly marked as simulated.
        </p>
      </Section>
    </div>
  );
};

const Section: React.FC<{ label: string; children: React.ReactNode }> = ({
  label,
  children,
}) => (
  <div className="space-y-3">
    <h3 className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">
      {label}
    </h3>
    {children}
  </div>
);
