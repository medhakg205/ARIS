// ============================================================
// ARIS Canonical TypeScript Types
// Adaptive Runtime Intelligence System for Embedded Devices
// Engineer 3 — Canonical contracts matching backend schemas exactly
// ============================================================

// ---- Veracity Classifications ----
export type MetricClassification = 'MEASURED' | 'ESTIMATED' | 'DERIVED' | 'PREDICTED';

// ---- Canonical Metric Names ----
export type CanonicalMetric =
  | 'cpu_load'
  | 'loop_time'
  | 'loop_frequency'
  | 'loop_jitter'
  | 'sram_used'
  | 'sram_free'
  | 'stack_used'
  | 'stack_high_water_mark'
  | 'interrupt_count'
  | 'interrupt_rate'
  | 'gpio_activity'
  | 'adc_activity'
  | 'uart_activity'
  | 'spi_activity'
  | 'i2c_activity'
  | 'timer_activity'
  | 'reset_event'
  | 'watchdog_event'
  | 'runtime_fault'
  | 'instrumentation_overhead';

// ---- Canonical Error Codes ----
export type ArisErrorCode =
  | 'ARIS_SERIAL_DISCONNECTED'
  | 'ARIS_BOARD_NOT_FOUND'
  | 'ARIS_UNSUPPORTED_BOARD'
  | 'ARIS_INVALID_FIRMWARE'
  | 'ARIS_BUILD_FAILED'
  | 'ARIS_FLASH_FAILED'
  | 'ARIS_TELEMETRY_INVALID'
  | 'ARIS_AI_UNAVAILABLE'
  | 'ARIS_OPTIMIZATION_INVALID'
  | 'ARIS_VALIDATION_FAILED'
  | 'ARIS_BACKEND_UNAVAILABLE';

export interface ArisError {
  error_code: ArisErrorCode;
  message: string;
  details: Record<string, unknown>;
  recoverable: boolean;
}

// ---- Canonical Telemetry Sample (v1.0 protocol) ----
export interface TelemetrySample {
  protocol_version: '1.0';
  run_id: string;
  board_id: string;
  mcu: string;
  timestamp_ms: number;
  sequence: number;
  metric: CanonicalMetric;
  value: number;
  unit: string;
  classification: MetricClassification;
  confidence: number;
  is_demo?: boolean;
}

// ---- Board Profile ----
export type BoardProfileSource =
  | 'EXACT_PROFILE'
  | 'TOOLCHAIN_DERIVED'
  | 'RUNTIME_VERIFIED'
  | 'PARTIALLY_RESOLVED'
  | 'UNKNOWN';

export type BoardConfidence =
  | 'CONFIRMED'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'UNCERTAIN'
  | 'UNKNOWN'
  | 'MISMATCH';

export interface BoardProfile {
  board_id: string;
  display_name: string;
  mcu?: string | null;
  architecture?: string | null;
  clock_hz?: number | null;
  flash_bytes?: number | null;
  sram_bytes?: number | null;
  eeprom_bytes?: number | null;
  gpio_count?: number | null;
  adc_channels?: number | null;
  uart_count?: number | null;
  spi_available?: boolean | null;
  i2c_available?: boolean | null;
  timer_count?: number | null;
  interrupt_capabilities?: string[];
  id?: string;
  name?: string;
  arch?: string | null;
  clock_mhz?: number | null;
  fqbn?: string | null;
  pins?: any[];
  mcu_model?: string;
  operating_voltage?: string;
  profile_source?: BoardProfileSource;
  confidence?: BoardConfidence;
  unavailable_properties?: string[];
  platform?: string | null;
  capabilities?: Record<string, any>;
  supported?: boolean;
}

// ---- Firmware ----
export interface FirmwareRecord {
  firmware_id: string;
  name: string;
  source_code?: string;
  hex_content?: string;
  elf_path?: string;
  map_content?: string;
  created_at: string;
}

export interface IDESketchInfo {
  name: string;
  path: string;
  last_modified: number;
  source_code?: string;
}

export interface IDERecentResponse {
  found: boolean;
  sketches: IDESketchInfo[];
  active_sketch: IDESketchInfo | null;
}

export interface IDESyncResponse {
  success: boolean;
  firmware: FirmwareRecord;
  path: string;
  source_code: string;
  name: string;
  error?: string;
}

// ---- Run ----
export type RunStatus =
  | 'CREATED'
  | 'BUILDING'
  | 'FLASHING'
  | 'RUNNING'
  | 'COLLECTING'
  | 'COMPLETED'
  | 'FAILED'
  | 'ROLLED_BACK';

export interface RunRecord {
  run_id: string;
  board_id: string;
  firmware_id?: string;
  instrumentation_mode: string;
  start_time?: string;
  end_time?: string;
  status: RunStatus;
  is_simulated: boolean;
  is_demo: boolean;
  baseline_id?: string;
}

