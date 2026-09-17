// ============================================================
// ARIS — Optimization View
// Shows one optimization candidate at a time with full detail:
// Problem, Before/After code, Rationale, Hardware consideration,
// Expected Effect (PREDICTED), Risk, Confidence.
// Requires explicit human approval before ANY action.
// ============================================================

import React, { useState } from 'react';
import { CheckCircle, XCircle, Eye, AlertTriangle, Zap, ChevronLeft, ChevronRight } from 'lucide-react';
import type { OptimizationCandidate } from '../../types';
import { MetricBadge } from '../common/MetricBadge';

interface OptimizationViewProps {
  optimizations: OptimizationCandidate[];
  loading: Record<string, boolean>;
  onApprove: (id: string) => Promise<OptimizationCandidate | null>;
  onReject: (id: string) => Promise<OptimizationCandidate | null>;
  onCreateExperiment: (title: string, optId: string) => Promise<unknown>;
}

const RISK_STYLES = {
  LOW: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
  MEDIUM: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
  HIGH: 'text-red-400 border-red-500/40 bg-red-500/10',
};

const STATUS_STYLES: Record<string, string> = {
  PROPOSED: 'text-slate-400 border-slate-600',
  APPROVED: 'text-emerald-400 border-emerald-600',
  BUILDING: 'text-amber-400 border-amber-600',
  TESTING: 'text-cyan-400 border-cyan-600',
  VALIDATED: 'text-emerald-400 border-emerald-500',
  REJECTED: 'text-red-400 border-red-600',
  ROLLED_BACK: 'text-orange-400 border-orange-600',
  FAILED: 'text-red-500 border-red-700',
};

