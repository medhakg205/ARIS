// ============================================================
// ARIS — Professional Top Navigation Bar (v3.0.0)
// Minimal status, project indicator, connection provenance, theme toggle
// ============================================================

import React, { useState } from 'react';
import {
  Search,
  Command,
  Sun,
  Moon,
  Monitor,
  Bell,
  HelpCircle,
  MoreVertical,
  Activity,
  Cpu,
  ShieldCheck,
  RotateCw,
} from 'lucide-react';
import { NavTab } from '../types/navigation';
import { ThemeMode } from '../hooks/useTheme';
import { BoardProfile, DeviceConnectionState } from '../types';

interface TopBarProps {
  activeTab: NavTab;
  projectName?: string;
  hardwareConnected: boolean;
  isDemo: boolean;
  selectedBoard?: BoardProfile | null;
  confidence?: string;
  connectedPort?: string;
  deviceState?: DeviceConnectionState;
  themeMode: ThemeMode;
  onThemeChange: (mode: ThemeMode) => void;
  onOpenCommandPalette: () => void;
  onOpenSearch: () => void;
  onOpenNotifications: () => void;
  onOpenInfo: () => void;
  onNavigate: (tab: NavTab) => void;
  unreadNotificationsCount?: number;
  telemetryActive?: boolean;
}

const TAB_TITLES: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: 'Dashboard', subtitle: 'System & Firmware Status' },
  firmware: { title: 'Firmware', subtitle: 'Arduino Project & Source Code' },
  telemetry: { title: 'Telemetry', subtitle: 'Real-time Runtime Observability' },
  analysis: { title: 'Analysis', subtitle: 'Detected Bottlenecks & Code Findings' },
  issues: { title: 'Analysis', subtitle: 'Detected Bottlenecks & Code Findings' },
  optimize: { title: 'Optimize', subtitle: 'Recommended Firmware Optimizations' },
  optimization: { title: 'Optimize', subtitle: 'Recommended Firmware Optimizations' },
  experiments: { title: 'Experiments', subtitle: 'Hardware Validation & Test Runs' },
  reports: { title: 'Reports', subtitle: 'Optimization Verification Reports' },
  settings: { title: 'Settings', subtitle: 'Arduino Toolchain & Environment' },
  devices: { title: 'Devices', subtitle: 'Microcontroller Discovery & Serial Hardware' },
  baselines: { title: 'Baselines', subtitle: 'Statistical Baseline Distributions' },
  diagnostics: { title: 'Diagnostics', subtitle: 'Subsystem Health & Status' },
  logs: { title: 'Log Viewer', subtitle: 'Subsystem Event Stream' },
  about: { title: 'About ARIS', subtitle: 'Platform Details' },
};

