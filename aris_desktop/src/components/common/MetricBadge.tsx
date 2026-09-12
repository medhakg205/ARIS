// ============================================================
// ARIS Common — MetricBadge
// Shows a metric value + unit + veracity classification badge.
// MEASURED = emerald, ESTIMATED = amber, DERIVED = cyan, PREDICTED = purple
// Never presents PREDICTED values as MEASURED.
// ============================================================

import React from 'react';
import type { MetricClassification } from '../../types';

const CLASSIFICATION_STYLES: Record<MetricClassification, string> = {
  MEASURED: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  ESTIMATED: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  DERIVED: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  PREDICTED: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
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
        <span className="text-xs font-mono text-slate-400 uppercase tracking-wider w-28 shrink-0">
          {label}
        </span>
        <span className="text-sm font-mono text-slate-100 tabular-nums">
          {value}
          {unit && <span className="text-slate-500 ml-0.5 text-xs">{unit}</span>}
        </span>
        <span className={`text-[9px] font-mono px-1 py-0.5 rounded border ${cls} ml-auto`}>
          {classification}
        </span>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded p-3 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">{label}</span>
        <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${cls}`}>
          {classification}
        </span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-xl font-mono font-semibold text-slate-100 tabular-nums">
          {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
        </span>
        {unit && <span className="text-xs font-mono text-slate-500">{unit}</span>}
      </div>
      {secondary && (
        <span className="text-[10px] font-mono text-slate-500">{secondary}</span>
      )}
      {confidence !== undefined && (
        <div className="flex items-center gap-1.5 mt-1">
          <div className="flex-1 h-0.5 bg-slate-800 rounded-full">
            <div
              className="h-full bg-slate-500 rounded-full"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
          <span className="text-[9px] font-mono text-slate-500">{(confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};
