// ARIS Common — ErrorBanner
// Displays human-readable messages for canonical ARIS_* error codes.

import React from 'react';
import { AlertTriangle, XCircle, RefreshCw, X } from 'lucide-react';
import type { ArisErrorCode } from '../../types';
import { ARISApiError } from '../../services/api';

const ERROR_MESSAGES: Record<ArisErrorCode, { title: string; hint: string }> = {
  ARIS_SERIAL_DISCONNECTED: {
    title: 'Serial Connection Lost',
    hint: 'The Arduino serial port was disconnected. Check USB cable and reconnect from Settings.',
  },
  ARIS_BOARD_NOT_FOUND: {
    title: 'Board Not Found',
    hint: 'No Arduino board detected on the selected serial port.',
  },
  ARIS_UNSUPPORTED_BOARD: {
    title: 'Unsupported Board',
    hint: 'ARIS supports arduino_uno, arduino_nano, and arduino_mega only.',
  },
  ARIS_INVALID_FIRMWARE: {
    title: 'Invalid Firmware',
    hint: 'The firmware file is missing, corrupt, or could not be parsed.',
  },
  ARIS_BUILD_FAILED: {
    title: 'Build Failed',
    hint: 'Firmware compilation failed. Check your Arduino sketch for syntax errors.',
  },
  ARIS_FLASH_FAILED: {
    title: 'Flash Failed',
    hint: 'Could not program the microcontroller. Verify avrdude is installed and the port is correct.',
  },
  ARIS_TELEMETRY_INVALID: {
    title: 'Invalid Telemetry',
    hint: 'Received a malformed telemetry packet. Check ARIS probe instrumentation on the target.',
  },
  ARIS_AI_UNAVAILABLE: {
    title: 'AI Engine Unavailable',
    hint: 'The AI optimization advisor is unavailable. Configure an API key in Settings or use the deterministic Rule Synthesizer.',
  },
  ARIS_OPTIMIZATION_INVALID: {
    title: 'Invalid Optimization Candidate',
    hint: 'The AI-generated candidate failed schema validation. Check the AI provider output.',
  },
  ARIS_VALIDATION_FAILED: {
    title: 'Validation Failed',
    hint: 'The closed-loop empirical validation encountered a failure or detected a regression.',
  },
  ARIS_BACKEND_UNAVAILABLE: {
    title: 'Backend Unavailable',
    hint: 'Cannot reach the ARIS backend server on port 8765. Run: python -m backend.api.app',
  },
};

interface ErrorBannerProps {
  error: ARISApiError | Error | string | null;
  onDismiss?: () => void;
  inline?: boolean;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error, onDismiss, inline = false }) => {
  if (!error) return null;

  let code: ArisErrorCode | null = null;
  let rawMessage = '';

  if (error instanceof ARISApiError) {
    code = error.error_code as ArisErrorCode;
    rawMessage = error.message;
  } else if (error instanceof Error) {
    rawMessage = error.message;
  } else {
    rawMessage = error;
  }

  const meta = code ? ERROR_MESSAGES[code] : null;
  const title = meta?.title || (code || 'Error');
  const hint = meta?.hint || rawMessage;

  const wrapClass = inline
    ? 'flex items-start gap-2 bg-red-900/20 border border-red-800/50 rounded px-3 py-2 text-xs'
    : 'flex items-start gap-3 bg-red-900/20 border border-red-800/50 rounded px-4 py-3 text-sm';

  return (
    <div className={wrapClass} role="alert">
      <XCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="font-mono font-semibold text-red-300">{title}</p>
        {code && (
          <p className="font-mono text-red-500/70 text-[10px] mb-1">{code}</p>
        )}
        <p className="text-slate-400">{hint}</p>
      </div>
      {onDismiss && (
        <button onClick={onDismiss} className="text-slate-500 hover:text-slate-300 transition-colors mt-0.5">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
