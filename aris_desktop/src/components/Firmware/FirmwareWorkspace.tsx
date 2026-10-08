// ============================================================
// ARIS — Firmware Workspace (v3.0.0)
// Read-Only Source Viewer & Local Arduino IDE Project Integration
// Workflow: Arduino IDE (edit/save) -> ARIS (auto-syncs source) -> [ Analyze Firmware ]
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  FileCode2,
  Play,
  RotateCw,
  HardDrive,
  Cpu,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Search,
  ExternalLink,
  FolderOpen,
  Info,
  Terminal,
  FileText,
  ChevronDown,
} from 'lucide-react';
import { BoardProfile, FirmwareRecord, IDESketchInfo } from '../../types';
import { apiCompileFirmware, apiInstrumentAndBuild, InstrumentAndBuildResponse } from '../../services/api';

interface FirmwareWorkspaceProps {
  firmwareList: FirmwareRecord[];
  activeFirmware: FirmwareRecord | null;
  selectedBoard: BoardProfile | null;
  ideSketches: IDESketchInfo[];
  activeIDESketch: IDESketchInfo | null;
  onSyncIDESketch: (path?: string) => Promise<boolean>;
  onRefreshIDESketches: () => Promise<void>;
  onSaveIDESketch?: (path: string, content: string) => Promise<boolean>;
  onSelectFirmware: (fw: FirmwareRecord) => void;
  onNavigate?: (tab: string) => void;
  connectedPort?: string;
  hardwareConnected?: boolean;
}

