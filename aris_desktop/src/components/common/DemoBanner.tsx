// ARIS Common — DemoBanner
// Persistent high-visibility DEMO MODE indicator.
// Shown at all times when synthetic/simulated telemetry is active.
// Never silently mixed with physical hardware data.

import React from 'react';
import { FlaskConical } from 'lucide-react';

interface DemoBannerProps {
  visible: boolean;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ visible }) => {
  if (!visible) return null;
  return (
    <div
      className="flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/40 rounded text-amber-400 font-mono text-xs select-none"
      title="ARIS is displaying simulated hardware telemetry. No physical Arduino is connected."
    >
      <FlaskConical className="w-3.5 h-3.5" />
      <span className="font-semibold tracking-widest uppercase">Demo Mode</span>
      <span className="text-amber-500/60">— Simulated Hardware</span>
    </div>
  );
};
