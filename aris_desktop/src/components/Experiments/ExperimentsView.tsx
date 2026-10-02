// ============================================================
// ARIS — Experiments View
// Step-by-step experiment pipeline visualizer:
// CREATED → BUILDING → FLASHING → RUNNING → COLLECTING → COMPARING → VALIDATED
// ============================================================

import React, { useEffect } from 'react';
import { FlaskConical, Clock, CheckCircle, XCircle, Loader2, Play, Sparkles } from 'lucide-react';
import type { ExperimentRecord, OptimizationCandidate } from '../../types';

interface ExperimentsViewProps {
  experiments: ExperimentRecord[];
  optimizations: OptimizationCandidate[];
  onRefresh: () => void;
  onNavigateValidation: (experimentId: string) => void;
  onRunExperiment?: (experimentId: string) => Promise<unknown>;
  loading?: Record<string, boolean>;
}

const PIPELINE_STEPS = [
  'CREATED',
  'BUILDING',
  'FLASHING',
  'RUNNING',
  'COLLECTING',
  'COMPARING',
  'VALIDATED',
] as const;

const STEP_DESCRIPTIONS: Record<string, string> = {
  CREATED: 'Experiment created. Ready to build & benchmark candidate firmware.',
  BUILDING: 'Compiling optimized firmware for the target MCU.',
  FLASHING: 'Programming the microcontroller via avrdude.',
  RUNNING: 'Executing instrumented firmware on hardware/simulator.',
  COLLECTING: 'Collecting telemetry samples from the target.',
  COMPARING: 'Comparing candidate telemetry against baseline.',
  VALIDATED: 'Closed-loop empirical validation complete.',
  COMPLETED: 'Experiment completed. Empirical validation report generated.',
  FAILED: 'Experiment encountered a failure.',
};

function stepIndex(status: string): number {
  const idx = PIPELINE_STEPS.indexOf(status as typeof PIPELINE_STEPS[number]);
  if (status === 'COMPLETED') return PIPELINE_STEPS.length;
  if (status === 'FAILED') return -1;
  return idx >= 0 ? idx : 0;
}

