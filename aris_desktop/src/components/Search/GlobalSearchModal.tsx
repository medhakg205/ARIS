// ============================================================
// ARIS — Global Search Modal (v3.0.0)
// Search across Experiments, Firmware, Telemetry, Optimizations, Issues
// ============================================================

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Search,
  FlaskConical,
  FileCode2,
  Zap,
  AlertTriangle,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { NavTab } from '../../types/navigation';
import {
  ExperimentRecord,
  FirmwareRecord,
  OptimizationCandidate,
  FindingRecord,
  RunRecord,
} from '../../types';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tab: NavTab) => void;
  experiments: ExperimentRecord[];
  firmwareList: FirmwareRecord[];
  optimizations: OptimizationCandidate[];
  findings: FindingRecord[];
  runs?: RunRecord[];
  onSelectExperiment?: (id: string) => void;
  onSelectOptimization?: (id: string) => void;
}

interface SearchResult {
  id: string;
  type: 'Experiment' | 'Firmware' | 'Optimization' | 'Finding' | 'Run';
  title: string;
  subtitle: string;
  badge?: string;
  badgeColor?: 'cyan' | 'green' | 'amber' | 'red';
  action: () => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
  experiments,
  firmwareList,
  optimizations,
  findings,
  runs = [],
  onSelectExperiment,
  onSelectOptimization,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const allItems: SearchResult[] = useMemo(() => {
    const list: SearchResult[] = [];

    // Experiments
    experiments.forEach((exp) => {
      list.push({
        id: `exp-${exp.experiment_id}`,
        type: 'Experiment',
        title: exp.title || exp.experiment_id,
        subtitle: `${exp.board_id} · Status: ${exp.status}`,
        badge: exp.status,
        badgeColor: exp.status === 'VALIDATED' ? 'green' : exp.status === 'FAILED' ? 'red' : 'cyan',
        action: () => {
          if (onSelectExperiment) onSelectExperiment(exp.experiment_id);
          onNavigate('experiments');
          onClose();
        },
      });
    });

    // Optimizations
    optimizations.forEach((opt) => {
      list.push({
        id: `opt-${opt.optimization_id}`,
        type: 'Optimization',
        title: opt.title,
        subtitle: `${opt.source_location?.file || 'Firmware'} · Status: ${opt.status}`,
        badge: opt.status,
        badgeColor: opt.status === 'VALIDATED' ? 'green' : opt.status === 'REJECTED' ? 'amber' : 'cyan',
        action: () => {
          if (onSelectOptimization) onSelectOptimization(opt.optimization_id);
          onNavigate('optimization');
          onClose();
        },
      });
    });

    // Findings / Issues
    findings.forEach((f) => {
      list.push({
        id: `find-${f.finding_id}`,
        type: 'Finding',
        title: f.title,
        subtitle: `${f.rule_id} · ${f.source_file}:${f.source_line}`,
        badge: f.severity,
        badgeColor: f.severity === 'CRITICAL' ? 'red' : f.severity === 'HIGH' ? 'amber' : 'cyan',
        action: () => {
          onNavigate('issues');
          onClose();
        },
      });
    });

    // Firmware
    firmwareList.forEach((fw) => {
      list.push({
        id: `fw-${fw.firmware_id}`,
        type: 'Firmware',
        title: fw.name,
        subtitle: `Uploaded: ${new Date(fw.created_at).toLocaleDateString()}`,
        action: () => {
          onNavigate('firmware');
          onClose();
        },
      });
    });

    // Runs
    runs.forEach((r) => {
      list.push({
        id: `run-${r.run_id}`,
        type: 'Run',
        title: `Execution Run ${r.run_id}`,
        subtitle: `${r.board_id} · ${r.status} ${r.is_demo ? '(Demo)' : '(Physical)'}`,
        badge: r.status,
        badgeColor: r.status === 'COMPLETED' ? 'green' : 'cyan',
        action: () => {
          onNavigate('telemetry');
          onClose();
        },
      });
    });

    return list;
  }, [experiments, optimizations, findings, firmwareList, runs, onNavigate, onClose, onSelectExperiment, onSelectOptimization]);

  const filteredResults = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allItems.slice(0, 15);
    return allItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.subtitle.toLowerCase().includes(q) ||
        item.type.toLowerCase().includes(q) ||
        (item.badge && item.badge.toLowerCase().includes(q))
    ).slice(0, 20);
  }, [allItems, query]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((idx) =>
          idx + 1 < filteredResults.length ? idx + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((idx) =>
          idx - 1 >= 0 ? idx - 1 : filteredResults.length - 1
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredResults[selectedIndex]) {
          filteredResults[selectedIndex].action();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredResults, selectedIndex, onClose]);

  if (!isOpen) return null;

  const getTypeIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'Experiment':
        return <FlaskConical size={15} className="text-[var(--accent-purple)]" />;
      case 'Optimization':
        return <Zap size={15} className="text-[var(--accent-cyan)]" />;
      case 'Finding':
        return <AlertTriangle size={15} className="text-[var(--accent-amber)]" />;
      case 'Firmware':
        return <FileCode2 size={15} className="text-[var(--accent-green)]" />;
      default:
        return <Activity size={15} className="text-[var(--text-muted)]" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/60 backdrop-blur-sm animate-fade-in select-none">
      <div
        className="w-full max-w-xl rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-header)]">
          <Search size={18} className="text-[var(--accent-cyan)] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search experiments, firmware, optimizations, findings..."
            className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none"
          />
          <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--border-color)] text-[var(--text-muted)]">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-1.5 space-y-0.5">
          {filteredResults.length === 0 ? (
            <div className="p-6 text-center text-xs text-[var(--text-muted)] font-mono">
              No matching records found for "{query}"
            </div>
          ) : (
            filteredResults.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-colors ${
                    isSelected
                      ? 'bg-[var(--accent-cyan-bg)] text-[var(--text-primary)] font-medium'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]'
                  }`}
                >
                  <div className="p-1.5 rounded bg-[var(--bg-surface)] border border-[var(--border-color)]">
                    {getTypeIcon(item.type)}
                  </div>
                  <div className="flex-1 text-left truncate">
                    <div className="font-medium text-[var(--text-primary)] truncate">
                      {item.title}
                    </div>
                    <div className="text-[11px] text-[var(--text-muted)] truncate font-mono">
                      {item.subtitle}
                    </div>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)] font-semibold">
                      {item.badge}
                    </span>
                  )}
                  <ArrowRight
                    size={14}
                    className={`shrink-0 ${
                      isSelected ? 'text-[var(--accent-cyan)]' : 'text-transparent'
                    }`}
                  />
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[var(--border-color)] bg-[var(--bg-surface)] flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
          <span>{filteredResults.length} records found</span>
          <span>Press ↵ Enter to navigate</span>
        </div>
      </div>
    </div>
  );
};
