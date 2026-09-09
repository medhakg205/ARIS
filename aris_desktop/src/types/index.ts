export interface PinMapping {
  pin_name: string;
  pin_type: string;
  port_register: string;
  pin_bit: number;
  timer_channel?: string | null;
  interrupt_num?: number | null;
}

export interface HardwareProfile {
  id: string;
  name: string;
  mcu_model: string;
  architecture: string;
  core_frequency_hz: number;
  flash_bytes: number;
  sram_bytes: number;
  eeprom_bytes: number;
  operating_voltage: number;
  active_power_ma: number;
  sleep_power_ma: number;
  hardware_uarts: number;
  adc_channels: number;
  adc_resolution_bits: number;
  timer_count: number;
  direct_port_registers: string[];
  pin_count: number;
  pins: Record<string, PinMapping>;
  hardware_notes: string;
}

export interface VirtualPinState {
  pin_name: string;
  mode: string;
  digital_value: number;
  analog_value: number;
  pwm_duty: number;
  voltage: number;
}

export interface TelemetryFrame {
  timestamp_ms: number;
  board_id: string;
  board_name: string;
  cpu_utilization_pct: number;
  cpu_compensated_pct: number;
  free_sram_bytes: number;
  used_sram_bytes: number;
  stack_high_watermark_bytes: number;
  loop_duration_us: number;
  loop_frequency_hz: number;
  jitter_us: number;
  isr_frequency_hz: number;
  adc_conversions_sec: number;
  gpio_toggles_sec: number;
  power_consumption_mw: number;
  active_current_ma: number;
  observer_overhead_pct: number;
  raw_packet: string;
  pin_states: Record<string, VirtualPinState>;
}

export interface CodeAntipattern {
  id: string;
  name: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  line_number: number;
  line_snippet: string;
  description: string;
  architectural_impact: string;
  estimated_overhead_cycles: number;
  estimated_sram_loss_bytes: number;
  remediation_suggestion: string;
  auto_fixable: boolean;
}

export interface FunctionProfile {
  name: string;
  return_type: string;
  parameters: string[];
  start_line: number;
  end_line: number;
  line_count: number;
  calls_blocking_delay: boolean;
  calls_slow_gpio: boolean;
  calls_float_math: boolean;
  is_isr: boolean;
}

export interface StaticAnalysisReport {
  board_id: string;
  board_name: string;
  total_lines: number;
  function_count: number;
  functions: FunctionProfile[];
  antipatterns: CodeAntipattern[];
  estimated_flash_bytes: number;
  estimated_sram_static_bytes: number;
  estimated_sram_stack_bytes: number;
  flash_utilization_pct: number;
  sram_utilization_pct: number;
  blocking_delay_count: number;
  gpio_call_count: number;
  float_op_count: number;
  ram_string_count: number;
  architectural_health_score: number;
}

export interface AIOptimizationRecommendation {
  id: string;
  category: string;
  title: string;
  severity: string;
  target_hardware_insight: string;
  theoretical_mechanism: string;
  estimated_gain: string;
  code_before_snippet: string;
  code_after_snippet: string;
}

export interface AIOptimizationResult {
  board_id: string;
  board_name: string;
  original_code: string;
  optimized_candidate_code: string;
  executive_summary: string;
  architectural_diagnostics: string[];
  applied_transforms: string[];
  recommendations: AIOptimizationRecommendation[];
  theoretical_speedup_factor: number;
  projected_sram_recovery_bytes: number;
  projected_power_savings_pct: number;
}

export interface BenchmarkMetricDelta {
  metric_name: string;
  unit: string;
  original_value: number;
  optimized_value: number;
  absolute_delta: number;
  percentage_improvement: number;
  is_positive_improvement: boolean;
}

export interface ClosedLoopVerificationReport {
  board_id: string;
  board_name: string;
  verification_status: string;
  summary: string;
  metrics: BenchmarkMetricDelta[];
  net_performance_score_before: number;
  net_performance_score_after: number;
  total_score_delta: number;
}

export interface MemorySection {
  name: string;
  target_memory: string;
  start_address_hex: string;
  size_bytes: number;
  utilization_pct: number;
  description: string;
}

export interface SymbolEntry {
  name: string;
  section: string;
  size_bytes: number;
  address_hex: string;
  symbol_type: string;
}

export interface FirmwareMemoryMap {
  board_id: string;
  board_name: string;
  total_flash_bytes: number;
  used_flash_bytes: number;
  free_flash_bytes: number;
  flash_pct: number;
  total_sram_bytes: number;
  data_section_bytes: number;
  bss_section_bytes: number;
  static_sram_bytes: number;
  estimated_heap_stack_bytes: number;
  free_sram_bytes: number;
  sram_pct: number;
  sections: MemorySection[];
  top_symbols: SymbolEntry[];
  disassembly_preview: Array<{ addr: string; opcode: string; mnemonic: string; operands: string; cycles: string }>;
}
