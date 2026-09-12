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
    <header className="h-10 bg-[#0d121f] border-b border-slate-800/80 flex items-center px-4 gap-6 shrink-0 select-none">
      {/* Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <Cpu className="w-4 h-4 text-cyan-400" />
        <span className="text-sm font-mono font-bold text-slate-100 tracking-widest">ARIS</span>
        <span className="text-[10px] font-mono text-slate-500 tracking-widest">v1.0</span>
      </div>

      <div className="w-px h-5 bg-slate-800" />

      {/* Nav Tabs */}
      <nav className="flex items-center gap-0.5">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onTabChange(item.id)}
            className={`px-3 h-8 text-[11px] font-mono rounded transition-colors ${
              activeTab === item.id
                ? 'bg-slate-800 text-cyan-400'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="flex-1" />

      {/* Demo Banner */}
      <DemoBanner visible={isDemo} />

      {/* Status Indicators */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Board */}
        {boardName && (
          <span className="text-[10px] font-mono text-slate-400">{boardName}</span>
        )}

        {/* Hardware connection */}
        <div className="flex items-center gap-1.5">
          {hardwareConnected ? (
            <><div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] font-mono text-emerald-400">Connected</span></>
          ) : (
            <><div className="w-1.5 h-1.5 rounded-full bg-slate-600" />
            <span className="text-[10px] font-mono text-slate-500">Disconnected</span></>
          )}
        </div>

        {/* Backend */}
        <div
          className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
            backendOnline
              ? 'text-slate-400 border-slate-700'
              : 'text-red-400 border-red-800/50 bg-red-900/20'
          }`}
        >
          {backendOnline ? 'API Online' : 'API Offline'}
        </div>
      </div>
    </header>
  );
};
