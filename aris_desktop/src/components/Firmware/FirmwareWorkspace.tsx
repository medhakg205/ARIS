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
  AlertTriangle,
  Clock,
  Layers,
  Search,
  ExternalLink,
  FolderOpen,
  Info,
  Terminal,
  FileText,
  ChevronDown,
  Activity,
  GitBranch,
} from 'lucide-react';
import { BoardProfile, FirmwareRecord, IDESketchInfo } from '../../types';
import { apiCompileFirmware, apiFlashFirmware, apiInstrumentAndBuild, apiReleaseSerial, apiHealth, apiTriggerHandshake, InstrumentAndBuildResponse } from '../../services/api';
import { pauseHardwareAutoDetect, resumeHardwareAutoDetect } from '../../hooks/useAris';

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
  onRunStarted?: (run: any) => void;
  onFindingsUpdated?: (findings: any[]) => void;
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
  onRunStarted,
  onFindingsUpdated,
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
  const [instrumentStage, setInstrumentStage] = useState<string | null>(null);
  const [instrumentationResult, setInstrumentationResult] = useState<InstrumentAndBuildResponse | null>(null);
  const [instrumentationError, setInstrumentationError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<any>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [instrumentationProfile, setInstrumentationProfile] = useState<'BALANCED' | 'LEAN'>('BALANCED');
  const [uploadFailure, setUploadFailure] = useState<any>(null);
  const [showUploadDetails, setShowUploadDetails] = useState(false);

  const handleRetryHandshake = async () => {
    if (isInstrumenting) return;
    const targetPort = connectedPort || (hardwareConnected ? 'COM4' : undefined);
    const activeRunId = instrumentationResult?.run_id;
    setIsInstrumenting(true);
    setInstrumentStage('Probing target for runtime handshake ($ARIS_HELLO#)...');
    try {
      const res: any = await apiTriggerHandshake(4.0, targetPort, activeRunId);
      if (res && res.handshake_success) {
        setInstrumentStage('Runtime handshake confirmed — telemetry active');
        setUploadFailure(null);
        if (instrumentationResult?.run && onRunStarted) {
          onRunStarted(instrumentationResult.run);
        }
        setTimeout(() => setInstrumentStage(null), 3000);
      } else {
        setInstrumentStage(null);
        setUploadFailure((prev: any) => ({
          ...prev,
          error_summary: 'Target responded to serial connection, but ARIS runtime handshake is not yet confirmed. Retrying probe...'
        }));
      }
    } catch (e: any) {
      setInstrumentStage(null);
    } finally {
      setIsInstrumenting(false);
    }
  };

  const handleRetryUpload = async () => {
    const binaryPath = instrumentationResult?.build_result?.binary_path;
    const targetPort = connectedPort || (hardwareConnected ? 'COM4' : undefined);
    if (isInstrumenting) return;
    if (!targetPort) {
      setUploadFailure({
        title: 'Upload aborted — No hardware port detected',
        error_summary: 'No serial or COM port was detected on the host. Connect your Arduino board via USB to retry upload.',
        failure_category: 'DEVICE_DISCONNECTED',
        guidance: [
          'Connect your Arduino board to a USB port.',
          'Verify the USB cable supports data transfer and not just power.',
          'Check Windows Device Manager to confirm the COM port assignment.'
        ],
        command: 'arduino-cli upload',
        exit_code: 1,
        raw_output: 'No target serial port available.',
        firmware_uploaded: false
      });
      return;
    }
    if (!binaryPath) {
      await handleInstrumentAndRun();
      return;
    }

    setIsInstrumenting(true);
    setUploadFailure(null);
    setInstrumentStage(`Retrying upload to ${targetPort}...`);

    try {
      pauseHardwareAutoDetect(60000);
      const res = await apiFlashFirmware(
        selectedBoard?.board_id || 'arduino_uno',
        targetPort,
        undefined,
        binaryPath
      );
      if (res.status === 'FLASH_SUCCESS') {
        setInstrumentStage('Upload confirmed — telemetry live');
        setUploadFailure(null);
        setTimeout(() => setInstrumentStage(null), 4000);
      }
    } catch (e: any) {
      setUploadFailure(e.details || {
        title: `Upload failed — ${selectedBoard?.display_name || 'Arduino Uno'} on ${targetPort}`,
        error_summary: e.message,
        failure_category: 'PROGRAMMER_ERROR',
        command: `arduino-cli upload -p ${targetPort}`,
        raw_output: e.message,
        firmware_uploaded: false
      });
      setInstrumentStage(null);
    } finally {
      resumeHardwareAutoDetect();
      setIsInstrumenting(false);
    }
  };

  const handleInstrumentAndRun = async (overrideProfile?: 'BALANCED' | 'LEAN') => {
    if (!currentSourceCode || isInstrumenting) return;
    const profileToUse = overrideProfile || instrumentationProfile;
    if (overrideProfile) {
      setInstrumentationProfile(overrideProfile);
    }
    setIsInstrumenting(true);
    setInstrumentationError(null);
    setErrorCode(null);
    setErrorDetails(null);
    setInstrumentationResult(null);
    setUploadFailure(null);

    const targetPort = connectedPort || (hardwareConnected ? 'COM4' : undefined);

    try {
      pauseHardwareAutoDetect(90000);

      if (targetPort && targetPort !== 'SIMULATED') {
        setInstrumentStage(`Preparing ${targetPort} for physical deployment...`);
        try {
          await apiReleaseSerial(targetPort, 500);
        } catch {
          // Fallback if already released
        }
      }

      setInstrumentStage(`Compiling & deploying ${profileToUse} instrumented firmware to ${targetPort || 'target'}...`);
      const res = await apiInstrumentAndBuild(
        currentSourceCode,
        activeIDESketch?.path,
        selectedBoard?.board_id || 'arduino_uno',
        targetPort,
        true,
        profileToUse
      );

      setInstrumentationResult(res);

      if (res.upload_result?.status === 'FLASH_FAILED') {
        setUploadFailure(res.upload_result);
        setInstrumentStage(null);
      } else {
        setUploadFailure(null);
        if (res.static_analysis?.findings && onFindingsUpdated) {
          onFindingsUpdated(res.static_analysis.findings);
        }
        if (res.run && onRunStarted) {
          onRunStarted(res.run);
        }
        setInstrumentStage('Handshake confirmed — telemetry live');
        setTimeout(() => {
          setInstrumentStage(null);
        }, 4000);
      }
    } catch (e: any) {
      if (e.error_code === 'ARIS_FLASH_FAILED' || e.details?.failure_category) {
        setUploadFailure({
          title: e.details?.title || `Upload failed — ${selectedBoard?.display_name || 'Arduino Uno'} on ${targetPort || 'COM4'}`,
          error_summary: e.details?.error_summary || e.message,
          failure_category: e.details?.failure_category || 'PROGRAMMER_ERROR',
          guidance: e.details?.guidance,
          command: e.details?.command,
          exit_code: e.details?.exit_code,
          raw_output: e.details?.raw_output || e.message,
          firmware_uploaded: e.details?.firmware_uploaded ?? false
        });
        setInstrumentationError(null);
      } else {
        setInstrumentationError(e.message || 'Transparent instrumentation failed');
        setErrorCode(e.error_code || null);
        setErrorDetails(e.details || null);
      }
      setInstrumentStage(null);
    } finally {
      resumeHardwareAutoDetect();
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
          {/* Profile Switcher (Tesla/Google Home minimal pill) */}
          <div className="flex items-center rounded-full bg-[var(--bg-surface)] border border-[var(--border-color)] p-0.5 text-xs font-sans">
            <button
              onClick={() => setInstrumentationProfile('BALANCED')}
              className={`px-3 py-1 rounded-full font-semibold transition-all ${
                instrumentationProfile === 'BALANCED'
                  ? 'bg-[var(--accent-cyan)] text-white shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
              title="BALANCED Profile: Loop time, CPU load, SRAM, jitter, and interrupts"
            >
              Balanced
            </button>
            <button
              onClick={() => setInstrumentationProfile('LEAN')}
              className={`px-3 py-1 rounded-full font-semibold transition-all ${
                instrumentationProfile === 'LEAN'
                  ? 'bg-[var(--accent-amber)] text-black shadow-xs font-bold'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
              title="LEAN Profile: Minimal footprint; omits peripheral probes to conserve Flash & SRAM"
            >
              Lean (AVR)
            </button>
          </div>

          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="aris-btn-secondary"
          >
            <RotateCw size={13} className={isRefreshing ? 'animate-spin' : ''} />
            <span>Sync with IDE</span>
          </button>

          {currentSourceCode && (
            <button
              onClick={() => handleInstrumentAndRun()}
              disabled={isInstrumenting}
              className={`aris-btn-primary ${
                isInstrumenting ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              <Play size={13} className={isInstrumenting ? 'animate-spin' : ''} />
              <span>{isInstrumenting ? (instrumentStage || 'Deploying...') : 'Deploy & Run'}</span>
            </button>
          )}

          {currentSourceCode && (
            <button
              onClick={() => onNavigate?.('analysis')}
              className="aris-btn-secondary"
            >
              <Search size={13} />
              <span>Analyze Code</span>
            </button>
          )}
        </div>
      </div>

      {/* Deployment Progression Banner */}
      {(isInstrumenting || instrumentStage) && (
        <div className="p-3.5 rounded-xl bg-[var(--accent-cyan-bg)] border border-[var(--accent-cyan)]/30 flex items-center justify-between gap-3 text-xs font-sans text-[var(--accent-cyan)]">
          <div className="flex items-center gap-2.5">
            <RotateCw size={14} className={isInstrumenting ? 'animate-spin text-[var(--accent-cyan)]' : 'text-[var(--accent-green)]'} />
            <span className="font-semibold">{instrumentStage}</span>
          </div>
          <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider font-bold">
            {isInstrumenting ? 'In Progress' : 'Confirmed'}
          </span>
        </div>
      )}

      {/* 2. Educational / Engineering Fidelity Notice */}
      <div className="p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] flex items-start gap-3 text-xs font-sans text-[var(--text-muted)] leading-relaxed shadow-xs">
        <Info size={16} className="text-[var(--accent-cyan)] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-[var(--text-primary)]">Local Project Source Integration: </span>
          Arduino IDE uploads compiled machine code binaries to the microcontroller. ARIS reads your original C/C++ sketch source directly from your local filesystem, preserving comments, macros, and file structure without guessing from compiled binaries.
        </div>
      </div>

      {/* 2a. Active Firmware Lineage & Version Card */}
      {activeFirmware && (
        <div className="p-3.5 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-sans shadow-xs">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]">
              <GitBranch size={15} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-[var(--text-primary)]">Firmware Lineage:</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                  activeFirmware.status === 'ACTIVE'
                    ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30'
                    : 'bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)]'
                }`}>
                  {activeFirmware.status || 'ACTIVE'}
                </span>
                {activeFirmware.applied && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30">
                    DISK APPLIED
                  </span>
                )}
              </div>
              <p className="text-[11px] font-mono text-[var(--text-muted)] mt-0.5">
                {activeFirmware.parent_firmware_id ? `Parent: ${activeFirmware.parent_firmware_id}` : 'Root / Baseline Version'}
                {activeFirmware.candidate_id ? ` · Candidate: ${activeFirmware.candidate_id}` : ''}
                {activeFirmware.source_hash ? ` · SHA-256: ${activeFirmware.source_hash.substring(0, 10)}...` : ''}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dedicated Upload Failure Card */}
      {uploadFailure && (
        <div className="p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--accent-amber)]/40 space-y-3 text-xs font-sans text-[var(--text-primary)] shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="text-[var(--accent-amber)] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-bold text-[var(--accent-amber)] text-sm">
                    {uploadFailure.title || `Upload failed — ${selectedBoard?.display_name || 'Arduino Uno'} on ${connectedPort || 'COM4'}`}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30">
                    {uploadFailure.failure_category ? uploadFailure.failure_category.replace(/_/g, ' ') : 'PROGRAMMER ERROR'}
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30">
                    BUILD SUCCEEDED
                  </span>
                  {uploadFailure.firmware_uploaded && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30">
                      FLASH UPLOADED
                    </span>
                  )}
                  {uploadFailure.failure_category === 'HANDSHAKE_TIMEOUT' && (
                    <>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30">
                        HANDSHAKE PENDING
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)]">
                        TELEMETRY INACTIVE
                      </span>
                    </>
                  )}
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {uploadFailure.error_summary || uploadFailure.message}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {uploadFailure.failure_category === 'HANDSHAKE_TIMEOUT' && (
                <button
                  onClick={() => handleRetryHandshake()}
                  disabled={isInstrumenting}
                  className="px-3 py-1.5 rounded-lg border border-[var(--accent-cyan)]/40 bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-mono text-xs font-bold hover:bg-[var(--accent-cyan)]/20 transition-all flex items-center gap-1.5"
                >
                  <Activity size={12} className={isInstrumenting ? 'animate-spin' : ''} />
                  <span>Retry Handshake</span>
                </button>
              )}
              <button
                onClick={() => handleRetryUpload()}
                disabled={isInstrumenting}
                className="aris-btn-primary shrink-0 text-xs py-1.5 px-3 flex items-center gap-1.5"
              >
                <RotateCw size={12} className={isInstrumenting ? 'animate-spin' : ''} />
                <span>Retry Upload</span>
              </button>
            </div>
          </div>

          {/* Actionable guidance checklist */}
          {uploadFailure.guidance && uploadFailure.guidance.length > 0 && (
            <div className="pt-2 border-t border-[var(--border-color)]">
              <div className="text-[11px] font-bold text-[var(--text-primary)] mb-1 flex items-center gap-1.5">
                <span>Actionable Troubleshooting Steps:</span>
              </div>
              <ul className="space-y-1 text-[11px] text-[var(--text-secondary)]">
                {uploadFailure.guidance.map((step: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-[var(--accent-amber)] font-bold shrink-0">{idx + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Expandable Technical Details Drawer */}
          <div className="pt-2 border-t border-[var(--border-color)]">
            <button
              onClick={() => setShowUploadDetails(!showUploadDetails)}
              className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--accent-cyan)] hover:text-white transition-colors"
            >
              <Terminal size={12} />
              <span>{showUploadDetails ? 'Hide Programmer Details & Output' : 'View Programmer Details & Output'}</span>
              <ChevronDown size={12} className={`transform transition-transform ${showUploadDetails ? 'rotate-180' : ''}`} />
            </button>

            {showUploadDetails && (
              <div className="mt-2 p-3 rounded-lg bg-[#07090E] border border-[var(--border-color)] space-y-2 font-mono text-[11px] text-[var(--text-secondary)]">
                {uploadFailure.command && (
                  <div>
                    <span className="text-[var(--text-muted)] text-[10px] uppercase font-bold block mb-0.5">Executed Command:</span>
                    <div className="p-2 rounded bg-black/40 text-[var(--text-primary)] break-all select-all text-[10px]">
                      {uploadFailure.command}
                    </div>
                  </div>
                )}
                {uploadFailure.exit_code !== undefined && (
                  <div className="text-[10px] text-[var(--text-muted)]">
                    Exit Code: <span className="font-bold text-[var(--accent-red)]">{uploadFailure.exit_code}</span>
                  </div>
                )}
                {uploadFailure.raw_output && (
                  <div>
                    <span className="text-[var(--text-muted)] text-[10px] uppercase font-bold block mb-0.5">Programmer Console Output:</span>
                    <pre className="p-2 rounded bg-black/40 text-[var(--accent-red)]/90 max-h-48 overflow-y-auto whitespace-pre-wrap leading-tight text-[10px]">
                      {uploadFailure.raw_output}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Safety notice */}
          <div className="flex items-center gap-2 pt-1 text-[11px] text-[var(--text-muted)] font-mono">
            <span className="px-1.5 py-0.5 rounded-full bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-color)] font-bold">
              SAFETY CONFIRMED
            </span>
            <span>Original sketch untouched · {uploadFailure.firmware_uploaded === false ? 'No firmware written to board' : 'Upload outcome unverified'}</span>
          </div>
        </div>
      )}

      {/* 2b. Transparent Instrumentation Feedback Card */}
      {instrumentationError && (
        <div className="p-4 rounded-xl bg-[var(--accent-red-bg)] border border-[var(--accent-red)]/30 space-y-3 text-xs font-sans text-[var(--text-primary)] shadow-sm">
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-[var(--accent-red)] shrink-0 mt-0.5" />
            <div className="space-y-1 flex-1">
              <div className="font-bold text-[var(--accent-red)] text-sm">
                {errorCode === 'ARIS_BACKEND_UNAVAILABLE'
                  ? 'ARIS Backend Service Unavailable'
                  : errorCode === 'ARIS_OPERATION_TIMEOUT'
                  ? 'Firmware Build / Operation Timeout'
                  : errorDetails?.overflow_type === 'FLASH'
                  ? 'Microcontroller Flash Memory Overflow'
                  : errorDetails?.overflow_type === 'SRAM'
                  ? 'Microcontroller Static SRAM Overflow'
                  : errorCode === 'BUILD_FAILED'
                  ? 'Firmware Compilation Failed'
                  : errorCode === 'ARIS_FLASH_FAILED'
                  ? 'Microcontroller Upload / Flash Failed'
                  : 'Instrumentation & Deployment Error'}
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                {instrumentationError}
              </p>
              {errorCode === 'ARIS_BACKEND_UNAVAILABLE' && (
                <div className="pt-2 flex items-center gap-2">
                  <button
                    onClick={async () => {
                      try {
                        await apiHealth();
                        setInstrumentationError(null);
                        setErrorCode(null);
                      } catch {
                        // Still unavailable
                      }
                    }}
                    className="aris-btn-secondary text-[11px] py-1 px-2.5"
                  >
                    Retry Connection
                  </button>
                </div>
              )}
            </div>
          </div>

          {errorDetails && (errorDetails.original_flash_bytes || errorDetails.instrumented_flash_bytes) && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-[var(--border-color)] text-[11px] font-mono">
              <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                <div className="text-[var(--text-muted)] text-[10px]">Original Firmware</div>
                <div className="font-bold text-[var(--text-primary)] mt-0.5">
                  {errorDetails.original_flash_bytes ? `${errorDetails.original_flash_bytes.toLocaleString()} B` : 'Unknown'}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                <div className="text-[var(--text-muted)] text-[10px]">Instrumented Build</div>
                <div className="font-bold text-[var(--accent-red)] mt-0.5">
                  {errorDetails.instrumented_flash_bytes ? `${errorDetails.instrumented_flash_bytes.toLocaleString()} B` : 'Unknown'}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                <div className="text-[var(--text-muted)] text-[10px]">Board Limit</div>
                <div className="font-bold text-[var(--text-primary)] mt-0.5">
                  {errorDetails.max_flash_bytes ? `${errorDetails.max_flash_bytes.toLocaleString()} B` : 'Unknown'}
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                <div className="text-[var(--text-muted)] text-[10px]">Overhead / Delta</div>
                <div className="font-bold text-[var(--accent-amber)] mt-0.5">
                  {errorDetails.instrumentation_overhead_bytes ? `+${errorDetails.instrumentation_overhead_bytes.toLocaleString()} B` : 'Unknown'}
                </div>
              </div>
            </div>
          )}

          {errorDetails && (errorDetails.original_sram_bytes || errorDetails.instrumented_sram_bytes) && (
            <div className="space-y-1.5 pt-2 border-t border-[var(--border-color)]">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px] font-mono">
                <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                  <div className="text-[var(--text-muted)] text-[10px]">Static SRAM (Original)</div>
                  <div className="font-bold text-[var(--text-primary)] mt-0.5">
                    {errorDetails.original_sram_bytes ? `${errorDetails.original_sram_bytes.toLocaleString()} B` : 'Unknown'}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                  <div className="text-[var(--text-muted)] text-[10px]">Static SRAM (Instrumented)</div>
                  <div className="font-bold text-[var(--accent-red)] mt-0.5">
                    {errorDetails.instrumented_sram_bytes ? `${errorDetails.instrumented_sram_bytes.toLocaleString()} B` : 'Unknown'}
                  </div>
                </div>
                <div className="p-2.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)]">
                  <div className="text-[var(--text-muted)] text-[10px]">Static SRAM Limit</div>
                  <div className="font-bold text-[var(--text-primary)] mt-0.5">
                    {errorDetails.max_sram_bytes ? `${errorDetails.max_sram_bytes.toLocaleString()} B` : 'Unknown'}
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-[var(--text-muted)] leading-normal font-sans">
                Static SRAM accounting includes only global and static variables (.data + .bss). It does NOT include dynamic heap allocations (such as OLED display buffers) or runtime stack frames. Stack safety cannot be guaranteed by static analysis alone.
              </p>
            </div>
          )}

          {errorDetails?.suggested_actions && errorDetails.suggested_actions.length > 0 && (
            <div className="pt-2 border-t border-[var(--border-color)]">
              <div className="text-[var(--text-primary)] font-bold mb-1">Recommended Next Actions:</div>
              <ul className="list-disc list-inside space-y-1 text-[var(--text-secondary)]">
                {errorDetails.suggested_actions.map((act: string, idx: number) => (
                  <li key={idx}>{act}</li>
                ))}
              </ul>
            </div>
          )}

          {errorDetails?.lean_profile_recommended && instrumentationProfile !== 'LEAN' && (
            <div className="pt-2 border-t border-[var(--border-color)] flex items-center gap-2">
              <button
                onClick={() => handleInstrumentAndRun('LEAN')}
                className="px-4 py-2 rounded-lg bg-[var(--accent-amber)] hover:opacity-90 text-black font-bold text-xs flex items-center gap-1.5 transition-all shadow-sm"
              >
                <RotateCw size={13} />
                <span>Switch to LEAN Profile & Retry Build</span>
              </button>
            </div>
          )}

          <div className="flex items-center gap-2 pt-1 text-[11px] text-[var(--text-muted)] font-mono">
            <span className="px-1.5 py-0.5 rounded-full bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-color)] font-bold">
              SAFEGUARD ACTIVE
            </span>
            <span>Original sketch on disk was NOT modified · No firmware uploaded</span>
          </div>
        </div>
      )}

      {instrumentationResult && (
        <div className="aris-card p-4 space-y-3 bg-[var(--bg-surface)]/80 border border-[var(--accent-green)]/40 text-xs font-mono">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-[var(--border-color)] pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} className="text-[var(--accent-green)]" />
              <span className="font-bold text-[var(--text-primary)]">
                {instrumentationResult.upload_result?.status === 'FLASH_SUCCESS' ? 'Transparent Physical Deployment Active' : 'Transparent Shadow Build Ready'}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-bold">
                ORIGINAL SKETCH UNTOUCHED
              </span>
            </div>
            <div className="flex items-center gap-2">
              {instrumentationResult.telemetry_active && (
                <button
                  onClick={() => onNavigate?.('telemetry')}
                  className="px-2.5 py-1 rounded bg-[var(--accent-cyan)] hover:opacity-90 text-white font-bold text-[10px] flex items-center gap-1 shadow-sm transition-all"
                >
                  <Activity size={12} />
                  <span>Live Telemetry →</span>
                </button>
              )}
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
              <div className="text-[10px] text-[var(--text-muted)] font-semibold uppercase">
                {instrumentationResult.upload_result ? 'Physical Deployment' : 'Hardware Target'}
              </div>
              <div className="text-[var(--text-primary)] font-bold">
                {instrumentationResult.upload_result?.status === 'FLASH_SUCCESS' ? (
                  <span className="text-emerald-400">
                    {instrumentationResult.upload_result.port || 'COM4'} Upload Complete
                  </span>
                ) : (
                  `${instrumentationResult.board_id} (${instrumentationResult.build_result.mcu})`
                )}
              </div>
              <div className="text-[10px]">
                {instrumentationResult.telemetry_active ? (
                  <span className="text-emerald-400 font-semibold">
                    Handshake Confirmed · Telemetry Live
                  </span>
                ) : (
                  <span className="text-emerald-400">
                    Deployment Ready (Verification Phase Complete)
                  </span>
                )}
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
