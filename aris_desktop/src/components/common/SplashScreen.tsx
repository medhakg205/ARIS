import React, { useState, useEffect } from 'react';

interface SplashScreenProps {
  onFinish: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const [stage, setStage] = useState<number>(1); // 1: Hex Draw, 2: Monogram Ignite, 3: ARIS & Subtitle, 4: 90%->100% Welcome, 5: Smooth Dissolve
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('INITIALIZING RUNTIME CORE...');

  useEffect(() => {
    // Initial start: progress climbs to 25%
    const p1 = setTimeout(() => {
      setProgress(25);
    }, 150);

    // Stage 1 -> 2 (700ms): Monogram Ignites, progress climbs to 60%
    const t1 = setTimeout(() => {
      setStage(2);
      setProgress(60);
      setStatusText('ANALYZING EMBEDDED BUS REGISTERS...');
    }, 700);

    // Stage 2 -> 3 (1500ms): ARIS Title & Subtitle Reveal, progress reaches 90%
    const t2 = setTimeout(() => {
      setStage(3);
      setProgress(90);
      setStatusText('ENGAGING TELEMETRY & AI ENGINE...');
    }, 1500);

    // Stage 3 -> 4 (2400ms): Progress Hits 100% and WELCOME is announced
    const t3 = setTimeout(() => {
      setStage(4);
      setProgress(100);
      setStatusText('WELCOME');
    }, 2400);

    // Stage 4 -> 5 (3500ms): Slow, graceful fade-out begins
    const t4 = setTimeout(() => {
      setStage(5);
    }, 3600);

    // Final completion (4600ms): Main App revealed smoothly
    const t5 = setTimeout(() => {
      onFinish();
    }, 4600);

    return () => {
      clearTimeout(p1);
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
    };
  }, [onFinish]);

  return (
    <div
      className={`fixed inset-0 z-[9999] bg-[#0c0e12] flex flex-col items-center justify-center select-none overflow-hidden transition-all duration-1000 ease-in-out ${
        stage === 5 ? 'opacity-0 scale-[1.03] pointer-events-none' : 'opacity-100 scale-100'
      }`}
    >
      {/* Background Engineering Matrix Grid & Ambient Glow */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#161a2218_1px,transparent_1px),linear-gradient(to_bottom,#161a2218_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      <div className="absolute w-[540px] h-[540px] rounded-full bg-[#00878a]/18 blur-[130px] pointer-events-none animate-pulse" />

      {/* Center Cinematic Container */}
      <div className="relative flex flex-col items-center z-10">
        {/* Animated Vector Logo */}
        <div className="relative w-36 h-36 sm:w-44 sm:h-44 flex items-center justify-center">
          <svg
            viewBox="0 0 200 200"
            className="w-full h-full drop-shadow-[0_0_28px_rgba(0,196,199,0.38)]"
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
              className="fill-[#161a22]/85"
              style={{
                strokeDasharray: 450,
                strokeDashoffset: stage >= 1 ? 0 : 450,
                transition: 'stroke-dashoffset 0.9s cubic-bezier(0.16, 1, 0.3, 1)',
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
              className={`transition-all duration-800 ease-out ${
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
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-[0.25em] text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-teal-200 font-samsung drop-shadow-[0_2px_12px_rgba(0,196,199,0.35)]">
            ARIS
          </h1>
        </div>

        {/* Subtitle Full Form Reveal */}
        <div
          className={`mt-2 text-center transition-all duration-700 transform ${
            stage >= 3 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
          }`}
        >
          <p className="text-xs sm:text-sm font-semibold tracking-[0.14em] text-[#00c4c7] uppercase font-sans">
            Arduino Runtime Intelligence System
          </p>
          <p className="text-[10px] text-slate-400 font-mono tracking-widest mt-1">
            ADVANCED MULTI-MCU PROFILER & AI OPTIMIZATION SUITE
          </p>
        </div>

        {/* Progress & Welcome Section */}
        <div className="mt-8 flex flex-col items-center gap-3">
          {/* Status Message / WELCOME Announcement */}
          <div
            className={`transition-all duration-500 flex items-center justify-center ${
              stage >= 4
                ? 'scale-110'
                : 'scale-100'
            }`}
          >
            {stage >= 4 ? (
              <div className="flex items-center gap-2 px-5 py-1.5 rounded-full bg-teal-500/15 border border-teal-400/40 shadow-[0_0_20px_rgba(0,196,199,0.3)] animate-pulse">
                <span className="w-2 h-2 rounded-full bg-[#00f0ff] shadow-sm shadow-[#00f0ff]" />
                <span className="font-samsung font-bold text-sm text-transparent bg-clip-text bg-gradient-to-r from-white via-teal-200 to-[#00f0ff] tracking-[0.3em] uppercase">
                  WELCOME
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-ping" />
                <span className="font-mono text-[10px] text-slate-300 tracking-wider">
                  {statusText}
                </span>
              </div>
            )}
          </div>

          {/* Smooth 0 -> 90 -> 100% Progress Bar */}
          <div className="w-56 h-1.5 bg-white/[0.06] rounded-full overflow-hidden p-0.5 border border-white/[0.06]">
            <div
              className="h-full bg-gradient-to-r from-[#00878a] via-[#00c4c7] to-[#00f0ff] rounded-full transition-all duration-800 ease-out shadow-[0_0_10px_rgba(0,240,255,0.4)]"
              style={{
                width: `${progress}%`,
              }}
            />
          </div>

          {/* Micro Progress Percentage */}
          <div className="text-[10px] font-mono text-slate-400 tracking-widest">
            {progress}%
          </div>
        </div>
      </div>
    </div>
  );
};
