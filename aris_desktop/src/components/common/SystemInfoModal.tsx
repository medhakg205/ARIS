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
        className="bg-[#22272e] border border-white/[0.1] rounded-xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-150 text-slate-200"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between bg-black/10">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded bg-[#00878a]/20 border border-[#00878a]/40 flex items-center justify-center text-[#00878a]">
              <Cpu className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-slate-100 font-samsung tracking-tight">
                  ARIS System Guide & Architecture
                </h2>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.06] text-slate-400">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                Overview of hardware CPU telemetry, code bottleneck analysis, and AI optimization.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/[0.06] transition-colors"
            title="Close Guide (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body - 4 Clean Sequential Steps */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3 text-xs">
          {/* Step 1: Getting CPU & Hardware Telemetry */}
          <div className="bg-[#1c2128] border border-white/[0.06] rounded-lg p-3.5">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded bg-white/[0.04] text-slate-300 shrink-0 mt-0.5">
                <Usb className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-slate-200 text-xs">
                    1. Microcontroller Hardware Connection & Telemetry
                  </h3>
                  <span className="text-[10px] font-mono text-slate-400 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.08]">
                    USB Serial
                  </span>
                </div>
                <p className="text-slate-400 leading-relaxed font-sans text-[11px]">
                  Connect your Arduino (Uno, Nano, or Mega) via USB. ARIS auto-detects the COM port, baud rate, and microcontroller architecture.
                </p>
                <div className="bg-black/20 rounded p-2 border border-white/[0.04] text-slate-400 space-y-0.5 font-mono text-[10.5px]">
                  <p className="text-slate-300">• Click <strong className="text-white">Start Hardware Stream</strong> on the Dashboard.</p>
                  <p>• Telemetry includes CPU Load (%), Loop Latency (ms), SRAM Free, Stack Headroom, and Interrupt Frequency.</p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Live Monitor & Veracity Classification */}
          <div className="bg-[#1c2128] border border-white/[0.06] rounded-lg p-3.5">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded bg-white/[0.04] text-slate-300 shrink-0 mt-0.5">
                <Activity className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-slate-200 text-xs">
                    2. Live Monitor & Veracity Classification
                  </h3>
                  <button
                    onClick={() => { onNavigate('monitor'); onClose(); }}
                    className="text-[10.5px] text-[#00878a] hover:underline flex items-center gap-0.5"
                  >
                    Open Live Monitor →
                  </button>
                </div>
                <p className="text-slate-400 leading-relaxed font-sans text-[11px]">
                  Visualizes time-series charts for loop timing, jitter, and memory headroom. Each metric has an explicit veracity tag:
                </p>
                <div className="grid grid-cols-3 gap-2 pt-1 font-sans text-[10.5px]">
                  <div className="p-2 rounded bg-black/20 border border-white/[0.04]">
                    <span className="text-slate-200 font-medium block">Measured</span>
                    <span className="text-slate-500 text-[9.5px]">Direct timer & register reads.</span>
                  </div>
                  <div className="p-2 rounded bg-black/20 border border-white/[0.04]">
                    <span className="text-slate-200 font-medium block">Estimated</span>
                    <span className="text-slate-500 text-[9.5px]">Execution cycle models.</span>
                  </div>
                  <div className="p-2 rounded bg-black/20 border border-white/[0.04]">
                    <span className="text-slate-200 font-medium block">Derived</span>
                    <span className="text-slate-500 text-[9.5px]">Mathematical inferences.</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Antipattern & Bottleneck Analysis */}
          <div className="bg-[#1c2128] border border-white/[0.06] rounded-lg p-3.5">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded bg-white/[0.04] text-slate-300 shrink-0 mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-slate-200 text-xs">
                    3. Antipattern Analysis (Bottleneck Detection)
                  </h3>
                  <button
                    onClick={() => { onNavigate('analysis'); onClose(); }}
                    className="text-[10.5px] text-[#00878a] hover:underline flex items-center gap-0.5"
                  >
                    Open Analysis →
                  </button>
                </div>
                <p className="text-slate-400 leading-relaxed font-sans text-[11px]">
                  The <strong>Analysis</strong> tab correlates hardware metrics with your source code AST:
                </p>
                <ul className="list-disc list-inside text-slate-400 space-y-0.5 font-sans text-[11px]">
                  <li><strong className="text-slate-300">Blocking delay() calls:</strong> Stalls the main loop and causes jitter.</li>
                  <li><strong className="text-slate-300">ISR Starvation:</strong> Expensive computation inside interrupt handlers.</li>
                  <li><strong className="text-slate-300">Dynamic Allocation:</strong> Heap fragmentation caused by String/malloc.</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Step 4: AI Code Optimization & Verified Suggestions */}
          <div className="bg-[#1c2128] border border-white/[0.06] rounded-lg p-3.5">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded bg-white/[0.04] text-slate-300 shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-slate-200 text-xs">
                    4. AI Code Optimization & 1-Click Save Back
                  </h3>
                  <button
                    onClick={() => { onNavigate('optimization'); onClose(); }}
                    className="text-[10.5px] text-[#00878a] hover:underline flex items-center gap-0.5"
                  >
                    Open Optimization →
                  </button>
                </div>
                <p className="text-slate-400 leading-relaxed font-sans text-[11px]">
                  The <strong>Optimization</strong> tab generates non-blocking code replacements:
                </p>
                <div className="bg-black/20 rounded p-2 border border-white/[0.04] text-slate-400 space-y-0.5 font-sans text-[10.5px]">
                  <p className="text-slate-300 font-medium">AST-Verified Safety:</p>
                  <p>• Preserves pin assignments, hardware registers, and sensor timings.</p>
                  <p>• Click <strong className="text-white">Save to .ino File</strong> to update your sketch on disk with a safety backup (.bak), then compile in Arduino IDE.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-white/[0.08] flex items-center justify-between bg-black/10 text-xs">
          <span className="text-[11px] text-slate-500 font-mono">
            Press <kbd className="px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-400 border border-white/[0.08]">Esc</kbd> to close
          </span>
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded bg-[#00878a] hover:bg-[#00979d] text-white font-medium text-xs transition-colors shadow-sm"
          >
            Close Guide
          </button>
        </div>
      </div>

    </div>
  );
};
