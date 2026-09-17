import React, { useState, useEffect } from 'react';
import { Upload, FileCode, CheckCircle, XCircle, RefreshCw, Cpu, Check, FolderOpen } from 'lucide-react';
import { ErrorBanner } from '../common/ErrorBanner';
import type { FirmwareRecord, BoardProfile, IDESketchInfo } from '../../types';
import { ARISApiError } from '../../services/api';

interface FirmwareViewProps {
  firmwareList: FirmwareRecord[];
  activeFirmware: FirmwareRecord | null;
  selectedBoard: BoardProfile | null;
  loading: Record<string, boolean>;
  lastError: ARISApiError | null;
  ideSketches?: IDESketchInfo[];
  activeIDESketch?: IDESketchInfo | null;
  onSyncIDESketch?: (path?: string) => Promise<FirmwareRecord | null>;
  onRefreshIDESketches?: () => Promise<void>;
  onUpload: (name: string, source: string) => Promise<FirmwareRecord | null>;
  onSelectFirmware: (fw: FirmwareRecord) => void;
  onClearError: () => void;
}

const EXAMPLE_SKETCH = `// ARIS Example: Blocking Delay Antipattern
// Target: Arduino Uno / Nano (ATmega328P)

void setup() {
  Serial.begin(115200);
  pinMode(13, OUTPUT);
}

void loop() {
  int sensorValue = analogRead(A0);
  Serial.print("Sensor: ");
  Serial.println(sensorValue);

  digitalWrite(13, HIGH);
  delay(20);        // <-- ARIS will flag this blocking delay
  digitalWrite(13, LOW);
  delay(20);
}`;

