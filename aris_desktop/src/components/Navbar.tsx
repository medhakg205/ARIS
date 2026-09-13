// ============================================================
// ARIS — Navigation Bar
// ============================================================
import React from 'react';
import { Cpu, Wifi, WifiOff } from 'lucide-react';
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
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  hardwareConnected,
  wsConnected,
  backendOnline,
  isDemo,
  boardName,
}) => {
  return (
    <header className="h-14 bg-[#07090e]/90 backdrop-blur-xl border-b border-white/[0.06] flex items-center px-6 gap-6 shrink-0 select-none z-30">
      {/* Brand */}
      <div className="flex items-center gap-2.5 shrink-0">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-sm shadow-cyan-500/10">
          <Cpu className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 leading-none">
            <span className="text-sm font-semibold tracking-wider text-white font-sans">ARIS</span>
            <span className="text-[10px] font-mono font-medium text-cyan-400 bg-cyan-500/10 px-1 py-0.5 rounded">v1.0</span>
          </div>
          <span className="text-[10px] text-slate-400 font-sans tracking-tight">Embedded Intelligence</span>
        </div>
      </div>

      <div className="w-px h-5 bg-white/[0.08]" />

      {/* Nav Tabs - Google Home Pill Navigation */}
      <nav className="flex items-center gap-1 bg-white/[0.03] p-1 rounded-full border border-white/[0.05]">
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`px-3.5 py-1.5 text-xs rounded-full font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-white/10 text-white shadow-sm border border-white/10 backdrop-blur-md'
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

      {/* Status Indicators - Tesla Style Minimalist Badges */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Board Profile */}
        {boardName && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-slate-300 text-xs">
            <span className="text-[10px] text-slate-500 uppercase font-mono">Target</span>
            <span className="font-medium text-slate-200">{boardName}</span>
          </div>
        )}

        {/* Hardware Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06]">
          <div className="relative flex items-center justify-center">
            <div className={`w-2 h-2 rounded-full ${hardwareConnected ? 'bg-emerald-400' : 'bg-slate-500'}`} />
            {hardwareConnected && (
              <div className="absolute w-4 h-4 rounded-full bg-emerald-400/30 animate-ping pointer-events-none" />
            )}
          </div>
          <span className={`text-xs font-medium ${hardwareConnected ? 'text-emerald-400' : 'text-slate-400'}`}>
            {hardwareConnected ? 'Hardware Live' : 'No Device'}
          </span>
        </div>

        {/* Backend Online Indicator */}
        <div
          className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border transition-colors ${
            backendOnline
              ? 'text-slate-300 border-white/[0.08] bg-white/[0.02]'
              : 'text-rose-400 border-rose-500/30 bg-rose-500/10'
          }`}
        >
          <div className={`w-1.5 h-1.5 rounded-full ${backendOnline ? 'bg-cyan-400' : 'bg-rose-400'}`} />
          <span>{backendOnline ? 'Cloud / API' : 'API Offline'}</span>
        </div>
      </div>
    </header>
  );
};