export const TopBar: React.FC<TopBarProps> = ({
  activeTab,
  projectName,
  hardwareConnected,
  isDemo,
  selectedBoard,
  confidence = 'UNKNOWN',
  connectedPort,
  deviceState = 'NO_HARDWARE',
  themeMode,
  onThemeChange,
  onOpenCommandPalette,
  onOpenSearch,
  onOpenNotifications,
  onOpenInfo,
  onNavigate,
  unreadNotificationsCount = 0,
  telemetryActive = false,
}) => {
  const [showThemeMenu, setShowThemeMenu] = useState(false);
  const [showAppMenu, setShowAppMenu] = useState(false);

  const currentTabInfo = TAB_TITLES[activeTab] || { title: 'ARIS', subtitle: '' };

  const isConnected = deviceState === 'CONNECTED' || (hardwareConnected && Boolean(selectedBoard));
  const isSimulation = deviceState === 'SIMULATION' || isDemo;
  const isDetecting = deviceState === 'DETECTING';

  return (
    <header className="h-12 bg-[var(--bg-header)] border-b border-[var(--border-color)] px-4 flex items-center justify-between shrink-0 select-none z-30">
      {/* Left: Project / Breadcrumbs */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-[var(--text-muted)] font-bold tracking-wider">ARIS</span>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="text-[var(--text-primary)] font-medium truncate max-w-[140px] sm:max-w-[220px]">
            {projectName ? projectName : <span className="text-[var(--text-muted)]">No project loaded</span>}
          </span>
        </div>

        {/* Authoritative Hardware Status Badge */}
        <div className="hidden md:flex items-center gap-1.5 pl-3 border-l border-[var(--border-color)]">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected
                ? 'bg-[var(--accent-green)] animate-soft-beacon'
                : isSimulation
                ? 'bg-[var(--accent-amber)]'
                : isDetecting
                ? 'bg-[var(--accent-cyan)] animate-ping'
                : 'bg-[var(--text-muted)]'
            }`}
          />
          <span className="text-xs font-mono font-medium text-[var(--text-secondary)]">
            {isConnected
              ? `${selectedBoard?.display_name || 'Arduino'} (${connectedPort || 'Connected'})`
              : isSimulation
              ? `Simulation Active (${selectedBoard?.display_name || 'Virtual'})`
              : isDetecting
              ? 'Scanning Ports...'
              : 'No Hardware Connected'}
          </span>
          {isConnected && confidence && confidence !== 'UNKNOWN' && (
            <span
              className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold ${
                confidence === 'CONFIRMED'
                  ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)]'
                  : 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)]'
              }`}
            >
              {confidence}
            </span>
          )}
        </div>
      </div>

      {/* Center: Current View Title */}
      <div className="hidden lg:flex flex-col items-center justify-center leading-none">
        <span className="text-xs font-heading font-bold text-[var(--text-primary)]">
          {currentTabInfo.title}
        </span>
        <span className="text-[10px] text-[var(--text-muted)] mt-0.5 font-mono">
          {currentTabInfo.subtitle}
        </span>
      </div>

      {/* Right: Actions, Command Palette, Theme, Notifications */}
      <div className="flex items-center gap-2">
        {/* Telemetry Status Badge */}
        {telemetryActive && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--border-color)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-cyan)] animate-pulse" />
            <span>LIVE TELEMETRY</span>
          </div>
        )}

        {/* Provenance Badge */}
        <span
          className={`text-[9px] font-mono font-bold tracking-wider px-2 py-0.5 rounded border ${
            isSimulation
              ? 'bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border-[var(--accent-amber)]/30'
              : isConnected
              ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border-[var(--accent-green)]/30'
              : 'bg-[var(--bg-surface)] text-[var(--text-muted)] border-[var(--border-color)]'
          }`}
        >
          {isSimulation ? 'SIMULATION' : isConnected ? 'PHYSICAL' : 'OFFLINE'}
        </span>

        {/* Command Palette Trigger */}
        <button
          onClick={onOpenCommandPalette}
          title="Command Palette (Ctrl+K)"
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--bg-surface)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs transition-colors"
        >
          <Command size={12} className="text-[var(--text-muted)]" />
          <span className="text-[11px] font-mono hidden sm:inline">Commands</span>
          <kbd className="hidden lg:inline text-[9px] font-mono px-1 py-0.2 rounded bg-[var(--bg-card)] border border-[var(--border-color)] text-[var(--text-muted)]">
            Ctrl+K
          </kbd>
        </button>

        {/* Theme Mode Toggle Button */}
        <div className="relative">
          <button
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            title="Theme Selection"
            className="p-1.5 rounded hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
          >
            {themeMode === 'light' ? (
              <Sun size={15} />
            ) : themeMode === 'system' ? (
              <Monitor size={15} />
            ) : (
              <Moon size={15} />
            )}
          </button>

          {showThemeMenu && (
            <div
              className="absolute right-0 top-full mt-1.5 w-32 aris-card p-1 shadow-lg z-50 text-xs font-mono"
              onMouseLeave={() => setShowThemeMenu(false)}
            >
              <button
                onClick={() => {
                  onThemeChange('dark');
                  setShowThemeMenu(false);
                }}
                className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded transition-colors ${
                  themeMode === 'dark'
                    ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface)]'
                }`}
              >
                <Moon size={13} />
                <span>Dark</span>
              </button>
              <button
                onClick={() => {
                  onThemeChange('light');
                  setShowThemeMenu(false);
                }}
                className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded transition-colors ${
                  themeMode === 'light'
                    ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface)]'
                }`}
              >
                <Sun size={13} />
                <span>Light</span>
              </button>
              <button
                onClick={() => {
                  onThemeChange('system');
                  setShowThemeMenu(false);
                }}
                className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded transition-colors ${
                  themeMode === 'system'
                    ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] font-semibold'
                    : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface)]'
                }`}
              >
                <Monitor size={13} />
                <span>System</span>
              </button>
            </div>
          )}
        </div>

        {/* Notifications */}
        <button
          onClick={onOpenNotifications}
          title="Notifications"
          className="relative p-1.5 rounded hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        >
          <Bell size={15} />
          {unreadNotificationsCount > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[var(--accent-cyan)]" />
          )}
        </button>

        {/* Settings Shortcut */}
        <button
          onClick={() => onNavigate('settings')}
          title="Settings"
          className="p-1.5 rounded hover:bg-[var(--bg-card-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        >
          <HelpCircle size={15} />
        </button>
      </div>
    </header>
  );
};
