// ============================================================
// ARIS — Experiments View
// Step-by-step experiment pipeline visualizer:
// CREATED → BUILDING → FLASHING → RUNNING → COLLECTING → COMPARING → VALIDATED
// ============================================================

import React, { useEffect } from 'react';
import { FlaskConical, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import type { ExperimentRecord, OptimizationCandidate } from '../../types';

interface ExperimentsViewProps {
  experiments: ExperimentRecord[];
  optimizations: OptimizationCandidate[];
  onRefresh: () => void;
  onNavigateValidation: (experimentId: string) => void;
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
  CREATED: 'Experiment created. Awaiting build.',
  BUILDING: 'Compiling optimized firmware for the target MCU.',
  FLASHING: 'Programming the microcontroller via avrdude.',
  RUNNING: 'Executing instrumented firmware on hardware.',
  COLLECTING: 'Collecting telemetry samples from the target.',
  COMPARING: 'Comparing candidate telemetry against baseline.',
  VALIDATED: 'Closed-loop empirical validation complete.',
  COMPLETED: 'Experiment completed.',
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
          Approve an optimization candidate to create a closed-loop experiment.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto p-4 gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono font-semibold text-slate-200">
          Experiments ({experiments.length})
        </h2>
        <button
          onClick={onRefresh}
          className="text-[10px] font-mono text-slate-500 hover:text-slate-300 transition-colors px-2 py-1 border border-slate-800 rounded"
        >
          Refresh
        </button>
      </div>

      {experiments.map((exp) => {
        const currentStep = stepIndex(exp.status);
        const opt = optimizations.find(
          (o) => o.optimization_id === exp.optimization_id,
        );
        const isFailed = exp.status === 'FAILED';
        const isComplete =
          exp.status === 'COMPLETED' || exp.status === 'VALIDATED';

        return (
          <div
            key={exp.experiment_id}
            className="bg-slate-900/60 border border-slate-800 rounded p-4 space-y-4"
          >
            {/* Header */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-sm font-mono font-semibold text-slate-100">
                  {exp.title}
                </h3>
                <div className="flex items-center gap-3 mt-1 text-[10px] font-mono text-slate-500">
                  <span>{exp.experiment_id}</span>
                  <span>·</span>
                  <span>Board: {exp.board_id}</span>
                  <span>·</span>
                  <span>
                    {new Date(exp.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <span
                className={`text-xs font-mono px-2 py-1 rounded border ${
                  isFailed
                    ? 'text-red-400 border-red-600 bg-red-900/20'
                    : isComplete
                    ? 'text-emerald-400 border-emerald-600 bg-emerald-900/20'
                    : 'text-amber-400 border-amber-600 bg-amber-900/20'
                }`}
              >
                {exp.status}
              </span>
            </div>

            {/* Pipeline Progress */}
            <div className="flex items-center gap-1">
              {PIPELINE_STEPS.map((step, idx) => {
                const isActive = idx === currentStep && !isFailed && !isComplete;
                const isDone = idx < currentStep || isComplete;
                const isFail = isFailed && idx === currentStep;

                return (
                  <React.Fragment key={step}>
                    <div
                      className={`flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-mono transition-all ${
                        isDone
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : isActive
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/40 animate-pulse'
                          : isFail
                          ? 'bg-red-500/10 text-red-400 border border-red-500/30'
                          : 'bg-slate-800/30 text-slate-600 border border-slate-800'
                      }`}
                      title={STEP_DESCRIPTIONS[step]}
                    >
                      {isDone ? (
                        <CheckCircle className="w-3 h-3" />
                      ) : isActive ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : isFail ? (
                        <XCircle className="w-3 h-3" />
                      ) : (
                        <Clock className="w-3 h-3" />
                      )}
                      {step}
                    </div>
                    {idx < PIPELINE_STEPS.length - 1 && (
                      <div
                        className={`w-4 h-px ${
                          isDone ? 'bg-emerald-500/50' : 'bg-slate-800'
                        }`}
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Phase description */}
            <p className="text-xs font-mono text-slate-400">
              {STEP_DESCRIPTIONS[exp.status] ||
                'Processing experiment workflow.'}
            </p>

            {/* Optimization info */}
            {opt && (
              <div className="bg-slate-800/30 rounded p-3 text-xs font-mono">
                <span className="text-slate-500">Optimization: </span>
                <span className="text-slate-300">{opt.title}</span>
                <span className="text-slate-500 ml-3">
                  ({opt.optimization_id})
                </span>
              </div>
            )}

            {/* Links */}
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-mono text-slate-500">
                Baseline: {exp.baseline_run_id}
              </span>
              {exp.candidate_run_id && (
                <span className="text-[10px] font-mono text-slate-500">
                  Candidate: {exp.candidate_run_id}
                </span>
              )}
              {(isComplete || exp.validation_id) && (
                <button
                  onClick={() =>
                    onNavigateValidation(exp.experiment_id)
                  }
                  className="ml-auto text-[10px] font-mono text-cyan-400 hover:text-cyan-300 transition-colors px-2 py-1 border border-cyan-500/30 rounded"
                >
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
