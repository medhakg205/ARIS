import React, { useState } from 'react';
import { 
  Code2, 
  Play, 
  Sparkles, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  FileCode, 
  Layers, 
  Cpu, 
  ChevronRight,
  Flame
} from 'lucide-react';
import { StaticAnalysisReport, HardwareProfile } from '../../types';

interface CodeStudioProps {
  sourceCode: string;
  setSourceCode: (code: string) => void;
  onAnalyze: (code: string) => void;
  onOptimize: (code: string) => void;
  staticReport: StaticAnalysisReport | null;
  boardDetail: HardwareProfile | null;
  loading: boolean;
  onSwitchToOptimizer: () => void;
}

const SAMPLE_SKETCHES = [
  {
    name: '01. Blocking Delay & ADC Antipattern',
    code: `// ARIS Benchmark Example 01: Blocking Delay & Sensor Polling Antipattern
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
  
  // Toggle LED using slow HAL function (56 cycles)
  digitalWrite(13, HIGH);
  
  // Severe blocking busy-wait stalls MCU execution for 20ms (320,000 clock cycles)
  delay(20);
  
  digitalWrite(13, LOW);
  delay(20);
}`
  },
  {
    name: '02. GPIO Bit-Banging Inefficiency',
    code: `// ARIS Benchmark Example 02: High-Frequency GPIO Bit-Banging Inefficiency
// Target: Arduino Uno / Mega / Nano

void setup() {
  pinMode(13, OUTPUT);
}

void loop() {
  // Slow HAL digitalWrite takes 56 clock cycles (3.5 µs) per call
  // Bit-banging a clock signal this way yields max ~140 kHz instead of 8 MHz
  digitalWrite(13, HIGH);
  digitalWrite(13, LOW);
  digitalWrite(13, HIGH);
  digitalWrite(13, LOW);
}`
  },
  {
    name: '03. SRAM String Exhaustion',
    code: `// ARIS Benchmark Example 03: RAM String Literal Exhaustion (Memory Starvation)
// Target: Arduino Uno / Nano (2KB SRAM limit)

void setup() {
  Serial.begin(115200);
}

void loop() {
  // All these raw string literals are duplicated in 2KB SRAM at startup
  Serial.println("=================================================");
  Serial.println("SYSTEM STATUS: RUNNING ATMEGA328P TELEMETRY");
  Serial.println("INITIALIZING ADC CHANNELS AND ANALOG SENSORS");
  Serial.println("WARNING: HIGH SRAM MEMORY ALLOCATION DETECTED");
  Serial.println("DATA FRAME PACKET DISPATCHED OVER SERIAL UART");
  Serial.println("=================================================");
  delay(100);
}`
  },
  {
    name: '04. Mega Multi-ADC Round-Robin',
    code: `// ARIS Benchmark Example 04: Mega 2560 Multi-ADC & Multi-UART Round-Robin
// Target: Arduino Mega 2560 (ATmega2560 - 16 ADC channels, 4 UARTs)

void setup() {
  Serial.begin(115200);
  Serial1.begin(9600);
  pinMode(13, OUTPUT);
}

void loop() {
  int a0 = analogRead(A0);
  int a1 = analogRead(A1);
  int a2 = analogRead(A2);
  int a3 = analogRead(A3);

  Serial.print("A0="); Serial.print(a0);
  Serial.print(" A1="); Serial.print(a1);
  Serial.print(" A2="); Serial.print(a2);
  Serial.print(" A3="); Serial.println(a3);

  digitalWrite(13, HIGH);
  delay(15);
  digitalWrite(13, LOW);
  delay(15);
}`
  },
  {
    name: '05. Software Float Filter',
    code: `// ARIS Benchmark Example 05: Nano Software Float Math Filter
// Target: Arduino Nano / Uno (8-bit ALU without FPU)

float raw_sensor = 0.0;
float filtered_voltage = 0.0;
float alpha = 0.15;

void setup() {
  Serial.begin(115200);
}

void loop() {
  raw_sensor = analogRead(A0);
  // Software float emulation costs 200+ cycles per operation
  float voltage = raw_sensor * (5.0 / 1023.0);
  filtered_voltage = (alpha * voltage) + ((1.0 - alpha) * filtered_voltage);
  
  Serial.print("Filtered Voltage: ");
  Serial.println(filtered_voltage);
  delay(10);
}`
  }
];

