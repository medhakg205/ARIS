import React from 'react';
import { FlaskConical } from 'lucide-react';

interface DemoBannerProps {
  visible: boolean;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({ visible }) => {
  if (!visible) return null;
  return (
    <div
      className="flex items-center gap-1.5 px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-300 font-sans text-xs select-none shrink-0"
      title="ARIS is displaying simulated hardware telemetry. No physical Arduino is connected."
    >
      <FlaskConical className="w-3.5 h-3.5 text-amber-400 shrink-0" />
      <span className="font-semibold text-[11px] tracking-wider uppercase">Demo Mode</span>
    </div>
  );
};
