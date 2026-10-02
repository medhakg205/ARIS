// ============================================================
// ARIS — Professional Navigation Types
// ============================================================

export type NavTab =
  | 'dashboard'      // Overview / Home
  | 'firmware'       // Firmware Workspace & Arduino IDE source
  | 'telemetry'      // Telemetry Lab
  | 'analysis'       // Analysis & Findings
  | 'optimize'       // Optimization Recommendations & Validation
  | 'experiments'    // Experiment Management & Replay
  | 'reports'        // Optimization Reports & Verification
  | 'settings'       // Configuration & Toolchains
  | 'devices'        // Devices & Serial Hardware (Advanced)
  | 'baselines'      // Baseline Distributions (Advanced)
  | 'diagnostics'    // System Diagnostics (Advanced)
  | 'logs'           // Event Log Stream (Advanced)
  | 'about'          // About ARIS
  // Aliases for compatibility
  | 'issues'
  | 'optimization';

export interface NavItemConfig {
  id: NavTab;
  label: string;
  badge?: string | number;
  badgeColor?: 'cyan' | 'green' | 'amber' | 'red';
  dividerBefore?: boolean;
}