// ---- Findings ----
export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type RuntimeCorrelation = 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH';

export interface FindingRecord {
  finding_id: string;
  run_id?: string;
  rule_id: string;
  severity: FindingSeverity;
  title: string;
  description: string;
  source_file: string;
  source_line: number;
  runtime_correlation: RuntimeCorrelation;
  confidence: number;
  evidence: Record<string, unknown>;
  recommended_action: string;
}

// ---- Optimization Candidates ----
export type OptimizationStatus =
  | 'PROPOSED'
  | 'APPROVED'
  | 'BUILDING'
  | 'TESTING'
  | 'VALIDATED'
  | 'REJECTED'
  | 'ROLLED_BACK'
  | 'FAILED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface OptimizationCandidate {
  optimization_id: string;
  finding_id: string;
  run_id?: string;
  title: string;
  problem: string;
  source_location: { file: string; line: number };
  before_code: string;
  after_code: string;
  reason: string;
  hardware_consideration: string;
  expected_effect: Record<string, unknown>;
  risk: RiskLevel;
  confidence: number;
  validation_required: boolean;
  status: OptimizationStatus;

  // ARIS 2.0 Hardware-Aware additions (optional for backwards compatibility)
  candidate_id?: string;
  transformation_id?: string;
  transformation_category?: string;
  rationale?: string;
  trade_offs_explained?: Record<string, string>;
  resource_impact?: {
    flash_headroom_bytes_remaining?: number;
    sram_headroom_bytes_remaining?: number;
    flash_utilization_pct?: number;
    sram_utilization_pct?: number;
    budget_explanation?: string;
  };
  uncertainty?: {
    lower_bound_pct?: number;
    upper_bound_pct?: number;
    confidence_score?: number;
    is_high_uncertainty?: boolean;
  };
  approval?: {
    decision?: 'PENDING' | 'APPROVED' | 'REJECTED';
    decided_by?: string;
    reason?: string;
  };
}

// ---- Experiments ----
export type ExperimentStatus = 'CREATED' | 'RUNNING' | 'COMPLETED' | 'VALIDATED' | 'FAILED' | 'ROLLED_BACK' | 'SUCCESS';

export interface ExperimentRecord {
  experiment_id: string;
  title: string;
  board_id: string;
  baseline_run_id: string;
  candidate_run_id?: string;
  optimization_id: string;
  status: ExperimentStatus;
  validation_id?: string;
  is_simulated?: boolean;
  is_demo?: boolean;
  created_at: string;
  id?: string;
  name?: string;
  result_summary?: {
    latency_improvement_pct?: number;
    cpu_load_reduction_pct?: number;
    sram_reduction_pct?: number;
    flash_reduction_pct?: number;
    baseline_loop_ms?: number;
    candidate_loop_ms?: number;
    baseline_cpu_pct?: number;
    candidate_cpu_pct?: number;
    baseline_sram_bytes?: number;
    candidate_sram_bytes?: number;
    baseline_flash_bytes?: number;
    candidate_flash_bytes?: number;
    [key: string]: any;
  };
}

// ---- Validation ----
export type ValidationStatus =
  | 'VALIDATED'
  | 'PARTIALLY_VALIDATED'
  | 'NO_SIGNIFICANT_CHANGE'
  | 'REGRESSION'
  | 'REJECTED'
  | 'INCONCLUSIVE';

export interface ValidationMetricDelta {
  metric: string;
  baseline_value: number;
  candidate_value: number;
  difference: number;
  percentage_change: number;
  is_improvement: boolean;
}

export interface ValidationResult {
  validation_id: string;
  experiment_id: string;
  baseline_run_id: string;
  candidate_run_id: string;
  metrics: Record<string, ValidationMetricDelta>;
  validation_status: ValidationStatus;
  reason: string;
  created_at: string;
  // Prediction vs Reality (set by frontend after comparison)
  prediction_accuracy?: {
    metrics_compared: Record<string, {
      predicted: number;
      actual: number;
      unit: string;
      absolute_error: number;
      relative_error_pct: number;
      directional_match: boolean;
    }>;
    mean_prediction_error_pct: number;
    prediction_accuracy_score: number;
    sample_count: number;
    scientific_note: string;
  };
}

// ---- Baseline ----
export interface BaselineMetricStats {
  metric: string;
  sample_count: number;
  mean: number;
  median: number;
  minimum: number;
  maximum: number;
  variance: number;
  jitter: number;
}

