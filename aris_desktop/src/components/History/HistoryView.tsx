// ============================================================
// ARIS — History View
// Searchable, filterable log of all prior experiments.
// ============================================================

import React, { useState, useMemo } from 'react';
import { History, Search } from 'lucide-react';
import type {
  ExperimentRecord,
  OptimizationCandidate,
  ValidationResult,
  ValidationStatus,
} from '../../types';

interface HistoryViewProps {
  experiments: ExperimentRecord[];
  optimizations: OptimizationCandidate[];
  validations: Record<string, ValidationResult>;
  onLoadValidation: (experimentId: string) => Promise<ValidationResult | null>;
  onNavigateValidation: (experimentId: string) => void;
}

const STATUS_COLOR: Record<string, string> = {
  VALIDATED: 'text-emerald-400',
  PARTIALLY_VALIDATED: 'text-[#00878a]',
  NO_SIGNIFICANT_CHANGE: 'text-slate-400',
  REGRESSION: 'text-red-400',
  REJECTED: 'text-red-500',
  INCONCLUSIVE: 'text-amber-400',
  COMPLETED: 'text-emerald-400',
  RUNNING: 'text-[#00878a]',
  CREATED: 'text-slate-400',
  FAILED: 'text-red-400',
};

export const HistoryView: React.FC<HistoryViewProps> = ({
  experiments,
  optimizations,
  validations,
  onLoadValidation,
  onNavigateValidation,
}) => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filtered = useMemo(() => {
    return experiments
      .filter((exp) => {
        if (statusFilter !== 'ALL' && exp.status !== statusFilter) return false;
        if (search) {
          const lower = search.toLowerCase();
          const opt = optimizations.find(
            (o) => o.optimization_id === exp.optimization_id,
          );
          const searchable = [
            exp.experiment_id,
            exp.title,
            exp.board_id,
            exp.optimization_id,
            opt?.title,
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase();
          if (!searchable.includes(lower)) return false;
        }
        return true;
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      );
  }, [experiments, optimizations, search, statusFilter]);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800 shrink-0">
        <History className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-mono text-slate-300">
          Optimization History
        </span>
        <div className="flex-1" />
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search experiments…"
            className="bg-slate-800/50 border border-slate-700 rounded pl-7 pr-3 py-1 text-xs font-mono text-slate-300 outline-none focus:border-slate-600 w-56"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-800/50 border border-slate-700 rounded px-2 py-1 text-xs font-mono text-slate-300 outline-none"
        >
          <option value="ALL">All Statuses</option>
          <option value="COMPLETED">Completed</option>
          <option value="RUNNING">Running</option>
          <option value="CREATED">Created</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-600 gap-2">
            <p className="font-mono text-sm">No matching experiments found.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-[#1e2229]">
              <tr className="border-b border-white/[0.08]">
                {[
                  'Date',
                  'Experiment',
                  'Board',
                  'Optimization',
                  'Status',
                  'Validation',
                  '',
                ].map((h) => (
                  <th
                    key={h}
                    className="text-left text-[9px] font-mono text-slate-400 uppercase tracking-widest px-4 py-2.5"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((exp) => {
                const opt = optimizations.find(
                  (o) => o.optimization_id === exp.optimization_id,
                );
                const val = validations[exp.experiment_id];

                return (
                  <tr
                    key={exp.experiment_id}
                    className="border-b border-white/[0.05] hover:bg-white/[0.03] transition-colors"
                  >
                    <td className="px-4 py-2.5 text-[10px] font-mono text-slate-500 whitespace-nowrap">
                      {new Date(exp.created_at).toLocaleDateString()}{' '}
                      {new Date(exp.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-2.5">
                      <p className="text-xs font-mono text-slate-300">
                        {exp.title}
                      </p>
                      <p className="text-[9px] font-mono text-slate-500">
                        {exp.experiment_id}
                      </p>
                    </td>
                    <td className="px-4 py-2.5 text-xs font-mono text-slate-400">
                      {exp.board_id}
                    </td>
                    <td className="px-4 py-2.5">
                      <p className="text-[10px] font-mono text-slate-300 max-w-48 truncate">
                        {opt?.title || exp.optimization_id}
                      </p>
                    </td>
                    <td className="px-4 py-2.5">
                      <span
                        className={`text-[10px] font-mono font-semibold ${
                          STATUS_COLOR[exp.status] || 'text-slate-400'
                        }`}
                      >
                        {exp.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      {val ? (
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                            STATUS_COLOR[val.validation_status]
                              ? `${STATUS_COLOR[val.validation_status]} border-current/30`
                              : 'text-slate-500 border-slate-700'
                          }`}
                        >
                          {val.validation_status}
                        </span>
                      ) : exp.validation_id ? (
                        <button
                          onClick={() =>
                            onLoadValidation(exp.experiment_id)
                          }
                          className="text-[9px] font-mono text-[#00878a] hover:text-[#00979d]"
                        >
                          Load
                        </button>
                      ) : (
                        <span className="text-[9px] font-mono text-slate-600">
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      {(exp.status === 'COMPLETED' ||
                        exp.validation_id) && (
                        <button
                          onClick={() =>
                            onNavigateValidation(exp.experiment_id)
                          }
                          className="text-[9px] font-mono text-[#00878a] hover:text-[#00979d]"
                        >
                          Details →
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center px-4 py-2 border-t border-slate-800 text-[10px] font-mono text-slate-500 shrink-0">
        Showing {filtered.length} of {experiments.length} experiments
      </div>
    </div>
  );
};
