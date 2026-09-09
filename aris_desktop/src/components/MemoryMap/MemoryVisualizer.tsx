import React from 'react';
import { Layers, HardDrive, Database, Cpu, Terminal, FileCode } from 'lucide-react';
import { FirmwareMemoryMap, HardwareProfile } from '../../types';

interface MemoryVisualizerProps {
  memoryMap: FirmwareMemoryMap | null;
  boardDetail: HardwareProfile | null;
}

export const MemoryVisualizer: React.FC<MemoryVisualizerProps> = ({
  memoryMap,
  boardDetail
}) => {
  if (!memoryMap || !boardDetail) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono text-xs">
        <Layers className="w-10 h-10 text-cyan-400 mx-auto mb-3" />
        <p>No compiled memory map loaded. Run code analysis in Code Studio first.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-h-[calc(100vh-65px)] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between bg-[#101522] border border-slate-800 p-4 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">
              Harvard Memory Layout & Disassembly Inspector ({boardDetail.name})
            </h2>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Flash ROM ({boardDetail.flash_bytes/1024}KB) vs Internal SRAM ({boardDetail.sram_bytes/1024}KB) Section Allocation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="px-3 py-1.5 rounded-lg bg-[#0a0d14] border border-slate-800">
            <span className="text-slate-400">Flash Used: </span>
            <span className="text-cyan-400 font-bold">{memoryMap.used_flash_bytes} B ({memoryMap.flash_pct}%)</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-[#0a0d14] border border-slate-800">
            <span className="text-slate-400">SRAM Used: </span>
            <span className="text-blue-400 font-bold">{memoryMap.static_sram_bytes + memoryMap.estimated_heap_stack_bytes} B ({memoryMap.sram_pct}%)</span>
          </div>
        </div>
      </div>

      {/* Memory Visual Section Bars */}
      <div className="grid grid-cols-2 gap-6">
        {/* Flash Memory Block */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase">Flash ROM Segments (32KB / 256KB)</h3>
            </div>
            <span className="text-xs font-mono text-cyan-400 font-bold">{memoryMap.free_flash_bytes} Bytes Free</span>
          </div>

          <div className="w-full bg-[#0a0d14] h-8 rounded-xl overflow-hidden flex border border-slate-800 p-1 gap-1">
            <div 
              className="bg-cyan-500 rounded h-full flex items-center justify-center text-[10px] font-mono font-bold text-black"
              style={{ width: `${Math.max(15, memoryMap.flash_pct * 0.8)}%` }}
              title=".text (Instructions)"
            >
              .text
            </div>
            <div 
              className="bg-purple-500 rounded h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
              style={{ width: '10%' }}
              title=".rodata / PROGMEM"
            >
              .rodata
            </div>
            <div 
              className="bg-slate-800 rounded h-full flex-1 flex items-center justify-center text-[10px] font-mono text-slate-500"
            >
              Free Flash
            </div>
          </div>

          <div className="space-y-2 pt-2">
            {memoryMap.sections.filter(s => s.target_memory.includes('Flash')).map((sec, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-[#0a0d14] border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="font-bold text-cyan-300">{sec.name}</span>
                  <span className="text-[10px] text-slate-500 ml-2">({sec.start_address_hex})</span>
                </div>
                <span className="text-slate-300">{sec.size_bytes} Bytes</span>
              </div>
            ))}
          </div>
        </div>

        {/* SRAM Memory Block */}
        <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              <h3 className="text-xs font-mono font-bold text-slate-200 uppercase">Internal SRAM Layout (2KB / 8KB)</h3>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">{memoryMap.free_sram_bytes} Bytes Free</span>
          </div>

          <div className="w-full bg-[#0a0d14] h-8 rounded-xl overflow-hidden flex border border-slate-800 p-1 gap-1">
            <div 
              className="bg-blue-500 rounded h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
              style={{ width: `${Math.max(12, (memoryMap.data_section_bytes / boardDetail.sram_bytes) * 100)}%` }}
              title=".data"
            >
              .data
            </div>
            <div 
              className="bg-teal-500 rounded h-full flex items-center justify-center text-[10px] font-mono font-bold text-black"
              style={{ width: `${Math.max(12, (memoryMap.bss_section_bytes / boardDetail.sram_bytes) * 100)}%` }}
              title=".bss"
            >
              .bss
            </div>
            <div 
              className="bg-slate-800 rounded h-full flex-1 flex items-center justify-center text-[10px] font-mono text-slate-500"
            >
              Free Headroom
            </div>
            <div 
              className="bg-purple-500 rounded h-full flex items-center justify-center text-[10px] font-mono font-bold text-white"
              style={{ width: `${Math.max(15, (memoryMap.estimated_heap_stack_bytes / boardDetail.sram_bytes) * 100)}%` }}
              title="Stack (SP)"
            >
              Stack
            </div>
          </div>

          <div className="space-y-2 pt-2">
            {memoryMap.sections.filter(s => s.target_memory.includes('SRAM')).map((sec, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-[#0a0d14] border border-slate-800 flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="font-bold text-blue-300">{sec.name}</span>
                  <span className="text-[10px] text-slate-500 ml-2">({sec.start_address_hex})</span>
                </div>
                <span className="text-slate-300">{sec.size_bytes} Bytes</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Disassembly Instruction Preview */}
      <div className="bg-[#101522] border border-slate-800 p-5 rounded-2xl shadow-xl space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold text-slate-200 uppercase">
            AVR Machine Code Disassembly (avr-objdump Instruction Cycle Counter)
          </h3>
        </div>

        <div className="space-y-1.5 font-mono text-xs max-h-48 overflow-y-auto">
          {memoryMap.disassembly_preview.map((d, i) => (
            <div key={i} className="p-2 rounded bg-[#0a0d14] border border-slate-800/80 flex items-center justify-between text-slate-300">
              <div className="flex items-center gap-4">
                <span className="text-cyan-400">{d.addr}</span>
                <span className="text-slate-500">{d.opcode}</span>
                <span className="font-bold text-white">{d.mnemonic}</span>
                <span className="text-slate-400">{d.operands}</span>
              </div>
              <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                {d.cycles} cycle{parseInt(d.cycles) > 1 ? 's' : ''}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
