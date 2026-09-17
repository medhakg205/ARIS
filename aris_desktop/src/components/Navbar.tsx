// ============================================================
// ARIS — Navigation Bar
// ============================================================
import React from 'react';
import { Cpu, HelpCircle } from 'lucide-react';
import { DemoBanner } from './common/DemoBanner';

export type NavTab =
  | 'dashboard'
  | 'monitor'
  | 'firmware'
  | 'analysis'
  | 'optimization'
  | 'experiments'
  | 'history'
  | 'settings';

const NAV_ITEMS: { id: NavTab; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'monitor', label: 'Live Monitor' },
  { id: 'firmware', label: 'Firmware' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'optimization', label: 'Optimization' },
  { id: 'experiments', label: 'Experiments' },
  { id: 'history', label: 'History' },
  { id: 'settings', label: 'Settings' },
];

interface NavbarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
  hardwareConnected: boolean;
  wsConnected: boolean;
  backendOnline: boolean;
  isDemo: boolean;
  boardName?: string;
  onOpenInfo: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  hardwareConnected,
  wsConnected,
  backendOnline,
  isDemo,
  boardName,
  onOpenInfo,
}) => {
  return (
    <header className="h-12 bg-[#1e2229] border-b border-white/[0.08] flex items-center px-4 gap-4 shrink-0 select-none z-30">
      {/* Brand */}
      <div className="flex items-center gap-2.5 shrink-0">
        <div className="w-7 h-7 rounded bg-[#00878a]/20 border border-[#00878a]/40 flex items-center justify-center text-[#00878a]">
          <Cpu className="w-3.5 h-3.5" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 leading-tight">
            <span className="text-sm font-semibold tracking-wide text-slate-100 font-samsung">ARIS</span>
            <span className="text-[10px] font-mono text-slate-400 bg-white/[0.06] px-1.5 py-0.2 rounded">v1.0</span>
          </div>
          <span className="text-[10px] text-slate-400 font-sans tracking-tight block">Embedded Studio</span>
        </div>
      </div>

      <div className="w-px h-4 bg-white/[0.08]" />

      {/* Nav Tabs */}
      <nav className="flex items-center gap-1 bg-black/20 p-1 rounded-lg border border-white/[0.05]">
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`px-3 py-1 text-xs rounded font-medium transition-colors ${
                isActive
                  ? 'bg-[#282e38] text-white shadow-sm border border-white/[0.08]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="flex-1" />

      {/* Demo Banner */}
      <DemoBanner visible={isDemo} />

      {/* Status Indicators */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Board Profile */}
        {hardwareConnected && boardName ? (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.08] text-xs text-slate-200 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Target:</span>
            <span>{boardName}</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-white/[0.02] border border-white/[0.06] text-xs text-slate-400 font-mono">
            <span className="text-[10px] text-slate-500 uppercase">Target:</span>
            <span>No Device</span>
          </div>
        )}

        {/* Hardware Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] text-xs text-slate-300">
          <div className={`w-2 h-2 rounded-full ${hardwareConnected ? 'bg-[#00878a]' : 'bg-slate-500'}`} />
          <span>{hardwareConnected ? 'Connected' : 'Disconnected'}</span>
        </div>

        {/* Backend Online Indicator */}
        <div
          className={`flex items-center gap-1.5 text-xs px-2.5 py-0.5 rounded border ${
            backendOnline
              ? 'text-slate-400 border-white/[0.06] bg-white/[0.02]'
              : 'text-rose-400 border-rose-500/30 bg-rose-500/10'
          }`}
        >
          <div className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'bg-slate-400' : 'bg-rose-400'}`} />
          <span>{backendOnline ? 'API Ready' : 'API Offline'}</span>
        </div>

        {/* System Guide (INFO) Button */}
        <button
          onClick={onOpenInfo}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.14] text-slate-300 hover:text-white text-xs font-medium transition-colors"
          title="Open System Architecture & Guide"
        >
          <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
          <span>Guide (i)</span>
        </button>
      </div>
    </header>
  );
};
