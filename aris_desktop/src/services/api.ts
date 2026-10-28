// ============================================================
// ARIS REST API Client
// Strictly uses canonical endpoint paths from INTEGRATION_CONTRACT.md
// Base URL: http://127.0.0.1:8765
// ============================================================

import type {
  BoardProfile,
  ConnectionStatus,
  FirmwareRecord,
  RunRecord,
  TelemetrySample,
  FindingRecord,
  OptimizationCandidate,
  ExperimentRecord,
  ValidationResult,
  HealthStatus,
  AIContextInput,
  AIProviderInfo,
  ArisError,
  RunStatus,
  DemoProject,
  DemoBoard,
  DemoSetupResponse,
} from '../types';

const DEFAULT_BASE = 'http://127.0.0.1:8765';

export function getApiBaseUrl(): string {
  return (window as unknown as Record<string, unknown>).__ARIS_API_BASE__ as string || DEFAULT_BASE;
}

function getBase(): string {
  return getApiBaseUrl();
}

class ARISApiError extends Error {
  constructor(
    public readonly error_code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly recoverable: boolean = true,
  ) {
    super(message);
    this.name = 'ARISApiError';
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  timeoutMs = 15000,
): Promise<T> {
  const url = `${getBase()}${path}`;
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(timeoutMs),
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  let resp: Response;
  try {
    resp = await fetch(url, opts);
  } catch (e: any) {
    if (e?.name === 'TimeoutError' || e?.name === 'AbortError') {
      throw new ARISApiError(
        'ARIS_OPERATION_TIMEOUT',
        `Operation timed out after ${Math.round(timeoutMs / 1000)}s waiting for ARIS backend.`,
        { url, path, timeoutMs },
        true,
      );
    }
    throw new ARISApiError(
      'ARIS_BACKEND_UNAVAILABLE',
      'Cannot reach ARIS backend. Is the server running on port 8765?',
      { url, path, originalError: e?.message },
      true,
    );
  }

  if (!resp.ok) {
    let err: ArisError | null = null;
    try { err = await resp.json(); } catch (_) { /* ignore */ }
    throw new ARISApiError(
      err?.error_code || 'ARIS_BACKEND_UNAVAILABLE',
      err?.message || `HTTP ${resp.status}`,
      err?.details || {},
      err?.recoverable ?? true,
    );
  }

  return resp.json() as Promise<T>;
}

const get = <T>(path: string, timeoutMs?: number) => request<T>('GET', path, undefined, timeoutMs);
const post = <T>(path: string, body?: unknown, timeoutMs?: number) => request<T>('POST', path, body, timeoutMs);

// ---- Health ----
export const apiHealth = () => get<HealthStatus>('/api/health');
export const apiLightweightHealth = () => get<{ status: string; service: string; port: number }>('/health');
export const apiPreDemoHealth = () => get<any>('/api/health/pre-demo');

// ---- Boards ----
export const apiGetBoards = () => get<BoardProfile[]>('/api/boards');
export const apiGetBoard = (boardId: string) => get<BoardProfile>(`/api/boards/${boardId}`);

// ---- Connection ----
export const apiConnectionStatus = () => get<ConnectionStatus>('/api/connection/status');
export const apiConnect = (port: string, baudRate = 115200, runId?: string) =>
  post<ConnectionStatus>('/api/connection/connect', { port, baud_rate: baudRate, run_id: runId });
export const apiDisconnect = () => post<{ connected: false }>('/api/connection/disconnect');
export const apiAutoDetect = (runId?: string) =>
  post<{
    found: boolean;
    connected: boolean;
    port?: string;
    board_id?: string;
    board_profile?: BoardProfile;
    description?: string;
  }>('/api/connection/auto-detect', { run_id: runId });

// ---- Firmware ----
export const apiUploadFirmware = (
  name: string,
  sourceCode: string,
  hexContent?: string,
  elfPath?: string,
  mapContent?: string,
) =>
  post<FirmwareRecord>('/api/firmware/upload', {
    name,
    source_code: sourceCode,
    hex_content: hexContent,
    elf_path: elfPath,
    map_content: mapContent,
  });
export const apiListFirmware = () => get<FirmwareRecord[]>('/api/firmware');
export const apiGetFirmware = (id: string) => get<FirmwareRecord>(`/api/firmware/${id}`);
export const apiGetRecentIDESketch = () => get<import('../types').IDERecentResponse>('/api/firmware/ide-recent');
export const apiSyncIDESketch = (path?: string) =>
  post<import('../types').IDESyncResponse>('/api/firmware/sync-ide', { path });
export const apiSaveIDESketch = (path: string, sourceCode: string) =>
  post<{ success: boolean; path?: string; backup_path?: string; error?: string }>('/api/firmware/save-ide', {
    path,
    source_code: sourceCode,
  });
export const apiCompileFirmware = (sourceCode: string, boardId = 'arduino_uno', isSimulation = false) =>
  post<{
    status: string;
    board_id: string;
    fqbn?: string;
    mcu: string;
    toolchain: string;
    binary_path?: string;
    binary_size_bytes: number;
    flash_usage_pct: number;
    sram_usage_bytes: number;
    sram_usage_pct: number;
    size_unavailable?: boolean;
    compiler_output: string;
  }>('/api/firmware/compile', { source_code: sourceCode, board_id: boardId, is_simulation: isSimulation }, 60000);
export const apiFlashFirmware = (boardId: string, port: string, sourceCode?: string, binaryPath?: string) =>
  post<{
    status: string;
    board_id: string;
    port: string;
    toolchain: string;
    bytes_written: number;
    verified: boolean;
    message: string;
  }>('/api/firmware/flash', { board_id: boardId, port, source_code: sourceCode, binary_path: binaryPath }, 60000);

export interface InstrumentAndBuildResponse {
  status: string;
  board_id: string;
  run_id: string;
  original_file_path?: string;
  original_source_preserved: boolean;
  original_file_hash?: string;
  shadow_sketch_path?: string;
  diff: string;
  inserted_blocks: string[];
  static_analysis: {
    findings_count: number;
    findings: any[];
    estimated_flash_bytes: number;
    estimated_sram_static_bytes: number;
  };
  build_result: {
    status: string;
    board_id: string;
    fqbn?: string;
    mcu: string;
    toolchain: string;
    binary_path?: string;
    binary_size_bytes: number;
    flash_usage_pct: number;
    sram_usage_bytes: number;
    sram_usage_pct: number;
    compiler_output: string;
  };
  upload_result?: any;
  handshake?: any;
  run?: any;
  telemetry_active?: boolean;
  ready_for_physical_deployment: boolean;
}

export const apiInstrumentAndBuild = (
  sourceCode?: string,
  sketchPath?: string,
  boardId = 'arduino_uno',
  port?: string,
  executeUpload = false,
  instrumentationMode = 'BALANCED',
  sramWarningThresholdBytes = 256,
) =>
  post<InstrumentAndBuildResponse>('/api/firmware/instrument-and-build', {
    source_code: sourceCode,
    sketch_path: sketchPath,
    board_id: boardId,
    port,
    execute_upload: executeUpload,
    instrumentation_mode: instrumentationMode,
    sram_warning_threshold_bytes: sramWarningThresholdBytes,
  }, 90000);

export const apiTriggerHandshake = (timeoutSec = 3.0, port?: string, runId?: string) =>
  post<Record<string, unknown>>('/api/connection/handshake', {
    timeout_sec: timeoutSec,
    port,
    run_id: runId,
  });

export const apiReleaseSerial = (port?: string, waitMs = 500) =>
  post<{ released: boolean; port?: string; is_open: boolean }>('/api/connection/release', {
    port,
    wait_ms: waitMs,
  });



// ---- Runs ----
export const apiCreateRun = (
  boardId: string,
  firmwareId?: string,
  instrumentationMode = 'BALANCED',
  isSimulated = false,
  isDemo = false,
) =>
  post<RunRecord>('/api/runs', {
    board_id: boardId,
    firmware_id: firmwareId,
    instrumentation_mode: instrumentationMode,
    is_simulated: isSimulated,
    is_demo: isDemo,
  });
export const apiListRuns = () => get<RunRecord[]>('/api/runs');
export const apiGetRun = (runId: string) => get<RunRecord>(`/api/runs/${runId}`);
export const apiStartRun = (runId: string) => post<RunRecord>(`/api/runs/${runId}/start`);
export const apiStopRun = (runId: string) => post<RunRecord>(`/api/runs/${runId}/stop`);

// ---- Telemetry ----
export const apiGetTelemetry = (runId: string, limit = 1000, metric?: string) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (metric) params.set('metric', metric);
  return get<TelemetrySample[]>(`/api/runs/${runId}/telemetry?${params}`);
};