export const OptimizationView: React.FC<OptimizationViewProps> = ({
  optimizations,
  loading,
  onApprove,
  onReject,
  onCreateExperiment,
}) => {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [confirmAction, setConfirmAction] = useState<'approve' | 'reject' | null>(null);

  if (optimizations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-3">
        <Zap className="w-10 h-10 text-slate-700" />
        <p className="font-mono text-sm">No optimization candidates yet.</p>
        <p className="font-mono text-xs text-slate-700">Go to Analysis → select a finding → Generate Optimization Candidate.</p>
      </div>
    );
  }

  const candidate = optimizations[Math.min(selectedIdx, optimizations.length - 1)];
  if (!candidate) return null;

  const isApproving = loading[`approve_${candidate.optimization_id}`];
  const isRejecting = loading[`reject_${candidate.optimization_id}`];

  const handleApprove = async () => {
    setConfirmAction(null);
    const result = await onApprove(candidate.optimization_id);
    if (result?.status === 'APPROVED') {
      await onCreateExperiment(
        `Experiment: ${candidate.title}`,
        candidate.optimization_id,
      );
    }
  };

  const handleReject = async () => {
    setConfirmAction(null);
    await onReject(candidate.optimization_id);
  };

  const expectedEffectEntries = Object.entries(candidate.expected_effect || {}).filter(
    ([k]) => k !== 'classification' && k !== 'hardware_notes',
  );

  return (
    <div className="flex h-full overflow-hidden">
      {/* Sidebar: candidate list */}
      <div className="w-64 shrink-0 border-r border-slate-800 flex flex-col">
        <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-3 border-b border-slate-800">
          Candidates ({optimizations.length})
        </p>
        <div className="flex-1 overflow-auto">
          {optimizations.map((opt, idx) => (
            <button
              key={opt.optimization_id}
              onClick={() => { setSelectedIdx(idx); setConfirmAction(null); }}
              className={`w-full text-left px-4 py-3 border-b border-slate-800/50 transition-colors hover:bg-slate-800/30 ${
                idx === selectedIdx ? 'bg-slate-800/50 border-l-2 border-l-blue-500' : ''
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${STATUS_STYLES[opt.status]}`}>
                  {opt.status}
                </span>
                <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${RISK_STYLES[opt.risk]}`}>
                  {opt.risk}
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-300 leading-tight">{opt.title}</p>
              <p className="text-[9px] font-mono text-slate-500 mt-0.5">{opt.optimization_id}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Main detail panel */}
      <div className="flex-1 overflow-auto p-5 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-mono font-semibold text-slate-100">{candidate.title}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] font-mono text-slate-500">{candidate.optimization_id}</span>
              <span className="text-[10px] font-mono text-slate-600">·</span>
              <span className="text-[10px] font-mono text-slate-500">finding: {candidate.finding_id}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <span className={`text-xs font-mono px-2 py-1 rounded border ${STATUS_STYLES[candidate.status]}`}>
              {candidate.status}
            </span>
            <span className={`text-xs font-mono px-2 py-1 rounded border ${RISK_STYLES[candidate.risk]}`}>
              RISK: {candidate.risk}
            </span>
          </div>
        </div>

        {/* Problem */}
        <Section label="PROBLEM">
          <p className="text-sm font-mono text-slate-300">{candidate.problem}</p>
          <p className="text-[10px] font-mono text-slate-500 mt-1">
            {candidate.source_location.file}:{candidate.source_location.line}
          </p>
        </Section>

        {/* Before / After */}
        <div className="grid grid-cols-2 gap-4">
          <Section label="BEFORE CODE">
            <pre className="text-xs font-mono text-red-300 bg-red-900/10 border border-red-900/30 rounded p-3 overflow-auto leading-relaxed whitespace-pre-wrap">
              {candidate.before_code}
            </pre>
          </Section>
          <Section label="AFTER CODE">
            <pre className="text-xs font-mono text-emerald-300 bg-emerald-900/10 border border-emerald-900/30 rounded p-3 overflow-auto leading-relaxed whitespace-pre-wrap">
              {candidate.after_code}
            </pre>
          </Section>
        </div>

        {/* Why This Helps */}
        <Section label="WHY THIS HELPS">
          <p className="text-sm font-mono text-slate-300">{candidate.reason}</p>
        </Section>

        {/* Hardware Consideration */}
        <Section label="HARDWARE CONSIDERATION">
          <p className="text-sm font-mono text-slate-300">{candidate.hardware_consideration}</p>
        </Section>

        {/* Predicted result */}
        <Section label="EXPECTED EFFECT — PREDICTED BEFORE HARDWARE TEST">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {expectedEffectEntries.map(([key, val]) => (
              <MetricBadge
                key={key}
                label={key.replace(/_/g, ' ')}
                value={typeof val === 'number' ? val : String(val)}
                unit=""
                classification="PREDICTED"
                compact
              />
            ))}
          </div>
          {(candidate.expected_effect as Record<string, unknown>).hardware_notes ? (
            <p className="text-[10px] font-mono text-purple-400/70 mt-2">
              {String((candidate.expected_effect as Record<string, unknown>).hardware_notes)}
            </p>
          ) : null}
        </Section>

        {/* Confidence */}
        <Section label="CONFIDENCE">
          <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-slate-800 rounded-full max-w-xs">
              <div
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${candidate.confidence * 100}%` }}
              />
            </div>
            <span className="text-sm font-mono text-slate-200">{(candidate.confidence * 100).toFixed(0)}%</span>
          </div>
        </Section>

        {/* Action Buttons — mandatory human approval */}
        {candidate.status === 'PROPOSED' && (
          <div className="bg-slate-900/60 border border-slate-800 rounded p-4">
            <p className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-3">
              Human Approval Required — AI-generated code is never automatically flashed to hardware
            </p>
            {confirmAction === null ? (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setConfirmAction('approve')}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-mono bg-emerald-500/10 border border-emerald-500/40 text-emerald-400 rounded hover:bg-emerald-500/20 transition-colors"
                >
                  <CheckCircle className="w-4 h-4" /> Approve &amp; Create Experiment
                </button>
                <button
                  onClick={() => setConfirmAction('reject')}
                  className="flex items-center gap-2 px-4 py-2 text-xs font-mono bg-red-500/10 border border-red-500/40 text-red-400 rounded hover:bg-red-500/20 transition-colors"
                >
                  <XCircle className="w-4 h-4" /> Reject
                </button>
              </div>
            ) : confirmAction === 'approve' ? (
              <div className="flex items-center gap-3">
                <p className="text-xs font-mono text-amber-400">
                  Confirm: approve this candidate and initiate the closed-loop experiment?
                </p>
                <button
                  onClick={handleApprove}
                  disabled={isApproving}
                  className="px-3 py-1.5 text-xs font-mono bg-emerald-500/20 border border-emerald-500/50 text-emerald-300 rounded hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
                >
                  {isApproving ? 'Approving…' : 'Confirm Approve'}
                </button>
                <button onClick={() => setConfirmAction(null)} className="text-xs font-mono text-slate-500 hover:text-slate-300">
                  Cancel
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <p className="text-xs font-mono text-red-400">Confirm: reject this candidate?</p>
                <button
                  onClick={handleReject}
                  disabled={isRejecting}
                  className="px-3 py-1.5 text-xs font-mono bg-red-500/20 border border-red-500/50 text-red-300 rounded hover:bg-red-500/30 transition-colors disabled:opacity-50"
                >
                  {isRejecting ? 'Rejecting…' : 'Confirm Reject'}
                </button>
                <button onClick={() => setConfirmAction(null)} className="text-xs font-mono text-slate-500 hover:text-slate-300">
                  Cancel
                </button>
              </div>
            )}
          </div>
        )}

        {candidate.status !== 'PROPOSED' && (
          <div className="bg-slate-900/40 border border-slate-800/50 rounded p-3">
            <p className="text-xs font-mono text-slate-400">
              This candidate is in status <span className="font-semibold text-slate-200">{candidate.status}</span>.
              {candidate.status === 'APPROVED' && ' An experiment has been created. View progress in Experiments tab.'}
              {candidate.status === 'VALIDATED' && ' Closed-loop validation completed. View results in Validation tab.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const Section: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div>
    <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-2">{label}</p>
    {children}
  </div>
);
