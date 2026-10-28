import React, { useState, useMemo } from 'react';
import {
  Terminal, Search, Filter, Copy, Download, Trash2, ArrowDown, Check,
  AlertCircle, AlertTriangle, Info, CheckCircle2
} from 'lucide-react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  subsystem: string;
  message: string;
}

const INITIAL_LOGS: LogEntry[] = [
  { id: '1', timestamp: '20:30:12.102', level: 'INFO', subsystem: 'CORE', message: 'ARIS Studio v3.0.0-PROFESSIONAL initialized.' },
  { id: '2', timestamp: '20:30:12.145', level: 'INFO', subsystem: 'FASTAPI', message: 'REST API service running on http://127.0.0.1:8000.' },
  { id: '3', timestamp: '20:30:12.210', level: 'DEBUG', subsystem: 'STORAGE', message: 'SQLite database connection pool established (WAL mode).' },
  { id: '4', timestamp: '20:30:12.350', level: 'INFO', subsystem: 'TOOLCHAIN', message: 'Arduino CLI v0.35.3 detected. Found 2 MCU cores installed.' },
  { id: '5', timestamp: '20:30:12.420', level: 'WARN', subsystem: 'SERIAL', message: 'Enumerating COM ports: 0 physical devices found. Demo simulation standby.' },
  { id: '6', timestamp: '20:30:13.010', level: 'INFO', subsystem: 'OBSERVER', message: 'Probe overhead calibration matrix loaded: 32 cycles subtracted per probe.' },
  { id: '7', timestamp: '20:30:13.500', level: 'INFO', subsystem: 'AST', message: 'Clang & Tree-sitter C++ AST parser ready. 9 optimization rules indexed.' },
  { id: '8', timestamp: '20:30:14.200', level: 'INFO', subsystem: 'TELEMETRY', message: 'Ring buffer allocated with 1,000 frame capacity.' },
  { id: '9', timestamp: '20:30:15.110', level: 'DEBUG', subsystem: 'OPTIMIZER', message: 'Multi-objective Pareto weight vector registered: [lat: 0.40, sram: 0.25, flash: 0.15, cpu: 0.15, isr: 0.05].' },
  { id: '10', timestamp: '20:30:16.890', level: 'INFO', subsystem: 'SYSTEM', message: 'All subsystems online and operating within specifications.' }
];

export const LogViewer: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [filterSubsystem, setFilterSubsystem] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  const subsystems = useMemo(() => {
    const set = new Set(logs.map((l) => l.subsystem));
    return ['ALL', ...Array.from(set)];
  }, [logs]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (filterLevel !== 'ALL' && log.level !== filterLevel) return false;
      if (filterSubsystem !== 'ALL' && log.subsystem !== filterSubsystem) return false;
      if (
        searchQuery &&
        !log.message.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !log.subsystem.toLowerCase().includes(searchQuery.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [logs, filterLevel, filterSubsystem, searchQuery]);

  const handleCopyLogs = () => {
    const text = filteredLogs
      .map((l) => `[${l.timestamp}] [${l.level}] [${l.subsystem}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  const handleExportLogs = () => {
    const text = filteredLogs
      .map((l) => `[${l.timestamp}] [${l.level}] [${l.subsystem}] ${l.message}`)
      .join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `aris_system_logs_${Date.now()}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden p-6 gap-4 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[var(--accent-cyan-bg)] border border-[var(--accent-cyan)]/20 text-[var(--accent-cyan)]">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[var(--text-primary)]">Engineering Log Stream</h2>
            <p className="text-xs text-[var(--text-muted)] font-sans">
              Real-time audit log of toolchain compilations, serial handshakes, telemetry packets, and AST mutations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-xs font-medium border border-[var(--border-color)] transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--accent-green)]" /> : <Copy className="w-3.5 h-3.5 text-[var(--text-muted)]" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={handleExportLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--text-primary)] text-xs font-medium border border-[var(--border-color)] transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            <span>Export</span>
          </button>

          <button
            onClick={handleClearLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] text-[var(--accent-red)] text-xs font-medium border border-[var(--border-color)] transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Control Bar: Filters & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] shrink-0">
        <div className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              placeholder="Search log messages, subsystems..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 bg-[var(--bg-app)] border border-[var(--border-color)] text-xs rounded-lg text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-cyan)]"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Level Filter */}
          <div className="flex items-center gap-1">
            {['ALL', 'INFO', 'WARN', 'ERROR', 'DEBUG'].map((level) => (
              <button
                key={level}
                onClick={() => setFilterLevel(level)}
                className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-medium transition-colors ${
                  filterLevel === level
                    ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30 font-semibold'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'
                }`}
              >
                {level}
              </button>
            ))}
          </div>

          {/* Subsystem Filter */}
          <select
            value={filterSubsystem}
            onChange={(e) => setFilterSubsystem(e.target.value)}
            className="bg-[var(--bg-app)] border border-[var(--border-color)] text-xs rounded-lg px-2.5 py-1 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-cyan)] font-mono"
          >
            {subsystems.map((sub) => (
              <option key={sub} value={sub}>
                {sub}
              </option>
            ))}
          </select>

          {/* Auto scroll toggle */}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              autoScroll
                ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
                : 'bg-[var(--bg-card)] text-[var(--text-muted)] border-[var(--border-color)]'
            }`}
          >
            <ArrowDown className="w-3.5 h-3.5" />
            <span>Auto-scroll</span>
          </button>
        </div>
      </div>

      {/* Terminal Log Console */}
      <div className="flex-1 overflow-y-auto p-4 rounded-2xl bg-[var(--bg-app)] border border-[var(--border-color)] font-mono text-xs space-y-1.5 select-text shadow-inner">
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12 text-[var(--text-muted)]">No log entries matching filter criteria.</div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              className="flex items-start gap-3 py-1 px-2 rounded hover:bg-[var(--bg-card-hover)] transition-colors leading-relaxed"
            >
              <span className="text-[var(--text-muted)]/60 shrink-0 text-[11px]">{log.timestamp}</span>

              <span
                className={`text-[10px] font-bold px-1.5 py-0.2 rounded shrink-0 uppercase ${
                  log.level === 'INFO'
                    ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]'
                    : log.level === 'WARN'
                    ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)]'
                    : log.level === 'ERROR'
                    ? 'bg-[var(--accent-red-bg)] text-[var(--accent-red)]'
                    : 'bg-[var(--accent-purple-bg)] text-[var(--accent-purple)]'
                }`}
              >
                {log.level}
              </span>

              <span className="text-[var(--text-muted)] shrink-0 text-[11px] font-semibold">[{log.subsystem}]</span>

              <span className="text-[var(--text-primary)] break-all font-sans text-xs">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