export const FirmwareWorkspace: React.FC<FirmwareWorkspaceProps> = ({
  firmwareList = [],
  activeFirmware,
  selectedBoard,
  ideSketches = [],
  activeIDESketch,
  onSyncIDESketch,
  onRefreshIDESketches,
  onSelectFirmware,
  onNavigate,
  connectedPort,
  hardwareConnected = false,
}) => {
  const [selectedFileTab, setSelectedFileTab] = useState<string>('main.ino');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAdvancedBuild, setShowAdvancedBuild] = useState(false);
  const [building, setBuilding] = useState(false);
  const [buildOutput, setBuildOutput] = useState<string | null>(null);

  const currentSourceCode = activeIDESketch?.source_code || activeFirmware?.source_code || '';
  const currentSketchName = activeIDESketch?.name || activeFirmware?.name || null;
  const currentPath = activeIDESketch?.path || (activeFirmware?.name ? `local://${activeFirmware.name}` : null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await onRefreshIDESketches();
      if (activeIDESketch?.path) {
        await onSyncIDESketch(activeIDESketch.path);
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleSelectSketch = async (sketch: IDESketchInfo) => {
    setIsRefreshing(true);
    try {
      await onSyncIDESketch(sketch.path);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCompileVerification = async () => {
    if (!currentSourceCode) return;
    setBuilding(true);
    setBuildOutput('Compiling sketch with arduino-cli...');
    try {
      const res = await apiCompileFirmware(currentSourceCode, selectedBoard?.board_id || 'arduino_uno');
      if (res.status === 'BUILD_SUCCESS') {
        setBuildOutput(
          `Build Succeeded!\nToolchain: ${res.toolchain}\nBinary Size: ${res.binary_size_bytes} bytes (${res.flash_usage_pct.toFixed(1)}% Flash)\nSRAM: ${res.sram_usage_bytes} bytes (${res.sram_usage_pct.toFixed(1)}% SRAM)`
        );
      } else {
        setBuildOutput(`Build Failed:\n${(res as any).error || res.compiler_output || 'Compilation error'}`);
      }
    } catch (e: any) {
      setBuildOutput(`Build execution error: ${e.message}`);
    } finally {
      setBuilding(false);
    }
  };

  const [isInstrumenting, setIsInstrumenting] = useState(false);
  const [instrumentationResult, setInstrumentationResult] = useState<InstrumentAndBuildResponse | null>(null);
  const [instrumentationError, setInstrumentationError] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  const handleInstrumentAndRun = async () => {
    if (!currentSourceCode) return;
    setIsInstrumenting(true);
    setInstrumentationError(null);
    try {
      const res = await apiInstrumentAndBuild(
        currentSourceCode,
        activeIDESketch?.path,
        selectedBoard?.board_id || 'arduino_uno',
        connectedPort,
        false
      );
      setInstrumentationResult(res);
    } catch (e: any) {
      setInstrumentationError(e.message || 'Transparent instrumentation failed');
    } finally {
      setIsInstrumenting(false);
    }
  };

  // Split source into numbered lines for professional read-only viewing
  const lines = currentSourceCode ? currentSourceCode.split('\n') : [];

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-heading font-extrabold text-[var(--text-primary)]">
              Firmware
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold border border-[var(--accent-cyan)]/30">
              ARDUINO IDE SOURCE
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 font-mono">
            {currentSketchName ? `${currentSketchName} · ` : ''}
            Target: {selectedBoard ? `${selectedBoard.display_name} (${selectedBoard.fqbn || selectedBoard.architecture || '—'})` : '—'}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all shadow-sm"
          >
            <RotateCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Sync with IDE</span>
          </button>

          {currentSourceCode && (
            <button
              onClick={handleInstrumentAndRun}
              disabled={isInstrumenting}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[var(--accent-green)] hover:opacity-90 text-black text-xs font-mono font-bold shadow-sm transition-all"
            >
              <Play size={13} className={isInstrumenting ? 'animate-spin' : ''} />
              <span>{isInstrumenting ? 'Instrumenting & Building...' : 'Instrument & Run'}</span>
            </button>
          )}

          {currentSourceCode && (
            <button
              onClick={() => onNavigate?.('analysis')}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-mono font-bold shadow-sm transition-all"
            >
              <Search size={13} />
              <span>Analyze Firmware</span>
            </button>
          )}
        </div>
      </div>

      {/* 2. Educational / Engineering Fidelity Notice */}
      <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] flex items-start gap-3 text-xs font-mono text-[var(--text-muted)] leading-relaxed">
        <Info size={16} className="text-[var(--accent-cyan)] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-[var(--text-primary)]">Local Project Source Integration: </span>
          Arduino IDE uploads compiled machine code binaries to the microcontroller. ARIS reads your original C/C++ sketch source directly from your local filesystem, preserving comments, macros, and file structure without guessing from compiled binaries.
        </div>
      </div>

      {/* 2b. Transparent Instrumentation Feedback Card */}
      {instrumentationError && (
        <div className="p-3.5 rounded-xl bg-red-950/30 border border-red-500/30 flex items-start gap-3 text-xs font-mono text-red-300">
          <AlertCircle size={16} className="text-red-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Instrumentation Failed: </span>
            {instrumentationError}
          </div>
        </div>
      )}

      {instrumentationResult && (
        <div className="aris-card p-4 space-y-3 bg-[var(--bg-surface)]/80 border border-[var(--accent-green)]/40 text-xs font-mono">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[var(--border-color)] pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-[var(--accent-green)]" />
              <span className="font-bold text-[var(--text-primary)]">
                Transparent Shadow Build Ready
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-bold">
                ORIGINAL SKETCH UNTOUCHED
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowDiff(!showDiff)}
                className="px-2.5 py-1 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--accent-cyan)] hover:text-white"
              >
                {showDiff ? 'Hide Diff' : 'View Injected Diff'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
            <div className="p-2.5 rounded bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase">Toolchain & Build</div>
              <div className="text-[var(--text-primary)] font-bold">arduino-cli ({instrumentationResult.build_result.toolchain})</div>
              <div className="text-[10px] text-[var(--text-muted)]">
                Flash: {instrumentationResult.build_result.binary_size_bytes} B ({instrumentationResult.build_result.flash_usage_pct}%) · SRAM: {instrumentationResult.build_result.sram_usage_bytes} B
              </div>
            </div>

            <div className="p-2.5 rounded bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase">Original Static Findings</div>
              <div className="text-[var(--text-primary)] font-bold">
                {instrumentationResult.static_analysis.findings_count} Finding(s) Detected
              </div>
              <div className="text-[10px] text-amber-400 truncate">
                {instrumentationResult.static_analysis.findings[0]?.rule_id || 'ARIS-001'}: {instrumentationResult.static_analysis.findings[0]?.title || 'None'}
              </div>
            </div>

            <div className="p-2.5 rounded bg-[var(--bg-card)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase">Hardware Target</div>
              <div className="text-[var(--text-primary)] font-bold">{instrumentationResult.board_id} ({instrumentationResult.build_result.mcu})</div>
              <div className="text-[10px] text-emerald-400">
                Deployment Ready (Verification Phase Complete)
              </div>
            </div>
          </div>

          {showDiff && instrumentationResult.diff && (
            <div className="pt-2">
              <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase">Generated Diff (Shadow Build vs Original):</span>
              <pre className="mt-1 p-3 rounded bg-[#050810] border border-[var(--border-color)] text-[11px] text-emerald-300 overflow-x-auto whitespace-pre font-mono leading-tight max-h-60">
                {instrumentationResult.diff}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* 3. Empty State (When no sketch is loaded) */}
      {!currentSourceCode ? (
        <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-4">
          <FileCode2 size={40} className="text-[var(--text-muted)] opacity-60" />
          <div className="space-y-1">
            <h3 className="font-heading font-bold text-sm text-[var(--text-primary)]">
              No Arduino Sketch Loaded
            </h3>
            <p className="text-xs font-mono text-[var(--text-muted)] max-w-md">
              Work normally in the Arduino IDE. When you open or save your sketch, ARIS will automatically detect it. You can also select any detected local sketch below.
            </p>
          </div>

          {ideSketches.length > 0 && (
            <div className="w-full max-w-lg text-left pt-4 space-y-2">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                Detected Arduino IDE Projects ({ideSketches.length})
              </span>
              <div className="space-y-1.5 max-h-48 overflow-y-auto">
                {ideSketches.map((sk, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSelectSketch(sk)}
                    className="p-2.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--border-color)] border border-[var(--border-color)] flex items-center justify-between cursor-pointer transition-colors"
                  >
                    <div className="min-w-0 pr-2">
                      <div className="text-xs font-mono font-bold text-[var(--text-primary)] truncate">
                        {sk.name}
                      </div>
                      <div className="text-[10px] font-mono text-[var(--text-muted)] truncate">
                        {sk.path}
                      </div>
                    </div>
                    <button className="px-2.5 py-1 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] text-[10px] font-mono font-bold shrink-0">
                      Open
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* 4. Active Read-Only Source Code Viewer */
        <div className="space-y-4">
          {/* Metadata Bar */}
          <div className="aris-card p-3 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs font-mono">
            <div className="flex items-center gap-2 min-w-0">
              <FileCode2 size={15} className="text-[var(--accent-green)] shrink-0" />
              <span className="font-bold text-[var(--text-primary)] truncate">
                {currentSketchName}
              </span>
              <span className="text-[var(--text-muted)] hidden md:inline truncate">
                ({currentPath})
              </span>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <span className="text-[11px] text-[var(--text-muted)]">
                {lines.length} lines · Read-Only
              </span>
              {ideSketches.length > 1 && (
                <select
                  value={currentPath || ''}
                  onChange={(e) => {
                    const matched = ideSketches.find((s) => s.path === e.target.value);
                    if (matched) handleSelectSketch(matched);
                  }}
                  className="px-2 py-1 rounded bg-[var(--bg-surface)] border border-[var(--border-color)] text-xs font-mono text-[var(--text-primary)]"
                >
                  {ideSketches.map((s, idx) => (
                    <option key={idx} value={s.path}>
                      {s.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {/* Clean Read-Only Code Panel with Line Numbers */}
          <div className="aris-card overflow-hidden border border-[var(--border-color)] bg-[#0A0D14]">
            {/* Header Tabs */}
            <div className="px-3 py-2 bg-[var(--bg-surface)] border-b border-[var(--border-color)] flex items-center justify-between text-xs font-mono">
              <div className="flex items-center gap-1.5">
                <span className="px-2 py-0.5 rounded bg-[var(--bg-card)] text-[var(--accent-cyan)] font-semibold border border-[var(--border-color)]">
                  {currentSketchName || 'sketch.ino'}
                </span>
              </div>
              <span className="text-[10px] text-[var(--text-muted)]">
                Auto-syncs on save in Arduino IDE
              </span>
            </div>

            {/* Code Content */}
            <div className="p-4 font-mono text-xs overflow-x-auto max-h-[500px] leading-relaxed select-text">
              <table className="w-full text-left border-collapse">
                <tbody>
                  {lines.map((lineText, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02]">
                      <td className="w-10 pr-4 text-right text-[var(--text-muted)]/50 select-none text-[11px] align-top">
                        {idx + 1}
                      </td>
                      <td className="text-[var(--text-primary)] whitespace-pre font-code">
                        {lineText || ' '}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Bottom Action Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
            <button
              onClick={() => setShowAdvancedBuild(!showAdvancedBuild)}
              className="text-xs font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1"
            >
              <span>{showAdvancedBuild ? 'Hide Toolchain Verification' : 'Advanced: Test Compile with arduino-cli'}</span>
              <ChevronDown size={13} className={showAdvancedBuild ? 'rotate-180' : ''} />
            </button>

            <button
              onClick={() => onNavigate?.('analysis')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-mono font-bold shadow-sm transition-all"
            >
              <Search size={14} />
              <span>Run ARIS Analysis on this Sketch</span>
            </button>
          </div>

          {/* Collapsible Advanced Toolchain Verification */}
          {showAdvancedBuild && (
            <div className="aris-card p-4 space-y-3 bg-[var(--bg-surface)]/50 border border-[var(--border-color)] text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[var(--text-primary)]">
                  Local arduino-cli Toolchain Test
                </span>
                <button
                  onClick={handleCompileVerification}
                  disabled={building}
                  className="px-3 py-1 rounded bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-[var(--text-primary)] font-semibold"
                >
                  {building ? 'Compiling...' : 'Run Test Compile'}
                </button>
              </div>

              {buildOutput && (
                <pre className="p-3 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)] whitespace-pre-wrap text-[11px] overflow-x-auto">
                  {buildOutput}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