export const CodeStudio: React.FC<CodeStudioProps> = ({
  sourceCode,
  setSourceCode,
  onAnalyze,
  onOptimize,
  staticReport,
  boardDetail,
  loading,
  onSwitchToOptimizer
}) => {
  const [selectedSample, setSelectedSample] = useState<number>(0);

  const handleLoadSample = (idx: number) => {
    setSelectedSample(idx);
    const code = SAMPLE_SKETCHES[idx].code;
    setSourceCode(code);
    onAnalyze(code);
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'MEDIUM': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-slate-700/40 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Top Header & Actions */}
      <div className="flex items-center justify-between bg-[#101522] border border-slate-800 p-4 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Firmware Code Studio & Static AST Inspector</h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Inspect and profile code structure against {boardDetail?.name} hardware registers.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <select
            value={selectedSample}
            onChange={(e) => handleLoadSample(parseInt(e.target.value))}
            className="bg-[#0a0d14] text-xs font-mono text-cyan-300 border border-slate-800 px-3 py-2 rounded-xl focus:outline-none cursor-pointer"
          >
            {SAMPLE_SKETCHES.map((s, i) => (
              <option key={i} value={i} className="bg-[#101522] text-slate-200">
                Load: {s.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => onAnalyze(sourceCode)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono font-bold transition shadow-lg shadow-cyan-600/20 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Analyze AST</span>
          </button>

          <button
            onClick={() => {
              onOptimize(sourceCode);
              onSwitchToOptimizer();
            }}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white text-xs font-mono font-bold transition shadow-lg shadow-purple-600/20"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Optimize with AI</span>
          </button>
        </div>
      </div>

      {/* Editor & Antipatterns Inspector Split */}
      <div className="grid grid-cols-5 gap-6">
        {/* Code Editor (3 cols) */}
        <div className="col-span-3 bg-[#101522] border border-slate-800 rounded-2xl shadow-xl overflow-hidden flex flex-col">
          <div className="bg-[#0d121f] px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-bold text-slate-300">sketch.ino</span>
            </div>
            {staticReport && (
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono text-slate-400">Health Score:</span>
                <span className={`text-xs font-mono font-extrabold px-2 py-0.5 rounded ${
                  staticReport.architectural_health_score > 75 
                    ? 'bg-emerald-500/20 text-emerald-400' 
                    : staticReport.architectural_health_score > 40
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {staticReport.architectural_health_score}/100
                </span>
              </div>
            )}
          </div>

          <textarea
            value={sourceCode}
            onChange={(e) => setSourceCode(e.target.value)}
            spellCheck={false}
            className="flex-1 p-4 bg-[#0a0d14] text-slate-200 font-mono text-xs leading-relaxed resize-none focus:outline-none selection:bg-cyan-500 selection:text-black min-h-[440px]"
          />
        </div>

        {/* Antipatterns & Architectural Findings (2 cols) */}
        <div className="col-span-2 bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col justify-between overflow-hidden">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
                  Detected Architectural Antipatterns
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {staticReport?.antipatterns.length || 0} issues
              </span>
            </div>

            {/* List of issues */}
            <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
              {staticReport?.antipatterns.map((ap) => (
                <div 
                  key={ap.id} 
                  className="p-3.5 rounded-xl bg-[#0a0d14] border border-slate-800 hover:border-cyan-500/40 transition group"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${getSeverityBadge(ap.severity)}`}>
                        {ap.severity}
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-200">{ap.name}</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500">Line {ap.line_number}</span>
                  </div>

                  <p className="text-[11px] text-slate-400 font-mono">{ap.description}</p>
                  
                  <div className="mt-2 text-[10px] font-mono text-cyan-400/90 bg-cyan-950/30 p-2 rounded border border-cyan-900/40">
                    <p className="text-slate-300"><span className="text-cyan-400 font-bold">Impact:</span> {ap.architectural_impact}</p>
                    <p className="text-emerald-300 mt-1"><span className="text-emerald-400 font-bold">Fix:</span> {ap.remediation_suggestion}</p>
                  </div>
                </div>
              ))}

              {(!staticReport || staticReport.antipatterns.length === 0) && (
                <div className="text-center py-12 text-slate-500 font-mono text-xs">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p>No architectural antipatterns detected.</p>
                  <p className="text-[10px] text-slate-600 mt-1">Code conforms to {boardDetail?.name} hardware limits.</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Metrics Footer */}
          {staticReport && (
            <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="p-2 rounded bg-[#0a0d14] border border-slate-800 text-slate-400">
                <span>Flash Est: </span>
                <span className="text-cyan-300 font-bold">{staticReport.estimated_flash_bytes} B ({staticReport.flash_utilization_pct}%)</span>
              </div>
              <div className="p-2 rounded bg-[#0a0d14] border border-slate-800 text-slate-400">
                <span>SRAM Est: </span>
                <span className="text-blue-300 font-bold">{staticReport.estimated_sram_static_bytes} B ({staticReport.sram_utilization_pct}%)</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
