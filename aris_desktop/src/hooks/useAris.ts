import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  HardwareProfile, 
  TelemetryFrame, 
  StaticAnalysisReport, 
  AIOptimizationResult, 
  ClosedLoopVerificationReport, 
  FirmwareMemoryMap 
} from '../types';

const API_BASE = 'http://127.0.0.1:8765/api';
const WS_URL = 'ws://127.0.0.1:8765/ws/telemetry';

export function useAris() {
  const [connected, setConnected] = useState<boolean>(false);
  const [boards, setBoards] = useState<any[]>([]);
  const [selectedBoardId, setSelectedBoardId] = useState<string>('arduino_uno');
  const [boardDetail, setBoardDetail] = useState<HardwareProfile | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryFrame | null>(null);
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryFrame[]>([]);
  const [isSimulating, setIsSimulating] = useState<boolean>(true);
  const [simMode, setSimMode] = useState<string>('blocking_delay');
  
  const [staticReport, setStaticReport] = useState<StaticAnalysisReport | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<AIOptimizationResult | null>(null);
  const [verificationReport, setVerificationReport] = useState<ClosedLoopVerificationReport | null>(null);
  const [memoryMap, setMemoryMap] = useState<FirmwareMemoryMap | null>(null);
  const [patentMarkdown, setPatentMarkdown] = useState<string>('');
  
  const [serialPorts, setSerialPorts] = useState<any[]>([]);
  const [connectedPort, setConnectedPort] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch initial boards
  useEffect(() => {
    fetch(`${API_BASE}/boards`)
      .then(res => res.json())
      .then(data => setBoards(data))
      .catch(err => console.error('Failed to load boards:', err));
  }, []);

  // Fetch board details when selected board changes
  useEffect(() => {
    fetch(`${API_BASE}/boards/${selectedBoardId}`)
      .then(res => res.json())
      .then(data => {
        setBoardDetail(data);
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'SET_BOARD', board_id: selectedBoardId }));
        }
      })
      .catch(err => console.error('Failed to load board details:', err));
  }, [selectedBoardId]);

  // WebSocket Telemetry Connection
  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;

    function connectWs() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        ws.send(JSON.stringify({ action: 'SET_BOARD', board_id: selectedBoardId }));
        ws.send(JSON.stringify({ action: 'SET_SIM_MODE', code_type: simMode, delay_ms: 20 }));
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'TELEMETRY_UPDATE') {
            const frame: TelemetryFrame = payload.data;
            setTelemetry(frame);
            setTelemetryHistory(prev => {
              const updated = [...prev, frame];
              return updated.length > 50 ? updated.slice(updated.length - 50) : updated;
            });
          }
        } catch (e) {
          console.error('Error parsing telemetry frame:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimer = setTimeout(connectWs, 2000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connectWs();

    return () => {
      clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, [selectedBoardId, simMode]);

  // Core Actions
  const analyzeCode = useCallback(async (sourceCode: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: sourceCode, board_id: selectedBoardId })
      });
      const report: StaticAnalysisReport = await res.json();
      setStaticReport(report);

      // Also refresh memory map
      const memRes = await fetch(`${API_BASE}/memory-map`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: sourceCode, board_id: selectedBoardId })
      });
      const map: FirmwareMemoryMap = await memRes.json();
      setMemoryMap(map);

      return report;
    } catch (err) {
      console.error('Analysis failed:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedBoardId]);

  const optimizeCode = useCallback(async (sourceCode: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: sourceCode, board_id: selectedBoardId })
      });
      const opt: AIOptimizationResult = await res.json();
      setOptimizationResult(opt);

      // Also trigger closed loop verification
      const vRes = await fetch(`${API_BASE}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: sourceCode, board_id: selectedBoardId })
      });
      const vData = await vRes.json();
      setVerificationReport(vData.verification_report);

      // Generate patent report
      const pRes = await fetch(`${API_BASE}/patent-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_code: sourceCode, board_id: selectedBoardId })
      });
      const pData = await pRes.json();
      setPatentMarkdown(pData.markdown_report);

      return opt;
    } catch (err) {
      console.error('Optimization failed:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedBoardId]);

  const setSimulationMode = useCallback((mode: string, delayMs: number = 20) => {
    setSimMode(mode);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'SET_SIM_MODE', code_type: mode, delay_ms: delayMs }));
    }
    fetch(`${API_BASE}/sim/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ board_id: selectedBoardId, code_type: mode, delay_ms: delayMs })
    });
  }, [selectedBoardId]);

  const setVirtualInput = useCallback((pinName: string, isAnalog: boolean, value: number) => {
    fetch(`${API_BASE}/sim/set-input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin_name: pinName, is_analog: isAnalog, value })
    });
  }, []);

  const refreshSerialPorts = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/ports`);
      const data = await res.json();
      setSerialPorts(data);
    } catch (e) {
      console.error('Failed to list serial ports:', e);
    }
  }, []);

  const connectSerial = useCallback(async (port: string) => {
    try {
      const res = await fetch(`${API_BASE}/serial/connect?port=${port}`, { method: 'POST' });
      const data = await res.json();
      if (data.connected) {
        setConnectedPort(port);
      }
    } catch (e) {
      console.error('Serial connect error:', e);
    }
  }, []);

  const disconnectSerial = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/serial/disconnect`, { method: 'POST' });
      setConnectedPort(null);
    } catch (e) {
      console.error('Serial disconnect error:', e);
    }
  }, []);

  return {
    connected,
    boards,
    selectedBoardId,
    setSelectedBoardId,
    boardDetail,
    telemetry,
    telemetryHistory,
    isSimulating,
    setIsSimulating,
    simMode,
    setSimulationMode,
    staticReport,
    optimizationResult,
    verificationReport,
    memoryMap,
    patentMarkdown,
    serialPorts,
    connectedPort,
    loading,
    analyzeCode,
    optimizeCode,
    setVirtualInput,
    refreshSerialPorts,
    connectSerial,
    disconnectSerial
  };
}
