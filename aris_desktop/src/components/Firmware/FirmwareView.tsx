// ============================================================
// ARIS — Firmware View
// Upload firmware, inspect source, view build/flash status.
// ============================================================

import React, { useState } from 'react';
import { Upload, FileCode, CheckCircle, XCircle } from 'lucide-react';
import { ErrorBanner } from '../common/ErrorBanner';
import type { FirmwareRecord, BoardProfile } from '../../types';
import { ARISApiError } from '../../services/api';

interface FirmwareViewProps {
  firmwareList: FirmwareRecord[];
  activeFirmware: FirmwareRecord | null;
  selectedBoard: BoardProfile | null;
  loading: Record<string, boolean>;
  lastError: ARISApiError | null;
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
  onUpload,
  onSelectFirmware,
  onClearError,
}) => {
  const [sourceCode, setSourceCode] = useState(EXAMPLE_SKETCH);
  const [firmwareName, setFirmwareName] = useState('MySketch');
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleUpload = async () => {
    setUploadStatus('idle');
    const result = await onUpload(firmwareName, sourceCode);
    setUploadStatus(result ? 'success' : 'error');
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left: Source editor */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-slate-800">
        {/* Toolbar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-800 bg-slate-900/40 shrink-0">
          <FileCode className="w-4 h-4 text-slate-400" />
          <input
            value={firmwareName}
            onChange={(e) => setFirmwareName(e.target.value)}
            className="bg-transparent text-sm font-mono text-slate-200 border-none outline-none w-40"
            placeholder="Firmware name"
          />
          <div className="text-[10px] font-mono text-slate-500">
            Target: {selectedBoard?.display_name || '—'} ({selectedBoard?.mcu?.toUpperCase() || '—'})
          </div>
          <div className="flex-1" />
          <button
            onClick={handleUpload}
            disabled={loading.firmware}
            className="flex items-center gap-2 px-3 py-1 text-xs font-mono bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded hover:bg-cyan-500/20 transition-colors disabled:opacity-50"
          >
            <Upload className="w-3.5 h-3.5" />
            {loading.firmware ? 'Uploading…' : 'Upload Firmware'}
          </button>
          {uploadStatus === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {uploadStatus === 'error' && <XCircle className="w-4 h-4 text-red-400" />}
        </div>

        {/* Error */}
        {lastError && (
          <div className="px-4 py-2">
            <ErrorBanner error={lastError} onDismiss={onClearError} inline />
          </div>
        )}

        {/* Code Editor (textarea) */}
        <textarea
          value={sourceCode}
          onChange={(e) => setSourceCode(e.target.value)}
          className="flex-1 bg-[#080c14] text-slate-300 font-mono text-xs leading-relaxed p-4 resize-none outline-none border-none"
          spellCheck={false}
        />

        {/* Footer stats */}
        <div className="flex items-center gap-4 px-4 py-1.5 border-t border-slate-800 text-[10px] font-mono text-slate-500 shrink-0">
          <span>{sourceCode.split('\n').length} lines</span>
          <span>{new Blob([sourceCode]).size} bytes</span>
          <span>Arduino C/C++</span>
        </div>
      </div>

      {/* Right: Firmware list + active info */}
      <div className="w-72 flex flex-col border-l border-slate-800 shrink-0">
        {/* Active firmware */}
        {activeFirmware && (
          <div className="p-4 border-b border-slate-800">
            <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-2">Active Firmware</p>
            <p className="text-xs font-mono text-cyan-400 font-semibold">{activeFirmware.name}</p>
            <p className="text-[10px] font-mono text-slate-500 mt-1">{activeFirmware.firmware_id}</p>
            <p className="text-[10px] font-mono text-slate-500">{new Date(activeFirmware.created_at).toLocaleString()}</p>
          </div>
        )}

        {/* Firmware list */}
        <div className="flex-1 overflow-auto">
          <p className="text-[9px] font-mono text-slate-500 uppercase tracking-widest px-4 py-3">
            Firmware Library ({firmwareList.length})
          </p>
          {firmwareList.length === 0 && (
            <p className="px-4 text-[10px] font-mono text-slate-600">No firmware uploaded yet.</p>
          )}
          {firmwareList.map((fw) => (
            <button
              key={fw.firmware_id}
              onClick={() => { onSelectFirmware(fw); setSourceCode(fw.source_code || ''); setFirmwareName(fw.name); }}
              className={`w-full text-left px-4 py-3 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${
                activeFirmware?.firmware_id === fw.firmware_id ? 'bg-slate-800/40' : ''
              }`}
            >
              <p className="text-xs font-mono text-slate-300">{fw.name}</p>
              <p className="text-[10px] font-mono text-slate-500">{fw.firmware_id}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
