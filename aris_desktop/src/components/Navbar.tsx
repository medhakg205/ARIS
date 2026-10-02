// ============================================================
// ARIS — Navigation Bar
// ============================================================
import React from 'react';
import { HelpCircle } from 'lucide-react';
import { DemoBanner } from './common/DemoBanner';
import { ArisLogo } from './common/ArisLogo';

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
  { id: 'monitor', label: 'Monitor' },
  { id: 'firmware', label: 'Firmware' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'optimization', label: 'Optimize' },
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
    <header className="h-11 bg-[#161920] border-b border-white/[0.08] flex items-center px-3 gap-2 shrink-0 select-none z-30 overflow-hidden">
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <ArisLogo size={24} glow={true} />
        <div className="leading-none">
          <div className="flex items-center gap-1">
            <span className="text-[13px] font-semibold tracking-wide text-slate-100 font-samsung">ARIS</span>
            <span className="text-[9px] font-mono text-slate-500 bg-white/[0.06] px-1 py-px rounded">v1.0</span>
          </div>
        </div>
      </div>

      <div className="w-px h-4 bg-white/[0.08] shrink-0" />

      {/* Nav Tabs — horizontally scrollable */}
      <nav className="flex items-center gap-0.5 bg-black/25 p-0.5 rounded-lg border border-white/[0.05] overflow-x-auto no-scrollbar shrink-0">
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`px-2 py-1 text-[11px] rounded font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? 'bg-[#222732] text-white shadow-sm border border-white/[0.08]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="flex-1 min-w-0" />

      {/* Right side indicators — compact */}
      <div className="flex items-center gap-1.5 shrink-0">
        {/* Demo Banner */}
        <DemoBanner visible={isDemo} />

        {/* Board Target — compact */}
        {(hardwareConnected || isDemo) && boardName && (
          <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border ${
            hardwareConnected
              ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300'
              : 'bg-[#00878a]/15 border-[#00878a]/30 text-teal-300'
          }`}>
            <span className="opacity-70">TARGET:</span>
            <span>{boardName}{isDemo && !hardwareConnected ? ' (Sim)' : ''}</span>
          </div>
        )}

        {/* Connection Status */}
        <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] border font-mono ${
          hardwareConnected
            ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300'
            : isDemo
            ? 'bg-[#00878a]/15 border-[#00878a]/30 text-teal-300'
            : 'bg-white/[0.02] border-white/[0.06] text-slate-400'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full ${
            hardwareConnected
              ? 'bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse'
              : isDemo
              ? 'bg-[#00878a] shadow-sm shadow-[#00878a] animate-pulse'
              : 'bg-slate-500'
          }`} />
          <span>{hardwareConnected ? 'HW' : isDemo ? 'Virtual MCU' : 'No Device'}</span>
        </div>

        {/* API Status */}
        <div className={`flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border ${
          backendOnline
            ? 'text-emerald-300 border-emerald-500/25 bg-emerald-500/10'
            : 'text-rose-400 border-rose-500/30 bg-rose-500/10'
        }`}>
          <div className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'bg-emerald-400' : 'bg-rose-400'}`} />
          <span>{backendOnline ? 'API' : 'Offline'}</span>
        </div>

        {/* Guide Button */}
        <button
          onClick={onOpenInfo}
          className="flex items-center gap-1 px-2 py-1 rounded bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/[0.14] text-slate-300 hover:text-white text-[10px] font-medium transition-colors"
          title="Open System Architecture & Guide"
        >
          <HelpCircle className="w-3 h-3 text-slate-400" />
        </button>
      </div>
    </header>
  );
};
