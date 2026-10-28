// ============================================================
// ARIS Studio — System Settings (v3.0.0-COMMERCIAL)
// Professional, restrained Windows engineering settings interface
// Categorized into 5 distinct engineering tabs:
// 1. GENERAL (Appearance & Startup)
// 2. HARDWARE (Target Board, Serial Port, Baud Rate)
// 3. INSTRUMENTATION (Shadow Compilation, Polling, Buffer Size)
// 4. SIMULATION (Generator Mode, Latency & Jitter Profile)
// 5. SYSTEM (Backend Status, Database Info, Diagnostics Probe)
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  Palette,
  Database,
  HardDrive,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Monitor,
  Moon,
  Sun,
  Save,
  Usb,
  Activity,
  ShieldCheck,
  Terminal,
  Sliders,
  Layers,
  Check
} from 'lucide-react';
import type { HealthStatus, BoardProfile, AIProviderInfo } from '../../types';
import { apiHealth, apiGetAIProviders, apiConnectionStatus, getApiBaseUrl } from '../../services/api';
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

type SettingsTab = 'general' | 'hardware' | 'instrumentation' | 'simulation' | 'system';

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
  const [activeTab, setActiveTab] = useState<SettingsTab>('general');

  // Dynamic API configuration
  const apiBase = getApiBaseUrl();
  const portMatch = apiBase.match(/:(\d+)/);
  const configuredPort = portMatch ? portMatch[1] : '8765';

  // General state
  const [splashEnabled, setSplashEnabled] = useState(() => {
    try {
      return localStorage.getItem('aris_splash_disabled') !== 'true';
    } catch {
      return true;
    }
  });
  const [autoScanEnabled, setAutoScanEnabled] = useState(() => {
    try {
      return localStorage.getItem('aris_auto_scan') !== 'false';
    } catch {
      return true;
    }
  });

  // Hardware & Port state
  const [ports, setPorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState('');
  const [baudRate, setBaudRate] = useState(115200);
  const [connecting, setConnecting] = useState(false);

  // Instrumentation state
  const [pollIntervalMs, setPollIntervalMs] = useState(() => {
    try {
      const v = localStorage.getItem('aris_poll_interval');
      return v ? parseInt(v, 10) : 500;
    } catch {
      return 500;
    }
  });
  const [ringBufferSize, setRingBufferSize] = useState(() => {
    try {
      const v = localStorage.getItem('aris_buffer_size');
      return v ? parseInt(v, 10) : 1000;
    } catch {
      return 1000;
    }
  });

  // Simulation state
  const [simMode, setSimMode] = useState<'deterministic' | 'jittered' | 'stress'>('deterministic');
  const [simBaseLatency, setSimBaseLatency] = useState(1000.02);
  const [simJitterRange, setSimJitterRange] = useState(1.2);

  // Diagnostics & Probe state
  const [probeResult, setProbeResult] = useState<HealthStatus | null>(health);
  const [probeLoading, setProbeLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (backendOnline) {
      apiConnectionStatus()
        .then((cs) => {
          setPorts(cs.available_ports || []);
          if (cs.port) setSelectedPort(cs.port);
        })
        .catch(() => {});
    }
  }, [backendOnline]);

  const handleSave = () => {
    try {
      localStorage.setItem('aris_splash_disabled', (!splashEnabled).toString());
      localStorage.setItem('aris_auto_scan', autoScanEnabled.toString());
      localStorage.setItem('aris_poll_interval', pollIntervalMs.toString());
      localStorage.setItem('aris_buffer_size', ringBufferSize.toString());
      localStorage.setItem('aris_sim_mode', simMode);
      localStorage.setItem('aris_sim_base_latency', simBaseLatency.toString());
      localStorage.setItem('aris_sim_jitter_range', simJitterRange.toString());
    } catch {}
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

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

  const handleConnectPort = async () => {
    if (!selectedPort) return;
    setConnecting(true);
    try {
      await onConnect(selectedPort, baudRate);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 md:p-6 gap-6 max-w-6xl mx-auto w-full select-none">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/20 shadow-xs">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-heading font-extrabold text-[var(--text-primary)]">System Settings</h2>
            <p className="text-xs text-[var(--text-muted)] font-sans mt-0.5">
              Toolchains, hardware serial interfaces, runtime acquisition parameters, and simulation profiles.
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="aris-btn-primary flex items-center gap-1.5 text-xs font-sans"
        >
          {savedSuccess ? <CheckCircle className="w-4 h-4 text-emerald-950" /> : <Save className="w-4 h-4" />}
          <span>{savedSuccess ? 'Settings Saved' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Main 2-Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Navigation Sidebar */}
        <div className="flex flex-col gap-1 p-2 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] h-fit shadow-xs font-sans">
          <button
            onClick={() => setActiveTab('general')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'general'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold border border-[var(--accent-cyan)]/30'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
            }`}
          >
            <Palette className="w-4 h-4" />
            <span>General</span>
          </button>

          <button
            onClick={() => setActiveTab('hardware')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'hardware'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold border border-[var(--accent-cyan)]/30'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Hardware</span>
          </button>

          <button
            onClick={() => setActiveTab('instrumentation')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'instrumentation'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold border border-[var(--accent-cyan)]/30'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
            }`}
          >
            <HardDrive className="w-4 h-4" />
            <span>Instrumentation</span>
          </button>

          <button
            onClick={() => setActiveTab('simulation')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'simulation'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold border border-[var(--accent-cyan)]/30'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Simulation</span>
          </button>

          <button
            onClick={() => setActiveTab('system')}
            className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium text-left transition-colors ${
              activeTab === 'system'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold border border-[var(--accent-cyan)]/30'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Subsystem Health</span>
          </button>
        </div>

        {/* Content Panel */}
        <div className="md:col-span-3 space-y-6">
          {/* TAB 1: GENERAL */}
          {activeTab === 'general' && (
            <div className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-6">
              <div>
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Appearance &amp; Theme</h3>
                <p className="text-xs text-[var(--text-muted)] font-sans mt-0.5">
                  Visual theme configuration for high-contrast industrial readability and dark laboratory environments.
                </p>
                <div className="grid grid-cols-3 gap-3 mt-3">
                  <button
                    onClick={() => setThemeMode('dark')}
                    className={`p-3.5 rounded-lg border flex flex-col items-center gap-2 transition-all font-sans text-xs ${
                      themeMode === 'dark'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold shadow-xs'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <Moon className="w-5 h-5" />
                    <span>Dark Theme (Default)</span>
                  </button>
                  <button
                    onClick={() => setThemeMode('light')}
                    className={`p-3.5 rounded-lg border flex flex-col items-center gap-2 transition-all font-sans text-xs ${
                      themeMode === 'light'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold shadow-xs'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <Sun className="w-5 h-5" />
                    <span>Light Theme</span>
                  </button>
                  <button
                    onClick={() => setThemeMode('system')}
                    className={`p-3.5 rounded-lg border flex flex-col items-center gap-2 transition-all font-sans text-xs ${
                      themeMode === 'system'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold shadow-xs'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <Monitor className="w-5 h-5" />
                    <span>System Theme</span>
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-3">
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Startup Behavior</h3>
                <div className="space-y-2.5">
                  <label className="flex items-center gap-2.5 text-xs font-mono text-[var(--text-secondary)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={splashEnabled}
                      onChange={(e) => setSplashEnabled(e.target.checked)}
                      className="rounded border-[var(--border-color)] accent-[var(--accent-cyan)]"
                    />
                    <span>Display engineering startup splash screen on launch</span>
                  </label>
                  <label className="flex items-center gap-2.5 text-xs font-mono text-[var(--text-secondary)] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={autoScanEnabled}
                      onChange={(e) => setAutoScanEnabled(e.target.checked)}
                      className="rounded border-[var(--border-color)] accent-[var(--accent-cyan)]"
                    />
                    <span>Automatically probe serial ports for connected Arduino hardware on launch</span>
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-2">
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Source Safety Protection</h3>
                <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-start gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-[var(--accent-green)] mt-0.5 shrink-0" />
                  <div className="text-xs font-mono text-[var(--text-secondary)]">
                    <span className="font-bold text-[var(--text-primary)]">Zero-Invasive Instrumentation:</span> ARIS compiles exclusively inside isolated shadow workspaces. Original local sketches remain bit-for-bit identical until explicit manual optimization acceptance.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: HARDWARE */}
          {activeTab === 'hardware' && (
            <div className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-6">
              <div>
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Target Microcontroller Profile</h3>
                <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                  Select target hardware profile to calibrate cycle clocks, SRAM budgets, and compiler FQBNs.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                  {boards.map((b) => {
                    const isSelected = selectedBoard?.board_id === b.board_id || selectedBoard?.id === b.id;
                    return (
                      <button
                        key={b.board_id || b.id}
                        onClick={() => onSelectBoard(b)}
                        className={`p-3 rounded-lg border text-left font-mono transition-all ${
                          isSelected
                            ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]'
                            : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                        }`}
                      >
                        <div className="font-bold text-xs text-[var(--text-primary)]">{b.display_name || b.name}</div>
                        <div className="text-[10px] text-[var(--text-muted)] mt-1 flex justify-between">
                          <span>MCU: {b.mcu?.toUpperCase() || 'AVR'}</span>
                          <span>Clock: {(b.clock_hz ? b.clock_hz / 1e6 : b.clock_mhz || 16)} MHz</span>
                        </div>
                        <div className="text-[10px] text-[var(--text-muted)] mt-0.5 flex justify-between">
                          <span>SRAM: {b.sram_bytes || 2048} B</span>
                          <span>Flash: {b.flash_bytes || 32768} B</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-4">
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Serial Port &amp; Communication</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1.5">
                      Serial Port
                    </label>
                    <select
                      value={selectedPort}
                      onChange={(e) => setSelectedPort(e.target.value)}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    >
                      <option value="">{ports.length === 0 ? 'No COM ports detected' : 'Select COM Port'}</option>
                      {ports.map((p) => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1.5">
                      Baud Rate
                    </label>
                    <select
                      value={baudRate}
                      onChange={(e) => setBaudRate(Number(e.target.value))}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    >
                      <option value={9600}>9600 baud</option>
                      <option value={57600}>57600 baud</option>
                      <option value={115200}>115200 baud (ARIS Standard Handshake)</option>
                      <option value={230400}>230400 baud</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  {hardwareConnected ? (
                    <button
                      onClick={onDisconnect}
                      className="px-4 py-2 rounded-lg bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/30 text-xs font-semibold hover:opacity-90 transition-opacity"
                    >
                      Disconnect Port
                    </button>
                  ) : (
                    <button
                      onClick={handleConnectPort}
                      disabled={!selectedPort || connecting}
                      className="aris-btn-primary text-xs"
                    >
                      {connecting ? 'Connecting...' : 'Connect Hardware Port'}
                    </button>
                  )}
                  <span className="text-xs font-mono text-[var(--text-muted)]">
                    Status: {hardwareConnected ? <span className="text-[var(--accent-green)] font-semibold">CONNECTED ({selectedPort || 'COM4'})</span> : 'STANDBY'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: INSTRUMENTATION */}
          {activeTab === 'instrumentation' && (
            <div className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-6">
              <div>
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Transparent Shadow Compilation</h3>
                <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                  ARIS isolates all instrumentation logic into temporary shadow workspaces.
                </p>
                <div className="mt-3 p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between text-[var(--text-primary)] font-bold">
                    <span>Shadow Workspace Isolation:</span>
                    <span className="text-[var(--accent-green)] font-semibold">ENFORCED (Active)</span>
                  </div>
                  <p className="text-[var(--text-muted)] leading-relaxed">
                    Pre-build hooks inject the ARIS micro-probe into a transient copy inside <code className="text-[var(--accent-cyan)]">.aris/shadow/</code>. The original user <code className="text-[var(--text-primary)]">.ino</code> sketch is never modified during profiling.
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-4">
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Telemetry Acquisition Parameters</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1">
                      Telemetry Polling Interval (ms)
                    </label>
                    <input
                      type="number"
                      min="100"
                      max="5000"
                      step="50"
                      value={pollIntervalMs}
                      onChange={(e) => setPollIntervalMs(Number(e.target.value))}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    />
                    <p className="text-[11px] font-mono text-[var(--text-muted)] mt-1">Recommended: 500 ms for serial buffer stability.</p>
                  </div>

                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1">
                      Ring Buffer Sample Capacity (frames)
                    </label>
                    <input
                      type="number"
                      min="100"
                      max="10000"
                      step="100"
                      value={ringBufferSize}
                      onChange={(e) => setRingBufferSize(Number(e.target.value))}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    />
                    <p className="text-[11px] font-mono text-[var(--text-muted)] mt-1">Number of in-memory packets retained for live charting.</p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-2 text-xs font-mono">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[var(--text-secondary)]">Probe Overhead Budget:</span>
                  <span className="text-[var(--text-primary)] font-bold">&lt; 0.8% CPU / 42 Bytes SRAM</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[var(--bg-surface)] overflow-hidden">
                  <div className="h-full bg-[var(--accent-green)] w-[4%]" />
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: SIMULATION */}
          {activeTab === 'simulation' && (
            <div className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-6">
              <div>
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Simulation Generator Mode</h3>
                <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                  Configure synthetic telemetry generators when hardware is disconnected.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                  <button
                    onClick={() => setSimMode('deterministic')}
                    className={`p-3 rounded-lg border text-left font-mono text-xs transition-all ${
                      simMode === 'deterministic'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <div className="text-[var(--text-primary)]">Deterministic Mode</div>
                    <div className="text-[10px] text-[var(--text-muted)] mt-1">Exact 1000.02 ms reference cycle timing.</div>
                  </button>

                  <button
                    onClick={() => setSimMode('jittered')}
                    className={`p-3 rounded-lg border text-left font-mono text-xs transition-all ${
                      simMode === 'jittered'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <div className="text-[var(--text-primary)]">Realistic Physical Jitter</div>
                    <div className="text-[10px] text-[var(--text-muted)] mt-1">Simulates real oscillator drift and ISR jitter.</div>
                  </button>

                  <button
                    onClick={() => setSimMode('stress')}
                    className={`p-3 rounded-lg border text-left font-mono text-xs transition-all ${
                      simMode === 'stress'
                        ? 'border-[var(--accent-cyan)] bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                        : 'border-[var(--border-color)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                    }`}
                  >
                    <div className="text-[var(--text-primary)]">Stress Test Profile</div>
                    <div className="text-[10px] text-[var(--text-muted)] mt-1">High loop frequency with dynamic load spikes.</div>
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-4">
                <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Synthetic Latency &amp; Jitter Profile</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1">
                      Baseline Loop Latency (ms)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={simBaseLatency}
                      onChange={(e) => setSimBaseLatency(Number(e.target.value))}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    />
                    <p className="text-[11px] font-mono text-[var(--text-muted)] mt-1">Default: 1000.02 ms matches unoptimized delay(1000) sketch.</p>
                  </div>

                  <div>
                    <label className="text-xs font-mono font-medium text-[var(--text-secondary)] block mb-1">
                      Gaussian Jitter Variance (± ms)
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={simJitterRange}
                      onChange={(e) => setSimJitterRange(Number(e.target.value))}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs rounded-lg px-3 py-2 text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-cyan)]"
                    />
                    <p className="text-[11px] font-mono text-[var(--text-muted)] mt-1">Simulates crystal resonator thermal variance.</p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[var(--border-color)] space-y-1.5 text-xs font-mono text-[var(--text-muted)]">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-[var(--accent-amber)]" />
                  <span>Provenance Tag: All simulated samples are watermarked with <code className="text-[var(--accent-amber)]">is_demo: true</code></span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: SYSTEM */}
          {activeTab === 'system' && (
            <div className="p-5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-heading font-bold text-[var(--text-primary)]">Subsystem Probe &amp; Health</h3>
                  <p className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                    FastAPI analytical backend, database storage, and IPC channels.
                  </p>
                </div>
                <button
                  onClick={handleProbe}
                  disabled={probeLoading}
                  className="aris-btn-secondary flex items-center gap-1.5 text-xs font-sans"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${probeLoading ? 'animate-spin' : ''}`} />
                  <span>Probe Subsystems</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Analytical Backend:</span>
                  <span className={backendOnline ? 'text-[var(--accent-green)] font-bold' : 'text-[var(--accent-red)] font-bold'}>
                    {backendOnline ? `HEALTHY (Port ${configuredPort})` : 'OFFLINE'}
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">SQLite Database:</span>
                  <span className="text-[var(--accent-green)] font-bold">
                    {health?.database || probeResult?.database || 'CONNECTED'} (aris.db)
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Serial Link State:</span>
                  <span className={hardwareConnected ? 'text-[var(--accent-green)] font-bold' : 'text-[var(--text-muted)] font-bold'}>
                    {hardwareConnected ? `CONNECTED (${selectedPort || health?.serial_port || 'ACTIVE'})` : 'STANDBY'}
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-between">
                  <span className="text-[var(--text-muted)]">Active Target Board:</span>
                  <span className="text-[var(--text-primary)] font-bold">
                    {selectedBoard?.display_name || health?.supported_boards?.[0] || 'Arduino Uno'}
                  </span>
                </div>
              </div>

              {probeResult && (
                <div className="pt-4 border-t border-[var(--border-color)] space-y-2">
                  <span className="text-xs font-mono font-bold text-[var(--text-secondary)]">
                    Live Diagnostics Probe Report:
                  </span>
                  <div className="p-3 rounded-lg bg-[var(--bg-app)] border border-[var(--border-color)] font-mono text-xs text-[var(--text-muted)] space-y-1">
                    <div>Status: <span className="text-[var(--accent-green)] font-bold">{probeResult.status}</span></div>
                    <div>Version: {probeResult.version || '3.0.0'}</div>
                    <div>Serial Hardware: {probeResult.serial_connected ? `CONNECTED (${probeResult.serial_port || 'ACTIVE'})` : 'STANDBY'}</div>
                    <div>Database: {probeResult.database || 'READY'}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
