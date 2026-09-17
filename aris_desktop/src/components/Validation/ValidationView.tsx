// ============================================================
// ARIS — Validation View
// Empirical comparison: BASELINE vs CANDIDATE
// Shows prediction vs reality, absolute/percentage deltas,
// and validation status badge.
// ============================================================

import React, { useEffect } from 'react';
import { ArrowDown, ArrowUp, Minus, BarChart3 } from 'lucide-react';
import type {
  ValidationResult,
  ValidationMetricDelta,
  ValidationStatus,
  ExperimentRecord,
} from '../../types';

interface ValidationViewProps {
  experiments: ExperimentRecord[];
  validations: Record<string, ValidationResult>;
  selectedExperimentId: string | null;
  onLoadValidation: (experimentId: string) => Promise<ValidationResult | null>;
}

const VALIDATION_BADGE: Record<ValidationStatus, string> = {
  VALIDATED: 'text-emerald-400 border-emerald-500/50 bg-emerald-500/10',
  PARTIALLY_VALIDATED: 'text-[#00878a] border-[#00878a]/50 bg-[#00878a]/10',
  NO_SIGNIFICANT_CHANGE: 'text-slate-400 border-slate-600 bg-slate-800/40',
  REGRESSION: 'text-red-400 border-red-500/50 bg-red-500/10',
  REJECTED: 'text-red-500 border-red-600 bg-red-900/20',
  INCONCLUSIVE: 'text-amber-400 border-amber-500/50 bg-amber-500/10',
};

const CANONICAL_VALIDATION_METRICS = [
  'cpu_load',
  'loop_time',
  'loop_jitter',
  'sram_used',
  'stack_used',
  'interrupt_rate',
  'runtime_fault',
];

