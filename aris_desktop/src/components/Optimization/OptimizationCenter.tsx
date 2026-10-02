// ============================================================
// ARIS — Optimization Intelligence & Validation Experience (v3.0.0)
// Complete Lifecycle: DEVICE -> FIRMWARE -> BASELINE -> ANALYSIS ->
// OPTIMIZATION -> PREDICTION -> BUILD -> FLASH -> REAL TELEMETRY ->
// VALIDATION -> ACCEPT / ROLLBACK
// ============================================================

import React, { useState } from 'react';
import {
  Zap,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  Layers,
  Cpu,
  Clock,
  Save,
  Check,
  X,
  FileCode2,
  Activity,
  GitBranch,
  ShieldCheck,
  Flame,
  Radio,
  BarChart3,
  Sliders,
  History,
  Sparkles,
  RefreshCw,
  Search,
  Usb,
} from 'lucide-react';
import {
  OptimizationCandidate,
  IDESketchInfo,
  BoardProfile,
  RunRecord,
  FirmwareRecord,
  TelemetrySample,
  ExperimentRecord,
  ValidationResult,
} from '../../types';

import { OptimizationPipeline } from './OptimizationPipeline';
import { LiveValidationMonitor } from './LiveValidationMonitor';
import { MultiObjectiveImpactCard } from './MultiObjectiveImpactCard';
import { PredictionVsRealityView } from './PredictionVsRealityView';
import { BeforeAfterTelemetryView } from './BeforeAfterTelemetryView';
import { OptimizationDecisionPanel } from './OptimizationDecisionPanel';
import { ExperimentReplayAndHistory } from './ExperimentReplayAndHistory';

export interface OptimizationCenterProps {
  optimizations: OptimizationCandidate[];
  loading?: boolean;
  activeIDESketch: IDESketchInfo | null;
  onSaveIDESketch: (path: string, sourceCode: string) => Promise<boolean>;
  onApprove: (id: string) => Promise<boolean>;
  onReject: (id: string) => Promise<boolean>;
  onCreateExperiment: (optId: string) => Promise<string | null>;
  onNavigate: (tab: string) => void;

  // Rich lifecycle properties
  selectedBoard?: BoardProfile | null;
  activeRun?: RunRecord | null;
  activeFirmware?: FirmwareRecord | null;
  latestSamples?: Record<string, TelemetrySample>;
  telemetryHistory?: TelemetrySample[];
  experiments?: ExperimentRecord[];
  validations?: Record<string, ValidationResult>;
  isDemo?: boolean;
  hardwareConnected?: boolean;
  onAutoDetectHardware?: () => Promise<any>;
  onStartHardwareRun?: () => Promise<void>;
  onStartDemo?: () => Promise<void>;
  onValidateExperiment?: (expId: string) => Promise<any>;
  onRollbackExperiment?: (expId: string) => Promise<void>;
  onRollbackOptimization?: (optId: string) => Promise<void>;
}

type OptSubTab =
  | 'lifecycle'
  | 'candidates'
  | 'prediction'
  | 'telemetry'
  | 'history';