// ---- Analysis ----
export const apiGetAnalysis = (runId: string) =>
  get<Record<string, unknown>>(`/api/runs/${runId}/analysis`);
export const apiGetFindings = (runId: string) =>
  get<FindingRecord[]>(`/api/runs/${runId}/findings`);
export const apiScanSource = (sourceCode?: string, sketchPath?: string, boardId = 'arduino_uno', sourceFile?: string) =>
  post<{
    board_id: string;
    source_file: string;
    static_metrics: any;
    findings_count: number;
    findings: FindingRecord[];
  }>('/api/analysis/scan', {
    source_code: sourceCode,
    sketch_path: sketchPath,
    board_id: boardId,
    source_file: sourceFile,
  }, 30000);

// ---- Optimizations ----
export const apiGetOptimizations = (runId: string) =>
  get<OptimizationCandidate[]>(`/api/runs/${runId}/optimizations`);
export const apiListAllOptimizations = () =>
  get<OptimizationCandidate[]>('/api/optimizations');
export const apiGetOptimization = (optimizationId: string) =>
  get<OptimizationCandidate>(`/api/optimizations/${optimizationId}`);
export const apiApproveOptimization = (optimizationId: string) =>
  post<OptimizationCandidate>(`/api/optimizations/${optimizationId}/approve`);
