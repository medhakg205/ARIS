import React, { useState } from 'react';
import { FileText, Copy, Check, Download, ShieldCheck, Award, Scale, BookOpen } from 'lucide-react';
import { HardwareProfile } from '../../types';

interface PatentStudioProps {
  patentMarkdown: string;
  boardDetail: HardwareProfile | null;
}

export const PatentStudio: React.FC<PatentStudioProps> = ({
  patentMarkdown,
  boardDetail
}) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(patentMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([patentMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ARIS_Patent_Disclosure_${boardDetail?.id || 'mcu'}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-tr from-amber-500/20 to-orange-500/20 border border-amber-500/40 text-amber-300">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-extrabold text-white">
                Patent Disclosure Specification & Research Dissertation Studio
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                PATENT-WORTHY NOVELTY
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Formal IEEE-formatted patent claims, mathematical proofs of watermarking, and empirical verification.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-bold transition border border-slate-700"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400" />}
            <span>{copied ? 'Copied' : 'Copy Document'}</span>
          </button>

          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white text-xs font-mono font-bold transition shadow-lg shadow-amber-600/20"
          >
            <Download className="w-4 h-4" />
            <span>Export Markdown / PDF</span>
          </button>
        </div>
      </div>

      {/* 3 Patent Pillars Cards */}
      <div className="grid grid-cols-3 gap-6">
        <div className="p-5 rounded-2xl bg-[#101522] border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold font-mono">
            <Scale className="w-4 h-4" />
            <span>Claim 1: Observer-Effect Self-Compensation</span>
          </div>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Eliminates profiler overhead distortions via deterministic cycle-subtraction model ($T_{'{actual}'} = T_{'{measured}'} - \sum C_{'{probe}'}$).
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#101522] border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-purple-400 text-xs font-bold font-mono">
            <BookOpen className="w-4 h-4" />
            <span>Claim 2: Static-Dynamic AST Correlation</span>
          </div>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Multi-dimensional correlation matrix mapping runtime UART packets directly to C++ AST nodes and Flash memory sections.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#101522] border border-slate-800 space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold font-mono">
            <ShieldCheck className="w-4 h-4" />
            <span>Claim 3: Closed-Loop AI Optimization</span>
          </div>
          <p className="text-xs text-slate-400 font-mono leading-relaxed">
            Architecture-aware refactoring that automatically validates candidates on hardware for verified speedup & SRAM recovery.
          </p>
        </div>
      </div>

      {/* Rendered Document Preview */}
      <div className="bg-[#101522] border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="prose prose-invert max-w-none font-mono text-xs leading-relaxed space-y-4">
          <pre className="p-5 rounded-xl bg-[#0a0d14] border border-slate-800 text-slate-300 overflow-x-auto whitespace-pre-wrap selection:bg-amber-500 selection:text-black">
            {patentMarkdown || 'Generating comprehensive patent specification... Run "Optimize with AI" to populate.'}
          </pre>
        </div>
      </div>
    </div>
  );
};
