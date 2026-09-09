"""
Static AST & Antipattern Analyzer for ARIS.
Performs deep structural code analysis against target microcontroller hardware specifications.
"""

import re
from typing import List, Dict, Any
from pydantic import BaseModel
from aris_core.hardware_profiles import HardwareProfile, get_hardware_profile

class CodeAntipattern(BaseModel):
    id: str
    name: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    line_number: int
    line_snippet: str
    description: str
    architectural_impact: str
    estimated_overhead_cycles: int
    estimated_sram_loss_bytes: int
    remediation_suggestion: str
    auto_fixable: bool

class FunctionProfile(BaseModel):
    name: str
    return_type: str
    parameters: List[str]
    start_line: int
    end_line: int
    line_count: int
    calls_blocking_delay: bool
    calls_slow_gpio: bool
    calls_float_math: bool
    is_isr: bool

class StaticAnalysisReport(BaseModel):
    board_id: str
    board_name: str
    total_lines: int
    function_count: int
    functions: List[FunctionProfile]
    antipatterns: List[CodeAntipattern]
    estimated_flash_bytes: int
    estimated_sram_static_bytes: int
    estimated_sram_stack_bytes: int
    flash_utilization_pct: float
    sram_utilization_pct: float
    blocking_delay_count: int
    gpio_call_count: int
    float_op_count: int
    ram_string_count: int
    architectural_health_score: int  # 0 to 100

