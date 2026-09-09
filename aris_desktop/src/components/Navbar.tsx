import React from 'react';
import { 
  Cpu, 
  Activity, 
  Code2, 
  Sparkles, 
  Layers, 
  FileText, 
  HardDrive, 
  Usb, 
  RefreshCw, 
  CheckCircle2, 
  PowerOff
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  boards: any[];
  selectedBoardId: string;
  onSelectBoard: (id: string) => void;
  boardDetail: any;
  connected: boolean;
  serialPorts: any[];
  connectedPort: string | null;
  onRefreshPorts: () => void;
  onConnectPort: (port: string) => void;
  onDisconnectPort: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  boards,
  selectedBoardId,
  onSelectBoard,
  boardDetail,
  connected,
  serialPorts,
  connectedPort,
  onRefreshPorts,
  onConnectPort,
  onDisconnectPort
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Live Telemetry', icon: Activity },
    { id: 'code', label: 'Code Studio', icon: Code2 },
    { id: 'optimizer', label: 'AI Optimizer', icon: Sparkles },
    { id: 'memory', label: 'Memory Map', icon: Layers },
    { id: 'patent', label: 'Patent & Report', icon: FileText }
  ];

  return (
    <header className="bg-[#101522] border-b border-slate-800 px-5 py-2.5 flex items-center justify-between shadow-2xl z-30 select-none">
      {/* Brand & Project Identity */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 ring-1 ring-cyan-400/30">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400">
                ARIS STUDIO
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-bold">
                PHYSICAL HARDWARE EDITION
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-tight">
              Real-Time Runtime Intelligence & Architecture-Aware AI
            </p>
          </div>
        </div>

        {/* Board Architecture Selector */}
        <div className="h-6 w-px bg-slate-800 mx-1" />

        <div className="flex items-center gap-2 bg-[#0a0d14] px-3 py-1.5 rounded-lg border border-slate-800">
          <HardDrive className="w-3.5 h-3.5 text-cyan-400" />
          <select
            value={selectedBoardId}
            onChange={(e) => onSelectBoard(e.target.value)}
            className="bg-transparent text-xs font-mono font-bold text-slate-200 focus:outline-none cursor-pointer"
          >
            {boards.map((b) => (
              <option key={b.id} value={b.id} className="bg-[#101522] text-slate-200">
                {b.name} ({b.mcu})
              </option>
            ))}
          </select>
          {boardDetail && (
            <span className="text-[10px] font-mono text-cyan-300/80 bg-cyan-950/50 px-1.5 py-0.5 rounded border border-cyan-800/40">
              {boardDetail.core_frequency_hz / 1e6}MHz | {boardDetail.sram_bytes / 1024}KB RAM
            </span>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 bg-[#0a0d14] p-1 rounded-xl border border-slate-800/80">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Physical Hardware USB COM Port Connector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-[#0a0d14] px-3 py-1 rounded-xl border border-slate-800">
          <Usb className={`w-4 h-4 ${connectedPort ? 'text-emerald-400 animate-pulse' : 'text-slate-400'}`} />
          
          <select
            value={connectedPort || ''}
            onChange={(e) => {
              if (e.target.value) onConnectPort(e.target.value);
              else onDisconnectPort();
            }}
            className="bg-transparent text-xs font-mono text-slate-300 focus:outline-none cursor-pointer max-w-[200px]"
          >
            <option value="" className="bg-[#101522]">Select Arduino COM Port...</option>
            {serialPorts.map((p) => (
              <option key={p.port} value={p.port} className="bg-[#101522]">
                {p.port} — {p.desc}
              </option>
            ))}
          </select>

          <button
            onClick={onRefreshPorts}
            title="Scan USB Ports"
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-cyan-400 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          {connectedPort && (
            <button
              onClick={onDisconnectPort}
              title="Disconnect"
              className="p-1 hover:bg-red-500/20 rounded text-red-400 transition ml-1"
            >
              <PowerOff className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Live Hardware Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800">
          <div className="relative flex items-center justify-center">
            <div className={`w-2 h-2 rounded-full ${connectedPort ? 'bg-emerald-400' : 'bg-slate-600'}`} />
            {connectedPort && (
              <div className="absolute w-4 h-4 rounded-full bg-emerald-400/40 radar-ping" />
            )}
          </div>
          <span className="text-[11px] font-mono font-bold text-slate-300">
            {connectedPort ? `${connectedPort} CONNECTED` : 'DISCONNECTED'}
          </span>
        </div>
      </div>
    </header>
  );
};
