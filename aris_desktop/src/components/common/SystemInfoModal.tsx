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
  ChevronRight,
  Usb,
  ShieldCheck,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="bg-[#0e121b] border border-white/[0.12] rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-150 text-slate-100"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center text-blue-400 shadow-sm">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white font-samsung tracking-tight">
                  ARIS System Guide & Workflow
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                  v1.0 Architecture
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Understand how ARIS acquires hardware CPU metrics, analyzes code bottlenecks, and provides AI optimizations.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title="Close Guide (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body - 4-Step Interactive Guide */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          {/* Step 1: Getting CPU & Hardware Telemetry */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 transition hover:border-white/[0.12]">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0 mt-0.5">
                <Usb className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white text-sm">
                    1. Connect Hardware & Stream CPU Telemetry
                  </h3>
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    Hardware Stream
                  </span>
                </div>
                <p className="text-slate-300 leading-relaxed font-sans">
                  Plug your bare-metal Arduino (Uno, Nano, or Mega) into any USB port. ARIS automatically probes serial COM ports, retrieves board descriptors, clock speed (16 MHz), and SRAM/Flash boundaries.
                </p>
                <div className="bg-black/30 rounded-lg p-2.5 border border-white/[0.04] text-slate-300 space-y-1 font-mono text-[11px]">
                  <p className="text-emerald-400 font-medium">⚡ To acquire CPU & telemetry metrics:</p>
                  <p>• Click <strong className="text-white bg-white/[0.08] px-1.5 py-0.5 rounded">Start Hardware Stream</strong> on the Dashboard.</p>
                  <p>• Measures: <span className="text-slate-200">CPU Load %, Loop Latency (ms), SRAM Free, Stack Headroom, and Interrupt Frequency (Hz)</span>.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Live Monitor & Veracity Classification */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 transition hover:border-white/[0.12]">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0 mt-0.5">
                <Activity className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white text-sm">
                    2. Real-Time Live Monitor & Veracity Classification
                  </h3>
                  <button
                    onClick={() => { onNavigate('monitor'); onClose(); }}
                    className="text-[11px] font-medium text-blue-400 hover:text-blue-300 flex items-center gap-1 transition"
                  >
                    Open Live Monitor <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
                <p className="text-slate-300 leading-relaxed font-sans">
                  The <strong>Live Monitor</strong> visualizes time-series charts of CPU execution loops, jitter, and memory headroom. Every telemetry value carries a strict veracity tag:
                </p>
                <div className="grid grid-cols-3 gap-2 pt-1 font-sans text-[11px]">
                  <div className="p-2 rounded bg-white/[0.02] border border-emerald-500/20">
                    <span className="text-emerald-400 font-semibold block">MEASURED</span>
                    <span className="text-slate-400 text-[10px]">Physical timer counters & hardware register reads.</span>
                  </div>
                  <div className="p-2 rounded bg-white/[0.02] border border-amber-500/20">
                    <span className="text-amber-400 font-semibold block">ESTIMATED</span>
                    <span className="text-slate-400 text-[10px]">Statistical cycle models & dynamic load estimation.</span>
                  </div>
                  <div className="p-2 rounded bg-white/[0.02] border border-blue-500/20">
                    <span className="text-blue-400 font-semibold block">DERIVED</span>
                    <span className="text-slate-400 text-[10px]">Mathematical inferences (loop jitter, stack delta).</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Antipattern & Bottleneck Analysis */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 transition hover:border-white/[0.12]">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0 mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white text-sm">
                    3. Antipattern Analysis (Where to find bottlenecks)
                  </h3>
                  <button
                    onClick={() => { onNavigate('analysis'); onClose(); }}
                    className="text-[11px] font-medium text-amber-400 hover:text-amber-300 flex items-center gap-1 transition"
                  >
                    Open Analysis <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
                <p className="text-slate-300 leading-relaxed font-sans">
                  Click the <strong>Analysis</strong> tab in the navigation bar to inspect detected code antipatterns. ARIS static AST inspectors catch:
                </p>
                <ul className="list-disc list-inside text-slate-300 space-y-0.5 font-sans">
                  <li><strong>Blocking `delay()` Calls:</strong> Freezes MCU loop execution and drops serial packets.</li>
                  <li><strong>ISR Starvation:</strong> Heavy computation or serial I/O inside Interrupt Service Routines.</li>
                  <li><strong>SRAM Dynamic Allocations:</strong> `malloc`/`String` calls causing heap fragmentation and hard resets.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Step 4: AI Code Optimization & Verified Suggestions */}
          <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 transition hover:border-white/[0.12]">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-white text-sm">
                    4. AI Code Optimization & Verified Patches
                  </h3>
                  <button
                    onClick={() => { onNavigate('optimization'); onClose(); }}
                    className="text-[11px] font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition"
                  >
                    Open Optimization <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
                <p className="text-slate-300 leading-relaxed font-sans">
                  Navigate to the <strong>Optimization</strong> tab to review AI engine suggestions. ARIS generates non-blocking, state-machine code replacements:
                </p>
                <div className="bg-black/30 rounded-lg p-2.5 border border-white/[0.04] text-slate-300 space-y-1 font-sans text-[11px]">
                  <p className="flex items-center gap-1.5 text-indigo-300 font-medium">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    AST-Verified Safety:
                  </p>
                  <p>• Every patch is formally verified against the original Abstract Syntax Tree to ensure pin assignments, sensor baud rates, and timing semantics are preserved without regressions.</p>
                  <p>• Review the side-by-side diff, benchmark before/after empirical metrics, and flash with 1-click.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-white/[0.08] flex items-center justify-between bg-white/[0.02] text-xs">
          <span className="text-[11px] text-slate-500 font-mono">
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/[0.08] text-slate-300 border border-white/[0.1]">Esc</kbd> anytime to return to ARIS
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors shadow-sm"
          >
            Got it, Let's Inspect Hardware
          </button>
        </div>
      </div>
    </div>
  );
};