// ---- AI Context ----
export interface AIContextInput {
  board_profile: Record<string, unknown>;
  firmware_source: string;
  static_findings: FindingRecord[];
  runtime_metrics: Record<string, number>;
  baseline_metrics: Record<string, BaselineMetricStats>;
  runtime_static_correlations: FindingRecord[];
  optimization_history: OptimizationCandidate[];
}

// ---- Connection Status ----
export type DeviceConnectionState =
  | 'NO_HARDWARE'
  | 'DETECTING'
  | 'CONNECTED'
  | 'DISCONNECTED'
  | 'UNKNOWN'
  | 'UNCERTAIN'
  | 'SIMULATION';

export interface DiscoveredPortInfo {
  device: string;
  description: string;
  display_name?: string;
  hwid: string;
  vid?: string;
  pid?: string;
  manufacturer?: string;
  is_arduino: boolean;
  suggested_board_id?: string;
  mcu?: string | null;
  architecture?: string | null;
  fqbn?: string | null;
  confidence?: BoardConfidence;
  profile_source?: BoardProfileSource;
  unavailable_properties?: string[];
}

export interface ConnectionStatus {
  connected: boolean;
  port?: string;
  baud_rate?: number;
  run_id?: string;
  available_ports: string[];
  discovered_ports?: DiscoveredPortInfo[];
  simulator_active?: boolean;
  mode?: string;
  board_profile?: BoardProfile | null;
  identity_mismatch?: boolean;
  mismatch_reason?: string | null;
}

// ---- Health ----
export interface HealthStatus {
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  version: string;
  subsystem: string;
  database: string;
  serial_connected: boolean;
  serial_port?: string;
  simulator_running: boolean;
  mode: string;
  supported_boards: string[];
}

// ---- WebSocket Frame ----
export interface WsFrame {
  type: 'TELEMETRY_UPDATE' | 'RUN_STATUS' | 'ERROR';
  data: TelemetrySample | RunRecord | ArisError;
  source: 'PHYSICAL_HARDWARE' | 'SIMULATOR' | 'DEMO';
}

// ---- AI Provider ----
export interface AIProviderInfo {
  provider_id: string;
  display_name: string;
  available: boolean;
  id?: string;
  name?: string;
  status?: string;
}

// ---- Demo Projects ----
export interface DemoProject {
  project_id: string;
  title: string;
  icon: string;
  category: string;
  description: string;
  antipatterns: string[];
}

export interface DemoBoard {
  board_id: string;
  display_name: string;
  mcu: string;
  clock_mhz: number;
  sram_kb: number;
  flash_kb: number;
}

export interface DemoSetupResponse {
  firmware_id: string;
  project: {
    project_id: string;
    title: string;
    icon: string;
    antipatterns: string[];
  };
  board_id: string;
  source_code: string;
}

export type HardwareProfile = BoardProfile;
export type Experiment = ExperimentRecord;
export interface TelemetryFrame {
  protocol_version?: '1.0';
  run_id?: string;
  board_id?: string;
  mcu?: string;
  timestamp_ms: number;
  sequence?: number;
  metric?: CanonicalMetric;
  value?: number;
  unit?: string;
  classification?: MetricClassification;
  confidence?: number;
  is_demo?: boolean;
  cpu_compensated_pct: number;
  loop_duration_us: number;
  power_consumption_mw: number;
  used_sram_bytes: number;
  stack_high_watermark_bytes: number;
  cpu_utilization_pct: number;
  observer_overhead_pct: number;
  free_sram_bytes: number;
  loop_frequency_hz: number;
  jitter_us: number;
  isr_frequency_hz?: number;
  adc_conversions_sec?: number;
  gpio_toggles_sec?: number;
  active_current_ma?: number;
  raw_packet?: string;
  [key: string]: any;
}

export interface TelemetryStats {
  mean?: number;
  median?: number;
  p95?: number;
  p99?: number;
  min?: number;
  max?: number;
  jitter?: number;
  variance?: number;
  sample_count?: number;
  [key: string]: any;
}

export interface StaticAnalysisReport {
  timestamp?: string;
  findings?: FindingRecord[];
  anti_patterns?: any[];
  [key: string]: any;
}

export interface VirtualPinState {
  pin: number | string;
  mode: string;
  state: number | boolean;
  pwm_value?: number;
  [key: string]: any;
}

export interface FirmwareMemoryMap {
  flash_used?: number;
  flash_total?: number;
  sram_used?: number;
  sram_total?: number;
  sections?: any[];
  [key: string]: any;
}

export interface AIOptimizationResult {
  optimization_id?: string;
  candidate?: OptimizationCandidate;
  candidates?: OptimizationCandidate[];
  summary?: string;
  [key: string]: any;
}

export interface ClosedLoopVerificationReport {
  experiment_id?: string;
  status?: string;
  metrics?: any;
  deltas?: any;
  [key: string]: any;
}


