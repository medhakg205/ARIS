import React, { useState, useEffect } from 'react';
import {
  Settings, Sliders, Cpu, Bell, Shield, Palette, Database, HardDrive,
  RefreshCw, CheckCircle, AlertTriangle, Monitor, Moon, Sun, Save
} from 'lucide-react';
import type { HealthStatus, BoardProfile, AIProviderInfo } from '../../types';
import { apiHealth, apiGetAIProviders, apiConnectionStatus, ARISApiError } from '../../services/api';
import { useTheme } from '../../hooks/useTheme';

interface SettingsCenterProps {
  health: HealthStatus | null;
  boards: BoardProfile[];
  selectedBoard: BoardProfile | null;
  onSelectBoard: (board: BoardProfile) => void;
  hardwareConnected: boolean;
  onConnect: (port: string, baud: number) => Promise<void>;
  onDisconnect: () => Promise<void>;
  backendOnline: boolean;
}

export const SettingsCenter: React.FC<SettingsCenterProps> = ({
  health,
  boards,
  selectedBoard,
  onSelectBoard,
  hardwareConnected,
  onConnect,
  onDisconnect,
  backendOnline
}) => {
  const { themeMode, setThemeMode } = useTheme();
  const [activeTab, setActiveTab] = useState<
    'general' | 'appearance' | 'hardware' | 'telemetry' | 'optimization' | 'notifications' | 'diagnostics'
  >('general');

  // General & Hardware state
  const [ports, setPorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState('');
  const [baudRate, setBaudRate] = useState(115200);
  const [providers, setProviders] = useState<AIProviderInfo[]>([]);
  const [selectedProvider, setSelectedProvider] = useState('rules_engine');
  const [pollIntervalMs, setPollIntervalMs] = useState(500);

  // Multi-objective weights state
  const [weights, setWeights] = useState({
    latency: 0.40,
    sram: 0.25,
    flash: 0.15,
    cpuLoad: 0.15,
    interruptSafety: 0.05
  });

  // Diagnostics probe
  const [probeResult, setProbeResult] = useState<HealthStatus | null>(null);
  const [probeLoading, setProbeLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

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
    setProbeLoading(true);
    try {
      const h = await apiHealth();
      setProbeResult(h);
    } catch {
      setProbeResult(null);
    } finally {
      setProbeLoading(false);
    }
  };

  const handleSave = () => {
    localStorage.setItem('aris_weights', JSON.stringify(weights));
    localStorage.setItem('aris_poll_interval', pollIntervalMs.toString());
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-6 gap-6 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-card border border-border shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-accent-cyan/10 border border-accent-cyan/20 text-accent-cyan">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-fg">Engineering System Settings</h2>
            <p className="text-xs text-muted font-sans mt-0.5">
              Configure toolchains, hardware interfaces, telemetry buffers, optimization weights, and UI preferences.
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-accent-cyan text-slate-950 text-xs font-bold transition-opacity hover:opacity-90 shadow-sm"
        >
          {savedSuccess ? <CheckCircle className="w-4 h-4 text-emerald-950" /> : <Save className="w-4 h-4" />}
          <span>{savedSuccess ? 'Settings Saved' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Tabs Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Left Navigation */}
        <div className="flex flex-col gap-1 p-2 rounded-xl bg-card border border-border">
          <button
            onClick={() => setActiveTab('general')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'general' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Settings className="w-4 h-4" />
            <span>General &amp; Environment</span>
          </button>
          <button
            onClick={() => setActiveTab('appearance')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'appearance' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Palette className="w-4 h-4" />
            <span>Appearance &amp; Theme</span>
          </button>
          <button
            onClick={() => setActiveTab('hardware')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'hardware' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Hardware &amp; Toolchain</span>
          </button>
          <button
            onClick={() => setActiveTab('telemetry')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'telemetry' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <HardDrive className="w-4 h-4" />
            <span>Telemetry &amp; Buffers</span>
          </button>
          <button
            onClick={() => setActiveTab('optimization')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'optimization' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Optimization Weights</span>
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'notifications' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Bell className="w-4 h-4" />
            <span>Notifications &amp; Alerts</span>
          </button>
          <button
            onClick={() => setActiveTab('diagnostics')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'diagnostics' ? 'bg-accent-cyan/10 text-accent-cyan font-semibold' : 'text-muted hover:text-fg hover:bg-hover'
            }`}
          >
            <Shield className="w-4 h-4" />
            <span>Diagnostics &amp; Health</span>
          </button>
        </div>

        {/* Right Content */}
        <div className="md:col-span-3 space-y-6">
          {activeTab === 'general' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <h3 className="text-sm font-bold text-fg">General Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-fg block mb-1">Telemetry Polling Interval (ms)</label>
                  <input
                    type="number"
                    min="100"
                    max="5000"
                    step="100"
                    value={pollIntervalMs}
                    onChange={(e) => setPollIntervalMs(Number(e.target.value))}
                    className="w-full max-w-xs bg-app border border-border text-xs rounded-lg px-3 py-2 text-fg focus:outline-none focus:border-accent-cyan font-mono"
                  />
                  <p className="text-[11px] text-muted mt-1">Recommended 500ms for stable high-resolution serial streaming.</p>
                </div>

                <div className="pt-3 border-t border-border">
                  <label className="text-xs font-medium text-fg block mb-1">AI Inference Engine</label>
                  <select
                    value={selectedProvider}
                    onChange={(e) => setSelectedProvider(e.target.value)}
                    className="w-full max-w-xs bg-app border border-border text-xs rounded-lg px-3 py-2 text-fg focus:outline-none focus:border-accent-cyan"
                  >
                    <option value="rules_engine">Deterministic Embedded Rules Engine (Offline / Safe)</option>
                    {providers.map((p) => (
                      <option key={p.provider_id || p.id} value={p.provider_id || p.id}>
                        {p.display_name || p.name} ({p.available ? 'AVAILABLE' : 'OFFLINE'})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <h3 className="text-sm font-bold text-fg">Appearance &amp; Theme</h3>
              <div className="grid grid-cols-3 gap-4">
                <button
                  onClick={() => setThemeMode('dark')}
                  className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    themeMode === 'dark'
                      ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                      : 'border-border bg-app text-muted hover:text-fg'
                  }`}
                >
                  <Moon className="w-6 h-6" />
                  <span className="text-xs font-semibold">Dark Theme</span>
                </button>
                <button
                  onClick={() => setThemeMode('light')}
                  className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    themeMode === 'light'
                      ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                      : 'border-border bg-app text-muted hover:text-fg'
                  }`}
                >
                  <Sun className="w-6 h-6" />
                  <span className="text-xs font-semibold">Light Theme</span>
                </button>
                <button
                  onClick={() => setThemeMode('system')}
                  className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                    themeMode === 'system'
                      ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                      : 'border-border bg-app text-muted hover:text-fg'
                  }`}
                >
                  <Monitor className="w-6 h-6" />
                  <span className="text-xs font-semibold">System Theme</span>
                </button>
              </div>
            </div>
          )}

          {activeTab === 'hardware' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <h3 className="text-sm font-bold text-fg">Hardware &amp; Communication Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-fg block mb-1">Target Architecture</label>
                  <div className="grid grid-cols-2 gap-3 max-w-md">
                    {boards.map((b) => (
                      <button
                        key={b.board_id || b.id}
                        onClick={() => onSelectBoard(b)}
                        className={`p-3 rounded-lg border text-left text-xs font-mono transition-all ${
                          (selectedBoard?.board_id === b.board_id || selectedBoard?.id === b.id)
                            ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                            : 'border-border bg-app text-muted hover:text-fg'
                        }`}
                      >
                        <div className="font-bold">{b.display_name || b.name}</div>
                        <div className="text-[10px] text-muted">{b.architecture || b.arch} &bull; {(b.clock_hz ? b.clock_hz / 1e6 : b.clock_mhz || 16)}MHz</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-3 border-t border-border">
                  <label className="text-xs font-medium text-fg block mb-1">Default Serial Baud Rate</label>
                  <select
                    value={baudRate}
                    onChange={(e) => setBaudRate(Number(e.target.value))}
                    className="w-full max-w-xs bg-app border border-border text-xs rounded-lg px-3 py-2 text-fg focus:outline-none focus:border-accent-cyan font-mono"
                  >
                    <option value={9600}>9600 baud</option>
                    <option value={57600}>57600 baud</option>
                    <option value={115200}>115200 baud (ARIS Standard)</option>
                    <option value={230400}>230400 baud</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'telemetry' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <h3 className="text-sm font-bold text-fg">Telemetry Buffering &amp; Baselines</h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-fg block mb-1">Ring Buffer Sample Capacity</label>
                  <input
                    type="number"
                    defaultValue={1000}
                    className="w-full max-w-xs bg-app border border-border text-xs rounded-lg px-3 py-2 text-fg font-mono"
                  />
                  <p className="text-[11px] text-muted mt-1">In-memory historical frames retained for real-time charting.</p>
                </div>
                <div>
                  <label className="text-xs font-medium text-fg block mb-1">Baseline Convergence Threshold (cycles)</label>
                  <input
                    type="number"
                    defaultValue={200}
                    className="w-full max-w-xs bg-app border border-border text-xs rounded-lg px-3 py-2 text-fg font-mono"
                  />
                  <p className="text-[11px] text-muted mt-1">Minimum contiguous valid packets before locking baseline reference.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'optimization' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-fg">Multi-Objective Optimization Weight Vector</h3>
                <span className="text-[11px] font-mono text-muted">Sum: {(weights.latency + weights.sram + weights.flash + weights.cpuLoad + weights.interruptSafety).toFixed(2)}</span>
              </div>
              <p className="text-xs text-muted">
                Assign importance weights across conflicting embedded engineering constraints.
              </p>

              <div className="space-y-4 pt-2">
                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span>Latency Reduction (W_lat)</span>
                    <span className="font-bold text-accent-cyan">{(weights.latency * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weights.latency}
                    onChange={(e) => setWeights({ ...weights, latency: parseFloat(e.target.value) })}
                    className="w-full accent-cyan-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span>SRAM Footprint Conservation (W_sram)</span>
                    <span className="font-bold text-accent-cyan">{(weights.sram * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weights.sram}
                    onChange={(e) => setWeights({ ...weights, sram: parseFloat(e.target.value) })}
                    className="w-full accent-cyan-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span>Flash Storage Optimization (W_flash)</span>
                    <span className="font-bold text-accent-cyan">{(weights.flash * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weights.flash}
                    onChange={(e) => setWeights({ ...weights, flash: parseFloat(e.target.value) })}
                    className="w-full accent-cyan-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span>CPU Active Load Factor (W_cpu)</span>
                    <span className="font-bold text-accent-cyan">{(weights.cpuLoad * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={weights.cpuLoad}
                    onChange={(e) => setWeights({ ...weights, cpuLoad: parseFloat(e.target.value) })}
                    className="w-full accent-cyan-500"
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
              <h3 className="text-sm font-bold text-fg">Alert Thresholds &amp; Notifications</h3>
              <div className="space-y-3 text-xs">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded border-border accent-cyan-500" />
                  <span className="text-fg">Alert immediately on MCU loop latency spike &gt; 2.0x baseline</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded border-border accent-cyan-500" />
                  <span className="text-fg">Notify on successful candidate compilation and verification</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded border-border accent-cyan-500" />
                  <span className="text-fg">Trigger automated emergency rollback on SLA breach</span>
                </label>
              </div>
            </div>
          )}

          {activeTab === 'diagnostics' && (
            <div className="p-5 rounded-2xl bg-card border border-border space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-fg">Subsystem Probe &amp; Health Status</h3>
                <button
                  onClick={handleProbe}
                  disabled={probeLoading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card hover:bg-hover border border-border text-xs text-fg font-medium"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${probeLoading ? 'animate-spin' : ''}`} />
                  <span>Run Probe</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3 rounded-lg bg-app border border-border flex items-center justify-between">
                  <span className="text-muted">FastAPI Service:</span>
                  <span className={backendOnline ? 'text-accent-green font-bold' : 'text-accent-red font-bold'}>
                    {backendOnline ? 'HEALTHY' : 'OFFLINE'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-app border border-border flex items-center justify-between">
                  <span className="text-muted">Serial Link:</span>
                  <span className={hardwareConnected ? 'text-accent-green font-bold' : 'text-muted font-bold'}>
                    {hardwareConnected ? 'CONNECTED' : 'DISCONNECTED'}
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-app border border-border flex items-center justify-between">
                  <span className="text-muted">Active Board:</span>
                  <span className="text-fg font-bold">{selectedBoard?.display_name || selectedBoard?.board_id || selectedBoard?.id || 'none'}</span>
                </div>
                <div className="p-3 rounded-lg bg-app border border-border flex items-center justify-between">
                  <span className="text-muted">SQLite Storage:</span>
                  <span className="text-accent-green font-bold">READY</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
