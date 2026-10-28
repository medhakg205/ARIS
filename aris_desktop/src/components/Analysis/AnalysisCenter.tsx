// ============================================================
// ARIS — Analysis Center (v3.0.0)
// Simple, Focused Findings View:
// - Severity Tag (HIGH, MEDIUM, LOW)
// - Location (file:line)
// - Why this causes performance/latency issues
// - Concrete practical recommendation
// - Action to inspect optimization
// ============================================================

import React, { useState, useMemo } from 'react';
import {
  Search,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Filter,
  Zap,
  ArrowRight,
  FileCode2,
  RotateCw,
  Cpu,
} from 'lucide-react';
import { FindingRecord, FindingSeverity, FirmwareRecord, IDESketchInfo } from '../../types';

interface AnalysisCenterProps {
  findings: FindingRecord[];
  activeFirmware: FirmwareRecord | null;
  activeIDESketch: IDESketchInfo | null;
  onGenerateCandidate?: (finding: FindingRecord) => void;
  onNavigate: (tab: string) => void;
  onRunAnalysis?: () => Promise<void>;
  loading?: boolean;
}

type SeverityFilter = 'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export const AnalysisCenter: React.FC<AnalysisCenterProps> = ({
  findings,
  activeFirmware,
  activeIDESketch,
  onGenerateCandidate,
  onNavigate,
  onRunAnalysis,
  loading = false,
}) => {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('ALL');
  const [search, setSearch] = useState('');
  const [hasExecutedAnalysis, setHasExecutedAnalysis] = useState(findings.length > 0);

  React.useEffect(() => {
    if (findings.length > 0) {
      setHasExecutedAnalysis(true);
    }
  }, [findings.length]);

  const handleRunAnalysis = async () => {
    if (onRunAnalysis) {
      setHasExecutedAnalysis(true);
      await onRunAnalysis();
    }
  };

  const currentProjectName = activeIDESketch?.name || activeFirmware?.name || 'Current Project';

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter !== 'ALL' && f.severity !== severityFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          f.title.toLowerCase().includes(q) ||
          f.description.toLowerCase().includes(q) ||
          f.source_file.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [findings, severityFilter, search]);

  const severityCounts = useMemo(() => {
    return {
      CRITICAL: findings.filter((f) => f.severity === 'CRITICAL').length,
      HIGH: findings.filter((f) => f.severity === 'HIGH').length,
      MEDIUM: findings.filter((f) => f.severity === 'MEDIUM').length,
      LOW: findings.filter((f) => f.severity === 'LOW').length,
    };
  }, [findings]);

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 md:p-6 space-y-6 select-none bg-[var(--bg-app)]">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-heading font-extrabold text-[var(--text-primary)]">
              Analysis
            </h1>
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono px-2.5 py-0.5 rounded-full font-semibold border bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-amber)]" />
              BOTTLENECK DETECTION
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-1 font-sans">
            {currentProjectName} · {findings.length} performance {findings.length === 1 ? 'issue' : 'issues'} identified by static and dynamic profiling
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          {onRunAnalysis && (
            <button
              onClick={handleRunAnalysis}
              disabled={loading}
              className="aris-btn-secondary flex items-center gap-1.5 text-xs"
            >
              <RotateCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>Re-run Analysis</span>
            </button>
          )}

          <button
            onClick={() => onNavigate('optimize')}
            className="aris-btn-primary flex items-center gap-1.5 text-xs"
          >
            <Zap size={13} />
            <span>View Recommended Optimizations</span>
          </button>
        </div>
      </div>

      {/* 2. Filters & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[var(--bg-surface)] border border-[var(--border-color)] p-1 rounded-xl text-xs font-sans flex-wrap">
          <button
            onClick={() => setSeverityFilter('ALL')}
            className={`px-3 py-1 rounded-lg text-xs transition-colors ${
              severityFilter === 'ALL'
                ? 'bg-[var(--bg-card)] text-[var(--text-primary)] font-semibold shadow-xs'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            All ({findings.length})
          </button>
          {severityCounts.HIGH > 0 && (
            <button
              onClick={() => setSeverityFilter('HIGH')}
              className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                severityFilter === 'HIGH'
                  ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] font-semibold border border-[var(--accent-red)]/30'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              High ({severityCounts.HIGH})
            </button>
          )}
          {severityCounts.MEDIUM > 0 && (
            <button
              onClick={() => setSeverityFilter('MEDIUM')}
              className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                severityFilter === 'MEDIUM'
                  ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-semibold border border-[var(--accent-amber)]/30'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Medium ({severityCounts.MEDIUM})
            </button>
          )}
          {severityCounts.LOW > 0 && (
            <button
              onClick={() => setSeverityFilter('LOW')}
              className={`px-3 py-1 rounded-lg text-xs transition-colors ${
                severityFilter === 'LOW'
                  ? 'bg-[var(--bg-card)] text-[var(--text-primary)] font-semibold shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Low ({severityCounts.LOW})
            </button>
          )}
        </div>

        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-2.5 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Search findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-xs font-sans text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] w-full sm:w-60 shadow-xs"
          />
        </div>
      </div>

      {/* 3. Staged Progress Loading State or Findings List */}
      {loading ? (
        <div className="aris-card p-8 max-w-lg mx-auto w-full space-y-5 shadow-sm my-8">
          <div className="flex items-center gap-3 border-b border-[var(--border-color)] pb-3">
            <RotateCw size={18} className="text-[var(--accent-cyan)] animate-spin" />
            <div>
              <h3 className="font-heading font-bold text-sm text-[var(--text-primary)]">
                Analyzing Firmware
              </h3>
              <p className="text-xs text-[var(--text-muted)] font-sans">
                Static AST inspection and deterministic rule evaluation
              </p>
            </div>
          </div>

          <div className="space-y-3 text-xs font-sans">
            <div className="flex items-center gap-2.5 text-emerald-400">
              <CheckCircle2 size={14} className="shrink-0" />
              <span>Loading sketch source code</span>
            </div>
            <div className="flex items-center gap-2.5 text-emerald-400">
              <CheckCircle2 size={14} className="shrink-0" />
              <span>Resolving microcontroller hardware profile</span>
            </div>
            <div className="flex items-center gap-2.5 text-[var(--accent-cyan)] font-semibold">
              <span className="w-3.5 h-3.5 rounded-full border-2 border-[var(--accent-cyan)] border-t-transparent animate-spin shrink-0" />
              <span>Static AST &amp; blocking delay analysis</span>
            </div>
            <div className="flex items-center gap-2.5 text-[var(--text-muted)]">
              <span className="w-3.5 h-3.5 rounded-full border border-[var(--border-color)] shrink-0" />
              <span>Runtime telemetry correlation</span>
            </div>
            <div className="flex items-center gap-2.5 text-[var(--text-muted)]">
              <span className="w-3.5 h-3.5 rounded-full border border-[var(--border-color)] shrink-0" />
              <span>Synthesizing non-blocking optimization proposals</span>
            </div>
          </div>
        </div>
      ) : findings.length === 0 ? (
        hasExecutedAnalysis ? (
          <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-center text-[var(--accent-green)] shadow-sm">
              <CheckCircle2 size={24} />
            </div>
            <div className="font-heading font-bold text-base text-[var(--text-primary)]">
              No Optimization Findings Detected
            </div>
            <p className="text-xs text-[var(--text-muted)] max-w-sm font-sans leading-relaxed">
              ARIS static and dynamic analyzers inspected {currentProjectName} and verified zero blocking delays or timing antipatterns.
            </p>
            {onRunAnalysis && (
              <button
                onClick={handleRunAnalysis}
                className="aris-btn-secondary text-xs mt-2"
              >
                Re-run Analysis
              </button>
            )}
          </div>
        ) : (
          <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-center justify-center text-[var(--text-muted)] shadow-sm">
              <Search size={24} />
            </div>
            <div className="font-heading font-bold text-base text-[var(--text-primary)]">
              Firmware Analysis Pending
            </div>
            <p className="text-xs text-[var(--text-muted)] max-w-sm font-sans leading-relaxed">
              {activeFirmware || activeIDESketch
                ? `Ready to analyze ${currentProjectName}. Execute analysis to detect blocking delays, memory pressure, and timing bottlenecks.`
                : 'Load an Arduino sketch or connect hardware to execute firmware analysis.'}
            </p>
            <div className="flex items-center gap-2.5 pt-2">
              {onRunAnalysis && (activeFirmware || activeIDESketch) && (
                <button
                  onClick={handleRunAnalysis}
                  className="aris-btn-primary text-xs"
                >
                  Run Firmware Analysis
                </button>
              )}
              <button
                onClick={() => onNavigate('firmware')}
                className="aris-btn-secondary text-xs"
              >
                Open Firmware Workspace
              </button>
            </div>
          </div>
        )
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((finding) => (
            <div
              key={finding.finding_id}
              className="aris-card p-4 space-y-3 hover:border-[var(--accent-cyan)] transition-colors"
            >
              {/* Finding Title & Badges */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-color)] pb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[var(--bg-surface)] border border-[var(--border-color)] text-[var(--text-secondary)] font-medium">
                    {finding.finding_id || finding.rule_id || 'FIND-001'}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded-full font-bold ${
                      finding.severity === 'CRITICAL' || finding.severity === 'HIGH'
                        ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/30'
                        : finding.severity === 'MEDIUM'
                        ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30'
                        : 'bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)]'
                    }`}
                  >
                    <span className={`w-1 h-1 rounded-full ${
                      finding.severity === 'CRITICAL' || finding.severity === 'HIGH'
                        ? 'bg-[var(--accent-red)]'
                        : finding.severity === 'MEDIUM'
                        ? 'bg-[var(--accent-amber)]'
                        : 'bg-[var(--text-muted)]'
                    }`} />
                    {finding.severity}
                  </span>
                  <h3 className="font-heading font-bold text-sm text-[var(--text-primary)]">
                    {finding.title}
                  </h3>
                </div>

                <div className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-muted)]">
                  <FileCode2 size={13} className="text-[var(--text-muted)]" />
                  <span>
                    {finding.source_file}:{finding.source_line}
                  </span>
                </div>
              </div>

              {/* Finding Description & Explanation */}
              <div className="space-y-2 text-xs">
                <p className="font-sans text-[var(--text-secondary)] leading-relaxed">
                  {finding.description}
                </p>

                <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-start gap-2">
                  <span className="font-sans font-semibold text-[var(--accent-cyan)] shrink-0">Opportunity:</span>
                  <span className="font-sans text-[var(--text-primary)] leading-relaxed">
                    {finding.recommended_action}
                  </span>
                </div>
              </div>

              {/* Action Button */}
              <div className="flex justify-end pt-1">
                <button
                  onClick={() => {
                    if (onGenerateCandidate) {
                      onGenerateCandidate(finding);
                    }
                    onNavigate('optimize');
                  }}
                  className="aris-btn-secondary flex items-center gap-1.5 text-xs"
                >
                  <Zap size={13} className="text-[var(--accent-cyan)]" />
                  <span>Inspect Optimization Candidate →</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
