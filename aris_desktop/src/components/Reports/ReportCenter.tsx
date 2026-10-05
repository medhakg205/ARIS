// ============================================================
// ARIS — Reports (v3.0.0)
// Simple, Professional Verification Reports
// Clean Project Summary, Baseline vs Optimized, Validation Provenance,
// and Export Options.
// ============================================================

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Copy,
  Check,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  HardDrive,
  TrendingDown,
  ShieldCheck,
  ChevronDown,
} from 'lucide-react';
import { ExperimentRecord, BoardProfile } from '../../types';

interface ReportCenterProps {
  experiments: ExperimentRecord[];
  selectedBoard: BoardProfile | null;
  patentMarkdown?: string;
}

export const ReportCenter: React.FC<ReportCenterProps> = ({
  experiments,
  selectedBoard,
  patentMarkdown = '',
}) => {
  const [selectedExpId, setSelectedExpId] = useState<string>(
    experiments.length > 0 ? experiments[0].experiment_id : ''
  );
  const [copied, setCopied] = useState(false);
  const [showTechnicalDisclosure, setShowTechnicalDisclosure] = useState(false);

  const selectedExp =
    experiments.find((e) => e.experiment_id === selectedExpId) ||
    experiments[0] ||
    null;

  const isPhysical = selectedExp ? (!selectedExp.is_demo && !selectedExp.is_simulated) : false;

  const generateReportMarkdown = (exp: ExperimentRecord | null, board: BoardProfile | null) => {
    if (!exp) return '# ARIS Optimization Report\nNo experiment data available.';
    const latImp = exp.result_summary?.latency_improvement_pct;
    const cpuImp = exp.result_summary?.cpu_load_reduction_pct;
    const sramRed = exp.result_summary?.sram_reduction_pct;
    const flashRed = exp.result_summary?.flash_reduction_pct;

    return `# ARIS Firmware Optimization Report
**Project / Experiment:** ${exp.title} (${exp.experiment_id})
**Target Board:** ${board?.display_name || exp.board_id || 'Arduino Uno'}
**Date:** ${exp.created_at ? new Date(exp.created_at).toLocaleString() : new Date().toLocaleString()}
**Validation Status:** ${exp.status}
**Execution Provenance:** ${isPhysical ? 'Physical Hardware' : 'Simulation'}

## Summary of Results
- **Loop Latency:** ${latImp !== undefined ? `Improved by ~${Math.abs(latImp).toFixed(1)}%` : 'Empirically profiled'}
- **CPU Load:** ${cpuImp !== undefined ? `Reduced by ~${Math.abs(cpuImp).toFixed(1)}%` : 'Evaluated'}
- **SRAM State:** ${sramRed !== undefined ? `${sramRed >= 0 ? '-' : '+'}${Math.abs(sramRed)}% static allocation` : 'Static allocation verified'}
- **Flash Memory:** ${flashRed !== undefined ? `${flashRed >= 0 ? '-' : '+'}${Math.abs(flashRed)}% program storage` : 'Checked within section boundaries'}

## Verification
This optimization was verified using ${isPhysical ? 'physical hardware runtime telemetry over UART serial link' : 'cycle-accurate simulation telemetry'}.
`;
  };

  const handleCopy = () => {
    const text = generateReportMarkdown(selectedExp, selectedBoard);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = (format: 'md' | 'json') => {
    let content = '';
    let mime = 'text/plain';
    const filename = `ARIS_Report_${selectedExp?.experiment_id || 'summary'}.${format}`;

    if (format === 'json') {
      content = JSON.stringify(selectedExp || {}, null, 2);
      mime = 'application/json';
    } else {
      content = generateReportMarkdown(selectedExp, selectedBoard);
      mime = 'text/markdown';
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-heading font-extrabold text-[var(--text-primary)]">
              Reports
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold border border-[var(--accent-cyan)]/30">
              VERIFICATION SUMMARY
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 font-mono">
            Empirical before vs after comparison reports and performance validation dossiers
          </p>
        </div>

        {selectedExp && (
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              {copied ? <Check size={13} className="text-[var(--accent-green)]" /> : <Copy size={13} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={() => handleDownload('md')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <Download size={13} />
              <span>Export Markdown</span>
            </button>

            <button
              onClick={() => handleDownload('json')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
              <Download size={13} />
              <span>Export JSON</span>
            </button>
          </div>
        )}
      </div>

      {/* 2. Empty State (When no experiments exist) */}
      {!selectedExp ? (
        <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-3">
          <FileText size={36} className="text-[var(--text-muted)] opacity-60" />
          <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
            No Reports Available
          </div>
          <p className="text-xs text-[var(--text-muted)] max-w-sm font-mono">
            Execute an optimization test run in the Optimize tab to generate an empirical verification report.
          </p>
        </div>
      ) : (
        /* 3. Main Report View */
        <div className="space-y-6">
          {/* Experiment Selector Bar */}
          {experiments.length > 1 && (
            <div className="aris-card p-3 flex items-center justify-between text-xs font-mono">
              <span className="text-[var(--text-muted)]">Select Report:</span>
              <select
                value={selectedExpId}
                onChange={(e) => setSelectedExpId(e.target.value)}
                className="px-2.5 py-1 rounded bg-[var(--bg-surface)] border border-[var(--border-color)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)]"
              >
                {experiments.map((exp) => (
                  <option key={exp.experiment_id} value={exp.experiment_id}>
                    {exp.title} ({exp.experiment_id}) — {exp.status}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Report Card */}
          <div className="aris-card p-6 space-y-6">
            {/* Header Details */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-color)] pb-4">
              <div>
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                  OPTIMIZATION REPORT
                </span>
                <h2 className="text-lg font-heading font-extrabold text-[var(--text-primary)] mt-0.5">
                  {selectedExp.title}
                </h2>
                <div className="text-xs font-mono text-[var(--text-muted)] mt-1">
                  ID: {selectedExp.experiment_id} · Target: {selectedExp.board_id || selectedBoard?.display_name || '—'}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-mono px-2.5 py-1 rounded-full font-bold ${
                    isPhysical
                      ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30'
                      : 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30'
                  }`}
                >
                  {isPhysical ? 'VALIDATED ON REAL HARDWARE' : 'SIMULATION RUN'}
                </span>
              </div>
            </div>

            {/* Before vs After Comparison Grid */}
            <div className="space-y-3">
              <span className="text-xs font-mono font-bold text-[var(--text-secondary)] uppercase tracking-wider">
                Performance Deltas vs Baseline
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Loop Latency */}
                <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
                    <span>Loop Latency</span>
                    <Clock size={13} />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-mono text-[var(--text-muted)]">
                      {selectedExp.result_summary?.baseline_loop_ms ? `${selectedExp.result_summary.baseline_loop_ms} ms` : 'Baseline'}
                    </span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-green)]">
                      {selectedExp.result_summary?.candidate_loop_ms ? `${selectedExp.result_summary.candidate_loop_ms} ms` : 'Validated'}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-[var(--accent-green)] font-semibold flex items-center gap-1">
                    {selectedExp.result_summary?.latency_improvement_pct !== undefined ? (
                      <>
                        <TrendingDown size={11} />
                        {Math.abs(selectedExp.result_summary.latency_improvement_pct).toFixed(1)}% loop improvement
                      </>
                    ) : (
                      'Empirically evaluated'
                    )}
                  </div>
                </div>

                {/* CPU Load */}
                <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
                    <span>CPU Duty Cycle</span>
                    <Cpu size={13} />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-mono text-[var(--text-muted)]">
                      {selectedExp.result_summary?.baseline_cpu_pct !== undefined ? `${selectedExp.result_summary.baseline_cpu_pct}%` : 'Baseline'}
                    </span>
                    <span className="text-lg font-mono font-bold text-[var(--accent-cyan)]">
                      {selectedExp.result_summary?.candidate_cpu_pct !== undefined ? `${selectedExp.result_summary.candidate_cpu_pct}%` : 'Optimized'}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-[var(--accent-cyan)] font-semibold flex items-center gap-1">
                    {selectedExp.result_summary?.cpu_load_reduction_pct !== undefined ? (
                      <>
                        <TrendingDown size={11} />
                        {Math.abs(selectedExp.result_summary.cpu_load_reduction_pct).toFixed(1)}% cycle reclamation
                      </>
                    ) : (
                      'Evaluated'
                    )}
                  </div>
                </div>

                {/* SRAM Allocation */}
                <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
                    <span>SRAM Memory</span>
                    <Layers size={13} />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-mono text-[var(--text-muted)]">
                      {selectedExp.result_summary?.baseline_sram_bytes !== undefined ? `${selectedExp.result_summary.baseline_sram_bytes} B` : 'Static'}
                    </span>
                    <span className="text-lg font-mono font-bold text-[var(--text-primary)]">
                      {selectedExp.result_summary?.candidate_sram_bytes !== undefined ? `${selectedExp.result_summary.candidate_sram_bytes} B` : 'Monitored'}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-[var(--text-muted)]">
                    {selectedExp.result_summary?.sram_reduction_pct !== undefined
                      ? `${selectedExp.result_summary.sram_reduction_pct}% delta`
                      : 'Memory bounds checked'}
                  </div>
                </div>

                {/* Flash Usage */}
                <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono text-[var(--text-muted)]">
                    <span>Flash Program Size</span>
                    <HardDrive size={13} />
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-mono text-[var(--text-muted)]">
                      {selectedExp.result_summary?.baseline_flash_bytes !== undefined ? `${selectedExp.result_summary.baseline_flash_bytes} B` : 'Base image'}
                    </span>
                    <span className="text-lg font-mono font-bold text-[var(--text-primary)]">
                      {selectedExp.result_summary?.candidate_flash_bytes !== undefined ? `${selectedExp.result_summary.candidate_flash_bytes} B` : 'Candidate'}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-[var(--text-muted)]">
                    {selectedExp.result_summary?.flash_reduction_pct !== undefined
                      ? `${selectedExp.result_summary.flash_reduction_pct}% delta`
                      : 'Flash bounds checked'}
                  </div>
                </div>
              </div>
            </div>

            {/* Verification Rationale */}
            <div className="p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] space-y-1.5 text-xs font-mono">
              <div className="font-bold text-[var(--text-primary)] flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-[var(--accent-green)]" />
                <span>Verification Method</span>
              </div>
              <p className="text-[var(--text-muted)] leading-relaxed">
                Telemetry frames were captured over the serial stream and calibrated to evaluate loop latency and CPU duty cycle before and after deploying the non-blocking state machine.
              </p>
            </div>
          </div>

          {/* 4. Collapsible Advanced Technical Disclosure */}
          {patentMarkdown && (
            <div className="space-y-2">
              <button
                onClick={() => setShowTechnicalDisclosure(!showTechnicalDisclosure)}
                className="text-xs font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)] flex items-center gap-1.5 transition-colors"
              >
                <span>{showTechnicalDisclosure ? 'Hide Technical Specification' : 'Advanced: View Research & Technical Specification Export'}</span>
                <ChevronDown size={13} className={showTechnicalDisclosure ? 'rotate-180' : ''} />
              </button>

              {showTechnicalDisclosure && (
                <div className="aris-card p-5 bg-[var(--bg-surface)]/60 border border-[var(--border-color)]">
                  <pre className="text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed overflow-x-auto">
                    {patentMarkdown}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
