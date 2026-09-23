import React from 'react';

interface ArisLogoProps {
  size?: number;
  className?: string;
  glow?: boolean;
  animated?: boolean;
}

export const ArisLogo: React.FC<ArisLogoProps> = ({
  size = 32,
  className = '',
  glow = true,
  animated = false,
}) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 200 200"
      width={size}
      height={size}
      className={`${className} ${animated ? 'animate-pulse' : ''}`}
      fill="none"
    >
      <defs>
        <radialGradient id="arisBgGlow" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="#00878a" stopOpacity="0.25" />
          <stop offset="60%" stopColor="#12151a" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#12151a" stopOpacity="1" />
        </radialGradient>

        <linearGradient id="arisNeonTeal" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00f0ff" />
          <stop offset="50%" stopColor="#00c4c7" />
          <stop offset="100%" stopColor="#00878a" />
        </linearGradient>

        <linearGradient id="arisCyberGold" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#e5a93c" />
          <stop offset="100%" stopColor="#ffd56b" />
        </linearGradient>

        {glow && (
          <filter id="arisGlowFilter" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>

      {/* Hex Chassis Base (Outer Hexagon) */}
      <polygon
        points="100,28 162.35,64 162.35,136 100,172 37.65,136 37.65,64"
        stroke="url(#arisNeonTeal)"
        strokeWidth="5"
        strokeLinejoin="round"
        filter={glow ? 'url(#arisGlowFilter)' : undefined}
        fill="#161a22"
        fillOpacity="0.85"
      />

      {/* Inner Track */}
      <polygon
        points="100,40 152,70 152,130 100,160 48,130 48,70"
        stroke="#00878a"
        strokeWidth="1.5"
        strokeOpacity="0.45"
        strokeDasharray="6 3"
        strokeLinejoin="round"
      />

      {/* Corner Nodes */}
      <circle cx="100" cy="28" r="3.5" fill="#00f0ff" />
      <circle cx="162.35" cy="64" r="3.5" fill="#00f0ff" />
      <circle cx="162.35" cy="136" r="3.5" fill="#00f0ff" />
      <circle cx="100" cy="172" r="3.5" fill="#00f0ff" />
      <circle cx="37.65" cy="136" r="3.5" fill="#00f0ff" />
      <circle cx="37.65" cy="64" r="3.5" fill="#00f0ff" />

      {/* Interlocking Monogram (A & R Circuit Traces) */}
      <g filter={glow ? 'url(#arisGlowFilter)' : undefined}>
        {/* Left vertical stem of AR */}
        <path d="M70 142 L70 58" stroke="url(#arisNeonTeal)" strokeWidth="7" strokeLinecap="round" />

        {/* Top curved loop of R */}
        <path
          d="M70 58 L112 58 C130 58, 134 74, 134 84 C134 96, 124 102, 110 102 L70 102"
          stroke="url(#arisNeonTeal)"
          strokeWidth="7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Right diagonal leg of R */}
        <path d="M106 102 L138 142" stroke="url(#arisCyberGold)" strokeWidth="7" strokeLinecap="round" />

        {/* Horizontal bridge */}
        <path d="M70 102 L110 102" stroke="url(#arisNeonTeal)" strokeWidth="7" strokeLinecap="round" />

        {/* Diagonal accent cross-trace */}
        <path d="M70 80 L124 46" stroke="url(#arisCyberGold)" strokeWidth="3" strokeLinecap="round" strokeDasharray="3 3" />
      </g>

      {/* Micro-via points */}
      <circle cx="70" cy="58" r="2.5" fill="#ffffff" />
      <circle cx="138" cy="142" r="3.5" fill="#ffd56b" />
      <circle cx="70" cy="142" r="3.5" fill="#00f0ff" />
    </svg>
  );
};
