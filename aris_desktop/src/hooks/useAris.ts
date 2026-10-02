// ============================================================
// ARIS — Main State Hook
// Aggregates all backend state: health, boards, connection,
// active run, telemetry stream, findings, optimizations,
// experiments, validation history, and AI providers.
// ============================================================

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
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
  DeviceConnectionState,
} from '../types';
import {
  apiHealth,
  apiGetBoards,
  apiConnectionStatus,
  apiConnect,
  apiDisconnect,
  apiUploadFirmware,
  apiListFirmware,
  apiGetFirmware,
  apiSetupDemo,
  apiCreateRun,
  apiStartRun,
  apiStopRun,
  apiGetFindings,
  apiGetOptimizations,
  apiGetOptimization,
  apiApproveOptimization,
  apiRejectOptimization,
  apiAiGenerateCandidate,
  apiCreateExperiment,
  apiListExperiments,
  apiGetExperiment,
  apiValidateExperiment,
  apiGetValidationResult,
  apiGetAIProviders,
  apiAutoDetect,
  apiRollbackExperiment,
  apiRollbackOptimization,
  apiCompileFirmware,
  apiFlashFirmware,
  apiTriggerHandshake,
  apiGetRecentIDESketch,
  apiSyncIDESketch,
  apiSaveIDESketch,
  ARISApiError,
} from '../services/api';
import type { IDESketchInfo } from '../types';
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

  // ---- Firmware & Arduino IDE Auto-Sync ----
  const [firmwareList, setFirmwareList] = useState<FirmwareRecord[]>([]);
  const [activeFirmware, setActiveFirmware] = useState<FirmwareRecord | null>(null);
  const [ideSketches, setIdeSketches] = useState<IDESketchInfo[]>([]);
  const [activeIDESketch, setActiveIDESketch] = useState<IDESketchInfo | null>(null);

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
    let retries = 0;
    const maxFastRetries = 5;

    const probe = async () => {
      try {
        const h = await apiHealth();
        if (!mounted) return;
        setHealth(h);
        setBackendOnline(true);
        setLastError(null);
        setHardwareConnected(h.serial_connected);
      } catch {
        if (!mounted) return;
        if (retries < maxFastRetries) {
          retries++;
          setTimeout(probe, 1000);
          return;
        }
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
    const interval = setInterval(probe, 8000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  // ---- Load boards ----
  // ---- Load boards catalog (metadata only, does not imply board is connected) ----
  useEffect(() => {
    if (!backendOnline) return;
    apiGetBoards()
      .then((b) => {
        setBoards(b);
      })
      .catch(() => {});
  }, [backendOnline]);

  // ---- Automatic Hardware Detection & Auto-Connection Polling ----
  // Scans USB/COM ports every 2.5s. When an Arduino is plugged in,
  // connects to the COM port, sets the verified hardware board profile,
  // and starts streaming physical telemetry.
  useEffect(() => {
    if (!backendOnline) return;
    let isDetecting = false;

    const scanHardware = async () => {
      if (isDetecting) return;
      try {
        const cs = await apiConnectionStatus();
        setConnectionStatus(cs);
        setHardwareConnected(cs.connected);

        // If hardware is physically connected, sync real board profile if available
        if (cs.connected) {
          setIsDemo(false);
          setIsSimulated(false);
          return;
        } else if (!isDemo && selectedBoard && !cs.connected) {
          // Hardware disconnected and not in demo mode
          setSelectedBoard(null);
        }

        // Check if any serial ports are physically present
        if (cs.available_ports && cs.available_ports.length > 0 && !cs.connected) {
          isDetecting = true;
          const result = await apiAutoDetect();
          if (result.found && result.connected) {
            setHardwareConnected(true);
            setIsDemo(false);
            setIsSimulated(false);
            if (result.board_profile) {
              setSelectedBoard(result.board_profile);
            } else if (result.board_id && boards.length > 0) {
              const matched = boards.find((b) => b.board_id === result.board_id);
              if (matched) setSelectedBoard(matched);
            }
          }
        }
      } catch {
        // Ignore polling errors
      } finally {
        isDetecting = false;
      }
    };

    scanHardware();
    const interval = setInterval(scanHardware, 2500);
    return () => clearInterval(interval);
  }, [backendOnline, boards, isDemo, selectedBoard]);

  // Authoritative connection state
  const deviceState: DeviceConnectionState = useMemo(() => {
    if (isDemo || isSimulated) return 'SIMULATION';
    if (loading['connect'] || loading['autodetect']) return 'DETECTING';
    if (hardwareConnected) {
      if (selectedBoard) return 'CONNECTED';
      return 'UNKNOWN';
    }
    return 'NO_HARDWARE';
  }, [isDemo, isSimulated, loading, hardwareConnected, selectedBoard]);

  // ---- Arduino IDE Auto-Sync: Auto-detects sketches from Arduino IDE 2.x ----
  const refreshIDESketches = useCallback(async () => {
    if (!backendOnline) return;
    try {
      const resp = await apiGetRecentIDESketch();
      if (resp.found && resp.sketches.length > 0) {
        setIdeSketches(resp.sketches);
      }
    } catch {
      // Ignore background sync errors
    }
  }, [backendOnline]);

  useEffect(() => {
    refreshIDESketches();
  }, [refreshIDESketches]);

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

        // Automatically synchronize board profile if sample indicates specific board
        if (sample.board_id && (!selectedBoard || selectedBoard.board_id !== sample.board_id)) {
          const matched = boards.find((b) => b.board_id === sample.board_id);
          if (matched) {
            setSelectedBoard(matched);
          }
        }
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
  const autoDetectHardware = useCallback(async () => {
    try {
      const res = await apiAutoDetect();
      if (res.found && res.connected) {
        setHardwareConnected(true);
        setIsDemo(false);
        setIsSimulated(false);
        if (res.board_profile) setSelectedBoard(res.board_profile);
      }
      return res;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    }
  }, []);

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
      setSelectedBoard(null);
      setActiveRun(null);
    } catch (e) {
      setLastError(e as ARISApiError);
    }
  }, []);

  const syncIDESketch = useCallback(async (path?: string) => {
    setLoad('firmware', true);
    try {
      const resp = await apiSyncIDESketch(path);
      if (resp.success && resp.firmware) {
        setActiveFirmware(resp.firmware);
        setActiveIDESketch({
          name: resp.name,
          path: resp.path,
          last_modified: Date.now() / 1000,
          source_code: resp.source_code,
        });
        await refreshFirmware();
        return resp.firmware;
      }
      return null;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('firmware', false);
    }
  }, [setLoad, refreshFirmware]);

  const saveIDESketch = useCallback(async (path: string, code: string) => {
    setLoad('firmware', true);
    try {
      const res = await apiSaveIDESketch(path, code);
      if (res.success) {
        await refreshIDESketches();
        return true;
      }
      return false;
    } catch (e) {
      setLastError(e as ARISApiError);
      return false;
    } finally {
      setLoad('firmware', false);
    }
  }, [setLoad, refreshIDESketches]);

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
    let board = selectedBoard;
    if (!board && boards.length > 0) {
      board = boards[0];
      setSelectedBoard(board);
    }
    if (!board) return null;
    setLoad('run', true);
    setIsDemo(demo);
    setIsSimulated(demo);
    try {
      let fwId = activeFirmware?.firmware_id;
      if (demo && !fwId) {
        fwId = 'ARIS-DEMO-FIRMWARE-001';
      }
      const run = await apiCreateRun(
        board.board_id,
        fwId,
        'BALANCED',
        demo,
        demo,
      );
      const started = await apiStartRun(run.run_id);
      setActiveRun(started);
      setTelemetryHistory({});
      setLatestSamples({});

      // Pre-fetch initial static analysis findings for this run
      try {
        const initialFindings = await apiGetFindings(started.run_id);
        if (initialFindings && initialFindings.length > 0) {
          setFindings(initialFindings);
        }
      } catch (_) {}

      // If demo run and activeFirmware is not loaded, fetch demo firmware record
      if (demo && !activeFirmware) {
        try {
          const demoFw = await apiGetFirmware('ARIS-DEMO-FIRMWARE-001');
          if (demoFw) {
            setActiveFirmware(demoFw);
          }
        } catch (_) {}
      }

      return started;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('run', false);
    }
  }, [selectedBoard, boards, activeFirmware, setLoad]);

  const startDemo = useCallback(async (boardId: string = 'arduino_uno', projectId: string = 'led_blink') => {
    setLoad('run', true);
    setIsDemo(true);
    setIsSimulated(true);
    try {
      // 1. Setup demo project and create firmware record in backend
      const setupRes = await apiSetupDemo(boardId, projectId);
      
      // Find matching board profile or synthesize canonical specs
      const targetBoard = boards.find((b) => b.board_id === boardId) || {
        board_id: boardId,
        display_name: boardId === 'arduino_mega' ? 'Arduino Mega 2560' : boardId === 'arduino_nano' ? 'Arduino Nano' : 'Arduino Uno',
        mcu: boardId === 'arduino_mega' ? 'atmega2560' : 'atmega328p',
        architecture: 'avr8',
        clock_hz: 16000000,
        flash_bytes: boardId === 'arduino_mega' ? 262144 : 32768,
        sram_bytes: boardId === 'arduino_mega' ? 8192 : 2048,
        eeprom_bytes: boardId === 'arduino_mega' ? 4096 : 1024,
        gpio_count: boardId === 'arduino_mega' ? 54 : 14,
        adc_channels: boardId === 'arduino_mega' ? 16 : 6,
        pwm_channels: boardId === 'arduino_mega' ? 15 : 6,
        uart_count: boardId === 'arduino_mega' ? 4 : 1,
        registers: {},
      };
      setSelectedBoard(targetBoard as BoardProfile);

      // Set active firmware
      const fwRecord: FirmwareRecord = {
        firmware_id: setupRes.firmware_id,
        name: `${setupRes.project.title} (${targetBoard.display_name})`,
        source_code: setupRes.source_code,
        created_at: new Date().toISOString(),
      };
      setActiveFirmware(fwRecord);

      // 2. Create and start simulated run
      const run = await apiCreateRun(boardId, setupRes.firmware_id, 'BALANCED', true, true);
      const started = await apiStartRun(run.run_id);
      setActiveRun(started);
      setTelemetryHistory({});
      setLatestSamples({});

      // 3. Pre-fetch initial static analysis findings
      try {
        const initialFindings = await apiGetFindings(started.run_id);
        if (initialFindings && initialFindings.length > 0) {
          setFindings(initialFindings);
        }
      } catch (_) {}

      return started;
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad('run', false);
    }
  }, [boards, setLoad]);

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
      if (isDemo || isSimulated) {
        setIsDemo(false);
        setIsSimulated(false);
        if (!hardwareConnected) {
          setSelectedBoard(null);
        }
      }
    } catch (e) {
      setLastError(e as ARISApiError);
    } finally {
      setLoad('stop', false);
    }
  }, [activeRun, isDemo, isSimulated, hardwareConnected, setLoad]);

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

  const runExperimentValidation = useCallback(async (experimentId: string) => {
    setLoad(`validate_${experimentId}`, true);
    try {
      // 1. Fetch or locate experiment record
      let exp = experiments.find((e) => e.experiment_id === experimentId);
      if (!exp) {
        exp = await apiGetExperiment(experimentId);
      }
      if (!exp) return null;

      let opt = optimizations.find((o) => o.optimization_id === exp.optimization_id);
      if (!opt) {
        try {
          opt = await apiGetOptimization(exp.optimization_id);
        } catch (_) {}
      }

      // 2. Prepare candidate firmware
      let candFwId = `ARIS-FW-CANDIDATE-${experimentId}`;
      const codeToUpload = opt?.after_code;
      if (codeToUpload) {
        try {
          const uploaded = await apiUploadFirmware(
            `Candidate: ${opt?.title || exp.title}`,
            codeToUpload
          );
          candFwId = uploaded.firmware_id;
        } catch {
          // fallback to synthesized candidate ID
        }
      }

      // 3. Determine execution provenance: physical hardware vs simulation
      const isPhysical = hardwareConnected && Boolean(selectedBoard) && Boolean(connectionStatus?.port);
      const targetBoard = exp.board_id || selectedBoard?.board_id || 'arduino_uno';

      if (isPhysical && codeToUpload && connectionStatus?.port) {
        // ---- PHYSICAL MCU VALIDATION WORKFLOW ----
        // Compile candidate firmware for target board
        await apiCompileFirmware(codeToUpload, targetBoard, false);

        // Flash candidate firmware onto physical microcontroller
        await apiFlashFirmware(targetBoard, connectionStatus.port, codeToUpload);

        // Verify runtime handshake from freshly booted instrumented firmware
        await apiTriggerHandshake(3.0);

        // Create authentic physical candidate run
        const candRun = await apiCreateRun(
          targetBoard,
          candFwId,
          'BALANCED',
          false, // is_simulated = false
          false  // is_demo = false
        );

        // Start candidate run and stream physical serial telemetry
        const started = await apiStartRun(candRun.run_id);
        setActiveRun(started);

        // Physical benchmark collection window: 3.5 seconds
        await new Promise((resolve) => setTimeout(resolve, 3500));

        // Stop candidate run
        await apiStopRun(candRun.run_id);

        // Empirically validate candidate against physical baseline
        const report = await apiValidateExperiment(experimentId, candRun.run_id);

        await refreshExperiments();
        await loadValidation(experimentId);
        return report;
      } else {
        // ---- EXPLICIT SIMULATION VALIDATION WORKFLOW ----
        const candRun = await apiCreateRun(
          targetBoard,
          candFwId,
          'BALANCED',
          true, // is_simulated = true
          true  // is_demo = true
        );

        // Start candidate run and stream simulation telemetry
        const started = await apiStartRun(candRun.run_id);
        setActiveRun(started);

        // Wait 1.6s for telemetry collection (16 frames of 20 canonical metrics = 320 samples)
        await new Promise((resolve) => setTimeout(resolve, 1600));

        // Stop candidate run (triggers baseline generation for candidate)
        await apiStopRun(candRun.run_id);

        // Run empirical validation comparison against baseline
        const report = await apiValidateExperiment(experimentId, candRun.run_id);

        // Refresh experiments and store validation result
        await refreshExperiments();
        await loadValidation(experimentId);

        return report;
      }
    } catch (e) {
      setLastError(e as ARISApiError);
      return null;
    } finally {
      setLoad(`validate_${experimentId}`, false);
    }
  }, [
    experiments,
    optimizations,
    selectedBoard,
    hardwareConnected,
    connectionStatus,
    setLoad,
    refreshExperiments,
    loadValidation,
  ]);

  const rollbackExperiment = useCallback(async (experimentId: string) => {
    try {
      await apiRollbackExperiment(experimentId);
      await refreshExperiments();
    } catch (e) {
      setLastError(e as ARISApiError);
    }
  }, [refreshExperiments]);

  const rollbackOptimization = useCallback(async (optimizationId: string) => {
    try {
      await apiRollbackOptimization(optimizationId);
      await refreshExperiments();
    } catch (e) {
      setLastError(e as ARISApiError);
    }
  }, [refreshExperiments]);

  const patentMarkdown = `# Formal Patent Claims & Research Specification
## Claim 1: Deterministic Observer-Effect Profiler Overhead Cancellation
A non-invasive runtime instrumentation system for microcontrollers that mathematically eliminates probe overhead cycle latency from execution timing.

## Claim 2: Dynamic Multi-Dimensional AST Section Correlation
Bidirectional mapping between real-time UART telemetry frames and abstract syntax tree structures.

## Claim 3: Autonomous Closed-Loop Rollback Protection
Automated compilation, flashing, and hypothesis-verified hardware recovery upon SLA violation.
`;

  return {
    // System
    health, backendOnline, wsConnected,
    // Boards
    boards, selectedBoard, setSelectedBoard,
    // Connection
    connectionStatus, hardwareConnected, deviceState,
    connectHardware, disconnectHardware, autoDetectHardware,
    // Demo mode
    isDemo, isSimulated,
    // Firmware & Arduino IDE
    firmwareList, activeFirmware, setActiveFirmware,
    uploadFirmware, refreshFirmware,
    ideSketches, activeIDESketch, syncIDESketch, saveIDESketch, refreshIDESketches,
    // Run
    activeRun, startRun, startDemo, stopRun,
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
    createExperiment, loadValidation, refreshExperiments, runExperimentValidation,
    rollbackExperiment, rollbackOptimization,
    patentMarkdown,
    // Errors
    lastError, clearError,
    // Loading
    loading,
  };
}
