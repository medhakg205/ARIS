// ============================================================
// ARIS — Professional Startup Experience (v3.0.0)
// Minimal, dark engineering theme with smooth progress sequence
// ============================================================

import React, { useState, useEffect } from 'react';
import { ArisLogo } from '../common/ArisLogo';
import { BoardProfile } from '../../types';

interface StartupSplashProps {
  backendOnline: boolean;
  hardwareConnected: boolean;
  selectedBoard: BoardProfile | null;
  onComplete: () => void;
}

export const StartupSplash: React.FC<StartupSplashProps> = ({
  backendOnline,
  hardwareConnected,
  selectedBoard,
  onComplete,
}) => {
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('Initializing runtime...');
  const [isFadingOut, setIsFadingOut] = useState(false);

  useEffect(() => {
    // 2-second calibrated startup sequence
    const t1 = setTimeout(() => {
      setProgress(30);
      setStatusMessage('Loading analysis engine...');
    }, 450);

    const t2 = setTimeout(() => {
      setProgress(70);
      if (hardwareConnected && selectedBoard) {
        setStatusMessage(`Target verified: ${selectedBoard.display_name}`);
      } else if (hardwareConnected) {
        setStatusMessage('Serial port connected');
      } else {
        setStatusMessage('Checking hardware ports... No device connected');
      }
    }, 1100);

    const t3 = setTimeout(() => {
      setProgress(100);
      setStatusMessage('Ready');
    }, 1800);

    const t4 = setTimeout(() => {
      setIsFadingOut(true);
    }, 2200);

    const t5 = setTimeout(() => {
      onComplete();
    }, 2500);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
      clearTimeout(t5);
    };
  }, [hardwareConnected, selectedBoard, onComplete]);

  return (
    <div
      onClick={onComplete}
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#07090E] select-none transition-opacity duration-300 cursor-pointer ${
        isFadingOut ? 'opacity-0 pointer-events-none' : 'opacity-100'
      }`}
    >
      <div className="flex flex-col items-center space-y-6 max-w-sm px-6 text-center">
        {/* ARIS Mark with subtle circuit ring */}
        <div className="relative flex items-center justify-center">
          <div className="absolute w-24 h-24 rounded-full border border-[var(--accent-cyan)]/20 animate-ping opacity-25" />
          <div className="w-16 h-16 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-color)] flex items-center justify-center shadow-lg relative z-10">
            <ArisLogo size={36} glow={false} />
          </div>
        </div>

        {/* Title & Product Identity */}
        <div className="space-y-1">
          <h1 className="text-3xl font-heading font-extrabold tracking-wider text-white">
            ARIS
          </h1>
          <p className="text-xs font-mono font-medium text-[var(--text-muted)] tracking-wide">
            Arduino Runtime Intelligence System
          </p>
        </div>

        {/* Engineering Progress Bar */}
        <div className="w-64 space-y-2 pt-2">
          <div className="w-full h-1 bg-[var(--bg-surface)] rounded-full overflow-hidden border border-[var(--border-color)]">
            <div
              className="h-full bg-[var(--accent-cyan)] transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Real Status Text */}
          <div className="flex items-center justify-between text-[11px] font-mono text-[var(--text-muted)] pt-1">
            <span className="truncate">{statusMessage}</span>
            <span className="text-[var(--text-secondary)] font-semibold shrink-0 ml-2">
              {progress}%
            </span>
          </div>
        </div>

        <div className="text-[10px] font-mono text-[var(--text-muted)] opacity-40 hover:opacity-100 transition-opacity">
          Click anywhere to skip
        </div>
      </div>
    </div>
  );
};
