// ============================================================
// ARIS — Professional Startup Experience (v3.0.0)
// Minimal, dark engineering theme with smooth progress sequence
// ============================================================

import React, { useState, useEffect } from 'react';
import { ArisLogo } from '../common/ArisLogo';
import { BoardProfile, BackendLifecycleState } from '../../types';
import { RefreshCw, Play, AlertCircle } from 'lucide-react';

interface StartupSplashProps {
  backendOnline: boolean;
  backendState?: BackendLifecycleState;
  hardwareConnected: boolean;
  selectedBoard: BoardProfile | null;
  onComplete: () => void;
  onRetry?: () => void;
}

export const StartupSplash: React.FC<StartupSplashProps> = ({
  backendOnline,
  backendState = 'STARTING',
  hardwareConnected,
  selectedBoard,
  onComplete,
  onRetry,
}) => {
  const [progress, setProgress] = useState(15);
  const [statusMessage, setStatusMessage] = useState('Starting application...');
  const [isFadingOut, setIsFadingOut] = useState(false);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    if (backendState === 'STARTING') {
      const t1 = setTimeout(() => {
        setProgress(35);
        setStatusMessage('Connecting to backend (port 8765)...');
      }, 350);
      return () => clearTimeout(t1);
    }

    if (backendState === 'ONLINE' || backendOnline) {
      setProgress(75);
      if (hardwareConnected && selectedBoard) {
        setStatusMessage(`Target verified: ${selectedBoard.display_name}`);
      } else if (hardwareConnected) {
        setStatusMessage('Serial port connected');
      } else {
        setStatusMessage('Hardware link standby (0 devices). Ready');
      }

      const tReady = setTimeout(() => {
        setProgress(100);
        setStatusMessage('Ready');
      }, 500);

      const tFade = setTimeout(() => {
        setIsFadingOut(true);
      }, 1000);

      const tDone = setTimeout(() => {
        onComplete();
      }, 1300);

      return () => {
        clearTimeout(tReady);
        clearTimeout(tFade);
        clearTimeout(tDone);
      };
    }

    if (backendState === 'RECOVERING') {
      setProgress(40);
      setStatusMessage('Recovering backend process...');
    }

    if (backendState === 'OFFLINE') {
      setProgress(40);
      setStatusMessage('Backend unavailable on port 8765');
    }
  }, [backendState, backendOnline, hardwareConnected, selectedBoard, onComplete]);

  const handleRetry = async () => {
    if (onRetry) {
      setRetrying(true);
      setStatusMessage('Retrying backend connection...');
      try {
        await onRetry();
      } finally {
        setRetrying(false);
      }
    }
  };

  const isFailed = backendState === 'OFFLINE';

  return (
    <div
      onClick={isFailed ? undefined : onComplete}
      className={`fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#07090E] select-none transition-opacity duration-300 ${
        isFailed ? 'cursor-default' : 'cursor-pointer'
      } ${isFadingOut ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}
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
              className={`h-full transition-all duration-300 ease-out ${
                isFailed ? 'bg-[var(--accent-red)]' : 'bg-[var(--accent-cyan)]'
              }`}
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

        {/* If Backend Offline, Show Actionable Recovery Choices */}
        {isFailed ? (
          <div className="space-y-3 pt-2 w-full animate-in fade-in duration-200">
            <div className="p-3 bg-[var(--accent-red-bg)] border border-[var(--accent-red)]/30 rounded-xl text-left text-xs text-[var(--text-secondary)] space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-[var(--accent-red)]">
                <AlertCircle size={14} />
                <span>Backend Unavailable</span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                Cannot reach FastAPI server on port 8765. Ensure no other process holds the port.
              </p>
            </div>

            <div className="flex flex-col gap-2 w-full">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRetry();
                }}
                disabled={retrying}
                className="aris-btn-primary flex items-center justify-center gap-2 text-xs py-2 w-full"
              >
                <RefreshCw size={13} className={retrying ? 'animate-spin' : ''} />
                <span>{retrying ? 'Retrying...' : 'Retry Connection'}</span>
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onComplete();
                }}
                className="aris-btn-secondary flex items-center justify-center gap-2 text-xs py-2 w-full text-[var(--text-muted)] hover:text-white"
              >
                <Play size={13} />
                <span>Continue to UI / Demo Mode</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="text-[10px] font-mono text-[var(--text-muted)] opacity-40 hover:opacity-100 transition-opacity">
            Click anywhere to skip
          </div>
        )}
      </div>
    </div>
  );
};