class StaticAnalyzer:
    def __init__(self, hardware_profile: HardwareProfile = None):
        self.hw = hardware_profile or get_hardware_profile("arduino_uno")

    def analyze(self, source_code: str, board_id: str = None) -> StaticAnalysisReport:
        if board_id:
            self.hw = get_hardware_profile(board_id)

        lines = source_code.splitlines()
        total_lines = len(lines)
        antipatterns: List[CodeAntipattern] = []
        functions: List[FunctionProfile] = []

        # 1. Parse functions and structure
        func_pattern = re.compile(r'^\s*(void|int|long|unsigned\s+int|unsigned\s+long|float|double|bool|byte|char|uint8_t|uint16_t|uint32_t|ISR)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{?')
        
        current_func = None
        func_start_line = 0
        brace_depth = 0

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Simple brace depth tracker
            brace_depth += line.count('{') - line.count('}')

            m = func_pattern.search(line)
            if m and (brace_depth <= 1 or current_func is None):
                ret_type = m.group(1)
                func_name = m.group(2)
                params = [p.strip() for p in m.group(3).split(',') if p.strip()]
                is_isr = "ISR" in ret_type or "ISR" in func_name or "interrupt" in func_name.lower()
                
                if current_func:
                    current_func.end_line = i - 1
                    current_func.line_count = max(1, current_func.end_line - current_func.start_line + 1)
                    functions.append(current_func)

                current_func = FunctionProfile(
                    name=func_name,
                    return_type=ret_type,
                    parameters=params,
                    start_line=i,
                    end_line=i,
                    line_count=1,
                    calls_blocking_delay=False,
                    calls_slow_gpio=False,
                    calls_float_math=False,
                    is_isr=is_isr
                )

        if current_func:
            current_func.end_line = total_lines
            current_func.line_count = max(1, current_func.end_line - current_func.start_line + 1)
            functions.append(current_func)

        # 2. Antipattern detection pass
        delay_count = 0
        gpio_count = 0
        float_count = 0
        ram_string_count = 0
        total_ram_leak = 0

        for i, line in enumerate(lines, 1):
            raw_line = line
            # strip comments
            clean_line = re.sub(r'//.*', '', raw_line)
            clean_line = re.sub(r'/\*.*?\*/', '', clean_line).strip()

            if not clean_line:
                continue

            # (A) Blocking Delays: delay(...)
            delay_matches = re.finditer(r'\bdelay\s*\(\s*([0-9]+|[a-zA-Z0-9_]+)\s*\)', clean_line)
            for dm in delay_matches:
                delay_val = dm.group(1)
                delay_count += 1
                try:
                    ms_val = int(delay_val)
                    cycles = int(ms_val * (self.hw.core_frequency_hz / 1000))
                except ValueError:
                    ms_val = 10
                    cycles = 160000

                antipatterns.append(CodeAntipattern(
                    id=f"AP_DELAY_{i}",
                    name="Synchronous Blocking Delay",
                    severity="CRITICAL" if ms_val >= 20 else "HIGH",
                    line_number=i,
                    line_snippet=raw_line.strip(),
                    description=f"Invocation of blocking delay({delay_val}ms) stalls MCU instruction pipeline.",
                    architectural_impact=f"Wastes ~{cycles:,} clock cycles in an idle busy-wait loop, blocking sensor interrupts, serial buffers, and real-time scheduling.",
                    estimated_overhead_cycles=cycles,
                    estimated_sram_loss_bytes=0,
                    remediation_suggestion="Refactor into a non-blocking millis() delta timer state machine.",
                    auto_fixable=True
                ))

            # (B) Slow GPIO Bit-banging: digitalWrite / digitalRead
            dw_matches = re.finditer(r'\b(digitalWrite|digitalRead)\s*\(\s*([^,)]+)(?:,\s*([^)]+))?\s*\)', clean_line)
            for gm in dw_matches:
                gpio_type = gm.group(1)
                pin_arg = gm.group(2).strip()
                gpio_count += 1
                
                # Check direct port mapping on this hardware
                reg_hint = "PORTB / PINB" if "328" in self.hw.mcu_model else "PORTA-PORTL"
                if pin_arg == "13" or pin_arg == "LED_BUILTIN":
                    reg_hint = "PORTB |= (1 << PB5)" if "328" in self.hw.mcu_model else "PORTB |= (1 << PB7)"

                antipatterns.append(CodeAntipattern(
                    id=f"AP_GPIO_{i}",
                    name=f"Suboptimal HAL GPIO Function ({gpio_type})",
                    severity="MEDIUM",
                    line_number=i,
                    line_snippet=raw_line.strip(),
                    description=f"{gpio_type}() performs pin-to-timer lookup and bit shifting (~56 clock cycles on 8-bit AVR).",
                    architectural_impact=f"Consumes 56 cycles (3.5 µs @ 16MHz) per toggle instead of 1 cycle (62.5 ns) using Direct Port Manipulation ({reg_hint}).",
                    estimated_overhead_cycles=55,
                    estimated_sram_loss_bytes=0,
                    remediation_suggestion=f"Use Direct Port Register manipulation ({reg_hint}) for high-frequency or deterministic I/O.",
                    auto_fixable=True
                ))

            # (C) RAM String Literal Starvation: Serial.print("...") without F()
            str_matches = re.finditer(r'\bSerial\d*\.print(?:ln)?\s*\(\s*"([^"]{3,})"\s*\)', clean_line)
            for sm in str_matches:
                str_content = sm.group(1)
                str_len = len(str_content) + 1  # include null terminator
                ram_string_count += 1
                total_ram_leak += str_len

                antipatterns.append(CodeAntipattern(
                    id=f"AP_RAM_STR_{i}",
                    name="SRAM String Literal Exhaustion",
                    severity="HIGH" if self.hw.sram_bytes <= 2048 else "MEDIUM",
                    line_number=i,
                    line_snippet=raw_line.strip(),
                    description=f'String literal "{str_content[:20]}..." is copied from Flash into scarce {self.hw.sram_bytes}B SRAM at boot.',
                    architectural_impact=f"Consumes {str_len} bytes of valuable dynamic SRAM. On {self.hw.name} (only {self.hw.sram_bytes} bytes SRAM total), this rapidly causes stack-heap collision.",
                    estimated_overhead_cycles=10,
                    estimated_sram_loss_bytes=str_len,
                    remediation_suggestion=f'Wrap literal with the flash helper macro: Serial.print(F("{str_content}")) to keep string strictly in Flash.',
                    auto_fixable=True
                ))

            # (D) Software Floating-Point Emulation on 8-bit MCU without FPU
            if "8-bit" in self.hw.architecture:
                float_matches = re.finditer(r'\b(float|double)\s+([a-zA-Z0-9_]+)\s*(=|;)', clean_line)
                for fm in float_matches:
                    var_name = fm.group(2)
                    float_count += 1
                    antipatterns.append(CodeAntipattern(
                        id=f"AP_FLOAT_{i}",
                        name="Software Float Emulation Overhead",
                        severity="MEDIUM",
                        line_number=i,
                        line_snippet=raw_line.strip(),
                        description=f"Variable '{var_name}' uses 32-bit IEEE 754 float on an 8-bit ALU without hardware FPU.",
                        architectural_impact="Every float multiplication/division requires 120-300 clock cycles of software emulation via libgcc, inflating binary size by ~1.5KB Flash.",
                        estimated_overhead_cycles=180,
                        estimated_sram_loss_bytes=4,
                        remediation_suggestion="Replace float with fixed-point Q15 arithmetic (scaled integer math) for 15x faster calculation.",
                        auto_fixable=True
                    ))

            # (E) Rapid Synchronous ADC Polling in loop
            if "analogRead" in clean_line and "delay" not in clean_line:
                antipatterns.append(CodeAntipattern(
                    id=f"AP_ADC_{i}",
                    name="High-Frequency Synchronous ADC Polling",
                    severity="LOW",
                    line_number=i,
                    line_snippet=raw_line.strip(),
                    description="analogRead() triggers a synchronous SAR ADC conversion taking 104 µs (1664 clock cycles).",
                    architectural_impact="Polling without prescaler tuning or timer trigger wastes ADC converter bandwidth.",
                    estimated_overhead_cycles=1664,
                    estimated_sram_loss_bytes=0,
                    remediation_suggestion="Increase ADC prescaler or read ADC in round-robin state machine slots.",
                    auto_fixable=False
                ))

        # 3. Compute memory and health metrics
        base_flash = 2400 + total_lines * 14 + float_count * 1200
        estimated_flash = min(self.hw.flash_bytes, max(1200, base_flash))
        
        base_sram_static = 180 + ram_string_count * 24 + float_count * 4 + total_ram_leak
        estimated_sram_static = min(self.hw.sram_bytes - 100, max(120, base_sram_static))
        estimated_sram_stack = min(self.hw.sram_bytes - estimated_sram_static, 240 + len(functions) * 32)

        flash_pct = round((estimated_flash / self.hw.flash_bytes) * 100, 1)
        sram_pct = round(((estimated_sram_static + estimated_sram_stack) / self.hw.sram_bytes) * 100, 1)

        # Health score calculation (100 is pristine)
        penalty = (delay_count * 20) + (ram_string_count * 12) + (float_count * 8) + (gpio_count * 3)
        health_score = max(10, min(100, 100 - penalty))

        return StaticAnalysisReport(
            board_id=self.hw.id,
            board_name=self.hw.name,
            total_lines=total_lines,
            function_count=len(functions),
            functions=functions,
            antipatterns=antipatterns,
            estimated_flash_bytes=estimated_flash,
            estimated_sram_static_bytes=estimated_sram_static,
            estimated_sram_stack_bytes=estimated_sram_stack,
            flash_utilization_pct=flash_pct,
            sram_utilization_pct=sram_pct,
            blocking_delay_count=delay_count,
            gpio_call_count=gpio_count,
            float_op_count=float_count,
            ram_string_count=ram_string_count,
            architectural_health_score=health_score
        )
