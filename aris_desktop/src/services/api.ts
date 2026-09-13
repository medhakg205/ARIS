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
} from '../types';

const DEFAULT_BASE = 'http://127.0.0.1:8765';

function getBase(): string {
  return (window as unknown as Record<string, unknown>).__ARIS_API_BASE__ as string || DEFAULT_BASE;
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
): Promise<T> {
  const url = `${getBase()}${path}`;
  const opts: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(15000),
  };
  if (body !== undefined) opts.body = JSON.stringify(body);

  let resp: Response;
  try {
    resp = await fetch(url, opts);
  } catch (e) {
    throw new ARISApiError(
      'ARIS_BACKEND_UNAVAILABLE',
      'Cannot reach ARIS backend. Is the server running on port 8765?',
      { url },
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

const get = <T>(path: string) => request<T>('GET', path);
const post = <T>(path: string, body?: unknown) => request<T>('POST', path, body);

// ---- Health ----
export const apiHealth = () => get<HealthStatus>('/api/health');

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

// ---- Optimizations ----
export const apiGetOptimizations = (runId: string) =>
  get<OptimizationCandidate[]>(`/api/runs/${runId}/optimizations`);
export const apiApproveOptimization = (optimizationId: string) =>
  post<OptimizationCandidate>(`/api/optimizations/${optimizationId}/approve`);
export const apiRejectOptimization = (optimizationId: string) =>
  post<OptimizationCandidate>(`/api/optimizations/${optimizationId}/reject`);

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
  });

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
  });

export const apiGetAIProviders = () =>
  get<{ providers: AIProviderInfo[] }>('/api/ai/providers');

export { ARISApiError };
