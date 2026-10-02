// ============================================================
// ARIS — Professional Sidebar Component (v3.0.0)
// Simplified 8-Item Primary Navigation, ARIS Product Branding,
// Collapsible Advanced Section
// ============================================================

import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Cpu,
  FileCode2,
  Activity,
  BarChart3,
  Zap,
  FlaskConical,
  Search,
  FileText,
  Settings,
  TerminalSquare,
  ShieldCheck,
  Info,
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  Sliders,
} from 'lucide-react';
import { NavTab } from '../types/navigation';
import { ArisLogo } from './common/ArisLogo';

interface SidebarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  issuesCount?: number;
  experimentsCount?: number;
  candidatesCount?: number;
  hardwareConnected?: boolean;
}

const STORAGE_KEY = 'aris-sidebar-collapsed';

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  issuesCount = 0,
  experimentsCount = 0,
  candidatesCount = 0,
  hardwareConnected = false,
}) => {
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const [advancedOpen, setAdvancedOpen] = useState(false);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(STORAGE_KEY, String(next));
      } catch (_) {}
      return next;
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        toggleCollapsed();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Primary 8 navigation destinations as defined in Part 8
  const primaryNavItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'firmware' as NavTab, label: 'Firmware', icon: FileCode2 },
    { id: 'telemetry' as NavTab, label: 'Telemetry', icon: Activity },
    {
      id: 'analysis' as NavTab,
      alias: 'issues' as NavTab,
      label: 'Analysis',
      icon: Search,
      badge: issuesCount > 0 ? issuesCount : undefined,
      badgeColor: 'amber' as const,
    },
    {
      id: 'optimize' as NavTab,
      alias: 'optimization' as NavTab,
      label: 'Optimize',
      icon: Zap,
      badge: candidatesCount > 0 ? candidatesCount : undefined,
      badgeColor: 'cyan' as const,
    },
    {
      id: 'experiments' as NavTab,
      label: 'Experiments',
      icon: FlaskConical,
      badge: experimentsCount > 0 ? experimentsCount : undefined,
    },
    { id: 'reports' as NavTab, label: 'Reports', icon: FileText },
    { id: 'settings' as NavTab, label: 'Settings', icon: Settings },
  ];

  // Secondary advanced tools
  const advancedNavItems = [
    {
      id: 'devices' as NavTab,
      label: 'Devices',
      icon: Cpu,
      badge: hardwareConnected ? 'ON' : undefined,
      badgeColor: 'green' as const,
    },
    { id: 'baselines' as NavTab, label: 'Baselines', icon: BarChart3 },
    { id: 'diagnostics' as NavTab, label: 'Diagnostics', icon: ShieldCheck },
    { id: 'logs' as NavTab, label: 'Log Viewer', icon: TerminalSquare },
    { id: 'about' as NavTab, label: 'About', icon: Info },
  ];

  const isTabActive = (item: { id: NavTab; alias?: NavTab }) => {
    return activeTab === item.id || (item.alias && activeTab === item.alias);
  };

  return (
    <aside
      className={`relative flex flex-col shrink-0 border-r border-[var(--border-color)] bg-[var(--bg-sidebar)] transition-all duration-200 select-none z-20 ${
        collapsed ? 'w-14' : 'w-60'
      }`}
    >
      {/* Brand Header */}
      <div className="h-14 flex items-center px-3.5 border-b border-[var(--border-color)] justify-between overflow-hidden">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <ArisLogo size={24} glow={false} />
          {!collapsed && (
            <div className="flex flex-col overflow-hidden leading-none">
              <span className="font-heading font-extrabold text-sm tracking-wider text-[var(--text-primary)]">
                ARIS
              </span>
              <span className="text-[10px] font-mono text-[var(--text-muted)] truncate mt-1">
                Arduino Runtime Intelligence
              </span>
            </div>
          )}
        </div>

        {!collapsed && (
          <button
            onClick={toggleCollapsed}
            title="Collapse Sidebar (Ctrl+B)"
            className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>

      {/* Primary Navigation */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {primaryNavItems.map((item) => {
          const active = isTabActive(item);
          const Icon = item.icon;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              title={collapsed ? item.label : undefined}
              className={`w-full flex items-center gap-3 px-2.5 py-2 rounded-lg text-xs font-mono font-medium transition-all ${
                active
                  ? 'bg-[var(--accent-cyan)] text-white shadow-sm font-semibold'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'
              }`}
            >
              <Icon size={16} className="shrink-0" />
              {!collapsed && (
                <div className="flex-1 flex items-center justify-between min-w-0">
                  <span className="truncate">{item.label}</span>
                  {item.badge !== undefined && (
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full font-bold ${
                        active
                          ? 'bg-white/20 text-white'
                          : item.badgeColor === 'amber'
                          ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)]'
                          : item.badgeColor === 'cyan'
                          ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]'
                          : 'bg-[var(--bg-surface)] text-[var(--text-muted)]'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}

        {/* Collapsible Advanced Section */}
        {!collapsed && (
          <div className="pt-3">
            <button
              onClick={() => setAdvancedOpen(!advancedOpen)}
              className="w-full flex items-center justify-between px-2.5 py-1.5 text-[10px] font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
            >
              <span>Advanced Tools</span>
              {advancedOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
            </button>

            {advancedOpen && (
              <div className="space-y-0.5 mt-1 pl-1 border-l border-[var(--border-color)] ml-2.5">
                {advancedNavItems.map((item) => {
                  const active = activeTab === item.id;
                  const Icon = item.icon;

                  return (
                    <button
                      key={item.id}
                      onClick={() => onTabChange(item.id)}
                      className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
                        active
                          ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold'
                          : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)]'
                      }`}
                    >
                      <Icon size={14} className="shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer / Toggle for collapsed mode */}
      {collapsed && (
        <div className="p-2 border-t border-[var(--border-color)] flex justify-center">
          <button
            onClick={toggleCollapsed}
            title="Expand Sidebar (Ctrl+B)"
            className="p-1.5 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </aside>
  );
};
