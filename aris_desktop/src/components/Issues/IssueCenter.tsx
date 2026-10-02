// ============================================================
// ARIS — Issue Center (v3.0.0)
// Categorized Static & Runtime Diagnostics Problem Organizer
// ============================================================

import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Filter,
  Zap,
  ArrowRight,
  FileCode2,
  Cpu,
} from 'lucide-react';
import { FindingRecord } from '../../types';

interface IssueCenterProps {
  findings: FindingRecord[];
  onGenerateCandidate?: (finding: FindingRecord) => void;
  onNavigate: (tab: string) => void;
}

type SeverityFilter = 'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export const IssueCenter: React.FC<IssueCenterProps> = ({
  findings,
  onGenerateCandidate,
  onNavigate,
}) => {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('ALL');
  const [search, setSearch] = useState('');

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter !== 'ALL' && f.severity !== severityFilter) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        return (
          f.title.toLowerCase().includes(q) ||
          f.description.toLowerCase().includes(q) ||
          f.rule_id.toLowerCase().includes(q) ||
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
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[var(--border-color)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-heading font-bold text-[var(--text-primary)]">
              Issue Center
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-semibold">
              DIAGNOSTICS & ANTIPATTERNS
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 font-mono">
            Static AST code findings correlated with physical hardware telemetry
          </p>
        </div>

        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[var(--bg-card)] border border-[var(--border-color)] p-1 rounded-lg text-xs font-mono">
          <button
            onClick={() => setSeverityFilter('ALL')}
            className={`px-2 py-0.5 rounded ${
              severityFilter === 'ALL'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            ALL ({findings.length})
          </button>
          <button
            onClick={() => setSeverityFilter('CRITICAL')}
            className={`px-2 py-0.5 rounded ${
              severityFilter === 'CRITICAL'
                ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            CRITICAL ({severityCounts.CRITICAL})
          </button>
          <button
            onClick={() => setSeverityFilter('HIGH')}
            className={`px-2 py-0.5 rounded ${
              severityFilter === 'HIGH'
                ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            HIGH ({severityCounts.HIGH})
          </button>
          <button
            onClick={() => setSeverityFilter('MEDIUM')}
            className={`px-2 py-0.5 rounded ${
              severityFilter === 'MEDIUM'
                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            MED ({severityCounts.MEDIUM})
          </button>
        </div>
      </div>

      {/* Issues List */}
      {filteredFindings.length === 0 ? (
        <div className="aris-card p-12 text-center flex flex-col items-center justify-center space-y-2">
          <CheckCircle2 size={36} className="text-[var(--accent-green)] opacity-80" />
          <div className="font-heading font-bold text-sm text-[var(--text-primary)]">
            No Active Issues Detected
          </div>
          <p className="text-xs text-[var(--text-muted)] max-w-sm">
            Firmware AST and runtime telemetry conform to 8-bit AVR hardware guidelines.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((finding) => (
            <div
              key={finding.finding_id}
              className="aris-card p-4 space-y-3 aris-card-hover"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold ${
                      finding.severity === 'CRITICAL'
                        ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/20'
                        : finding.severity === 'HIGH'
                        ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/20'
                        : 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/20'
                    }`}
                  >
                    {finding.severity}
                  </span>
                  <span className="font-heading font-bold text-sm text-[var(--text-primary)]">
                    {finding.title}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono text-[var(--text-muted)]">
                  <span>Rule: {finding.rule_id}</span>
                  <span>{finding.source_file}:{finding.source_line}</span>
                </div>
              </div>

              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                {finding.description}
              </p>

              <div className="p-2.5 rounded bg-[var(--bg-surface)] border border-[var(--border-color)] flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
                <div>
                  <span className="text-[var(--text-muted)]">Remediation: </span>
                  <span className="text-[var(--text-primary)] font-medium">
                    {finding.recommended_action}
                  </span>
                </div>

                {onGenerateCandidate && (
                  <button
                    onClick={() => onGenerateCandidate(finding)}
                    className="flex items-center gap-1.5 px-3 py-1 rounded bg-[var(--accent-cyan)] hover:opacity-90 text-white text-xs font-semibold shadow-sm transition-opacity shrink-0"
                  >
                    <Zap size={12} />
                    <span>Generate Candidate</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
