"""
ARIS Firmware Analyzer.
Static structural inspector tailored to AVR Arduino C/C++ firmware sketches.
Extracts architectural characteristics, hardware interactions, and antipatterns.
"""

import re
from typing import Dict, Any, List


class FirmwareAnalyzer:
    """Specialized AVR firmware static structural analyzer."""

    @staticmethod
    def analyze_sketch(source_code: str) -> Dict[str, Any]:
        """Performs structural and architectural analysis of the Arduino sketch."""
        lines = source_code.splitlines()

        has_delay = bool(re.search(r"\bdelay\s*\(\s*(\d+)\s*\)", source_code))
        delay_matches = re.findall(r"\bdelay\s*\(\s*(\d+)\s*\)", source_code)
        total_delay_ms = sum(int(d) for d in delay_matches)

        has_serial_in_loop = False
        loop_body = FirmwareAnalyzer._extract_loop_body(source_code)
        if loop_body:
            has_serial_in_loop = bool(re.search(r"\bSerial\.(print|println|write)\b", loop_body))

        has_dynamic_memory = bool(re.search(r"\b(String\s+\w+|malloc|calloc|realloc|new\s+)\b", source_code))
        has_float_math = bool(re.search(r"\b(float|double)\s+\w+", source_code))
        has_slow_gpio = bool(re.search(r"\b(digitalWrite|digitalRead)\b", source_code))
        has_non_progmem_strings = bool(re.search(r'Serial\.print(ln)?\s*\(\s*"[^"]{6,}"\s*\)', source_code))
        has_isr = bool(re.search(r"\bISR\s*\(", source_code))

        # Direct hardware register access
        has_direct_port = bool(re.search(r"\b(PORT[B-L]|DDR[B-L]|PIN[B-L])\b", source_code))

        return {
            "total_lines": len(lines),
            "has_delay": has_delay,
            "total_delay_ms": total_delay_ms,
            "has_serial_in_loop": has_serial_in_loop,
            "has_dynamic_memory": has_dynamic_memory,
            "has_float_math": has_float_math,
            "has_slow_gpio": has_slow_gpio,
            "has_non_progmem_strings": has_non_progmem_strings,
            "has_isr": has_isr,
            "has_direct_port": has_direct_port,
        }

    @staticmethod
    def _extract_loop_body(source: str) -> str:
        """Helper to extract the body of void loop() {...}."""
        match = re.search(r"void\s+loop\s*\(\s*\)\s*\{", source)
        if not match:
            return ""
        start = match.end()
        brace_count = 1
        i = start
        while i < len(source) and brace_count > 0:
            if source[i] == '{':
                brace_count += 1
            elif source[i] == '}':
                brace_count -= 1
            i += 1
        return source[start:i - 1]
