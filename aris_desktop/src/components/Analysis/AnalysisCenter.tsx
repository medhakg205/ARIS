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
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-heading font-extrabold text-[var(--text-primary)]">
              Analysis
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-bold border border-[var(--accent-amber)]/30">
              BOTTLENECKS
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 font-mono">
            {currentProjectName} · {findings.length} issues identified by ARIS
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {onRunAnalysis && (
            <button
              onClick={onRunAnalysis}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--text-muted)] text-xs font-mono text-[var(--text-primary)] transition-all shadow-sm"
            >
              <RotateCw size={13} className={loading ? 'animate-spin' : ''} />
              <span>Re-run Analysis</span>
            </button>
          )}

          <button
            onClick={() => onNavigate('optimize')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-mono font-bold shadow-sm transition-all"
          >
            <Zap size={13} />
            <span>View Recommended Optimizations</span>
          </button>
        </div>
      </div>

      {/* 2. Filters & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[var(--bg-card)] border border-[var(--border-color)] p-1 rounded-lg text-xs font-mono flex-wrap">
          <button
            onClick={() => setSeverityFilter('ALL')}
            className={`px-2.5 py-1 rounded transition-colors ${
              severityFilter === 'ALL'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            ALL ({findings.length})
          </button>
          {severityCounts.HIGH > 0 && (
            <button
              onClick={() => setSeverityFilter('HIGH')}
              className={`px-2.5 py-1 rounded transition-colors ${
                severityFilter === 'HIGH'
                  ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] font-bold'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              HIGH ({severityCounts.HIGH})
            </button>
          )}
          {severityCounts.MEDIUM > 0 && (
            <button
              onClick={() => setSeverityFilter('MEDIUM')}
              className={`px-2.5 py-1 rounded transition-colors ${
                severityFilter === 'MEDIUM'
                  ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-bold'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              MEDIUM ({severityCounts.MEDIUM})
            </button>
          )}
          {severityCounts.LOW > 0 && (
            <button
              onClick={() => setSeverityFilter('LOW')}
              className={`px-2.5 py-1 rounded transition-colors ${
                severityFilter === 'LOW'
                  ? 'bg-[var(--bg-surface)] text-[var(--text-primary)] font-bold'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              LOW ({severityCounts.LOW})
            </button>
          )}
        </div>

        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-2.5 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Filter findings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-3 py-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-color)] text-xs font-mono text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] w-full sm:w-60"
          />
        </div>
      </div>

      {/* 3. Findings Cards */}
      {findings.length === 0 ? (
        <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-3">
          <CheckCircle2 size={36} className="text-[var(--accent-green)]" />
          <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
            No Bottlenecks Detected
          </div>
          <p className="text-xs text-[var(--text-muted)] max-w-sm font-mono">
            {activeFirmware || activeIDESketch
              ? 'ARIS static and dynamic analyzers inspected the sketch and found no blocking delays or timing antipatterns.'
              : 'Load an Arduino sketch or connect hardware to execute firmware analysis.'}
          </p>
          <button
            onClick={() => onNavigate('firmware')}
            className="px-4 py-1.5 rounded-lg bg-[var(--accent-cyan)] text-white text-xs font-mono font-semibold hover:opacity-90"
          >
            Go to Firmware Workspace
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredFindings.map((finding) => (
            <div
              key={finding.finding_id}
              className="aris-card p-5 space-y-3 border-l-4 border-l-[var(--border-color)] hover:border-l-[var(--accent-cyan)] transition-colors"
            >
              {/* Finding Title & Badges */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-color)] pb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      finding.severity === 'CRITICAL' || finding.severity === 'HIGH'
                        ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/30'
                        : finding.severity === 'MEDIUM'
                        ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30'
                        : 'bg-[var(--bg-surface)] text-[var(--text-muted)]'
                    }`}
                  >
                    {finding.severity}
                  </span>
                  <h3 className="font-heading font-bold text-sm text-[var(--text-primary)]">
                    {finding.title}
                  </h3>
                </div>

                <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-muted)]">
                  <FileCode2 size={13} className="text-[var(--text-muted)]" />
                  <span>
                    {finding.source_file}:{finding.source_line}
                  </span>
                </div>
              </div>

              {/* Finding Description & Why */}
              <div className="space-y-2 text-xs font-mono">
                <div>
                  <span className="font-bold text-[var(--text-secondary)]">Why: </span>
                  <span className="text-[var(--text-muted)] leading-relaxed">
                    {finding.description}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-color)] flex items-start gap-2">
                  <span className="font-bold text-[var(--accent-cyan)] shrink-0">Recommendation: </span>
                  <span className="text-[var(--text-primary)] leading-relaxed">
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
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--border-color)] border border-[var(--border-color)] text-xs font-mono font-semibold text-[var(--text-primary)] transition-colors"
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
