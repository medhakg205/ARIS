// ============================================================
// ARIS — Main State Hook
// Aggregates all backend state: health, boards, connection,
// active run, telemetry stream, findings, optimizations,
// experiments, validation history, and AI providers.
// ============================================================

import { useState, useEffect, useCallback, useRef } from 'react';
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
  CanonicalMetric,
} from '../types';
import {
  apiHealth,
  apiGetBoards,
  apiConnectionStatus,
  apiConnect,
  apiDisconnect,
  apiUploadFirmware,
  apiListFirmware,
  apiCreateRun,
  apiStartRun,
  apiStopRun,
  apiGetFindings,
  apiGetOptimizations,
  apiApproveOptimization,
  apiRejectOptimization,
  apiAiGenerateCandidate,
  apiCreateExperiment,
  apiListExperiments,
  apiGetValidationResult,
  apiGetAIProviders,
  ARISApiError,
} from '../services/api';
import { arisWs } from '../services/websocket';

// Max telemetry samples to keep in memory per metric
const MAX_HISTORY = 200;

export interface MetricHistory {
  metric: CanonicalMetric;
  samples: TelemetrySample[];
}

export function useARIS() {
  // ---- System State ----
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // ---- Boards ----
  const [boards, setBoards] = useState<BoardProfile[]>([]);
  const [selectedBoard, setSelectedBoard] = useState<BoardProfile | null>(null);

  // ---- Hardware Connection ----
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [hardwareConnected, setHardwareConnected] = useState(false);

  // ---- Active Run ----
  const [activeRun, setActiveRun] = useState<RunRecord | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [isSimulated, setIsSimulated] = useState(false);

  // ---- Firmware ----
  const [firmwareList, setFirmwareList] = useState<FirmwareRecord[]>([]);
  const [activeFirmware, setActiveFirmware] = useState<FirmwareRecord | null>(null);

  // ---- Telemetry ----
  const [latestSamples, setLatestSamples] = useState<Record<string, TelemetrySample>>({});
  const [telemetryHistory, setTelemetryHistory] = useState<Record<string, TelemetrySample[]>>({});

  // ---- Analysis ----
  const [findings, setFindings] = useState<FindingRecord[]>([]);
  const [optimizations, setOptimizations] = useState<OptimizationCandidate[]>([]);

  // ---- Experiments & Validation ----
  const [experiments, setExperiments] = useState<ExperimentRecord[]>([]);
  const [validations, setValidations] = useState<Record<string, ValidationResult>>({});

  // ---- Errors ----
  const [lastError, setLastError] = useState<ARISApiError | null>(null);

  // ---- Loading States ----
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const setLoad = useCallback((key: string, val: boolean) =>
    setLoading((prev) => ({ ...prev, [key]: val })), []);

  const clearError = useCallback(() => setLastError(null), []);

  // ---- Bootstrap: health check ----
  useEffect(() => {
    let mounted = true;
    const probe = async () => {
      try {
        const h = await apiHealth();
        if (!mounted) return;
        setHealth(h);
        setBackendOnline(true);
        setHardwareConnected(h.serial_connected);
      } catch {
        if (!mounted) return;
        setBackendOnline(false);
        setLastError(new ARISApiError(
          'ARIS_BACKEND_UNAVAILABLE',
          'Cannot reach ARIS backend. Is the server running on port 8765?',
          {},
          true,
        ));
      }
    };
    probe();
    const interval = setInterval(probe, 10000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  // ---- Load boards ----
  useEffect(() => {
    if (!backendOnline) return;
    apiGetBoards()
      .then((b) => {
        setBoards(b);
        if (b.length > 0 && !selectedBoard) setSelectedBoard(b[0]);
      })
      .catch(() => {});
  }, [backendOnline]);

  // ---- Load firmware list ----
  const refreshFirmware = useCallback(() => {
    if (!backendOnline) return;
    apiListFirmware()
      .then(setFirmwareList)
      .catch(() => {});
  }, [backendOnline]);

  useEffect(() => { refreshFirmware(); }, [refreshFirmware]);

  // ---- Load experiments ----
  const refreshExperiments = useCallback(() => {
    if (!backendOnline) return;
    apiListExperiments()
      .then(setExperiments)
      .catch(() => {});
  }, [backendOnline]);

  useEffect(() => { refreshExperiments(); }, [refreshExperiments]);

  // ---- WebSocket subscription ----
  useEffect(() => {
    const unsub = arisWs.subscribe((msg) => {
      if (msg.type === 'CONNECTION_STATE') {
        setWsConnected(msg.connected);
        return;
      }
      if (msg.type === 'TELEMETRY_UPDATE') {
        const sample = msg.data as TelemetrySample;
        setLatestSamples((prev) => ({ ...prev, [sample.metric]: sample }));
        setTelemetryHistory((prev) => {
          const existing = prev[sample.metric] || [];
          const updated = [...existing, sample];
          return {
            ...prev,
            [sample.metric]: updated.length > MAX_HISTORY
              ? updated.slice(updated.length - MAX_HISTORY)
              : updated,
          };
        });
      }
      if (msg.type === 'ERROR') {
        const err = msg.data as import('../types').ArisError;
        setLastError(new ARISApiError(
          err.error_code as import('../types').ArisErrorCode,
          err.message,
          err.details,
          err.recoverable,
        ));
      }
    });
    return unsub;
  }, []);

  // Connect WS when we have an active run
  useEffect(() => {
    if (activeRun && backendOnline) {
      arisWs.connect(activeRun.run_id);
    } else if (!activeRun) {
      arisWs.disconnect();
    }
    return () => {};
  }, [activeRun?.run_id, backendOnline]);

  // ---- Actions ----
  const connectHardware = useCallback(async (port: string, baud = 115200) => {
    setLoad('connect', true);
    try {
      await apiConnect(port, baud);
      setHardwareConnected(true);
      setIsDemo(false);
      setIsSimulated(false);
    } catch (e) {
      setLastError(e as ARISApiError);
    } finally {
      setLoad('connect', false);
    }
  }, [setLoad]);

  const disconnectHardware = useCallback(async () => {
    try {
      await apiDisconnect();
      setHardwareConnected(false);
    } catch (e) {
      setLastError(e as ARISApiError);
    }
  }, []);

  const uploadFirmware = useCallback(async (name: string, source: string) => {
    setLoad('firmware', true);
    try {
      const fw = await apiUploadFirmware(name, source);
      setActiveFirmware(fw);
      await refreshFirmware();
      return fw;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('firmware', false);
    }
  }, [setLoad, refreshFirmware]);

  const startRun = useCallback(async (demo = false) => {
    if (!selectedBoard) return null;
    setLoad('run', true);
    setIsDemo(demo);
    setIsSimulated(demo);
    try {
      const run = await apiCreateRun(
        selectedBoard.board_id,
        activeFirmware?.firmware_id,
        'BALANCED',
        demo,
        demo,
      );
      const started = await apiStartRun(run.run_id);
      setActiveRun(started);
      setTelemetryHistory({});
      setLatestSamples({});
      return started;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('run', false);
    }
  }, [selectedBoard, activeFirmware, setLoad]);

  const stopRun = useCallback(async () => {
    if (!activeRun) return;
    setLoad('stop', true);
    try {
      const stopped = await apiStopRun(activeRun.run_id);
      setActiveRun(stopped);
      // Load findings + optimizations after run
      const [f, o] = await Promise.all([
        apiGetFindings(activeRun.run_id),
        apiGetOptimizations(activeRun.run_id),
      ]);
      setFindings(f);
      setOptimizations(o);
    } catch (e) {
      setLastError(e as ARISApiError);
    } finally {
      setLoad('stop', false);
    }
  }, [activeRun, setLoad]);

  const generateCandidate = useCallback(async (
    finding: FindingRecord,
    sourceCode: string,
    provider = 'auto',
  ) => {
    if (!selectedBoard || !activeRun) return null;
    setLoad('ai', true);
    try {
      const candidate = await apiAiGenerateCandidate(
        finding,
        sourceCode,
        selectedBoard.board_id,
        activeRun.run_id,
        provider,
      );
      setOptimizations((prev) => {
        const exists = prev.find((o) => o.optimization_id === candidate.optimization_id);
        return exists ? prev.map((o) => o.optimization_id === candidate.optimization_id ? candidate : o) : [...prev, candidate];
      });
      return candidate;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('ai', false);
    }
  }, [selectedBoard, activeRun, setLoad]);

  const approveOptimization = useCallback(async (optimizationId: string) => {
    setLoad(`approve_${optimizationId}`, true);
    try {
      const updated = await apiApproveOptimization(optimizationId);
      setOptimizations((prev) => prev.map((o) => o.optimization_id === optimizationId ? updated : o));
      return updated;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad(`approve_${optimizationId}`, false);
    }
  }, [setLoad]);

  const rejectOptimization = useCallback(async (optimizationId: string) => {
    setLoad(`reject_${optimizationId}`, true);
    try {
      const updated = await apiRejectOptimization(optimizationId);
      setOptimizations((prev) => prev.map((o) => o.optimization_id === optimizationId ? updated : o));
      return updated;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad(`reject_${optimizationId}`, false);
    }
  }, [setLoad]);

  const createExperiment = useCallback(async (
    title: string,
    optimizationId: string,
    baselineRunId?: string,
  ) => {
    if (!selectedBoard || !activeRun) return null;
    setLoad('experiment', true);
    try {
      const exp = await apiCreateExperiment(
        title,
        selectedBoard.board_id,
        baselineRunId || activeRun.run_id,
        optimizationId,
      );
      await refreshExperiments();
      return exp;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('experiment', false);
    }
  }, [selectedBoard, activeRun, setLoad, refreshExperiments]);

  const loadValidation = useCallback(async (experimentId: string) => {
    try {
      const result = await apiGetValidationResult(experimentId);
      setValidations((prev) => ({ ...prev, [experimentId]: result }));
      return result;
    } catch {
      return null;
    }
  }, []);

  return {
    // System
    health, backendOnline, wsConnected,
    // Boards
    boards, selectedBoard, setSelectedBoard,
    // Connection
    connectionStatus, hardwareConnected,
    connectHardware, disconnectHardware,
    // Demo mode
    isDemo, isSimulated,
    // Firmware
    firmwareList, activeFirmware, setActiveFirmware,
    uploadFirmware, refreshFirmware,
    // Run
    activeRun, startRun, stopRun,
    // Telemetry
    latestSamples, telemetryHistory,
    // Analysis
    findings, optimizations,
    // AI
    generateCandidate,
    // Approval
    approveOptimization, rejectOptimization,
    // Experiments & Validation
    experiments, validations,
    createExperiment, loadValidation, refreshExperiments,
    // Errors
    lastError, clearError,
    // Loading
    loading,
  };
}