export const ValidationView: React.FC<ValidationViewProps> = ({
  experiments,
  validations,
  selectedExperimentId,
  onLoadValidation,
}) => {
  const expId = selectedExperimentId;

  useEffect(() => {
    if (expId && !validations[expId]) {
      onLoadValidation(expId);
    }
  }, [expId, validations, onLoadValidation]);

  const result = expId ? validations[expId] : null;

  if (!expId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3">
        <BarChart3 className="w-10 h-10 text-slate-700" />
        <p className="font-mono text-sm">
          Select an experiment from the Experiments tab to view validation results.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3">
        <BarChart3 className="w-10 h-10 text-slate-700" />
        <p className="font-mono text-sm">
          Loading validation results for experiment {expId}…
        </p>
        <p className="font-mono text-xs text-slate-700">
          If the experiment has not completed, results may not be available yet.
        </p>
      </div>
    );
  }

  const metricEntries = Object.entries(result.metrics || {});

  return (
    <div className="flex flex-col h-full overflow-auto p-4 gap-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-mono font-semibold text-slate-100">
            Validation Results
          </h2>
          <div className="flex items-center gap-3 mt-1 text-[10px] font-mono text-slate-500">
            <span>{result.validation_id}</span>
            <span>·</span>
            <span>Experiment: {result.experiment_id}</span>
            <span>·</span>
            <span>{new Date(result.created_at).toLocaleString()}</span>
          </div>
        </div>
        <span
          className={`text-sm font-mono px-3 py-1.5 rounded border font-semibold ${
            VALIDATION_BADGE[result.validation_status]
          }`}
        >
          {result.validation_status}
        </span>
      </div>

      {/* Run IDs */}
      <div className="flex items-center gap-6 bg-[#22272e] border border-white/[0.08] rounded-xl px-4 py-3">
        <div>
          <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">
            Baseline Run
          </p>
          <p className="text-xs font-mono text-slate-300 mt-0.5">
            {result.baseline_run_id}
          </p>
        </div>
        <div className="text-slate-600 font-mono">vs</div>
        <div>
          <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">
            Candidate Run
          </p>
          <p className="text-xs font-mono text-slate-300 mt-0.5">
            {result.candidate_run_id}
          </p>
        </div>
      </div>

      {/* Reason */}
      <div className="bg-[#22272e] border border-white/[0.08] rounded-xl p-3">
        <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-1">
          Validation Rationale
        </p>
        <p className="text-xs font-mono text-slate-300">{result.reason}</p>
      </div>

      {/* Metric comparison table */}
      <div className="bg-[#22272e] border border-white/[0.08] rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="text-left text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Metric
              </th>
              <th className="text-right text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Baseline
              </th>
              <th className="text-right text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Candidate
              </th>
              <th className="text-right text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Δ Absolute
              </th>
              <th className="text-right text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Δ Percent
              </th>
              <th className="text-center text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-2.5">
                Result
              </th>
            </tr>
          </thead>
          <tbody>
            {metricEntries.map(([key, delta]) => {
              const d = delta as ValidationMetricDelta;
              return (
                <tr
                  key={key}
                  className="border-b border-slate-800/40 hover:bg-slate-800/20"
                >
                  <td className="px-4 py-2.5 text-xs font-mono text-slate-300">
                    {d.metric || key}
                  </td>
                  <td className="px-4 py-2.5 text-xs font-mono text-slate-400 text-right tabular-nums">
                    {d.baseline_value.toFixed(2)}
                  </td>
                  <td className="px-4 py-2.5 text-xs font-mono text-slate-300 text-right tabular-nums">
                    {d.candidate_value.toFixed(2)}
                  </td>
                  <td
                    className={`px-4 py-2.5 text-xs font-mono text-right tabular-nums ${
                      d.is_improvement
                        ? 'text-emerald-400'
                        : d.difference === 0
                        ? 'text-slate-500'
                        : 'text-red-400'
                    }`}
                  >
                    <span className="inline-flex items-center gap-1">
                      {d.is_improvement ? (
                        <ArrowDown className="w-3 h-3" />
                      ) : d.difference === 0 ? (
                        <Minus className="w-3 h-3" />
                      ) : (
                        <ArrowUp className="w-3 h-3" />
                      )}
                      {d.difference.toFixed(3)}
                    </span>
                  </td>
                  <td
                    className={`px-4 py-2.5 text-xs font-mono text-right tabular-nums ${
                      d.is_improvement
                        ? 'text-emerald-400'
                        : d.percentage_change === 0
                        ? 'text-slate-500'
                        : 'text-red-400'
                    }`}
                  >
                    {d.percentage_change >= 0 ? '+' : ''}
                    {d.percentage_change.toFixed(1)}%
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    {d.is_improvement ? (
                      <span className="text-[9px] font-mono text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30 bg-emerald-500/10">
                        IMPROVED
                      </span>
                    ) : d.difference === 0 ? (
                      <span className="text-[9px] font-mono text-slate-500 px-1.5 py-0.5 rounded border border-slate-700">
                        NO CHANGE
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono text-red-400 px-1.5 py-0.5 rounded border border-red-500/30 bg-red-500/10">
                        REGRESSION
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Prediction vs Reality */}
      {result.prediction_accuracy && (
        <div className="bg-[#22272e] border border-white/[0.08] rounded-xl p-4 space-y-3">
          <h3 className="text-[9px] font-mono text-slate-500 uppercase tracking-widest">
            Prediction vs Reality
          </h3>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-[9px] font-mono text-slate-500">
                Prediction Accuracy Score
              </p>
              <p className="text-xl font-mono font-bold text-[#00878a] tabular-nums">
                {(
                  result.prediction_accuracy.prediction_accuracy_score * 100
                ).toFixed(1)}
                %
              </p>
            </div>
            <div>
              <p className="text-[9px] font-mono text-slate-500">
                Mean Prediction Error
              </p>
              <p className="text-xl font-mono font-bold text-amber-400 tabular-nums">
                {result.prediction_accuracy.mean_prediction_error_pct.toFixed(
                  1,
                )}
                %
              </p>
            </div>
            <div>
              <p className="text-[9px] font-mono text-slate-500">
                Metrics Compared
              </p>
              <p className="text-xl font-mono font-bold text-slate-300 tabular-nums">
                {result.prediction_accuracy.sample_count}
              </p>
            </div>
          </div>

          {/* Per-metric prediction comparison */}
          {Object.entries(
            result.prediction_accuracy.metrics_compared,
          ).map(([metric, cmp]) => (
            <div
              key={metric}
              className="flex items-center gap-4 bg-white/[0.02] border border-white/[0.04] rounded px-3 py-2"
            >
              <span className="text-xs font-mono text-slate-400 w-24">
                {metric}
              </span>
              <div className="flex-1 grid grid-cols-4 gap-4 text-[10px] font-mono">
                <div>
                  <span className="text-slate-400">PREDICTED: </span>
                  <span className="text-slate-300 tabular-nums">
                    {cmp.predicted.toFixed(2)} {cmp.unit}
                  </span>
                </div>
                <div>
                  <span className="text-emerald-400">ACTUAL: </span>
                  <span className="text-slate-300 tabular-nums">
                    {cmp.actual.toFixed(2)} {cmp.unit}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Error: </span>
                  <span className="text-amber-300 tabular-nums">
                    {cmp.relative_error_pct.toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Direction: </span>
                  <span
                    className={
                      cmp.directional_match
                        ? 'text-emerald-400'
                        : 'text-red-400'
                    }
                  >
                    {cmp.directional_match ? '✓ Match' : '✗ Mismatch'}
                  </span>
                </div>
              </div>
            </div>
          ))}

          <p className="text-[9px] font-mono text-slate-600 italic">
            {result.prediction_accuracy.scientific_note}
          </p>
        </div>
      )}
    </div>
  );
};