export const ExperimentsView: React.FC<ExperimentsViewProps> = ({
  experiments,
  optimizations,
  onRefresh,
  onNavigateValidation,
  onRunExperiment,
  loading = {},
}) => {
  // Auto-refresh every 5 seconds when experiments are running
  useEffect(() => {
    const hasRunning = experiments.some(
      (e) => e.status === 'RUNNING' || e.status === 'CREATED',
    );
    if (!hasRunning) return;
    const iv = setInterval(onRefresh, 5000);
    return () => clearInterval(iv);
  }, [experiments, onRefresh]);

  if (experiments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3">
        <FlaskConical className="w-10 h-10 text-slate-700" />
        <p className="font-mono text-sm">No experiments yet.</p>
        <p className="font-mono text-xs text-slate-700">
          Approve an optimization candidate in the Optimization tab to create a closed-loop experiment.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto p-4 gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-mono font-semibold text-slate-200">
            Experiments &amp; Benchmarks ({experiments.length})
          </h2>
          <p className="text-[11px] font-mono text-slate-500 mt-0.5">
            Empirical closed-loop validation comparing baseline telemetry against optimized candidate execution.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="text-[10px] font-mono text-slate-500 hover:text-slate-300 transition-colors px-2 py-1 border border-slate-800 rounded hover:border-slate-700"
        >
          Refresh
        </button>
      </div>

      {experiments.map((exp) => {
        const isRunningExp = loading[`validate_${exp.experiment_id}`];
        const currentStep = isRunningExp ? 4 : stepIndex(exp.status);
        const opt = optimizations.find(
          (o) => o.optimization_id === exp.optimization_id,
        );
        const isFailed = exp.status === 'FAILED';
        const isComplete =
          exp.status === 'COMPLETED' || exp.status === 'VALIDATED';
        const isCreated = exp.status === 'CREATED';

        return (
          <div
            key={exp.experiment_id}
            className="bg-[#22272e] border border-white/[0.08] rounded-xl p-5 space-y-4 shadow-lg shadow-black/20"
          >
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-mono font-semibold text-slate-100 flex items-center gap-2">
                  <span>{exp.title}</span>
                  {isComplete && (
                    <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30 flex items-center gap-1">
                      <Sparkles className="w-2.5 h-2.5" /> Empirical Report Ready
                    </span>
                  )}
                </h3>
                <div className="flex items-center gap-3 mt-1.5 text-[10px] font-mono text-slate-500">
                  <span className="text-slate-400 font-semibold">{exp.experiment_id}</span>
                  <span>·</span>
                  <span>Board: <strong className="text-slate-300">{exp.board_id}</strong></span>
                  <span>·</span>
                  <span>Created: {new Date(exp.created_at).toLocaleString()}</span>
                </div>
              </div>
              <span
                className={`text-xs font-mono px-2.5 py-1 rounded-md border font-semibold ${
                  isFailed
                    ? 'text-red-400 border-red-600 bg-red-900/20'
                    : isComplete
                    ? 'text-emerald-400 border-emerald-600 bg-emerald-900/20'
                    : isRunningExp
                    ? 'text-[#00878a] border-[#00878a]/60 bg-[#00878a]/10 animate-pulse'
                    : 'text-amber-400 border-amber-600 bg-amber-900/20'
                }`}
              >
                {isRunningExp ? 'VALIDATING…' : exp.status}
              </span>
            </div>

            {/* Pipeline Progress */}
            <div className="flex items-center gap-1.5 overflow-x-auto py-1">
              {PIPELINE_STEPS.map((step, idx) => {
                const isActive = (idx === currentStep && !isFailed && !isComplete) || (isRunningExp && idx >= 1 && idx <= 5);
                const isDone = (idx < currentStep || isComplete) && !isRunningExp;
                const isFail = isFailed && idx === currentStep;

                return (
                  <React.Fragment key={step}>
                    <div
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[9px] font-mono transition-all shrink-0 ${
                        isDone
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium'
                          : isActive
                          ? 'bg-[#00878a]/20 text-[#00878a] border border-[#00878a]/50 font-bold shadow-sm shadow-[#00878a]/20 animate-pulse'
                          : isFail
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                          : 'bg-white/[0.02] text-slate-500 border border-white/[0.06]'
                      }`}
                      title={STEP_DESCRIPTIONS[step]}
                    >
                      {isDone ? (
                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                      ) : isActive ? (
                        <Loader2 className="w-3 h-3 animate-spin text-[#00878a]" />
                      ) : isFail ? (
                        <XCircle className="w-3 h-3 text-red-400" />
                      ) : (
                        <Clock className="w-3 h-3 text-slate-600" />
                      )}
                      {step}
                    </div>
                    {idx < PIPELINE_STEPS.length - 1 && (
                      <div
                        className={`w-3 h-px shrink-0 ${
                          isDone ? 'bg-emerald-500/50' : 'bg-slate-800'
                        }`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Action Banner for CREATED status */}
            {isCreated && !isRunningExp && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-[#00878a]/10 border border-[#00878a]/30">
                <div className="space-y-0.5">
                  <p className="text-xs font-mono font-semibold text-[#00878a] flex items-center gap-1.5">
                    <Play className="w-3.5 h-3.5 fill-current" /> Ready to Run &amp; Benchmark Candidate
                  </p>
                  <p className="text-[11px] font-mono text-slate-300">
                    Click to execute the optimized candidate on {exp.board_id}, stream runtime telemetry, and generate an empirical before-and-after validation report.
                  </p>
                </div>
                <button
                  onClick={() => onRunExperiment?.(exp.experiment_id)}
                  disabled={isRunningExp}
                  className="px-4 py-2 bg-[#00878a] hover:bg-[#009da0] disabled:opacity-50 text-white text-xs font-mono font-semibold rounded-lg flex items-center gap-2 shadow-lg shadow-[#00878a]/25 transition-all shrink-0 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run &amp; Validate Candidate →</span>
                </button>
              </div>
            )}

            {/* Phase description */}
            <p className="text-xs font-mono text-slate-400">
              {isRunningExp
                ? 'Streaming candidate telemetry and computing statistical delta across all 8 canonical metrics...'
                : STEP_DESCRIPTIONS[exp.status] || 'Processing experiment workflow.'}
            </p>

            {/* Optimization info */}
            {opt && (
              <div className="bg-white/[0.03] border border-white/[0.05] rounded-lg p-3 text-xs font-mono">
                <span className="text-slate-500">Optimization: </span>
                <span className="text-slate-200 font-semibold">{opt.title}</span>
                <span className="text-slate-500 ml-3">({opt.optimization_id})</span>
              </div>
            )}

            {/* Links and Actions */}
            <div className="flex items-center gap-3 pt-1 border-t border-white/[0.04]">
              <span className="text-[10px] font-mono text-slate-500">
                Baseline: <strong className="text-slate-400">{exp.baseline_run_id}</strong>
              </span>
              {exp.candidate_run_id && (
                <span className="text-[10px] font-mono text-slate-500">
                  Candidate: <strong className="text-slate-400">{exp.candidate_run_id}</strong>
                </span>
              )}

              {/* Action Buttons */}
              {isCreated && !isRunningExp && (
                <button
                  onClick={() => onRunExperiment?.(exp.experiment_id)}
                  className="ml-auto text-xs font-mono text-white bg-[#00878a] hover:bg-[#009da0] transition-colors px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-semibold shadow-md shadow-[#00878a]/20 cursor-pointer"
                >
                  <Play className="w-3 h-3 fill-current" />
                  Run Candidate →
                </button>
              )}

              {isRunningExp && (
                <div className="ml-auto flex items-center gap-2 text-xs font-mono text-[#00878a] font-semibold animate-pulse">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Running &amp; Measuring...
                </div>
              )}

              {(isComplete || exp.validation_id) && !isRunningExp && (
                <button
                  onClick={() => onNavigateValidation(exp.experiment_id)}
                  className="ml-auto text-xs font-mono text-emerald-400 hover:text-emerald-300 font-semibold transition-colors px-3 py-1.5 border border-emerald-500/40 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 flex items-center gap-1.5 cursor-pointer"
                >
                  <Sparkles className="w-3 h-3" />
                  View Validation Results →
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
