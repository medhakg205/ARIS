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
export interface BoardProfile {
  board_id: string;
  display_name: string;
  mcu: string;
  architecture: string;
  clock_hz: number;
  flash_bytes: number;
  sram_bytes: number;
  eeprom_bytes: number;
  gpio_count: number;
  adc_channels: number;
  uart_count: number;
  spi_available: boolean;
  i2c_available: boolean;
  timer_count: number;
  interrupt_capabilities: string[];
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
}

// ---- Experiments ----
export type ExperimentStatus = 'CREATED' | 'RUNNING' | 'COMPLETED' | 'VALIDATED' | 'FAILED';

export interface ExperimentRecord {
  experiment_id: string;
  title: string;
  board_id: string;
  baseline_run_id: string;
  candidate_run_id?: string;
  optimization_id: string;
  status: ExperimentStatus;
  validation_id?: string;
  created_at: string;
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
export interface DiscoveredPortInfo {
  device: string;
  description: string;
  hwid: string;
  vid?: string;
  pid?: string;
  manufacturer?: string;
  is_arduino: boolean;
  suggested_board_id?: string;
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
}
