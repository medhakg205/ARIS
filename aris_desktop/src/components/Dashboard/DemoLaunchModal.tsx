import React, { useState, useEffect } from 'react';
import {
  X,
  Cpu,
  Zap,
  Play,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Sparkles,
  Info,
  ChevronRight,
  Layers,
} from 'lucide-react';
import type { DemoProject, DemoBoard } from '../../types';
import { apiListDemoProjects, apiListDemoBoards } from '../../services/api';

interface DemoLaunchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLaunch: (boardId: string, projectId: string) => Promise<void>;
}

export const DemoLaunchModal: React.FC<DemoLaunchModalProps> = ({
  isOpen,
  onClose,
  onLaunch,
}) => {
  const [boards, setBoards] = useState<DemoBoard[]>([]);
  const [projects, setProjects] = useState<DemoProject[]>([]);
  const [selectedBoardId, setSelectedBoardId] = useState<string>('arduino_uno');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('led_blink');
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      Promise.all([apiListDemoBoards(), apiListDemoProjects()])
        .then(([b, p]) => {
          setBoards(b);
          setProjects(p);
          if (b.length > 0 && !selectedBoardId) {
            setSelectedBoardId(b[0].board_id);
          }
          if (p.length > 0 && !selectedProjectId) {
            setSelectedProjectId(p[0].project_id);
          }
        })
        .catch((err) => {
          console.error('Failed to load demo metadata', err);
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const selectedProject = projects.find((p) => p.project_id === selectedProjectId) || projects[0];
  const selectedBoard = boards.find((b) => b.board_id === selectedBoardId) || boards[0];

  const handleConfirmLaunch = async () => {
    if (!selectedBoardId || !selectedProjectId || launching) return;
    setLaunching(true);
    try {
      await onLaunch(selectedBoardId, selectedProjectId);
      onClose();
    } catch (err) {
      console.error('Failed to launch demo:', err);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#12151a] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-[#161a22]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#00878a]/20 border border-[#00878a]/40 flex items-center justify-center text-[#00c4c7]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white tracking-wide flex items-center gap-2">
                Virtual Hardware Simulation Demo
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20">
                  Interactive Lab
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Explore ARIS runtime telemetry, automated static diagnostics, and AI optimization candidates without physical hardware.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {/* Step 1: Select Target Microcontroller */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#00878a]/20 border border-[#00878a]/40 text-[#00c4c7] flex items-center justify-center text-[10px]">
                  1
                </span>
                Select Virtual Microcontroller Target
              </label>
              <span className="text-[11px] text-slate-400">Exact clock & memory emulation</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {boards.map((b) => {
                const isSelected = b.board_id === selectedBoardId;
                return (
                  <button
                    key={b.board_id}
                    onClick={() => setSelectedBoardId(b.board_id)}
                    className={`relative text-left p-3.5 rounded-xl border transition-all ${
                      isSelected
                        ? 'bg-[#1a232f] border-[#00878a] shadow-lg shadow-[#00878a]/10 ring-1 ring-[#00878a]'
                        : 'bg-[#161a22] border-white/5 hover:border-white/15 hover:bg-[#1a1f28]'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Cpu className={`w-4 h-4 ${isSelected ? 'text-teal-400' : 'text-slate-400'}`} />
                        <span className="text-sm font-semibold text-white">{b.display_name}</span>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className="w-4 h-4 text-teal-400 animate-in zoom-in-50" />
                      )}
                    </div>
                    <div className="mt-2 text-[11px] text-slate-400 space-y-0.5">
                      <div className="flex justify-between">
                        <span>MCU:</span>
                        <span className="font-mono text-slate-200">{b.mcu}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Clock / SRAM:</span>
                        <span className="font-mono text-slate-200">
                          {b.clock_mhz} MHz / {b.sram_kb} KB
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Flash Storage:</span>
                        <span className="font-mono text-slate-200">{b.flash_kb} KB</span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Step 2: Select Example Scenario */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-[#00878a]/20 border border-[#00878a]/40 text-[#00c4c7] flex items-center justify-center text-[10px]">
                  2
                </span>
                Select Example Project & Anti-Pattern Scenario
              </label>
              <span className="text-[11px] text-slate-400">6 Curated Real-World Case Studies</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {projects.map((p) => {
                const isSelected = p.project_id === selectedProjectId;
                return (
                  <button
                    key={p.project_id}
                    onClick={() => setSelectedProjectId(p.project_id)}
                    className={`relative text-left p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                      isSelected
                        ? 'bg-[#1a232f] border-[#00878a] shadow-lg shadow-[#00878a]/10 ring-1 ring-[#00878a]'
                        : 'bg-[#161a22] border-white/5 hover:border-white/15 hover:bg-[#1a1f28]'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{p.icon}</span>
                          <span className="text-xs font-semibold text-white leading-tight">
                            {p.title}
                          </span>
                        </div>
                        {isSelected && (
                          <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                        )}
                      </div>

                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed mb-2.5">
                        {p.description}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1 mt-auto">
                      {p.antipatterns.map((ap, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300/90 border border-amber-500/20 font-mono"
                        >
                          ⚠ {ap}
                        </span>
                      ))}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Deep Dive Breakdown Card for Selected Scenario */}
          {selectedProject && (
            <div className="bg-[#161a22] border border-white/10 rounded-xl p-4.5 space-y-3">
              <div className="flex items-center justify-between border-b border-white/10 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{selectedProject.icon}</span>
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-teal-400">
                      Scenario Deep Dive: {selectedProject.title}
                    </h4>
                    <span className="text-[11px] text-slate-400">{selectedProject.category}</span>
                  </div>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 text-slate-300 border border-white/10">
                  Target: {selectedBoard?.display_name}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                {/* How usually coded */}
                <div className="bg-[#12151a] p-3 rounded-lg border border-red-500/20 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-red-400">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    How It's Usually Coded
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Beginners rely on blocking loops, repeated serial spam, and heavy software floating-point math without non-blocking schedulers.
                  </p>
                </div>

                {/* What ARIS AI Finds */}
                <div className="bg-[#12151a] p-3 rounded-lg border border-amber-500/20 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400">
                    <Sparkles className="w-3.5 h-3.5" />
                    What ARIS Engine Detects
                  </div>
                  <ul className="text-[11px] text-slate-300 space-y-1 list-disc list-inside">
                    {selectedProject.antipatterns.map((ap, i) => (
                      <li key={i} className="truncate">
                        {ap}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* How ARIS Optimizes */}
                <div className="bg-[#12151a] p-3 rounded-lg border border-teal-500/20 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-400">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    How ARIS Optimizes It
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed">
                    Synthesizes non-blocking state machines, ISR event handlers, integer fixed-point LUTs, and differential telemetry streams.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-[#161a22]">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Info className="w-4 h-4 text-slate-500" />
            <span>Actual USB hardware plugged in will seamlessly override demo mode anytime.</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              disabled={launching}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirmLaunch}
              disabled={launching || loading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#00878a] hover:bg-[#009da0] text-white text-xs font-semibold tracking-wide transition-all shadow-lg shadow-[#00878a]/20 disabled:opacity-50"
            >
              {launching ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Initializing Simulation...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Launch Virtual Demo ({selectedBoard?.display_name})
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
