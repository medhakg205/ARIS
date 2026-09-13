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
    <div className="bg-[#0d111a]/80 backdrop-blur-md border border-white/[0.08] hover:border-white/[0.18] transition-all duration-200 rounded-2xl p-4 flex flex-col justify-between group shadow-sm hover:shadow-lg hover:shadow-cyan-500/5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-sans font-medium text-slate-400 tracking-wider uppercase">
          {label}
        </span>
        <span className={`text-[10px] font-sans font-medium px-2 py-0.5 rounded-full border ${cls}`}>
          {classification}
        </span>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="text-2xl font-sans font-bold text-white tabular-nums tracking-tight">
          {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
        </span>
        {unit && <span className="text-xs font-mono font-medium text-slate-400">{unit}</span>}
      </div>

      {secondary && (
        <span className="text-[11px] text-slate-400 font-sans mt-1">{secondary}</span>
      )}

      {confidence !== undefined && (
        <div className="flex items-center gap-2 mt-3 pt-2 border-t border-white/[0.04]">
          <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className="h-full bg-cyan-400/80 rounded-full transition-all duration-500"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-slate-400">{(confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};
