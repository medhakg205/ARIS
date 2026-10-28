// ============================================================
// ARIS Common — MetricBadge
// Shows a metric value + unit + veracity classification badge.
// MEASURED = emerald, ESTIMATED = amber, DERIVED = cyan, PREDICTED = purple
// Never presents PREDICTED values as MEASURED.
// ============================================================

import React from 'react';
import type { MetricClassification } from '../../types';

const CLASSIFICATION_STYLES: Record<MetricClassification, string> = {
  MEASURED: 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30',
  ESTIMATED: 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30',
  DERIVED: 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border-[var(--accent-cyan)]/30',
  PREDICTED: 'bg-[var(--accent-purple-bg)] text-[var(--accent-purple)] border-[var(--accent-purple)]/30',
};

interface MetricBadgeProps {
  label: string;
  value: number | string;
  unit?: string;
  classification: MetricClassification;
  confidence?: number;
  secondary?: string;
  compact?: boolean;
}

export const MetricBadge: React.FC<MetricBadgeProps> = ({
  label,
  value,
  unit,
  classification,
  confidence,
  secondary,
  compact = false,
}) => {
  const cls = CLASSIFICATION_STYLES[classification];

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1">
        <span className="text-xs font-mono text-[var(--text-muted)] uppercase tracking-wider w-28 shrink-0">
          {label}
        </span>
        <span className="text-sm font-mono text-[var(--text-primary)] tabular-nums">
          {value}
          {unit && <span className="text-[var(--text-muted)] ml-0.5 text-xs">{unit}</span>}
        </span>
        <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${cls} ml-auto`}>
          {classification}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--border-hover)] transition-all duration-200 rounded-xl p-2.5 sm:p-3 flex flex-col justify-between group shadow-sm">
      <div className="flex items-center justify-between gap-1.5">
        <span className="text-[10px] font-sans font-medium text-[var(--text-muted)] tracking-wider uppercase truncate">
          {label}
        </span>
        <span className={`text-[8.5px] font-sans font-semibold px-1.5 py-0.5 rounded-full border ${cls} shrink-0`}>
          {classification}
        </span>
      </div>

      <div className="mt-1.5 flex items-baseline gap-1">
        <span className="text-lg sm:text-xl font-bold font-mono text-[var(--text-primary)] tabular-nums tracking-tight">
          {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
        </span>
        {unit && <span className="text-[11px] font-sans font-medium text-[var(--text-muted)]">{unit}</span>}
      </div>

      {secondary && (
        <span className="text-[9px] text-[var(--text-muted)] font-sans mt-0.5 truncate">{secondary}</span>
      )}

      {confidence !== undefined && (
        <div className="flex items-center gap-1.5 mt-1.5 pt-1 border-t border-[var(--border-color)]">
          <div className="flex-1 h-1 bg-[var(--bg-app)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--accent-cyan)] rounded-full transition-all duration-500"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
          <span className="text-[9px] font-mono text-[var(--text-muted)]">{(confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};
