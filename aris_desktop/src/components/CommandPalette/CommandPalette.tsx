// ============================================================
// ARIS — Global Command Palette (v3.0.0)
// Quick keyboard navigation & action dispatcher (Ctrl+K)
// ============================================================

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Search,
  Cpu,
  FileCode2,
  Activity,
  Zap,
  FlaskConical,
  RotateCw,
  Sun,
  Moon,
  ShieldCheck,
  Settings,
  HelpCircle,
  Play,
  Square,
  Undo2,
  FileText,
  AlertTriangle,
} from 'lucide-react';
import { NavTab } from '../../types/navigation';

export interface CommandItem {
  id: string;
  title: string;
  category: 'Devices' | 'Build & Flash' | 'Telemetry' | 'Optimization' | 'Navigation' | 'System';
  shortcut?: string;
  icon: React.ElementType;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tab: NavTab) => void;
  onAutoDetect: () => void;
  onCompileFirmware: () => void;
  onFlashFirmware: () => void;
  onStartBaseline: () => void;
  onStopBaseline: () => void;
  onToggleTheme: () => void;
  onToggleSidebar: () => void;
  onGenerateReport: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  onAutoDetect,
  onCompileFirmware,
  onFlashFirmware,
  onStartBaseline,
  onStopBaseline,
  onToggleTheme,
  onToggleSidebar,
  onGenerateReport,
}) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = useMemo(() => [
    {
      id: 'detect-board',
      title: 'Detect Microcontroller Board',
      category: 'Devices',
      icon: Cpu,
      action: () => {
        onAutoDetect();
        onClose();
      },
    },
    {
      id: 'compile-firmware',
      title: 'Compile Active Firmware (arduino-cli)',
      category: 'Build & Flash',
      icon: FileCode2,
      action: () => {
        onCompileFirmware();
        onClose();
      },
    },
    {
      id: 'flash-firmware',
      title: 'Flash Firmware to Microcontroller',
      category: 'Build & Flash',
      icon: RotateCw,
      action: () => {
        onFlashFirmware();
        onClose();
      },
    },
    {
      id: 'start-baseline',
      title: 'Start Baseline Telemetry Collection',
      category: 'Telemetry',
      icon: Play,
      action: () => {
        onStartBaseline();
        onClose();
      },
    },
    {
      id: 'stop-baseline',
      title: 'Stop Telemetry Collection',
      category: 'Telemetry',
      icon: Square,
      action: () => {
        onStopBaseline();
        onClose();
      },
    },
    {
      id: 'generate-report',
      title: 'Generate Engineering Experiment Report',
      category: 'Optimization',
      icon: FileText,
      action: () => {
        onGenerateReport();
        onNavigate('reports');
        onClose();
      },
    },
    // Navigation items
    {
      id: 'nav-dashboard',
      title: 'Go to Overview Dashboard',
      category: 'Navigation',
      icon: Activity,
      action: () => {
        onNavigate('dashboard');
        onClose();
      },
    },
    {
      id: 'nav-devices',
      title: 'Go to Device Center',
      category: 'Navigation',
      icon: Cpu,
      action: () => {
        onNavigate('devices');
        onClose();
      },
    },
    {
      id: 'nav-firmware',
      title: 'Go to Firmware Workspace',
      category: 'Navigation',
      icon: FileCode2,
      action: () => {
        onNavigate('firmware');
        onClose();
      },
    },
    {
      id: 'nav-telemetry',
      title: 'Go to Telemetry Lab',
      category: 'Navigation',
      icon: Activity,
      action: () => {
        onNavigate('telemetry');
        onClose();
      },
    },
    {
      id: 'nav-baselines',
      title: 'Go to Baseline Center',
      category: 'Navigation',
      icon: Activity,
      action: () => {
        onNavigate('baselines');
        onClose();
      },
    },
    {
      id: 'nav-optimization',
      title: 'Go to Optimization Center',
      category: 'Navigation',
      icon: Zap,
      action: () => {
        onNavigate('optimization');
        onClose();
      },
    },
    {
      id: 'nav-experiments',
      title: 'Go to Experiment Center',
      category: 'Navigation',
      icon: FlaskConical,
      action: () => {
        onNavigate('experiments');
        onClose();
      },
    },
    {
      id: 'nav-issues',
      title: 'Go to Issue Center',
      category: 'Navigation',
      icon: AlertTriangle,
      action: () => {
        onNavigate('issues');
        onClose();
      },
    },
    {
      id: 'nav-diagnostics',
      title: 'Go to System Diagnostics',
      category: 'System',
      icon: ShieldCheck,
      action: () => {
        onNavigate('diagnostics');
        onClose();
      },
    },
    {
      id: 'nav-settings',
      title: 'Go to Settings',
      category: 'System',
      icon: Settings,
      action: () => {
        onNavigate('settings');
        onClose();
      },
    },
    {
      id: 'toggle-theme',
      title: 'Toggle Dark / Light Theme',
      category: 'System',
      icon: Sun,
      action: () => {
        onToggleTheme();
        onClose();
      },
    },
    {
      id: 'toggle-sidebar',
      title: 'Toggle Sidebar Collapse (Ctrl+B)',
      category: 'System',
      shortcut: 'Ctrl+B',
      icon: Settings,
      action: () => {
        onToggleSidebar();
        onClose();
      },
    },
  ], [
    onAutoDetect,
    onCompileFirmware,
    onFlashFirmware,
    onStartBaseline,
    onStopBaseline,
    onGenerateReport,
    onNavigate,
    onToggleTheme,
    onToggleSidebar,
    onClose,
  ]);

  const filteredCommands = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return commands;
    return commands.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q)
    );
  }, [commands, query]);

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
          idx + 1 < filteredCommands.length ? idx + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((idx) =>
          idx - 1 >= 0 ? idx - 1 : filteredCommands.length - 1
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/60 backdrop-blur-sm animate-fade-in select-none">
      <div
        className="w-full max-w-xl rounded-xl bg-[var(--bg-card)] border border-[var(--border-color)] shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-color)] bg-[var(--bg-header)]">
          <Search size={18} className="text-[var(--text-muted)] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search action..."
            className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none"
          />
          <kbd className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--border-color)] text-[var(--text-muted)]">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-1.5 space-y-0.5">
          {filteredCommands.length === 0 ? (
            <div className="p-6 text-center text-xs text-[var(--text-muted)] font-mono">
              No matching commands found for "{query}"
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={cmd.id}
                  onClick={cmd.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-colors ${
                    isSelected
                      ? 'bg-[var(--accent-cyan-bg)] text-[var(--text-primary)] font-medium'
                      : 'text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]'
                  }`}
                >
                  <Icon
                    size={16}
                    className={`shrink-0 ${
                      isSelected ? 'text-[var(--accent-cyan)]' : 'text-[var(--text-muted)]'
                    }`}
                  />
                  <span className="flex-1 text-left truncate">{cmd.title}</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-color)]">
                    {cmd.category}
                  </span>
                  {cmd.shortcut && (
                    <kbd className="text-[9px] font-mono px-1 py-0.5 rounded bg-[var(--border-color)] text-[var(--text-muted)]">
                      {cmd.shortcut}
                    </kbd>
                  )}
                </button>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[var(--border-color)] bg-[var(--bg-surface)] flex items-center justify-between text-[11px] text-[var(--text-muted)] font-mono">
          <span>Navigate with ↑ / ↓</span>
          <span>Select with ↵ Enter</span>
        </div>
      </div>
    </div>
  );
};
