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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl animate-in zoom-in-95 duration-150 text-[var(--text-primary)]"
        role="dialog"
        aria-modal="true"
      >
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-app)] shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[var(--accent-cyan-bg)] border border-[var(--accent-cyan)]/30 flex items-center justify-center text-[var(--accent-cyan)] shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-base font-bold text-[var(--text-primary)] font-sans tracking-normal">
                  ARIS System Guide &amp; Architecture
                </h2>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-color)]">
                  v3.0.0
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] font-sans mt-0.5">
                End-to-end overview of hardware CPU telemetry, code bottleneck detection, and verified optimization.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card-hover)] transition-colors"
            title="Close Guide (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body - 4 Spacious, Clean Sequential Steps */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          {/* Step 1: Hardware Connection & Telemetry */}
          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] hover:border-[var(--accent-green)]/40 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-[var(--accent-green-bg)] border border-[var(--accent-green)]/30 text-[var(--accent-green)] flex items-center justify-center shrink-0 mt-0.5">
                <Usb className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] font-sans">
                    1. Microcontroller Hardware Connection &amp; Telemetry
                  </h3>
                  <span className="text-[10.5px] font-mono font-medium text-[var(--accent-green)] bg-[var(--accent-green-bg)] px-2.5 py-0.5 rounded-full border border-[var(--accent-green)]/30 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
                    USB Serial Link
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
                  Connect your Arduino (Uno, Nano, or Mega) via USB. ARIS auto-detects the COM port, baud rate, and microcontroller architecture without manual configuration.
                </p>
                <div className="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border-color)] text-xs text-[var(--text-secondary)] space-y-1 font-mono">
                  <p className="text-[var(--accent-green)] flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--accent-green)] shrink-0" />
                    <span>Click <strong>Start Telemetry Stream</strong> on Dashboard to begin live sampling.</span>
                  </p>
                  <p className="text-[var(--text-muted)] pl-5">
                    Captures CPU Load (%), Loop Latency (ms), SRAM Free, Stack Headroom, and Interrupt Rates.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Live Monitor & Veracity Classification */}
          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] hover:border-[var(--accent-cyan)]/40 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-[var(--accent-cyan-bg)] border border-[var(--accent-cyan)]/30 text-[var(--accent-cyan)] flex items-center justify-center shrink-0 mt-0.5">
                <Activity className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] font-sans">
                    2. Live Monitor &amp; Veracity Classification
                  </h3>
                  <button
                    onClick={() => { onNavigate('monitor'); onClose(); }}
                    className="text-xs font-medium text-[var(--accent-cyan)] hover:opacity-80 flex items-center gap-1 transition-colors group font-mono font-semibold"
                  >
                    <span>Open Live Monitor</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
                  Visualizes time-series charts for loop timing, jitter, and memory headroom. Each metric has an explicit veracity tag so you know exactly how the data was obtained:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
                  {/* Measured - Green */}
                  <div className="p-3 rounded-lg bg-[var(--accent-green-bg)] border border-[var(--accent-green)]/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-[var(--accent-green)]" />
                      <span className="text-xs font-semibold text-[var(--accent-green)] font-mono">Measured</span>
                    </div>
                    <span className="text-[11px] text-[var(--text-secondary)] block leading-snug font-sans">
                      Direct hardware timer &amp; register reads (Loop time, Free SRAM).
                    </span>
                  </div>

                  {/* Estimated - Yellow / Amber */}
                  <div className="p-3 rounded-lg bg-[var(--accent-amber-bg)] border border-[var(--accent-amber)]/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-[var(--accent-amber)]" />
                      <span className="text-xs font-semibold text-[var(--accent-amber)] font-mono">Estimated</span>
                    </div>
                    <span className="text-[11px] text-[var(--text-secondary)] block leading-snug font-sans">
                      Cycle-calibrated execution models (e.g. CPU Load percentage).
                    </span>
                  </div>

                  {/* Derived - Cyan / Blue */}
                  <div className="p-3 rounded-lg bg-[var(--accent-cyan-bg)] border border-[var(--accent-cyan)]/30">
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="w-2 h-2 rounded-full bg-[var(--accent-cyan)]" />
                      <span className="text-xs font-semibold text-[var(--accent-cyan)] font-mono">Derived</span>
                    </div>
                    <span className="text-[11px] text-[var(--text-secondary)] block leading-snug font-sans">
                      Mathematical inferences &amp; delta math (e.g. Loop Jitter EMA).
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Antipattern Analysis (Bottleneck Detection) */}
          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] hover:border-[var(--accent-red)]/40 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-[var(--accent-red-bg)] border border-[var(--accent-red)]/30 text-[var(--accent-red)] flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] font-sans">
                    3. Antipattern Analysis (Bottleneck Detection)
                  </h3>
                  <button
                    onClick={() => { onNavigate('analysis'); onClose(); }}
                    className="text-xs font-medium text-[var(--accent-cyan)] hover:opacity-80 flex items-center gap-1 transition-colors group font-mono font-semibold"
                  >
                    <span>Open Analysis</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
                  The <strong>Analysis</strong> tab correlates live hardware performance metrics directly with your source code AST:
                </p>
                <div className="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--border-color)] space-y-2 text-xs">
                  {/* Critical - Red */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--accent-red-bg)] text-[var(--accent-red)] border border-[var(--accent-red)]/40 shrink-0 mt-0.5">
                      CRITICAL
                    </span>
                    <p className="text-[var(--text-secondary)] leading-relaxed font-sans">
                      <strong className="text-[var(--text-primary)]">Blocking delay() calls:</strong> Freezes MCU main loop, causes severe timing jitter, and drops sensor events.
                    </p>
                  </div>
                  {/* High - Orange/Amber */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/40 shrink-0 mt-0.5">
                      HIGH
                    </span>
                    <p className="text-[var(--text-secondary)] leading-relaxed font-sans">
                      <strong className="text-[var(--text-primary)]">ISR Starvation:</strong> Costly calculations or Serial prints executed inside interrupt handlers.
                    </p>
                  </div>
                  {/* Medium - Yellow */}
                  <div className="flex items-start gap-2.5">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--accent-amber-bg)] text-[var(--accent-amber)] border border-[var(--accent-amber)]/30 shrink-0 mt-0.5">
                      MEDIUM
                    </span>
                    <p className="text-[var(--text-secondary)] leading-relaxed font-sans">
                      <strong className="text-[var(--text-primary)]">Dynamic Allocation:</strong> String and malloc calls causing heap-stack collisions in limited SRAM.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Step 4: AI Code Optimization & 1-Click Save Back */}
          <div className="bg-[var(--bg-app)] border border-[var(--border-color)] hover:border-[var(--accent-green)]/40 rounded-xl p-5 transition-colors">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 rounded-lg bg-[var(--accent-green-bg)] border border-[var(--accent-green)]/30 text-[var(--accent-green)] flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <h3 className="text-sm font-semibold text-[var(--text-primary)] font-sans">
                    4. Verified Code Optimization &amp; Local Source Application
                  </h3>
                  <button
                    onClick={() => { onNavigate('optimization'); onClose(); }}
                    className="text-xs font-medium text-[var(--accent-cyan)] hover:opacity-80 flex items-center gap-1 transition-colors group font-mono font-semibold"
                  >
                    <span>Open Optimization</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
                  The <strong>Optimization</strong> tab generates verified non-blocking code replacements tailored to your microcontroller:
                </p>
                <div className="bg-[var(--bg-card)] rounded-lg p-3.5 border border-[var(--border-color)] space-y-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/40">
                      AST VERIFIED
                    </span>
                    <span className="text-[var(--text-primary)] font-medium font-sans">Preserves pin mappings, registers, and sensor timings</span>
                  </div>
                  <p className="text-[var(--text-secondary)] leading-relaxed font-sans pl-1">
                    Click <strong className="text-[var(--text-primary)]">Accept Optimization</strong> to apply the verified non-blocking code directly to your sketch on disk with an automatic safety backup (<code className="text-[var(--accent-cyan)] font-mono">.aris/backups/</code>). You can also revert to original source at any time with 1-click rollback!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-[var(--border-color)] flex items-center justify-between bg-[var(--bg-app)] shrink-0 text-xs">
          <span className="text-xs text-[var(--text-muted)] font-mono">
            Press <kbd className="px-2 py-0.5 rounded bg-[var(--bg-card)] text-[var(--text-secondary)] border border-[var(--border-color)]">Esc</kbd> to close
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[var(--accent-cyan)] hover:opacity-90 text-white font-medium text-xs transition-opacity shadow-sm"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
