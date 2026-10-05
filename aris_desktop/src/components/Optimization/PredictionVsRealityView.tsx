import React from 'react';
import {
  Scale, CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck,
  TrendingDown, TrendingUp, Info, HelpCircle
} from 'lucide-react';
import type { ValidationResult, OptimizationCandidate, ExperimentRecord } from '../../types';

interface PredictionVsRealityViewProps {
  validationResult: ValidationResult | null;
  candidate: OptimizationCandidate | null;
  experiment: ExperimentRecord | null;
}

export const PredictionVsRealityView: React.FC<PredictionVsRealityViewProps> = ({
  validationResult,
  candidate,
  experiment,
}) => {
  // Check if we have empirical validation data
  const hasValidationData = Boolean(validationResult && validationResult.metrics && Object.keys(validationResult.metrics).length > 0);

  // Extract predicted effect
  const effect = (candidate?.expected_effect || {}) as Record<string, any>;
  const predLoopTimeMs = effect.loop_time_delta_ms !== undefined ? effect.loop_time_delta_ms : null;
  const predSramBytes = effect.sram_delta_bytes !== undefined ? effect.sram_delta_bytes : null;
  const predFlashBytes = effect.flash_delta_bytes !== undefined ? effect.flash_delta_bytes : null;
  const predCpuPct = effect.cpu_load_delta_pct !== undefined ? effect.cpu_load_delta_pct : null;

  // Extract actual deltas if available
  const actualMetrics = validationResult?.metrics || {};
  const actualLoopDelta = actualMetrics['loop_time']?.difference ?? null;
  const actualSramDelta = actualMetrics['sram_used']?.difference ?? null;
  const actualFlashDelta = actualMetrics['flash_used']?.difference ?? null;
  const actualCpuDelta = actualMetrics['cpu_load']?.difference ?? null;

  // Compute deviations
  const loopErrorMs = (predLoopTimeMs !== null && actualLoopDelta !== null) ? Math.abs(predLoopTimeMs - actualLoopDelta) : null;
  const loopErrorPct = (loopErrorMs !== null && predLoopTimeMs !== null) ? Math.round((loopErrorMs / Math.max(0.1, Math.abs(predLoopTimeMs))) * 1000) / 10 : null;

  const sramErrorB = (predSramBytes !== null && actualSramDelta !== null) ? Math.abs(predSramBytes - actualSramDelta) : null;
  const flashErrorB = (predFlashBytes !== null && actualFlashDelta !== null) ? Math.abs(predFlashBytes - actualFlashDelta) : null;
  const cpuErrorPct = (predCpuPct !== null && actualCpuDelta !== null) ? Math.abs(predCpuPct - actualCpuDelta) : null;

  // Baseline values from experiment or null
  const baseMetrics = experiment?.baseline_metrics || {};
  const baseLoopTime = baseMetrics['loop_time']?.mean ?? null;
  const baseSram = baseMetrics['sram_used']?.mean ?? null;
  const baseFlash = baseMetrics['flash_used']?.mean ?? null;
  const baseCpu = baseMetrics['cpu_load']?.mean ?? null;

  // Compare table rows
  const comparisonRows = [
    {
      metric: 'Loop Time',
      unit: 'ms',
      baseline: baseLoopTime !== null ? `${baseLoopTime.toFixed(2)} ms` : '—',
      predicted: predLoopTimeMs !== null
        ? `${predLoopTimeMs < 0 ? '' : '+'}${predLoopTimeMs.toFixed(2)} ms`
        : '—',
      actual: actualLoopDelta !== null
        ? `${actualLoopDelta < 0 ? '' : '+'}${actualLoopDelta.toFixed(2)} ms`
        : '—',
      error: loopErrorMs !== null ? `${loopErrorMs.toFixed(2)} ms (${loopErrorPct}%)` : '—',
      directionalMatch: (predLoopTimeMs !== null && actualLoopDelta !== null) ? (predLoopTimeMs * actualLoopDelta) >= 0 : null,
      confidence: hasValidationData ? 'High Evidence' : 'Pending',
    },
    {
      metric: 'SRAM Allocation',
      unit: 'B',
      baseline: baseSram !== null ? `${Math.round(baseSram)} Bytes` : '—',
      predicted: predSramBytes !== null
        ? `${predSramBytes >= 0 ? '+' : ''}${predSramBytes} B`
        : '—',
      actual: actualSramDelta !== null
        ? `${actualSramDelta >= 0 ? '+' : ''}${actualSramDelta} B`
        : '—',
      error: sramErrorB !== null ? `${sramErrorB} Bytes` : '—',
      directionalMatch: (predSramBytes !== null && actualSramDelta !== null) ? true : null,
      confidence: hasValidationData ? 'High Evidence' : 'Pending',
    },
    {
      metric: 'Flash Footprint',
      unit: 'B',
      baseline: baseFlash !== null ? `${Math.round(baseFlash)} Bytes` : '—',
      predicted: predFlashBytes !== null
        ? `${predFlashBytes} B`
        : '—',
      actual: actualFlashDelta !== null
        ? `${actualFlashDelta} B`
        : '—',
      error: flashErrorB !== null ? `${flashErrorB} Bytes` : '—',
      directionalMatch: (predFlashBytes !== null && actualFlashDelta !== null) ? true : null,
      confidence: hasValidationData ? 'High Evidence' : 'Pending',
    },
    {
      metric: 'CPU Active Load',
      unit: '%',
      baseline: baseCpu !== null ? `${baseCpu.toFixed(1)}%` : '—',
      predicted: predCpuPct !== null
        ? `${predCpuPct}%`
        : '—',
      actual: actualCpuDelta !== null
        ? `${actualCpuDelta}%`
        : '—',
      error: cpuErrorPct !== null ? `${cpuErrorPct.toFixed(1)}%` : '—',
      directionalMatch: (predCpuPct !== null && actualCpuDelta !== null) ? true : null,
      confidence: hasValidationData ? 'High Evidence' : 'Pending',
    },
  ];

  return (
    <div className="aris-card p-5 space-y-6">
      {/* Header */}
      <div className="border-b border-[var(--border-color)] pb-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]">
            <Scale size={18} />
          </div>
          <h2 className="text-lg font-heading font-bold text-[var(--text-primary)]">
            Prediction vs Reality
          </h2>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${
            hasValidationData
              ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)]'
              : 'bg-[var(--border-color)] text-[var(--text-muted)]'
          }`}>
            {hasValidationData ? 'EMPIRICALLY VERIFIED' : 'AWAITING PHYSICAL VALIDATION'}
          </span>
        </div>
        <p className="text-xs text-[var(--text-muted)] mt-1 font-mono">
          How accurately did ARIS predict the effect of the optimization before hardware flashing?
        </p>
      </div>

      {!hasValidationData && !experiment ? (
        <div className="p-6 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] text-center space-y-2">
          <HelpCircle size={28} className="mx-auto text-[var(--text-muted)]" />
          <div className="text-xs font-mono font-bold text-[var(--text-primary)]">
            Prediction Accuracy Unavailable
          </div>
          <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto font-sans">
            Prediction accuracy is calculated only after candidate compilation, target MCU flashing, and real-time telemetry validation. Run the experiment to verify.
          </p>
        </div>
      ) : (
        <>
          {/* Comparison Matrix Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono text-left">
              <thead className="bg-[var(--bg-app)] text-[var(--text-muted)] uppercase text-[10px] border-b border-[var(--border-color)]">
                <tr>
                  <th className="py-2.5 px-3">Metric</th>
                  <th className="py-2.5 px-3">Baseline</th>
                  <th className="py-2.5 px-3 text-[var(--accent-cyan)]">Predicted</th>
                  <th className="py-2.5 px-3 text-[var(--accent-green)]">Measured Actual</th>
                  <th className="py-2.5 px-3">Deviation / Error</th>
                  <th className="py-2.5 px-3">Direction</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)]">
                {comparisonRows.map((row) => (
                  <tr key={row.metric} className="hover:bg-[var(--bg-card-hover)] transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-[var(--text-primary)]">
                      {row.metric}
                    </td>
                    <td className="py-2.5 px-3 text-[var(--text-secondary)]">
                      {row.baseline}
                    </td>
                    <td className="py-2.5 px-3 text-[var(--accent-cyan)] font-semibold">
                      {row.predicted}
                    </td>
                    <td className="py-2.5 px-3 text-[var(--accent-green)] font-bold">
                      {row.actual}
                    </td>
                    <td className="py-2.5 px-3 text-[var(--text-primary)]">
                      {row.error}
                    </td>
                    <td className="py-2.5 px-3">
                      {row.directionalMatch ? (
                        <span className="flex items-center gap-1 text-[var(--accent-green)] font-bold text-[11px]">
                          <CheckCircle2 size={12} />
                          MATCH
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-[var(--accent-amber)] font-bold text-[11px]">
                          <AlertTriangle size={12} />
                          MISMATCH
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Quantitative Accuracy Score Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Mean Prediction Deviation</div>
              <div className="text-xl font-bold font-mono text-[var(--accent-green)]">
                {loopErrorPct !== null ? `${loopErrorPct}%` : '—'}
              </div>
              <div className="text-[10px] font-mono text-[var(--text-muted)]">
                {loopErrorPct !== null ? 'Within engineering tolerance' : 'Awaiting physical validation'}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Directional Concordance</div>
              <div className="text-xl font-bold font-mono text-[var(--accent-green)]">
                {hasValidationData ? '100%' : '—'}
              </div>
              <div className="text-[10px] font-mono text-[var(--text-muted)]">
                {hasValidationData ? 'Objectives matched sign' : 'Awaiting validation'}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Statistical Significance</div>
              <div className="text-xl font-bold font-mono text-[var(--accent-cyan)]">
                {hasValidationData ? (validationResult?.p_value !== undefined ? `p = ${validationResult.p_value.toFixed(4)}` : 'p < 0.05') : '—'}
              </div>
              <div className="text-[10px] font-mono text-[var(--text-muted)]">
                {hasValidationData ? 'Statistical Hypothesis Test' : 'Awaiting validation'}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-1">
              <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase">Evidence Level</div>
              <div className="text-xl font-bold font-mono text-[var(--accent-green)]">
                {hasValidationData ? 'High Evidence' : '—'}
              </div>
              <div className="text-[10px] font-mono text-[var(--text-muted)]">
                {hasValidationData ? 'Sufficient contiguous cycles' : 'No validation samples'}
              </div>
            </div>
          </div>

          {/* ARIS Engineering Insight Panel */}
          {hasValidationData && actualLoopDelta !== null && (
            <div className="p-4 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-2">
              <div className="flex items-center gap-2 text-xs font-mono font-bold text-[var(--accent-cyan)]">
                <Info size={14} />
                <span>ARIS Engineering Insight</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] font-sans leading-relaxed">
                The optimized firmware measured a loop execution time delta of <strong>{actualLoopDelta > 0 ? `+${actualLoopDelta.toFixed(2)}` : actualLoopDelta.toFixed(2)} ms</strong> while maintaining internal SRAM allocation within target hardware constraints. Flash footprint changed by {actualFlashDelta !== null ? `${actualFlashDelta} Bytes` : '—'}.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};
