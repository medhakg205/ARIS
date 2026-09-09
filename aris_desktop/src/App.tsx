import React, { useState, useEffect } from 'react';
import { useAris } from './hooks/useAris';
import { Navbar } from './components/Navbar';
import { TelemetryDashboard } from './components/Dashboard/TelemetryDashboard';
import { InteractiveBoardVisualizer } from './components/Hardware/InteractiveBoardVisualizer';
import { CodeStudio } from './components/CodeStudio/CodeStudio';
import { OptimizationStudio } from './components/Optimizer/OptimizationStudio';
import { MemoryVisualizer } from './components/MemoryMap/MemoryVisualizer';
import { PatentStudio } from './components/PatentReport/PatentStudio';

const INITIAL_SKETCH = `// ARIS Benchmark Example 01: Blocking Delay & Sensor Polling Antipattern
// Target: Arduino Uno / Nano (ATmega328P)

void setup() {
  Serial.begin(115200);
  pinMode(13, OUTPUT);
}

void loop() {
  // Synchronous ADC reading
  int sensorValue = analogRead(A0);
  
  // High-overhead RAM string literals (consumes SRAM)
  Serial.print("Sensor Raw ADC Reading: ");
  Serial.println(sensorValue);
  
  // Toggle LED using slow HAL function
  digitalWrite(13, HIGH);
  
  // Severe blocking busy-wait stalls MCU execution for 20ms (320,000 clock cycles)
  delay(20);
  
  digitalWrite(13, LOW);
  delay(20);
}`;

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [sourceCode, setSourceCode] = useState<string>(INITIAL_SKETCH);

  const {
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
  } = useAris();

  // Run initial analysis on boot
  useEffect(() => {
    analyzeCode(sourceCode);
  }, [selectedBoardId]);

  const handleApplyOptimization = (optimizedCode: string) => {
    setSourceCode(optimizedCode);
    analyzeCode(optimizedCode);
    setSimulationMode('optimized', 0);
    setActiveTab('code');
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0a0d14] text-slate-100 overflow-hidden select-none">
      {/* Top Main Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        boards={boards}
        selectedBoardId={selectedBoardId}
        onSelectBoard={setSelectedBoardId}
        boardDetail={boardDetail}
        connected={connected}
        serialPorts={serialPorts}
        connectedPort={connectedPort}
        onRefreshPorts={refreshSerialPorts}
        onConnectPort={connectSerial}
        onDisconnectPort={disconnectSerial}
        isSimulating={isSimulating}
        onToggleSim={() => setIsSimulating(!isSimulating)}
      />

      {/* Main Screen Content View */}
      <main className="flex-1 overflow-hidden bg-[#0a0d14]">
        {activeTab === 'dashboard' && (
          <TelemetryDashboard
            telemetry={telemetry}
            telemetryHistory={telemetryHistory}
            boardDetail={boardDetail}
            simMode={simMode}
            onSetSimMode={setSimulationMode}
          />
        )}

        {activeTab === 'code' && (
          <CodeStudio
            sourceCode={sourceCode}
            setSourceCode={setSourceCode}
            onAnalyze={analyzeCode}
            onOptimize={optimizeCode}
            staticReport={staticReport}
            boardDetail={boardDetail}
            loading={loading}
            onSwitchToOptimizer={() => setActiveTab('optimizer')}
          />
        )}

        {activeTab === 'optimizer' && (
          <OptimizationStudio
            optimizationResult={optimizationResult}
            verificationReport={verificationReport}
            boardDetail={boardDetail}
            onApplyOptimization={handleApplyOptimization}
            onRunVerification={() => optimizeCode(sourceCode)}
          />
        )}

        {activeTab === 'hardware' && (
          <InteractiveBoardVisualizer
            boardDetail={boardDetail}
            pinStates={telemetry?.pin_states || {}}
            onSetVirtualInput={setVirtualInput}
          />
        )}

        {activeTab === 'memory' && (
          <MemoryVisualizer
            memoryMap={memoryMap}
            boardDetail={boardDetail}
          />
        )}

        {activeTab === 'patent' && (
          <PatentStudio
            patentMarkdown={patentMarkdown}
            boardDetail={boardDetail}
          />
        )}
      </main>

      {/* Bottom Status Bar */}
      <footer className="h-6 bg-[#0d121f] border-t border-slate-800/80 px-4 flex items-center justify-between text-[10px] font-mono text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            Core: {boardDetail?.architecture || 'AVR 8-bit'}
          </span>
          <span>Clock: {boardDetail ? boardDetail.core_frequency_hz / 1e6 : 16} MHz</span>
          <span>Flash: {boardDetail ? boardDetail.flash_bytes / 1024 : 32} KB</span>
          <span>SRAM: {boardDetail ? boardDetail.sram_bytes / 1024 : 2} KB</span>
        </div>

        <div className="flex items-center gap-4">
          <span>Latency Jitter: ±{telemetry?.jitter_us || 0} µs</span>
          <span>Observer Bias: -{telemetry?.observer_overhead_pct.toFixed(2) || '0.00'}%</span>
          <span className="text-cyan-400">ARIS v2.0 Desktop Active</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