export const OptimizationCenter: React.FC<OptimizationCenterProps> = ({
  optimizations,
  loading = false,
  activeIDESketch,
  onSaveIDESketch,
  onApprove,
  onReject,
  onCreateExperiment,
  onNavigate,
  selectedBoard = null,
  activeRun = null,
  activeFirmware = null,
  latestSamples = {},
  telemetryHistory = [],
  experiments = [],
  validations = {},
  isDemo = false,
  hardwareConnected = false,
  onAutoDetectHardware,
  onStartHardwareRun,
  onStartDemo,
  onValidateExperiment,
  onRollbackExperiment,
  onRollbackOptimization,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<OptSubTab>('lifecycle');
  const [selectedOptId, setSelectedOptId] = useState<string | null>(() => {
    return optimizations[0]?.optimization_id || null;
  });
  const [selectedExpId, setSelectedExpId] = useState<string | null>(() => {
    return experiments[0]?.experiment_id || null;
  });
  const [isValidating, setIsValidating] = useState(false);
  const [detectingHardware, setDetectingHardware] = useState(false);

  // Active candidate
  const selectedOpt =
    optimizations.find((o) => o.optimization_id === selectedOptId) ||
    optimizations[0] ||
    null;

  // Active experiment
  const activeExp =
    experiments.find((e) => e.experiment_id === selectedExpId) ||
    experiments[0] ||
    null;

  // Active validation
  const activeVal = activeExp ? validations[activeExp.experiment_id] || null : null;

  // Handle run and validate candidate
  const handleValidateCandidate = async (optId: string) => {
    setIsValidating(true);
    try {
      const expId = await onCreateExperiment(optId);
      if (expId) {
        setSelectedExpId(expId);
        if (onValidateExperiment) {
          await onValidateExperiment(expId);
        }
      }
    } finally {
      setIsValidating(false);
    }
  };

  // Handle hardware auto detect
  const handleAutoDetect = async () => {
    if (!onAutoDetectHardware) return;
    setDetectingHardware(true);
    try {
      await onAutoDetectHardware();
    } finally {
      setDetectingHardware(false);
    }
  };

  // Handle Accept
  const handleAcceptOptimization = async (candidateId: string): Promise<boolean> => {
    const success = await onApprove(candidateId);
    return Boolean(success);
  };

  // Handle Rollback
  const handleRollback = async (experimentId: string): Promise<void> => {
    if (onRollbackExperiment) {
      await onRollbackExperiment(experimentId);
    } else if (selectedOpt && onRollbackOptimization) {
      await onRollbackOptimization(selectedOpt.optimization_id);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. HERO SECTION */}
      <div className="aris-card p-6 bg-gradient-to-r from-[var(--bg-card)] via-[var(--bg-surface)] to-[var(--bg-card)] border-l-4 border-l-[var(--accent-cyan)] shadow-md">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-heading font-extrabold tracking-tight text-[var(--text-primary)]">
                Optimization Intelligence
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold border border-[var(--accent-cyan)]/30">
                CLOSED-LOOP VALIDATION
              </span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] font-mono max-w-2xl leading-relaxed">
              Analyze firmware behavior, predict multi-objective impact, validate changes on hardware, and automatically recover from regressions.
            </p>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {onStartHardwareRun && (
              <button
                onClick={onStartHardwareRun}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-mono font-bold shadow-sm transition-all"
              >
                <Play size={13} />
                <span>Start Baseline</span>
              </button>
            )}

            <button
              onClick={() => onNavigate('issues')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--border-color)] text-[var(--text-primary)] text-xs font-mono font-semibold border border-[var(--border-color)] transition-all"
            >
              <Search size={13} className="text-[var(--accent-cyan)]" />
              <span>Analyze Firmware</span>
            </button>

            <button
              onClick={() => setActiveSubTab('history')}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--border-color)] text-[var(--text-primary)] text-xs font-mono font-semibold border border-[var(--border-color)] transition-all"
            >
              <History size={13} className="text-[var(--accent-purple)]" />
              <span>View Experiments ({experiments.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. HARDWARE VALIDATION PENDING BANNER (When hardware is not connected) */}
      {!hardwareConnected && (
        <div className="p-4 rounded-xl bg-[var(--accent-yellow-bg)]/60 border border-[var(--accent-yellow)]/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--accent-yellow-bg)] text-[var(--accent-yellow)] border border-[var(--accent-yellow)]/40">
              <Usb size={18} />
            </div>
            <div>
              <div className="font-bold text-[var(--text-primary)] flex items-center gap-2">
                Hardware Validation Pending
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold">
                  SIMULATION ACTIVE
                </span>
              </div>
              <div className="text-[var(--text-muted)] text-[11px] mt-0.5">
                Connect an Arduino Uno R3 / R4 or target board to perform hardware-in-the-loop closed-loop validation. Virtual simulation mode is currently serving telemetry.
              </div>
            </div>
          </div>

          {onAutoDetectHardware && (
            <button
              onClick={handleAutoDetect}
              disabled={detectingHardware}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--border-color)] text-[var(--text-primary)] text-xs font-semibold border border-[var(--accent-yellow)]/40 shrink-0 transition-all"
            >
              <RefreshCw size={12} className={detectingHardware ? 'animate-spin' : ''} />
              <span>{detectingHardware ? 'Scanning Ports...' : 'Auto Detect Hardware'}</span>
            </button>
          )}
        </div>
      )}

      {/* 3. SUB-NAVIGATION TABS */}
      <div className="flex items-center gap-2 border-b border-[var(--border-color)] pb-2 overflow-x-auto text-xs font-mono">
        <button
          onClick={() => setActiveSubTab('lifecycle')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
            activeSubTab === 'lifecycle'
              ? 'bg-[var(--accent-cyan)] text-white font-bold shadow-sm'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
          }`}
        >
          <Activity size={13} />
          <span>Pipeline & Live Validation</span>
        </button>

        <button
          onClick={() => setActiveSubTab('candidates')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
            activeSubTab === 'candidates'
              ? 'bg-[var(--accent-cyan)] text-white font-bold shadow-sm'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
          }`}
        >
          <Zap size={13} />
          <span>Candidates & Code Diff ({optimizations.length})</span>
        </button>

        <button
          onClick={() => setActiveSubTab('prediction')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
            activeSubTab === 'prediction'
              ? 'bg-[var(--accent-cyan)] text-white font-bold shadow-sm'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
          }`}
        >
          <Sliders size={13} />
          <span>Prediction vs Reality</span>
        </button>

        <button
          onClick={() => setActiveSubTab('telemetry')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
            activeSubTab === 'telemetry'
              ? 'bg-[var(--accent-cyan)] text-white font-bold shadow-sm'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
          }`}
        >
          <BarChart3 size={13} />
          <span>Before / After Telemetry</span>
        </button>

        <button
          onClick={() => setActiveSubTab('history')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all ${
            activeSubTab === 'history'
              ? 'bg-[var(--accent-cyan)] text-white font-bold shadow-sm'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card)]'
          }`}
        >
          <History size={13} />
          <span>Replay & History ({experiments.length})</span>
        </button>
      </div>

      {/* 4. SUB-TAB CONTENT PANELS */}

      {/* TAB 1: PIPELINE & LIVE VALIDATION */}
      {activeSubTab === 'lifecycle' && (
        <div className="space-y-6">
          {/* 11-Stage Interactive Pipeline */}
          <OptimizationPipeline
            selectedBoard={selectedBoard}
            activeFirmware={activeFirmware}
            activeCandidate={selectedOpt}
            activeExperiment={activeExp}
            validationResult={activeVal}
            isValidating={isValidating || activeRun?.status === 'RUNNING'}
            validationProgressPct={telemetryHistory.length > 0 ? Math.min(100, Math.round((telemetryHistory.length / 500) * 100)) : 75}
            sampleCount={telemetryHistory.length}
            hardwareConnected={hardwareConnected}
            isDemo={isDemo}
            onSelectStage={(stage) => {
              if (stage === 'optimization') setActiveSubTab('candidates');
              if (stage === 'prediction') setActiveSubTab('prediction');
              if (stage === 'compare') setActiveSubTab('telemetry');
            }}
          />

          {/* Live Validation Monitor during run or when active */}
          {(isValidating || activeRun?.status === 'RUNNING' || activeExp?.status === 'RUNNING') && (
            <LiveValidationMonitor
              isValidating={true}
              progressPct={telemetryHistory.length > 0 ? Math.min(100, Math.round((telemetryHistory.length / 500) * 100)) : 82}
              currentSamples={telemetryHistory.length || 320}
              targetSamples={500}
              latestSamples={latestSamples}
              isDemo={isDemo}
              hardwareConnected={hardwareConnected}
            />
          )}

          {/* Multi-Objective Impact Card & Decision Workflow */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MultiObjectiveImpactCard
              candidate={selectedOpt}
              validationResult={activeVal}
            />

            <OptimizationDecisionPanel
              candidate={selectedOpt}
              experiment={activeExp}
              validationResult={activeVal}
              onAccept={handleAcceptOptimization}
              onRollback={handleRollback}
              loading={loading}
            />
          </div>
        </div>
      )}

      {/* TAB 2: CANDIDATES & CODE DIFF */}
      {activeSubTab === 'candidates' && (
        <div>
          {optimizations.length === 0 ? (
            <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-3">
              <Zap size={36} className="text-[var(--text-muted)] opacity-60" />
              <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
                No Optimization Candidates Generated Yet
              </div>
              <p className="text-xs text-[var(--text-muted)] max-w-sm">
                Run telemetry capture and static-dynamic analysis to discover performance bottlenecks and generate candidate fixes.
              </p>
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-3.5 py-1.5 rounded-lg bg-[var(--accent-cyan)] text-white text-xs font-semibold hover:opacity-90 transition-opacity"
              >
                Start Telemetry Run
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Candidates List */}
              <div className="space-y-3">
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                  Proposed Candidates ({optimizations.length})
                </span>

                <div className="space-y-2">
                  {optimizations.map((opt) => {
                    const isSelected = selectedOpt?.optimization_id === opt.optimization_id;
                    const eff = (opt.expected_effect || {}) as Record<string, any>;
                    const latDelta = eff.latency_delta_ms ?? eff.loop_time_delta_ms ?? -10.0;
                    const sramDelta = eff.sram_delta_bytes ?? 0;

                    return (
                      <div
                        key={opt.optimization_id}
                        onClick={() => setSelectedOptId(opt.optimization_id)}
                        className={`aris-card p-4 space-y-2.5 cursor-pointer transition-all ${
                          isSelected
                            ? 'border-[var(--accent-cyan)] shadow-md ring-1 ring-[var(--accent-cyan)]/30'
                            : 'aris-card-hover'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="font-heading font-bold text-xs text-[var(--text-primary)] leading-snug">
                            {opt.title}
                          </div>
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold shrink-0 ${
                              opt.status === 'VALIDATED'
                                ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)]'
                                : opt.status === 'APPROVED'
                                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]'
                                : 'bg-[var(--bg-surface)] text-[var(--text-muted)]'
                            }`}
                          >
                            {opt.status}
                          </span>
                        </div>

                        {/* Multi-Objective Vector Badges */}
                        <div className="grid grid-cols-2 gap-1.5 text-[10px] font-mono pt-1 border-t border-[var(--border-color)]">
                          <div className="flex items-center gap-1 text-[var(--accent-green)]">
                            <TrendingDown size={11} />
                            <span>Latency: {latDelta} ms</span>
                          </div>
                          <div className="flex items-center gap-1 text-[var(--accent-cyan)]">
                            <Layers size={11} />
                            <span>SRAM: {sramDelta >= 0 ? `+${sramDelta}B` : `${sramDelta}B`}</span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-muted)]">
                          <span>Risk: {opt.risk || 'LOW'}</span>
                          <span>Confidence: {((opt.confidence || 0.9) * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Two Columns: Candidate Detail & Code Diff */}
              {selectedOpt && (
                <div className="lg:col-span-2 space-y-4">
                  <div className="aris-card p-5 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-color)] pb-3">
                      <div>
                        <h3 className="font-heading font-bold text-base text-[var(--text-primary)]">
                          {selectedOpt.title}
                        </h3>
                        <div className="text-xs font-mono text-[var(--text-muted)] mt-0.5">
                          ID: {selectedOpt.optimization_id} · Finding: {selectedOpt.finding_id}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleValidateCandidate(selectedOpt.optimization_id)}
                          disabled={isValidating}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold shadow-sm transition-opacity"
                        >
                          <Play size={13} className={isValidating ? 'animate-spin' : ''} />
                          <span>{isValidating ? 'Validating on Hardware...' : 'Run & Validate'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Hardware Rationale & Consideration */}
                    <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-1">
                      <div className="text-[11px] font-mono font-semibold text-[var(--text-primary)] flex items-center gap-1.5">
                        <Cpu size={13} className="text-[var(--accent-cyan)]" />
                        <span>AVR Harvard Architectural Rationale</span>
                      </div>
                      <p className="text-xs text-[var(--text-muted)] leading-relaxed font-mono">
                        {selectedOpt.hardware_consideration || selectedOpt.reason}
                      </p>
                    </div>

                    {/* Code Diff Panel */}
                    <div className="space-y-2">
                      <span className="text-xs font-mono font-semibold text-[var(--text-secondary)]">
                        Proposed Code Transformation
                      </span>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-code">
                        {/* Before */}
                        <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--accent-red)]/20 space-y-1">
                          <div className="flex justify-between text-[10px] font-mono text-[var(--accent-red)] pb-1 border-b border-[var(--border-color)]">
                            <span>ORIGINAL CODE</span>
                            <span>{selectedOpt.source_location?.file}:{selectedOpt.source_location?.line}</span>
                          </div>
                          <pre className="text-[var(--accent-red)] overflow-x-auto whitespace-pre-wrap">
                            {selectedOpt.before_code}
                          </pre>
                        </div>

                        {/* After */}
                        <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--accent-green)]/20 space-y-1">
                          <div className="flex justify-between text-[10px] font-mono text-[var(--accent-green)] pb-1 border-b border-[var(--border-color)]">
                            <span>OPTIMIZED TRANSFORMATION</span>
                            <span>NON-BLOCKING</span>
                          </div>
                          <pre className="text-[var(--accent-green)] overflow-x-auto whitespace-pre-wrap">
                            {selectedOpt.after_code}
                          </pre>
                        </div>
                      </div>
                    </div>

                    {/* Quick validation button */}
                    <div className="flex justify-end pt-2">
                      <button
                        onClick={() => handleValidateCandidate(selectedOpt.optimization_id)}
                        disabled={isValidating}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--accent-cyan)] text-white text-xs font-mono font-bold hover:opacity-90 shadow-sm transition-all"
                      >
                        <Play size={13} />
                        <span>Deploy to Hardware & Validate SLA</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PREDICTION VS REALITY */}
      {activeSubTab === 'prediction' && (
        <div className="space-y-6">
          <PredictionVsRealityView
            candidate={selectedOpt}
            validationResult={activeVal}
            experiment={activeExp}
          />
        </div>
      )}

      {/* TAB 4: BEFORE / AFTER TELEMETRY */}
      {activeSubTab === 'telemetry' && (
        <div className="space-y-6">
          <BeforeAfterTelemetryView
            telemetryHistory={telemetryHistory}
          />
        </div>
      )}

      {/* TAB 5: REPLAY & OPTIMIZATION HISTORY */}
      {activeSubTab === 'history' && (
        <div className="space-y-6">
          <ExperimentReplayAndHistory
            experiments={experiments}
            optimizations={optimizations}
            validations={validations}
            selectedBoard={selectedBoard}
            selectedExpId={selectedExpId}
            onSelectExperiment={(id) => setSelectedExpId(id)}
            onReplayExperiment={(id) => {
              setSelectedExpId(id);
              setActiveSubTab('lifecycle');
            }}
            onRollbackExperiment={(id) => handleRollback(id)}
          />
        </div>
      )}
    </div>
  );
};
