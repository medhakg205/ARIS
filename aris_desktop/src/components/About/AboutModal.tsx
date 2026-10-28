import React from 'react';
import { X, Award, ShieldCheck, Scale, BookOpen, ExternalLink, Cpu, HardDrive } from 'lucide-react';
import { ArisLogo } from '../common/ArisLogo';

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal: React.FC<AboutModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-2xl bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--border-color)] bg-[var(--bg-app)]/50">
          <div className="flex items-center gap-3">
            <ArisLogo size={32} />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-[var(--text-primary)]">ARIS Studio</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/20 font-bold">
                  v3.0.0-PROFESSIONAL
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)]">Adaptive Runtime Intelligence System for Embedded Devices</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[70vh] text-xs">
          <div>
            <h3 className="font-semibold text-[var(--text-primary)] text-sm mb-1.5">Overview</h3>
            <p className="text-[var(--text-muted)] leading-relaxed font-sans">
              ARIS Studio is a professional embedded systems observability, optimization, and closed-loop
              verification platform. It bridges high-level C++ AST transformations with physical MCU
              cycle-accurate runtime telemetry, delivering measurable latency, memory, and energy reductions without
              violating real-time deadlines.
            </p>
          </div>

          {/* Architectural Innovations */}
          <div className="p-4 rounded-xl bg-[var(--bg-app)] border border-[var(--border-color)] space-y-3">
            <div className="flex items-center gap-2 text-[var(--accent-cyan)] font-bold font-mono text-xs">
              <Award className="w-4 h-4" />
              <span>Core System Architecture Innovations</span>
            </div>
            <div className="space-y-2 text-[var(--text-muted)] font-sans">
              <div className="flex items-start gap-2">
                <Scale className="w-4 h-4 text-[var(--accent-cyan)] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[var(--text-primary)]">Claim 1: Deterministic Observer-Effect Compensation</strong> — Mathematically removes
                  instrumentation probe execution cycles from measurements, recovering true hardware latency.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <BookOpen className="w-4 h-4 text-[var(--accent-purple)] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[var(--text-primary)]">Claim 2: AST-Telemetry Multi-Dimensional Grounding</strong> — Direct bidirectional mapping
                  between runtime UART telemetry frames and source-level abstract syntax tree nodes.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-[var(--accent-green)] shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[var(--text-primary)]">Claim 3: Autonomous Closed-Loop Verification &amp; Rollback</strong> — Automated compile,
                  flash, validate, and safe source rollback cycles backed by statistical hypothesis testing.
                </div>
              </div>
            </div>
          </div>

          {/* Specifications Table */}
          <div className="border border-[var(--border-color)] rounded-xl overflow-hidden">
            <table className="w-full font-mono text-[11px] text-left">
              <thead className="bg-[var(--bg-app)] text-[var(--text-muted)] uppercase text-[10px] border-b border-[var(--border-color)]">
                <tr>
                  <th className="py-2 px-3">Subsystem</th>
                  <th className="py-2 px-3">Engine / Version</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-color)] text-[var(--text-primary)]">
                <tr>
                  <td className="py-2 px-3 font-semibold">Compiler Toolchain</td>
                  <td className="py-2 px-3 text-[var(--text-muted)]">Arduino CLI v0.35.3 (avr-gcc / arm-none-eabi)</td>
                  <td className="py-2 px-3 text-[var(--accent-green)] font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">AST Analysis</td>
                  <td className="py-2 px-3 text-[var(--text-muted)]">Clang LibTooling &amp; Tree-sitter C++ Visitor</td>
                  <td className="py-2 px-3 text-[var(--accent-green)] font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">Persistence Engine</td>
                  <td className="py-2 px-3 text-[var(--text-muted)]">SQLite WAL Mode (Zero-copy serialization)</td>
                  <td className="py-2 px-3 text-[var(--accent-green)] font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">Serial Protocol</td>
                  <td className="py-2 px-3 text-[var(--text-muted)]">ARIS Telemetry Framing Protocol v3.0 (CRC16)</td>
                  <td className="py-2 px-3 text-[var(--accent-green)] font-bold">OPERATIONAL</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="pt-2 text-center text-[var(--text-muted)] font-sans text-[11px]">
            &copy; 2026 ARIS Embedded Intelligence System. All rights reserved. Built for mission-critical embedded systems.
          </div>
        </div>
      </div>
    </div>
  );
};
