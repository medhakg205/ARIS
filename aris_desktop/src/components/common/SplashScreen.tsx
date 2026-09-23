import React, { useState, useEffect } from 'react';
import { Cpu, Zap, Activity } from 'lucide-react';

interface SplashScreenProps {
  onFinish: () => void;
  minDurationMs?: number;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({
  onFinish,
  minDurationMs = 3200,
}) => {
  const [stage, setStage] = useState<number>(1); // 1: Hex Draw, 2: Monogram Ignite, 3: ARIS Reveal, 4: Subtitle, 5: FadeOut
  const [statusText, setStatusText] = useState<string>('INITIALIZING RUNTIME CORE...');

  useEffect(() => {
    // Stage 1 -> Stage 2: Ignite Monogram
    const t1 = setTimeout(() => {
      setStage(2);
      setStatusText('ENGAGING HARDWARE BUS MONITOR...');
    }, 700);

    // Stage 2 -> Stage 3: ARIS Brand Title Reveal
    const t2 = setTimeout(() => {
      setStage(3);
      setStatusText('SYNCHRONIZING EMBEDDED DIAGNOSTICS...');
    }, 1500);

    // Stage 3 -> Stage 4: Subtitle Full Form Reveal
    const t3 = setTimeout(() => {
      setStage(4);
      setStatusText('SYSTEM READY');
    }, 2200);

    // Stage 4 -> Stage 5: Dissolve Transition
    const t4 = setTimeout(() => {
      setStage(5);
    }, minDurationMs);

    // Final Finish
    const t5 = setTimeout(() => {
      onFinish();
    }, minDurationMs + 500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
    };
  }, [minDurationMs, onFinish]);

  const handleSkip = () => {
    setStage(5);
    setTimeout(onFinish, 200);
  };

  return (
    <div
      onClick={handleSkip}
      className={`fixed inset-0 z-[9999] bg-[#0c0e12] flex flex-col items-center justify-center select-none cursor-pointer overflow-hidden transition-all duration-700 ease-out ${
        stage === 5 ? 'opacity-0 scale-105 pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      {/* Background Animated Engineering Grid & Glow */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#161a2218_1px,transparent_1px),linear-gradient(to_bottom,#161a2218_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div className="absolute w-[500px] h-[500px] rounded-full bg-[#00878a]/15 blur-[120px] pointer-events-none animate-pulse" />

      {/* Center Cinematic Logo Container */}
      <div className="relative flex flex-col items-center z-10">
        {/* Animated Vector Logo */}
        <div className="relative w-36 h-36 sm:w-44 sm:h-44 flex items-center justify-center">
          <svg
            viewBox="0 0 200 200"
            className="w-full h-full drop-shadow-[0_0_25px_rgba(0,196,199,0.35)]"
            fill="none"
          >
            <defs>
              <linearGradient id="splashTeal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="50%" stopColor="#00c4c7" />
                <stop offset="100%" stopColor="#00878a" />
              </linearGradient>

              <linearGradient id="splashGold" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#e5a93c" />
                <stop offset="100%" stopColor="#ffd56b" />
              </linearGradient>

              <filter id="splashGlow" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="4.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Outer Hexagon Chassis with Dash Animation */}
            <polygon
              points="100,28 162.35,64 162.35,136 100,172 37.65,136 37.65,64"
              stroke="url(#splashTeal)"
              strokeWidth="5"
              strokeLinejoin="round"
              filter="url(#splashGlow)"
              className="transition-all duration-1000 ease-out fill-[#161a22]/80"
              style={{
                strokeDasharray: 450,
                strokeDashoffset: stage >= 1 ? 0 : 450,
                transition: 'stroke-dashoffset 0.9s ease-out',
              }}
            />

            {/* Secondary Concentric Hex Track */}
            <polygon
              points="100,42 150,71 150,129 100,158 50,129 50,71"
              stroke="#00878a"
              strokeWidth="1.5"
              strokeOpacity={stage >= 2 ? 0.6 : 0}
              strokeDasharray="6 3"
              strokeLinejoin="round"
              className="transition-opacity duration-700"
            />

            {/* Corner Node Micro-Vias */}
            <g className={`transition-opacity duration-500 ${stage >= 1 ? 'opacity-100' : 'opacity-0'}`}>
              <circle cx="100" cy="28" r="4" fill="#00f0ff" />
              <circle cx="162.35" cy="64" r="4" fill="#00f0ff" />
              <circle cx="162.35" cy="136" r="4" fill="#00f0ff" />
              <circle cx="100" cy="172" r="4" fill="#00f0ff" />
              <circle cx="37.65" cy="136" r="4" fill="#00f0ff" />
              <circle cx="37.65" cy="64" r="4" fill="#00f0ff" />
            </g>

            {/* Interlocking Monogram (A & R Circuit Traces) */}
            <g
              filter="url(#splashGlow)"
              className={`transition-all duration-700 ease-out ${
                stage >= 2 ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
              }`}
              style={{ transformOrigin: 'center' }}
            >
              {/* Left vertical stem */}
              <path
                d="M70 142 L70 58"
                stroke="url(#splashTeal)"
                strokeWidth="7.5"
                strokeLinecap="round"
              />

              {/* Top loop of R */}
              <path
                d="M70 58 L112 58 C130 58, 134 74, 134 84 C134 96, 124 102, 110 102 L70 102"
                stroke="url(#splashTeal)"
                strokeWidth="7.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              {/* Right diagonal leg of R */}
              <path
                d="M106 102 L138 142"
                stroke="url(#splashGold)"
                strokeWidth="7.5"
                strokeLinecap="round"
              />

              {/* Crossbar bridge */}
              <path
                d="M70 102 L110 102"
                stroke="url(#splashTeal)"
                strokeWidth="7.5"
                strokeLinecap="round"
              />

              {/* Diagonal accent antenna trace */}
              <path
                d="M70 80 L124 46"
                stroke="url(#splashGold)"
                strokeWidth="3.5"
                strokeLinecap="round"
                strokeDasharray="4 4"
              />

              {/* Micro solder pads */}
              <circle cx="70" cy="58" r="3" fill="#ffffff" />
              <circle cx="138" cy="142" r="4" fill="#ffd56b" />
              <circle cx="70" cy="142" r="4" fill="#00f0ff" />
            </g>
          </svg>
        </div>

        {/* Brand Name "ARIS" Reveal */}
        <div
          className={`mt-4 text-center transition-all duration-700 transform ${
            stage >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
          }`}
        >
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-[0.25em] text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-teal-200 font-samsung drop-shadow-[0_2px_10px_rgba(0,196,199,0.3)]">
            ARIS
          </h1>
        </div>

        {/* Subtitle Full Form Reveal */}
        <div
          className={`mt-2 text-center transition-all duration-700 transform ${
            stage >= 4 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
          }`}
        >
          <p className="text-xs sm:text-sm font-medium tracking-[0.12em] text-[#00c4c7] uppercase font-sans">
            Arduino Runtime Intelligence System
          </p>
          <p className="text-[10px] text-slate-500 font-mono tracking-widest mt-1">
            ADVANCED MULTI-MCU PROFILER & AI OPTIMIZATION SUITE
          </p>
        </div>

        {/* Micro System Diagnostics Ticker Bar */}
        <div className="mt-8 flex flex-col items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] backdrop-blur-md">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-ping" />
            <span className="font-mono text-[10px] text-slate-400 tracking-wider">
              {statusText}
            </span>
          </div>

          <div className="w-48 h-1 bg-white/[0.06] rounded-full overflow-hidden mt-1">
            <div
              className="h-full bg-gradient-to-r from-[#00878a] to-[#00f0ff] rounded-full transition-all duration-700 ease-out"
              style={{
                width: stage === 1 ? '20%' : stage === 2 ? '50%' : stage === 3 ? '78%' : '100%',
              }}
            />
          </div>
        </div>
      </div>

      {/* Skip Hint */}
      <div className="absolute bottom-6 text-[10px] font-mono text-slate-600 hover:text-slate-400 transition-colors">
        Click anywhere to continue →
      </div>
    </div>
  );
};
