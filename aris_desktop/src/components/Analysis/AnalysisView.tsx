// ============================================================
// ARIS — Analysis View
// Shows static & correlated findings with filtering.
// ============================================================

import React, { useState, useMemo } from 'react';
import { AlertTriangle, AlertCircle, Info, ChevronDown, ChevronRight, Zap } from 'lucide-react';
import type { FindingRecord, FindingSeverity, RunRecord } from '../../types';

interface AnalysisViewProps {
  findings: FindingRecord[];
  activeRun: RunRecord | null;
  loading: Record<string, boolean>;
  onGenerateCandidate: (finding: FindingRecord) => void;
}

const SEVERITY_STYLES: Record<FindingSeverity, string> = {
  CRITICAL: 'text-red-400 border-red-500/40 bg-red-500/10',
  HIGH: 'text-orange-400 border-orange-500/40 bg-orange-500/10',
  MEDIUM: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
  LOW: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
  INFO: 'text-slate-400 border-slate-600 bg-slate-800/40',
};

const CORRELATION_BADGE: Record<string, string> = {
  HIGH: 'text-red-300 bg-red-900/20 border-red-700/40',
  MEDIUM: 'text-amber-300 bg-amber-900/20 border-amber-700/40',
  LOW: 'text-slate-400 bg-slate-800/40 border-slate-700',
  NONE: 'text-slate-600 bg-slate-900/20 border-slate-800',
};

export const AnalysisView: React.FC<AnalysisViewProps> = ({
  findings,
  activeRun,
  loading,
  onGenerateCandidate,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [correlationFilter, setCorrelationFilter] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return findings.filter((f) => {
      if (severityFilter !== 'ALL' && f.severity !== severityFilter) return false;
      if (correlationFilter !== 'ALL' && f.runtime_correlation !== correlationFilter) return false;
      return true;
    });
  }, [findings, severityFilter, correlationFilter]);

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
    findings.forEach((f) => { counts[f.severity] = (counts[f.severity] || 0) + 1; });
    return counts;
  }, [findings]);

  if (!activeRun) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-600">
        <AlertCircle className="w-10 h-10 mb-3 text-slate-700" />
        <p className="font-mono text-sm">Start a run to generate analysis findings.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Severity summary bar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800 shrink-0">
        {Object.entries(severityCounts).map(([sev, cnt]) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev === severityFilter ? 'ALL' : sev)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded border text-[10px] font-mono transition-all ${
              SEVERITY_STYLES[sev as FindingSeverity]
            } ${severityFilter === sev ? 'ring-1 ring-current' : 'opacity-70 hover:opacity-100'}`}
          >
            <span className="font-bold">{cnt}</span>
            <span>{sev}</span>
          </button>
        ))}
        <div className="w-px h-4 bg-slate-800" />
        <span className="text-[10px] font-mono text-slate-500">
          Correlation:
        </span>
        {['ALL', 'HIGH', 'MEDIUM', 'LOW', 'NONE'].map((c) => (
          <button
            key={c}
            onClick={() => setCorrelationFilter(c)}
            className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
              correlationFilter === c
                ? 'border-slate-500 text-slate-200 bg-slate-800'
                : 'border-slate-800 text-slate-500 hover:text-slate-300'
            }`}
          >
            {c}
          </button>
        ))}
        <div className="flex-1" />
        <span className="text-[10px] font-mono text-slate-500">
          {filtered.length} / {findings.length} findings
        </span>
      </div>

      {/* Findings list */}
      <div className="flex-1 overflow-auto">
        {findings.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 gap-2 text-slate-600">
            <p className="font-mono text-sm">No findings yet. Run analysis after collecting telemetry.</p>
          </div>
        )}
        {filtered.map((finding) => {
          const isExpanded = expandedId === finding.finding_id;
          return (
            <div key={finding.finding_id} className="border-b border-slate-800/60">
              <button
                className="w-full text-left px-4 py-3 hover:bg-slate-800/20 transition-colors flex items-start gap-3"
                onClick={() => setExpandedId(isExpanded ? null : finding.finding_id)}
              >
                {/* Severity badge */}
                <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border shrink-0 mt-0.5 ${SEVERITY_STYLES[finding.severity]}`}>
                  {finding.severity}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-mono text-slate-200">{finding.title}</span>
                    <span className="text-[9px] font-mono text-slate-500">
                      {finding.source_file}:{finding.source_line}
                    </span>
                    <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${CORRELATION_BADGE[finding.runtime_correlation]}`}>
                      ↔ {finding.runtime_correlation} correlation
                    </span>
                    <span className="text-[9px] font-mono text-slate-500">
                      {(finding.confidence * 100).toFixed(0)}% conf
                    </span>
                  </div>
                  {!isExpanded && (
                    <p className="text-[10px] font-mono text-slate-500 mt-0.5 truncate">
                      {finding.description}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[9px] font-mono text-slate-500">{finding.finding_id}</span>
                  {isExpanded ? (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                  )}
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-slate-800/40 bg-slate-900/30">
                  <div className="pt-3 space-y-3">
                    <DetailRow label="Description" value={finding.description} />
                    <DetailRow label="Recommended Action" value={finding.recommended_action} />
                    {finding.evidence && Object.keys(finding.evidence).length > 0 && (
                      <div>
                        <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-1">Evidence</p>
                        <pre className="text-[10px] font-mono text-slate-300 bg-slate-800/50 rounded p-2 overflow-auto">
                          {JSON.stringify(finding.evidence, null, 2)}
                        </pre>
                      </div>
                    )}
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={() => onGenerateCandidate(finding)}
                        disabled={loading.ai}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded hover:bg-blue-500/20 transition-colors disabled:opacity-50"
                      >
                        <Zap className="w-3.5 h-3.5" />
                        {loading.ai ? 'Generating…' : 'Generate Optimization Candidate'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const DetailRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-0.5">{label}</p>
    <p className="text-xs font-mono text-slate-300">{value}</p>
  </div>
);
