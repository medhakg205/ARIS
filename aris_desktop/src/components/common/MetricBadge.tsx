// ============================================================
// ARIS Common — MetricBadge
// Shows a metric value + unit + veracity classification badge.
// MEASURED = emerald, ESTIMATED = amber, DERIVED = cyan, PREDICTED = purple
// Never presents PREDICTED values as MEASURED.
// ============================================================

import React from 'react';
import type { MetricClassification } from '../../types';

const CLASSIFICATION_STYLES: Record<MetricClassification, string> = {
  MEASURED: 'bg-white/[0.04] text-slate-300 border-white/[0.1]',
  ESTIMATED: 'bg-white/[0.04] text-slate-300 border-white/[0.1]',
  DERIVED: 'bg-white/[0.04] text-slate-300 border-white/[0.1]',
  PREDICTED: 'bg-white/[0.04] text-slate-300 border-white/[0.1]',
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
    <div className="bg-[#22272e] border border-white/[0.07] hover:border-white/[0.14] transition-all duration-200 rounded-xl p-3 sm:p-3.5 flex flex-col justify-between group shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10.5px] font-sans font-medium text-slate-400 tracking-wider uppercase">
          {label}
        </span>
        <span className={`text-[9.5px] font-sans font-normal px-2 py-0.5 rounded-full border ${cls}`}>
          {classification}
        </span>
      </div>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="text-xl sm:text-2xl font-bold font-mono text-white tabular-nums tracking-tight">
          {typeof value === 'number' ? (Number.isInteger(value) ? value : value.toFixed(2)) : value}
        </span>
        {unit && <span className="text-xs font-sans font-medium text-slate-400">{unit}</span>}
      </div>

      {secondary && (
        <span className="text-[10px] text-slate-400 font-sans mt-1">{secondary}</span>
      )}

      {confidence !== undefined && (
        <div className="flex items-center gap-2 mt-2 pt-1.5 border-t border-white/[0.04]">
          <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500/80 rounded-full transition-all duration-500"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
          <span className="text-[9.5px] font-mono text-slate-400">{(confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};