export const FirmwareView: React.FC<FirmwareViewProps> = ({
  firmwareList,
  activeFirmware,
  selectedBoard,
  loading,
  lastError,
  ideSketches = [],
  activeIDESketch,
  onSyncIDESketch,
  onRefreshIDESketches,
  onUpload,
  onSelectFirmware,
  onClearError,
}) => {
  const [sourceCode, setSourceCode] = useState(() => {
    return activeFirmware?.source_code || activeIDESketch?.source_code || '';
  });
  const [firmwareName, setFirmwareName] = useState(() => {
    return activeFirmware?.name || activeIDESketch?.name || '';
  });
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [isSyncing, setIsSyncing] = useState(false);

  // Synchronize editor if activeFirmware or activeIDESketch updates
  useEffect(() => {
    if (activeFirmware?.source_code) {
      setSourceCode(activeFirmware.source_code);
      setFirmwareName(activeFirmware.name);
    } else if (activeIDESketch?.source_code) {
      setSourceCode(activeIDESketch.source_code);
      setFirmwareName(activeIDESketch.name);
    }
  }, [activeFirmware, activeIDESketch]);

  const handleUpload = async () => {
    setUploadStatus('idle');
    const result = await onUpload(firmwareName, sourceCode);
    setUploadStatus(result ? 'success' : 'error');
  };

  const handleSwitchSketch = async (sketch: IDESketchInfo) => {
    if (onSyncIDESketch) {
      setIsSyncing(true);
      await onSyncIDESketch(sketch.path);
      setIsSyncing(false);
    }
    if (sketch.source_code) {
      setSourceCode(sketch.source_code);
      setFirmwareName(sketch.name);
    }
  };

  const handleManualRefresh = async () => {
    if (onRefreshIDESketches) {
      setIsSyncing(true);
      await onRefreshIDESketches();
      setIsSyncing(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Source editor */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-slate-800/80">
        {/* Arduino IDE Auto-Sync Banner */}
        {activeIDESketch && sourceCode ? (
          <div className="px-4 py-2 bg-[#1e2229] border-b border-white/[0.08] flex items-center justify-between gap-3 shrink-0">
            <div className="flex items-center gap-2 min-w-0">
              <span className="flex h-2 w-2 relative shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00878a] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#00878a]"></span>
              </span>
              <span className="text-[11px] font-mono text-[#00878a] font-medium">
                Auto-Synced with Arduino IDE:
              </span>
              <span className="text-[11px] font-mono font-semibold text-slate-100 truncate">
                {activeIDESketch.name}
              </span>
              <span className="text-[10px] font-mono text-slate-400 hidden sm:inline truncate max-w-xs" title={activeIDESketch.path}>
                ({activeIDESketch.path})
              </span>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={handleManualRefresh}
                disabled={isSyncing}
                className="flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono bg-[#00878a]/10 hover:bg-[#00878a]/20 text-[#00878a] border border-[#00878a]/30 rounded transition-colors disabled:opacity-50"
                title="Scan for recent Arduino IDE changes"
              >
                <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Scanning…' : 'Rescan IDE'}
              </button>
            </div>
          </div>
        ) : (
          <div className="px-4 py-2 bg-[#1e2229] border-b border-white/[0.08] text-[11px] font-mono text-slate-400 flex items-center justify-between">
            <span>⚡ Arduino IDE Sync: Code uploaded to your microcontroller will automatically appear here.</span>
            <button
              onClick={handleManualRefresh}
              disabled={isSyncing}
              className="flex items-center gap-1 px-2 py-0.5 text-[10px] text-[#00878a] hover:text-[#00979d] border border-[#00878a]/30 rounded"
            >
              <RefreshCw className={`w-3 h-3 ${isSyncing ? 'animate-spin' : ''}`} /> Check Arduino IDE
            </button>
          </div>
        )}

        {/* Toolbar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-white/[0.08] bg-[#1e2229] shrink-0">
          <FileCode className="w-4 h-4 text-slate-400" />
          <input
            value={firmwareName}
            onChange={(e) => setFirmwareName(e.target.value)}
            className="bg-transparent text-sm font-mono text-slate-200 border-none outline-none w-56 font-medium placeholder:text-slate-600"
            placeholder="No sketch loaded..."
          />
          <div className="text-[10px] font-mono text-slate-500 flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-slate-400" />
            Target MCU: <span className="text-slate-300">{selectedBoard?.display_name || 'Hardware Not Connected'}</span>
          </div>
          <div className="flex-1" />
          {sourceCode ? (
            <button
              onClick={handleUpload}
              disabled={loading.firmware}
              className="flex items-center gap-2 px-3 py-1 text-xs font-mono bg-[#00878a]/10 border border-[#00878a]/30 text-[#00878a] rounded hover:bg-[#00878a]/20 transition-colors disabled:opacity-50"
              title="Register snapshot into ARIS Firmware Vault"
            >
              <Upload className="w-3.5 h-3.5" />
              {loading.firmware ? 'Saving…' : 'Snapshot to Library'}
            </button>
          ) : null}
          {uploadStatus === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {uploadStatus === 'error' && <XCircle className="w-4 h-4 text-red-400" />}
        </div>

        {/* Error */}
        {lastError && (
          <div className="px-4 py-2">
            <ErrorBanner error={lastError} onDismiss={onClearError} inline />
          </div>
        )}

        {/* Code Editor or Blank State */}
        {sourceCode ? (
          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            className="flex-1 bg-[#181b1f] text-slate-200 font-mono text-xs leading-relaxed p-4 resize-none outline-none border-none selection:bg-[#00878a]/30"
            spellCheck={false}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[#181b1f] select-none text-center">
            <div className="w-16 h-16 rounded-2xl bg-[#22272e] border border-white/[0.08] flex items-center justify-center mb-4 shadow-inner text-[#00878a]">
              <FileCode className="w-8 h-8 stroke-[1.5]" />
            </div>
            <h3 className="text-sm font-sans font-semibold text-slate-200 tracking-tight mb-1">
              Code not uploaded from Arduino IDE yet...
            </h3>
            <p className="text-xs font-sans text-slate-400 max-w-md leading-relaxed mb-6">
              When you upload or verify your sketch in the official Arduino IDE, the source code will automatically pop up here for runtime analysis and closed-loop optimization.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={handleManualRefresh}
                disabled={isSyncing}
                className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-mono bg-[#00878a]/10 hover:bg-[#00878a]/20 text-[#00878a] border border-[#00878a]/30 rounded-lg transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                {isSyncing ? 'Checking IDE...' : 'Scan Arduino IDE'}
              </button>
            </div>
          </div>
        )}

        {/* Footer stats */}
        <div className="flex items-center justify-between px-4 py-1.5 border-t border-white/[0.08] text-[10px] font-mono text-slate-500 shrink-0 bg-[#1e2229]">
          <div className="flex items-center gap-4">
            <span>{sourceCode ? sourceCode.split('\n').length : 0} lines</span>
            <span>{sourceCode ? new Blob([sourceCode]).size : 0} bytes</span>
            <span>Arduino C/C++ (.ino)</span>
          </div>
          <div className="text-slate-400">
            {sourceCode ? (activeIDESketch ? '⚡ Auto-synchronized with Arduino IDE' : 'Ready for runtime correlation') : 'Awaiting sketch upload from Arduino IDE'}
          </div>
        </div>
      </div>

      {/* Right: Arduino IDE Sketches & Firmware library */}
      <div className="w-72 flex flex-col border-l border-white/[0.08] shrink-0 bg-[#1e2229]">
        {/* Arduino IDE Recent Sketches Section */}
        <div className="p-3 border-b border-white/[0.08] bg-[#22272e]">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-mono text-[#00878a] uppercase tracking-widest font-semibold flex items-center gap-1.5">
              <FolderOpen className="w-3.5 h-3.5 text-[#00878a]" />
              Arduino IDE Sketches
            </p>
            <span className="text-[9px] font-mono text-slate-300 bg-white/[0.06] px-1.5 py-0.5 rounded">
              {ideSketches.length}
            </span>
          </div>
          <p className="text-[10px] font-sans text-slate-400 leading-tight">
            Detected automatically from your local Arduino IDE workspace:
          </p>
        </div>

        <div className="max-h-56 overflow-auto border-b border-white/[0.08]">
          {ideSketches.length === 0 ? (
            <p className="px-4 py-3 text-[10px] font-mono text-slate-500">
              No recent sketches found. Open a sketch in Arduino IDE.
            </p>
          ) : (
            ideSketches.map((sketch) => {
              const isSelected = activeIDESketch?.path === sketch.path || activeFirmware?.name === sketch.name;
              return (
                <button
                  key={sketch.path}
                  onClick={() => handleSwitchSketch(sketch)}
                  className={`w-full text-left px-3 py-2 border-b border-white/[0.05] hover:bg-white/[0.04] transition-colors flex items-center justify-between ${
                    isSelected ? 'bg-[#282e38] border-l-2 border-l-[#00878a]' : ''
                  }`}
                >
                  <div className="min-w-0 flex-1 pr-2">
                    <p className={`text-xs font-mono truncate ${isSelected ? 'text-slate-100 font-semibold' : 'text-slate-300'}`}>
                      {sketch.name}
                    </p>
                    <p className="text-[9px] font-mono text-slate-500 truncate" title={sketch.path}>
                      {sketch.path}
                    </p>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-[#00878a] shrink-0" />}
                </button>
              );
            })
          )}
        </div>

        {/* Active Firmware Detail */}
        {activeFirmware && (
          <div className="p-3 border-b border-white/[0.08] bg-[#22272e]">
            <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-1.5">Active In Telemetry Correlator</p>
            <p className="text-xs font-mono text-[#00878a] font-semibold truncate">{activeFirmware.name}</p>
            <p className="text-[9px] font-mono text-slate-500 mt-0.5">{activeFirmware.firmware_id}</p>
          </div>
        )}

        {/* Firmware library archive */}
        <div className="flex-1 overflow-auto">
          <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest px-3 py-2 border-b border-slate-800/50">
            Saved Snapshots ({firmwareList.length})
          </p>
          {firmwareList.length === 0 && (
            <p className="px-3 py-2 text-[10px] font-mono text-slate-600">No saved snapshots yet.</p>
          )}
          {firmwareList.map((fw) => (
            <button
              key={fw.firmware_id}
              onClick={() => {
                onSelectFirmware(fw);
                setSourceCode(fw.source_code || '');
                setFirmwareName(fw.name);
              }}
              className={`w-full text-left px-3 py-2 border-b border-slate-800/30 hover:bg-slate-800/30 transition-colors ${
                activeFirmware?.firmware_id === fw.firmware_id ? 'bg-slate-800/40' : ''
              }`}
            >
              <p className="text-xs font-mono text-slate-300">{fw.name}</p>
              <p className="text-[9px] font-mono text-slate-500">{fw.firmware_id}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

