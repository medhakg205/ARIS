import React, { useState, useEffect, useRef } from 'react';

interface SplashScreenProps {
  onFinish: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const [stage, setStage] = useState<number>(1); // 1: Logo & Draw, 2: Brand & Subtitle, 3: 100% Welcome, 4: FadeOut
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('Initializing runtime core...');
  const onFinishRef = useRef(onFinish);
  onFinishRef.current = onFinish;
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    // Step 1: Start smooth progress climb
    const t1 = setTimeout(() => {
      setProgress(35);
      setStatusText('Probing microcontroller bus...');
    }, 400);

    // Step 2: Monogram + Brand text reveal
    const t2 = setTimeout(() => {
      setStage(2);
      setProgress(70);
      setStatusText('Loading analytical diagnostics...');
    }, 1100);

    // Step 3: Progress reaches 90%
    const t3 = setTimeout(() => {
      setProgress(90);
      setStatusText('Readying optimization engine...');
    }, 1800);

    // Step 4: Progress reaches 100% and WELCOME is displayed
    const t4 = setTimeout(() => {
      setStage(3);
      setProgress(100);
      setStatusText('WELCOME');
    }, 2500);

    // Step 5: Start slow fade-out transition
    const t5 = setTimeout(() => {
      setStage(4);
    }, 3600);

    // Step 6: Complete and hand over to main app
    const t6 = setTimeout(() => {
      onFinishRef.current();
    }, 4400);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
      clearTimeout(t6);
    };
  }, []);

  return (
    <div
      className={`fixed inset-0 z-[9999] bg-[#12151a] flex flex-col items-center justify-center select-none overflow-hidden transition-opacity duration-700 ease-in-out ${
        stage === 4 ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      {/* Ambient background glow */}
      <div className="absolute w-[450px] h-[450px] rounded-full bg-[#00878a]/12 blur-[100px] pointer-events-none" />

      <div className="relative flex flex-col items-center z-10 max-w-md w-full px-6">
        {/* Hex Logo */}
        <div className="relative w-28 h-28 sm:w-32 sm:h-32 flex items-center justify-center mb-5">
          <svg viewBox="0 0 200 200" className="w-full h-full" fill="none">
            <defs>
              <linearGradient id="splashTeal" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00f0ff" />
                <stop offset="60%" stopColor="#00c4c7" />
                <stop offset="100%" stopColor="#00878a" />
              </linearGradient>

              <linearGradient id="splashGold" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#e5a93c" />
                <stop offset="100%" stopColor="#ffd56b" />
              </linearGradient>

              <filter id="splashGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Outer Hexagon */}
            <polygon
              points="100,28 162.35,64 162.35,136 100,172 37.65,136 37.65,64"
              stroke="url(#splashTeal)"
              strokeWidth="4.5"
              strokeLinejoin="round"
              filter="url(#splashGlow)"
              fill="#161a22"
              fillOpacity="0.8"
            />

            {/* Micro-nodes */}
            <circle cx="100" cy="28" r="3.5" fill="#00f0ff" />
            <circle cx="162.35" cy="64" r="3.5" fill="#00f0ff" />
            <circle cx="162.35" cy="136" r="3.5" fill="#00f0ff" />
            <circle cx="100" cy="172" r="3.5" fill="#00f0ff" />
            <circle cx="37.65" cy="136" r="3.5" fill="#00f0ff" />
            <circle cx="37.65" cy="64" r="3.5" fill="#00f0ff" />

            {/* Interlocking Monogram (A & R Circuit Traces) */}
            <g filter="url(#splashGlow)">
              <path d="M70 142 L70 58" stroke="url(#splashTeal)" strokeWidth="7" strokeLinecap="round" />
              <path
                d="M70 58 L112 58 C130 58, 134 74, 134 84 C134 96, 124 102, 110 102 L70 102"
                stroke="url(#splashTeal)"
                strokeWidth="7"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M106 102 L138 142" stroke="url(#splashGold)" strokeWidth="7" strokeLinecap="round" />
              <path d="M70 102 L110 102" stroke="url(#splashTeal)" strokeWidth="7" strokeLinecap="round" />
            </g>

            {/* Solder Points */}
            <circle cx="70" cy="58" r="2.5" fill="#ffffff" />
            <circle cx="138" cy="142" r="3.5" fill="#ffd56b" />
            <circle cx="70" cy="142" r="3.5" fill="#00f0ff" />
          </svg>
        </div>

        {/* Brand Name "ARIS" */}
        <h1 className="text-3xl sm:text-4xl font-semibold tracking-wider text-slate-100 font-sans leading-none text-center">
          ARIS
        </h1>

        {/* Full Title Subtitle */}
        <p className="text-xs sm:text-sm font-medium text-[#00878a] tracking-wide mt-2 text-center font-sans">
          Arduino Runtime Intelligence System
        </p>

        <p className="text-[11px] text-slate-400 font-sans mt-1 text-center">
          Multi-MCU Runtime Intelligence & AI Optimization Platform
        </p>

        {/* Progress & Welcome Section */}
        <div className="mt-7 w-full flex flex-col items-center gap-2.5">
          {/* Status Text or Welcome Badge */}
          {stage === 3 ? (
            <div className="flex items-center gap-2 px-4 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-semibold text-emerald-300 font-sans tracking-wider uppercase">
                WELCOME
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-3 py-0.5 rounded bg-white/[0.04] border border-white/[0.08]">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              <span className="text-[11px] text-slate-300 font-sans">
                {statusText}
              </span>
            </div>
          )}

          {/* Clean Progress Bar */}
          <div className="w-64 h-1.5 bg-white/[0.06] rounded-full overflow-hidden border border-white/[0.06] mt-1">
            <div
              className="h-full bg-gradient-to-r from-[#00878a] to-[#00f0ff] rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          <span className="text-[10px] font-mono text-slate-400">
            {progress}%
          </span>
        </div>
      </div>
    </div>
  );
};