export const apiAcceptOptimization = (optimizationId: string, sketchPath?: string, expectedHash?: string) =>
  post<{
    success: boolean;
    status: string;
    applied?: boolean;
    optimization: OptimizationCandidate;
    active_firmware?: any;
    source_application?: any;
    message?: string;
  }>(
    `/api/optimizations/${optimizationId}/accept`,
    { sketch_path: sketchPath, expected_hash: expectedHash, apply_to_source: true }
  );
export const apiRejectOptimization = (optimizationId: string) =>
  post<OptimizationCandidate>(`/api/optimizations/${optimizationId}/reject`);

export const apiApplyCandidate = (candidateId: string, sketchPath?: string, expectedHash?: string) =>
  post<{
    success: boolean;
    applied: boolean;
    candidate_id: string;
    sketch_path: string;
    backup_path: string;
    parent_source_hash: string;
    candidate_source_hash: string;
    applied_at: string;
  }>('/api/firmware/apply-candidate', {
    candidate_id: candidateId,
    sketch_path: sketchPath,
    expected_hash: expectedHash,
  });

export const apiRevertCandidate = (candidateId?: string, sketchPath?: string, backupPath?: string) =>
  post<{ success: boolean; reverted: boolean; sketch_path: string; restored_from: string }>(
    '/api/firmware/revert-candidate',
    {
      candidate_id: candidateId,
      sketch_path: sketchPath,
      backup_path: backupPath,
    }
  );

export const apiGetActiveFirmware = () =>
  get<FirmwareRecord>('/api/firmware/active');

// ---- Experiments ----
export const apiCreateExperiment = (
  title: string,
  boardId: string,
  baselineRunId: string,
  optimizationId: string,
) =>
  post<ExperimentRecord>('/api/experiments', {
    title,
    board_id: boardId,
    baseline_run_id: baselineRunId,
    optimization_id: optimizationId,
  });
export const apiListExperiments = () => get<ExperimentRecord[]>('/api/experiments');
export const apiGetExperiment = (expId: string) =>
  get<ExperimentRecord>(`/api/experiments/${expId}`);
export const apiRollbackExperiment = (expId: string) =>
  post<{ status: string; message: string; experiment_id: string }>(`/api/experiments/${expId}/rollback`);
export const apiRollbackOptimization = (optId: string) =>
  post<OptimizationCandidate>(`/api/optimizations/${optId}/rollback`);


// ---- Validation ----
export const apiValidateExperiment = (expId: string, candidateRunId: string) =>
  post<ValidationResult>(`/api/experiments/${expId}/validate`, {
    candidate_run_id: candidateRunId,
  });
export const apiGetValidationResult = (expId: string) =>
  get<ValidationResult>(`/api/experiments/${expId}/result`);

// ---- AI ----
export const apiAiAnalyze = (
  boardId: string,
  sourceCode?: string,
  runId?: string,
) =>
  post<AIContextInput>('/api/ai/analyze', {
    board_id: boardId,
    source_code: sourceCode,
    run_id: runId,
  }, 60000);

export const apiAiGenerateCandidate = (
  finding: FindingRecord,
  sourceCode: string,
  boardId: string,
  runId?: string,
  provider = 'auto',
) =>
  post<OptimizationCandidate>('/api/ai/generate-candidate', {
    finding,
    source_code: sourceCode,
    board_id: boardId,
    run_id: runId,
    provider,
  }, 60000);

export const apiGetAIProviders = () =>
  get<{ providers: AIProviderInfo[] }>('/api/ai/providers');

// ---- Demo Projects & Virtual Hardware ----
export const apiListDemoProjects = () =>
  get<DemoProject[]>('/api/demo/projects');

export const apiListDemoBoards = () =>
  get<DemoBoard[]>('/api/demo/boards');

export const apiSetupDemo = (boardId: string, projectId: string) =>
  post<DemoSetupResponse>('/api/demo/setup', {
    board_id: boardId,
    project_id: projectId,
  });

export { ARISApiError };
