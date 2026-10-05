// ============================================================
// ARIS — Device Center (v3.0.0)
// Hardware Discovery, Multi-source Confidence & Serial Handshake
// ============================================================

import React, { useState } from 'react';
import {
  Cpu,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Zap,
  Activity,
  HardDrive,
  Clock,
  Layers,
  ShieldAlert,
  Sliders,
  ExternalLink,
} from 'lucide-react';
import { BoardProfile, ConnectionStatus, DiscoveredPortInfo } from '../../types';

interface DevicesViewProps {
  boards: BoardProfile[];
  selectedBoard: BoardProfile | null;
  onSelectBoard: (board: BoardProfile) => void;
  connectionStatus: ConnectionStatus;
  hardwareConnected: boolean;
  onConnect: (port: string, baudRate?: number) => Promise<boolean>;
  onDisconnect: () => Promise<boolean>;
  onAutoDetect: () => Promise<boolean>;
  onTriggerHandshake?: () => Promise<void>;
  isDemo: boolean;
  onNavigate: (tab: string) => void;
  loading?: boolean;
}

export const DevicesView: React.FC<DevicesViewProps> = ({
  boards,
  selectedBoard,
  onSelectBoard,
  connectionStatus,
  hardwareConnected,
  onConnect,
  onDisconnect,
  onAutoDetect,
  onTriggerHandshake,
  isDemo,
  onNavigate,
  loading = false,
}) => {
  const [detecting, setDetecting] = useState(false);
  const [detectionStep, setDetectionStep] = useState(0);
  const [selectedPortDetail, setSelectedPortDetail] = useState<DiscoveredPortInfo | null>(null);

  const discoveredPorts: DiscoveredPortInfo[] = connectionStatus.discovered_ports || [];

  const handleStartAutoDetect = async () => {
    setDetecting(true);
    setDetectionStep(1); // 1. Scanning serial ports
    await new Promise((r) => setTimeout(r, 350));
    setDetectionStep(2); // 2. Inspecting USB identifiers
    await new Promise((r) => setTimeout(r, 350));
    setDetectionStep(3); // 3. Checking Arduino CLI
    await new Promise((r) => setTimeout(r, 350));
    setDetectionStep(4); // 4. Identifying board
    await new Promise((r) => setTimeout(r, 350));
    setDetectionStep(5); // 5. Establishing ARIS handshake

    try {
      await onAutoDetect();
    } finally {
      setDetecting(false);
      setDetectionStep(0);
    }
  };

  const detectionSteps = [
    'Scanning system serial COM ports...',
    'Inspecting USB VID/PID hardware descriptors...',
    'Querying Arduino CLI board detection JSON...',
    'Resolving board architecture and FQBN profile...',
    'Performing bidirectional runtime serial handshake ($ARIS_HELLO#)...',
  ];

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* Top Banner & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <h2 className="text-xl font-heading font-bold text-[var(--text-primary)]">
            Device Center
          </h2>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Microcontroller board discovery, USB-UART bridge classification, and physical serial link
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleStartAutoDetect}
            disabled={detecting || loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold shadow-sm transition-opacity disabled:opacity-50"
          >
            <RefreshCw size={14} className={detecting ? 'animate-spin' : ''} />
            <span>{detecting ? 'Scanning Hardware...' : 'Auto-Detect Board'}</span>
          </button>
        </div>
      </div>

      {/* Auto-Detect Progress Overlay */}
      {detecting && (
        <div className="p-4 rounded-xl border border-[var(--accent-cyan)]/30 bg-[var(--accent-cyan-bg)] space-y-2">
          <div className="flex items-center justify-between text-xs font-mono font-semibold text-[var(--accent-cyan)]">
            <span className="flex items-center gap-2">
              <RefreshCw size={14} className="animate-spin" />
              <span>Multi-Source Hardware Discovery Active</span>
            </span>
            <span>Step {detectionStep} of 5</span>
          </div>
          <div className="w-full bg-[var(--border-color)] h-1.5 rounded-full overflow-hidden">
            <div
              className="bg-[var(--accent-cyan)] h-full transition-all duration-300"
              style={{ width: `${(detectionStep / 5) * 100}%` }}
            />
          </div>
          <p className="text-[11px] font-mono text-[var(--text-secondary)]">
            {detectionSteps[detectionStep - 1] || 'Scanning...'}
          </p>
        </div>
      )}

      {/* Active Connection Status Card */}
      <div className="aris-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Active Connection Status
          </span>
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                hardwareConnected
                  ? 'bg-[var(--accent-green)] animate-soft-beacon'
                  : 'bg-[var(--text-muted)]'
              }`}
            />
            <span className="text-xs font-mono font-semibold">
              {hardwareConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
        </div>

        {hardwareConnected ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)]">
              <div className="text-[10px] text-[var(--text-muted)] font-mono">TARGET BOARD</div>
              <div className="text-sm font-bold text-[var(--text-primary)] mt-0.5">
                {selectedBoard?.display_name || 'Arduino Microcontroller'}
              </div>
              <div className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                {selectedBoard?.mcu?.toUpperCase()} ({selectedBoard?.architecture?.toUpperCase()})
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)]">
              <div className="text-[10px] text-[var(--text-muted)] font-mono">SERIAL PORT</div>
              <div className="text-sm font-bold text-[var(--text-primary)] mt-0.5">
                {connectionStatus.port || 'COM'}
              </div>
              <div className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                {connectionStatus.baud_rate || 115200} BAUD · 8N1
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)]">
              <div className="text-[10px] text-[var(--text-muted)] font-mono">VERACITY MODE</div>
              <div className="text-sm font-bold text-[var(--accent-green)] mt-0.5">
                PHYSICAL HARDWARE
              </div>
              <div className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                is_demo = False (Strict Provenance)
              </div>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex flex-col justify-between">
              <div className="text-[10px] text-[var(--text-muted)] font-mono">ACTIONS</div>
              <div className="flex gap-2 mt-1">
                {onTriggerHandshake && (
                  <button
                    onClick={onTriggerHandshake}
                    className="flex-1 py-1 px-2 rounded bg-[var(--bg-card)] border border-[var(--border-color)] hover:bg-[var(--bg-card-hover)] text-[11px] font-medium transition-colors"
                  >
                    Handshake
                  </button>
                )}
                <button
                  onClick={onDisconnect}
                  className="flex-1 py-1 px-2 rounded bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/20 hover:opacity-90 text-[11px] font-medium transition-colors"
                >
                  Disconnect
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-6 px-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex flex-col items-center justify-center text-center space-y-2">
            <Cpu size={32} className="text-[var(--text-muted)] opacity-60" />
            <div className="text-sm font-semibold text-[var(--text-primary)]">
              No Physical Hardware Connected
            </div>
            <p className="text-xs text-[var(--text-muted)] max-w-md">
              Connect an official Arduino Uno, Nano, or Mega via USB. ARIS interrogates system ports, identifies microcontroller profiles, and initializes the $ARIS_HELLO# protocol.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={handleStartAutoDetect}
                className="px-3 py-1.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold transition-opacity"
              >
                Scan Serial Ports
              </button>
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              >
                Use Simulation Mode
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Discovered Physical Serial Ports */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Discovered COM / USB TTY Ports ({discoveredPorts.length})
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            Direct Host Inspection
          </span>
        </div>

        {discoveredPorts.length === 0 ? (
          <div className="aris-card p-6 text-center text-xs text-[var(--text-muted)] font-mono">
            No active serial COM or USB TTY ports detected on this workstation.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {discoveredPorts.map((port) => (
              <div
                key={port.device}
                className="aris-card p-4 space-y-3 aris-card-hover"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)]">
                      <Cpu size={18} className="text-[var(--accent-cyan)]" />
                    </div>
                    <div>
                      <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
                        {port.device}
                      </div>
                      <div className="text-xs text-[var(--text-muted)] truncate max-w-[220px]">
                        {port.description || 'USB Serial Device'}
                      </div>
                    </div>
                  </div>

                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                      port.is_arduino
                        ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/20'
                        : 'bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)]'
                    }`}
                  >
                    {port.is_arduino ? 'ARDUINO' : 'SERIAL BRIDGE'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1 border-t border-[var(--border-color)]">
                  <div>
                    <span className="text-[var(--text-muted)]">VID:PID: </span>
                    <span className="text-[var(--text-primary)]">
                      {port.vid || '—'}:{port.pid || '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[var(--text-muted)]">Target: </span>
                    <span className="text-[var(--text-primary)]">
                      {port.suggested_board_id || 'Generic'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    onClick={() => setSelectedPortDetail(port)}
                    className="text-xs font-mono text-[var(--accent-cyan)] hover:underline flex items-center gap-1"
                  >
                    Inspect Hardware <ExternalLink size={12} />
                  </button>

                  <button
                    onClick={() => onConnect(port.device, 115200)}
                    disabled={hardwareConnected && connectionStatus.port === port.device}
                    className="px-3 py-1 rounded bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold disabled:opacity-40 transition-opacity"
                  >
                    {hardwareConnected && connectionStatus.port === port.device
                      ? 'Connected'
                      : 'Connect'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Supported Microcontroller Profiles */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            Architectural Board Profiles
          </span>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            AVR8 Core Invariants
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {boards.map((b) => {
            const isSelected = selectedBoard?.board_id === b.board_id;
            return (
              <div
                key={b.board_id}
                onClick={() => onSelectBoard(b)}
                className={`aris-card p-4 space-y-3 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-[var(--accent-cyan)] shadow-md ring-1 ring-[var(--accent-cyan)]/30'
                    : 'aris-card-hover'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
                      {b.display_name}
                    </div>
                    <div className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                      {b.mcu.toUpperCase()} · {b.architecture.toUpperCase()}
                    </div>
                  </div>
                  {isSelected && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold">
                      ACTIVE
                    </span>
                  )}
                </div>

                <div className="space-y-1.5 text-xs font-mono pt-2 border-t border-[var(--border-color)]">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Clock:</span>
                    <span className="text-[var(--text-primary)]">{(b.clock_hz / 1e6).toFixed(0)} MHz (62.5ns)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Flash ROM:</span>
                    <span className="text-[var(--text-primary)]">{b.flash_bytes / 1024} KB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">SRAM:</span>
                    <span className="text-[var(--text-primary)]">{b.sram_bytes / 1024} KB ({b.sram_bytes}B)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Timers:</span>
                    <span className="text-[var(--text-primary)]">{b.timer_count} Hardware</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Port Inspection Drawer/Modal */}
      {selectedPortDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-3">
              <div className="font-heading font-bold text-base text-[var(--text-primary)]">
                Hardware Port Telemetry: {selectedPortDetail.device}
              </div>
              <button
                onClick={() => setSelectedPortDetail(null)}
                className="text-xs font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              >
                Close
              </button>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">Device:</span>
                <span className="text-[var(--text-primary)] font-bold">{selectedPortDetail.device}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">Description:</span>
                <span className="text-[var(--text-primary)]">{selectedPortDetail.description}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">HWID:</span>
                <span className="text-[var(--text-primary)] truncate max-w-xs">{selectedPortDetail.hwid}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">Vendor ID:</span>
                <span className="text-[var(--text-primary)]">{selectedPortDetail.vid || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">Product ID:</span>
                <span className="text-[var(--text-primary)]">{selectedPortDetail.pid || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[var(--border-color)]">
                <span className="text-[var(--text-muted)]">Suggested Board:</span>
                <span className="text-[var(--accent-cyan)] font-bold">{selectedPortDetail.suggested_board_id || '—'}</span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setSelectedPortDetail(null)}
                className="px-3 py-1.5 rounded bg-[var(--bg-surface)] text-xs font-medium border border-[var(--border-color)]"
              >
                Close
              </button>
              <button
                onClick={() => {
                  onConnect(selectedPortDetail.device, 115200);
                  setSelectedPortDetail(null);
                }}
                className="px-3 py-1.5 rounded bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold"
              >
                Connect Port
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
