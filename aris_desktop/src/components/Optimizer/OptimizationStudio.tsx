import React from 'react';
import { 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  Zap, 
  Database, 
  Clock, 
  TrendingDown, 
  ShieldCheck, 
  Copy, 
  Check, 
  Cpu, 
  RotateCcw 
} from 'lucide-react';
import { AIOptimizationResult, ClosedLoopVerificationReport, HardwareProfile } from '../../types';

interface OptimizationStudioProps {
  optimizationResult: AIOptimizationResult | null;
  verificationReport: ClosedLoopVerificationReport | null;
  boardDetail: HardwareProfile | null;
  onApplyOptimization: (code: string) => void;
  onRunVerification: () => void;
}

export const OptimizationStudio: React.FC<OptimizationStudioProps> = ({
  optimizationResult,
  verificationReport,
  boardDetail,
  onApplyOptimization,
  onRunVerification
}) => {
  const [copied, setCopied] = React.useState<boolean>(false);

  if (!optimizationResult) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono text-xs">
        <Sparkles className="w-10 h-10 text-purple-400 mx-auto mb-3 animate-pulse" />
        <h3 className="text-slate-300 font-bold text-sm">No Active Optimization Run</h3>
        <p className="mt-1">Go to Code Studio and click "Optimize with AI" to generate architecture-aware refactorings.</p>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(optimizationResult.optimized_candidate_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Executive Summary Header */}
      <div className="bg-gradient-to-r from-purple-950/40 via-[#101522] to-blue-950/40 border border-purple-500/30 p-5 rounded-2xl shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-purple-500/20 border border-purple-500/40 text-purple-300 shadow-lg shadow-purple-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-extrabold text-white">
                  ARIS Architecture-Aware AI Refactor Engine
                </h2>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40">
                  {optimizationResult.theoretical_speedup_factor}x Theoretical Speedup
                </span>
              </div>
              <p className="text-xs text-slate-300 font-mono mt-1">
                {optimizationResult.executive_summary}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-bold transition border border-slate-700"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-slate-400" />}
              <span>{copied ? 'Copied' : 'Copy Code'}</span>
            </button>

            <button
              onClick={() => onApplyOptimization(optimizationResult.optimized_candidate_code)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-mono font-bold transition shadow-lg shadow-emerald-600/20"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Apply Optimization</span>
            </button>
          </div>
        </div>

        {/* Applied Transforms Tags */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap gap-2">
          {optimizationResult.applied_transforms.map((t, idx) => (
            <span 
              key={idx} 
              className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-purple-950/60 text-purple-200 border border-purple-800/50 flex items-center gap-1.5"
            >
              <Zap className="w-3 h-3 text-purple-400" />
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Closed-Loop Hardware Benchmark Verification Grid */}
      {verificationReport && (
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wider">
                Closed-Loop Empirical Verification Matrix ({boardDetail?.name})
              </h3>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-800/50">
              Score: {verificationReport.net_performance_score_before} → {verificationReport.net_performance_score_after} (+{verificationReport.total_score_delta} pts)
            </span>
          </div>

          <div className="grid grid-cols-5 gap-4">
            {verificationReport.metrics.map((m, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-[#0a0d14] border border-slate-800 relative overflow-hidden">
                <span className="text-[10px] font-mono text-slate-400 block truncate">{m.metric_name}</span>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-xs font-mono text-slate-500 line-through">
                    {m.original_value}
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-400">
                    → {m.optimized_value} {m.unit}
                  </span>
                </div>
                <div className="mt-2 text-[11px] font-mono font-bold text-emerald-300">
                  {m.percentage_improvement > 0 ? `-${m.percentage_improvement}%` : `+${Math.abs(m.percentage_improvement)}%`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-Side Code Diff (Original vs Optimized) */}
      <div className="grid grid-cols-2 gap-6">
        {/* Original Baseline Code */}
        <div className="bg-[#101522] border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col">
          <div className="bg-[#0d121f] px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-400">Baseline Firmware (Before)</span>
            <span className="text-[10px] font-mono text-amber-400/80 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40">
              Antipatterns Present
            </span>
          </div>
          <textarea
            value={optimizationResult.original_code}
            readOnly
            className="flex-1 p-4 bg-[#0a0d14] text-slate-400 font-mono text-xs leading-relaxed resize-none focus:outline-none min-h-[360px]"
          />
        </div>

        {/* Optimized Candidate Code */}
        <div className="bg-[#101522] border border-emerald-500/30 rounded-2xl shadow-xl overflow-hidden flex flex-col neon-border-green">
          <div className="bg-[#0d121f] px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-emerald-400">ARIS Optimized Candidate (After)</span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
              Hardware Verified
            </span>
          </div>
          <textarea
            value={optimizationResult.optimized_candidate_code}
            readOnly
            className="flex-1 p-4 bg-[#071318] text-emerald-300 font-mono text-xs leading-relaxed resize-none focus:outline-none min-h-[360px]"
          />
        </div>
      </div>
    </div>
  );
};
