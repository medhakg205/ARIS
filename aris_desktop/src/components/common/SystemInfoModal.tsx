// ============================================================
// ARIS — System Workflow & Architecture Guide Modal (INFO)
// Explains the end-to-end workflow: hardware CPU telemetry,
// antipattern analysis, and deterministic AI code optimization.
// ============================================================

import React, { useEffect } from 'react';
import {
  X,
  Cpu,
  Activity,
  AlertTriangle,
  Sparkles,
  Usb,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';

interface SystemInfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (tab: string) => void;
}

export const SystemInfoModal: React.FC<SystemInfoModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="bg-[#12151b] border border-white/[0.12] rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-150 text-slate-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-white/[0.08] flex items-center justify-between bg-[#171b22] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#00878a]/20 border border-[#00878a]/40 flex items-center justify-center text-[#00878a] shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-white font-sans tracking-normal">
                  ARIS System Guide &amp; Architecture
                </h2>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-white/[0.08] text-slate-300 border border-white/[0.1]">
                  v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                End-to-end overview of hardware CPU telemetry, code bottleneck detection, and AI optimization.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.08] transition-colors"
            title="Close Guide (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body - 4 Spacious, Clean Sequential Steps */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          {/* Step 1: Hardware Connection & Telemetry */}
          <div className="bg-[#181c24] border border-white/[0.08] hover:border-emerald-500/30 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                <Usb className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-white font-sans">
                    1. Microcontroller Hardware Connection &amp; Telemetry
                  </h3>
                  <span className="text-[10.5px] font-mono font-medium text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    USB Serial Link
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  Connect your Arduino (Uno, Nano, or Mega) via USB. ARIS auto-detects the COM port, baud rate, and microcontroller architecture without manual configuration.
                </p>
                <div className="bg-[#0e1117] rounded-lg p-3 border border-white/[0.06] text-xs text-slate-300 space-y-1 font-mono">
                  <p className="text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Click <strong>Start Hardware Stream</strong> on Dashboard to begin live sampling.</span>
                  </p>
                  <p className="text-slate-400 pl-5">
                    Captures CPU Load (%), Loop Latency (ms), SRAM Free, Stack Headroom, and Interrupt Rates.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Live Monitor & Veracity Classification */}
          <div className="bg-[#181c24] border border-white/[0.08] hover:border-cyan-500/30 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center shrink-0 mt-0.5">
                <Activity className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-white font-sans">
                    2. Live Monitor &amp; Veracity Classification
                  </h3>
                  <button
                    onClick={() => { onNavigate('monitor'); onClose(); }}
                    className="text-xs font-medium text-[#00878a] hover:text-[#00979d] flex items-center gap-1 transition-colors group"
                  >
                    <span>Open Live Monitor</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  Visualizes time-series charts for loop timing, jitter, and memory headroom. Each metric has an explicit veracity tag so you know exactly how the data was obtained:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
                  {/* Measured - Green */}
                  <div className="p-3 rounded-lg bg-emerald-500/[0.08] border border-emerald-500/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
                      <span className="text-xs font-semibold text-emerald-300 font-mono">Measured</span>
                    </div>
                    <span className="text-[11px] text-slate-300 block leading-snug font-sans">
                      Direct hardware timer &amp; register reads (Loop time, Free SRAM).
                    </span>
                  </div>

                  {/* Estimated - Yellow / Amber */}
                  <div className="p-3 rounded-lg bg-amber-500/[0.08] border border-amber-500/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" />
                      <span className="text-xs font-semibold text-amber-300 font-mono">Estimated</span>
                    </div>
                    <span className="text-[11px] text-slate-300 block leading-snug font-sans">
                      Cycle-calibrated execution models (e.g. CPU Load percentage).
                    </span>
                  </div>

                  {/* Derived - Cyan / Blue */}
                  <div className="p-3 rounded-lg bg-cyan-500/[0.08] border border-cyan-500/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-sm shadow-cyan-400/50" />
                      <span className="text-xs font-semibold text-cyan-300 font-mono">Derived</span>
                    </div>
                    <span className="text-[11px] text-slate-300 block leading-snug font-sans">
                      Mathematical inferences &amp; delta math (e.g. Loop Jitter EMA).
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Antipattern Analysis (Bottleneck Detection) */}
          <div className="bg-[#181c24] border border-white/[0.08] hover:border-rose-500/30 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-400 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-white font-sans">
                    3. Antipattern Analysis (Bottleneck Detection)
                  </h3>
                  <button
                    onClick={() => { onNavigate('analysis'); onClose(); }}
                    className="text-xs font-medium text-[#00878a] hover:text-[#00979d] flex items-center gap-1 transition-colors group"
                  >
                    <span>Open Analysis</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  The <strong>Analysis</strong> tab correlates live hardware performance metrics directly with your source code AST:
                </p>
                <div className="bg-[#0e1117] rounded-lg p-3 border border-white/[0.06] space-y-2 text-xs">
                  {/* Critical - Red */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 shrink-0 mt-0.5">
                      CRITICAL
                    </span>
                    <p className="text-slate-300 leading-relaxed font-sans">
                      <strong className="text-white">Blocking delay() calls:</strong> Freezes MCU main loop, causes severe timing jitter, and drops sensor events.
                    </p>
                  </div>
                  {/* High - Orange/Amber */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 shrink-0 mt-0.5">
                      HIGH
                    </span>
                    <p className="text-slate-300 leading-relaxed font-sans">
                      <strong className="text-white">ISR Starvation:</strong> Costly calculations or Serial prints executed inside interrupt handlers.
                    </p>
                  </div>
                  {/* Medium - Yellow */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-yellow-500/20 text-yellow-300 border border-yellow-500/40 shrink-0 mt-0.5">
                      MEDIUM
                    </span>
                    <p className="text-slate-300 leading-relaxed font-sans">
                      <strong className="text-white">Dynamic Allocation:</strong> String and malloc calls causing heap-stack collisions in limited SRAM.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 4: AI Code Optimization & 1-Click Save Back */}
          <div className="bg-[#181c24] border border-white/[0.08] hover:border-emerald-500/30 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-white font-sans">
                    4. AI Code Optimization &amp; 1-Click Save Back
                  </h3>
                  <button
                    onClick={() => { onNavigate('optimization'); onClose(); }}
                    className="text-xs font-medium text-[#00878a] hover:text-[#00979d] flex items-center gap-1 transition-colors group"
                  >
                    <span>Open Optimization</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">
                  The <strong>Optimization</strong> tab generates verified non-blocking code replacements tailored to your microcontroller:
                </p>
                <div className="bg-[#0e1117] rounded-lg p-3.5 border border-white/[0.06] space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      AST VERIFIED
                    </span>
                    <span className="text-white font-medium font-sans">Preserves pin mappings, registers, and sensor timings</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed font-sans pl-1">
                    Click <strong className="text-white">Save to .ino File</strong> to write the optimized non-blocking code directly to your sketch on disk with an automatic safety backup (<code className="text-slate-300 font-mono">.bak</code>). You can then immediately compile and flash in Arduino IDE!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-white/[0.08] flex items-center justify-between bg-[#171b22] shrink-0 text-xs">
          <span className="text-xs text-slate-400 font-mono">
            Press <kbd className="px-2 py-0.5 rounded bg-white/[0.08] text-slate-300 border border-white/[0.1]">Esc</kbd> to close
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[#00878a] hover:bg-[#00979d] text-white font-medium text-xs transition-colors shadow-sm"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
