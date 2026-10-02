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
        className="w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border bg-app/50">
          <div className="flex items-center gap-3">
            <ArisLogo size={32} />
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-fg">ARIS Studio</h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 font-bold">
                  v3.0.0-PROFESSIONAL
                </span>
              </div>
              <p className="text-xs text-muted">Adaptive Runtime Intelligence System for Embedded Devices</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted hover:text-fg hover:bg-hover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[70vh] text-xs">
          <div>
            <h3 className="font-semibold text-fg text-sm mb-1.5">Overview</h3>
            <p className="text-muted leading-relaxed font-sans">
              ARIS Studio is a professional-grade embedded systems observability, optimization, and closed-loop
              verification platform. It autonomously bridges high-level C++ AST transformations with physical MCU
              cycle-accurate runtime telemetry, delivering measurable latency, memory, and energy reductions without
              violating real-time deadlines.
            </p>
          </div>

          {/* Patent Novelty Claims */}
          <div className="p-4 rounded-xl bg-app border border-border space-y-3">
            <div className="flex items-center gap-2 text-accent-cyan font-bold font-mono text-xs">
              <Award className="w-4 h-4" />
              <span>Core Patent-Grade Innovations</span>
            </div>
            <div className="space-y-2 text-muted font-sans">
              <div className="flex items-start gap-2">
                <Scale className="w-4 h-4 text-accent-cyan shrink-0 mt-0.5" />
                <div>
                  <strong className="text-fg">Claim 1: Deterministic Observer-Effect Compensation</strong> — Mathematically removes
                  instrumentation probe execution cycles from measurements, recovering true hardware latency.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <BookOpen className="w-4 h-4 text-accent-purple shrink-0 mt-0.5" />
                <div>
                  <strong className="text-fg">Claim 2: AST-Telemetry Multi-Dimensional Grounding</strong> — Direct bidirectional mapping
                  between runtime UART telemetry frames and source-level abstract syntax tree nodes.
                </div>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
                <div>
                  <strong className="text-fg">Claim 3: Autonomous Closed-Loop Verification &amp; Rollback</strong> — Self-driving compile,
                  flash, validate, and microsecond rollback cycles backed by statistical hypothesis testing.
                </div>
              </div>
            </div>
          </div>

          {/* Specifications Table */}
          <div className="border border-border rounded-xl overflow-hidden">
            <table className="w-full font-mono text-[11px] text-left">
              <thead className="bg-app text-muted uppercase text-[10px] border-b border-border">
                <tr>
                  <th className="py-2 px-3">Subsystem</th>
                  <th className="py-2 px-3">Engine / Version</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-fg">
                <tr>
                  <td className="py-2 px-3 font-semibold">Compiler Toolchain</td>
                  <td className="py-2 px-3 text-muted">Arduino CLI v0.35.3 (avr-gcc / arm-none-eabi)</td>
                  <td className="py-2 px-3 text-accent-green font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">AST Analysis</td>
                  <td className="py-2 px-3 text-muted">Clang LibTooling &amp; Tree-sitter C++ Visitor</td>
                  <td className="py-2 px-3 text-accent-green font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">Persistence Engine</td>
                  <td className="py-2 px-3 text-muted">SQLite WAL Mode (Zero-copy serialization)</td>
                  <td className="py-2 px-3 text-accent-green font-bold">OPERATIONAL</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 font-semibold">Serial Protocol</td>
                  <td className="py-2 px-3 text-muted">ARIS Telemetry Framing Protocol v3.0 (CRC16)</td>
                  <td className="py-2 px-3 text-accent-green font-bold">OPERATIONAL</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="pt-2 text-center text-muted font-sans text-[11px]">
            &copy; 2026 ARIS Embedded Intelligence System. All rights reserved. Built for mission-critical embedded systems.
          </div>
        </div>
      </div>
    </div>
  );
};
