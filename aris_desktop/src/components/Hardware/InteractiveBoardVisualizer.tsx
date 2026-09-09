import React, { useState } from 'react';
import { Cpu, Zap, Activity, Info, Sliders, ToggleLeft, ToggleRight } from 'lucide-react';
import { HardwareProfile, VirtualPinState } from '../../types';

interface BoardVisualizerProps {
  boardDetail: HardwareProfile | null;
  pinStates: Record<string, VirtualPinState>;
  onSetVirtualInput: (pinName: string, isAnalog: boolean, value: number) => void;
}

export const InteractiveBoardVisualizer: React.FC<BoardVisualizerProps> = ({
  boardDetail,
  pinStates,
  onSetVirtualInput
}) => {
  const [selectedPin, setSelectedPin] = useState<string>('D13');
  const [analogVal, setAnalogVal] = useState<number>(512);

  if (!boardDetail) return null;

  const isUno = boardDetail.id === 'arduino_uno';
  const isMega = boardDetail.id === 'arduino_mega';
  const isNano = boardDetail.id === 'arduino_nano';

  const currentPinState = pinStates[selectedPin];
  const currentPinMapping = boardDetail.pins[selectedPin];

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Top Header */}
      <div className="flex items-center justify-between bg-[#101522] border border-slate-800 p-4 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-100">{boardDetail.name} — Interactive Virtual Pinout Testbed</h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {boardDetail.mcu_model}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Click any pin to inspect registers or inject virtual analog voltages & digital signals.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Interactive Visual Board Representation (2 cols) */}
        <div className="col-span-2 bg-[#101522] border border-slate-800 p-6 rounded-2xl shadow-xl flex flex-col items-center justify-center relative min-h-[460px] overflow-hidden">
          {/* Board PCB Canvas */}
          <div className={`relative rounded-3xl p-6 shadow-2xl border-2 transition-all duration-300 ${
            isMega 
              ? 'w-[580px] h-[360px] bg-gradient-to-r from-teal-950/80 via-[#0d2830] to-teal-950/80 border-cyan-500/40' 
              : isNano 
              ? 'w-[320px] h-[380px] bg-gradient-to-b from-[#0b242e] to-teal-950 border-cyan-400/40'
              : 'w-[480px] h-[360px] bg-gradient-to-br from-[#0c2b36] via-[#091f28] to-[#0c2b36] border-cyan-400/40'
          }`}>
            {/* Silk Screen Labels */}
            <div className="absolute top-4 left-6 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-400 ring-2 ring-amber-400/30 animate-pulse" />
              <span className="font-extrabold text-sm font-mono tracking-widest text-cyan-200">
                {boardDetail.name.toUpperCase()}
              </span>
            </div>

            {/* MCU Chip Centerpiece */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#05080f] border border-slate-700 rounded-lg p-5 shadow-2xl flex flex-col items-center justify-center w-36 h-36">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-800 absolute top-2 left-2" />
              <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-wider">ATMEL / MICROCHIP</span>
              <span className="text-xs font-mono font-extrabold text-white mt-1">{boardDetail.mcu_model}</span>
              <span className="text-[9px] font-mono text-slate-500 mt-0.5">16.000 MHz</span>
              <span className="text-[8px] font-mono text-emerald-400/80 mt-2 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
                {boardDetail.sram_bytes}B SRAM
              </span>
            </div>

            {/* Built-in LED (Pin 13) */}
            <div className="absolute top-16 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-[#05080f] px-3 py-1.5 rounded-full border border-slate-800">
              <span className="text-[10px] font-mono text-slate-400">LED (L):</span>
              <div className={`w-3.5 h-3.5 rounded-full border transition-all ${
                pinStates['D13']?.digital_value === 1
                  ? 'bg-amber-400 border-amber-300 shadow-lg shadow-amber-400/80 ring-2 ring-amber-400/40'
                  : 'bg-slate-800 border-slate-700'
              }`} />
            </div>

            {/* Top Digital Header Pins */}
            <div className="absolute top-2 right-6 left-28 flex justify-between bg-[#05080f]/80 p-1.5 rounded-lg border border-slate-800">
              {['D13', 'D12', 'D11', 'D10', 'D9', 'D8', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'D0'].map((p) => {
                const state = pinStates[p];
                const isSelected = selectedPin === p;
                return (
                  <button
                    key={p}
                    onClick={() => setSelectedPin(p)}
                    className={`flex flex-col items-center p-1 rounded transition ${
                      isSelected ? 'bg-cyan-500/30 border border-cyan-400 text-cyan-200' : 'hover:bg-slate-800/60 text-slate-400'
                    }`}
                  >
                    <span className="text-[8px] font-mono">{p}</span>
                    <div className={`w-2 h-2 rounded-full mt-1 ${state?.digital_value ? 'bg-cyan-400 shadow-sm' : 'bg-slate-700'}`} />
                  </button>
                );
              })}
            </div>

            {/* Bottom Analog & Power Header Pins */}
            <div className="absolute bottom-2 right-6 left-28 flex justify-between bg-[#05080f]/80 p-1.5 rounded-lg border border-slate-800">
              {['A0', 'A1', 'A2', 'A3', 'A4', 'A5'].map((p) => {
                const state = pinStates[p];
                const isSelected = selectedPin === p;
                return (
                  <button
                    key={p}
                    onClick={() => {
                      setSelectedPin(p);
                      if (state) setAnalogVal(state.analog_value);
                    }}
                    className={`flex flex-col items-center p-1 px-2 rounded transition ${
                      isSelected ? 'bg-blue-500/30 border border-blue-400 text-blue-200' : 'hover:bg-slate-800/60 text-slate-400'
                    }`}
                  >
                    <span className="text-[8px] font-mono">{p}</span>
                    <div className="w-2 h-2 rounded-full mt-1 bg-blue-400/80" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Pin Inspection & Control Panel (1 col) */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold font-mono text-slate-200 uppercase tracking-wider">
                  Pin Control: {selectedPin}
                </h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                {currentPinMapping?.pin_type.toUpperCase() || 'DIGITAL'}
              </span>
            </div>

            {currentPinMapping && (
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0d14] border border-slate-800">
                  <span className="text-slate-400">Direct Register:</span>
                  <span className="text-cyan-300 font-bold">{currentPinMapping.port_register} (Bit {currentPinMapping.pin_bit})</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0d14] border border-slate-800">
                  <span className="text-slate-400">Timer Channel:</span>
                  <span className="text-slate-200">{currentPinMapping.timer_channel || 'None (GPIO only)'}</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded-lg bg-[#0a0d14] border border-slate-800">
                  <span className="text-slate-400">Measured Voltage:</span>
                  <span className="text-emerald-400 font-bold">{currentPinState?.voltage.toFixed(2) || '0.00'} V</span>
                </div>
              </div>
            )}

            {/* Virtual Signal Injection */}
            <div className="mt-6 pt-4 border-t border-slate-800 space-y-4">
              <h4 className="text-xs font-mono font-bold text-slate-300 uppercase">Inject Virtual Signal:</h4>

              {selectedPin.startsWith('A') ? (
                /* Analog Potentiometer Slider */
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Analog Voltage (0-5V):</span>
                    <span className="text-blue-400 font-bold">{((analogVal / 1023) * boardDetail.operating_voltage).toFixed(2)}V (ADC: {analogVal})</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="1023"
                    value={analogVal}
                    onChange={(e) => {
                      const v = parseInt(e.target.value);
                      setAnalogVal(v);
                      onSetVirtualInput(selectedPin, true, v);
                    }}
                    className="w-full accent-cyan-400 cursor-pointer"
                  />
                </div>
              ) : (
                /* Digital High/Low Toggle */
                <div className="flex gap-2">
                  <button
                    onClick={() => onSetVirtualInput(selectedPin, false, 1)}
                    className="flex-1 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition shadow-lg shadow-cyan-600/20"
                  >
                    Set HIGH (5V)
                  </button>
                  <button
                    onClick={() => onSetVirtualInput(selectedPin, false, 0)}
                    className="flex-1 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs font-bold transition border border-slate-700"
                  >
                    Set LOW (0V)
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/40 text-[11px] font-mono text-cyan-300/80">
            <p>Direct Port SBI/CBI instructions toggle {currentPinMapping?.port_register} in 1 clock cycle (62.5ns @ 16MHz).</p>
          </div>
        </div>
      </div>
    </div>
  );
};
