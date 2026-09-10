"""
ARIS Static Firmware Analyzer.
Analyzes firmware from available formats:
- C++/Ino Sketch Source
- ELF binary
- Intel HEX image
- MAP symbol tables
Evaluates the 10 canonical ARIS analysis rules (ARIS-001 through ARIS-010)
and outputs structured Finding instances conforming to the canonical Finding Schema.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.firmware.board_profiles import get_board_profile, BoardProfile
from backend.analysis.rules import Finding, RuleEvaluator


class FunctionInfo(BaseModel):
    """Information extracted about a C/C++ function."""
    name: str
    return_type: str
    parameters: List[str]
    start_line: int
    end_line: int
    line_count: int
    is_isr: bool = False


class StaticAnalysisResult(BaseModel):
    """Consolidated static firmware analysis output."""
    board_id: str
    display_name: str
    total_lines: int
    function_count: int
    functions: List[FunctionInfo]
    findings: List[Finding]
    estimated_flash_bytes: int
    estimated_sram_static_bytes: int
    flash_utilization_pct: float
    sram_utilization_pct: float


class StaticAnalyzer:
    """
    Performs static structural code and binary analysis against target board constraints.
    """

    def __init__(self, default_board_id: str = "arduino_uno"):
        self.default_board_id = default_board_id

    def analyze_source(
        self,
        source_code: str,
        board_id: Optional[str] = None,
        source_file: str = "main.ino"
    ) -> StaticAnalysisResult:
        """
        Performs static analysis on source code using AST/regex parsing and evaluates
        canonical rules ARIS-001 through ARIS-010.
        """
        bid = board_id or self.default_board_id
        profile = get_board_profile(bid)

        lines = source_code.splitlines()
        total_lines = len(lines)

        # 1. Parse function profiles
        functions = self._extract_functions(lines)

        # 2. Evaluate the 10 canonical rules
        findings = RuleEvaluator.evaluate_all(source_code, source_file)

        # 3. Estimate flash and sram footprints from source
        string_chars = sum(len(s) for s in re.findall(r'"([^"\\]*(\\.[^"\\]*)*)"', source_code))
        est_flash = min(profile.flash_bytes, 1500 + (total_lines * 22) + string_chars)
        est_sram = min(profile.sram_bytes // 2, 190 + string_chars + (len(functions) * 12))

        return StaticAnalysisResult(
            board_id=bid,
            display_name=profile.display_name,
            total_lines=total_lines,
            function_count=len(functions),
            functions=functions,
            findings=findings,
            estimated_flash_bytes=est_flash,
            estimated_sram_static_bytes=est_sram,
            flash_utilization_pct=round((est_flash / profile.flash_bytes) * 100, 2),
            sram_utilization_pct=round((est_sram / profile.sram_bytes) * 100, 2)
        )

    def _extract_functions(self, lines: List[str]) -> List[FunctionInfo]:
        """Extracts declared functions, parameter lists, and ISR designations."""
        functions = []
        func_regex = re.compile(
            r'^\s*(void|int|long|unsigned\s+int|unsigned\s+long|float|double|bool|byte|char|uint8_t|uint16_t|uint32_t|ISR)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{?'
        )

        current_func: Optional[FunctionInfo] = None

        for idx, line in enumerate(lines, 1):
            m = func_regex.search(line)
            if m:
                if current_func:
                    current_func.end_line = idx - 1
                    current_func.line_count = max(1, current_func.end_line - current_func.start_line + 1)
                    functions.append(current_func)

                ret_type = m.group(1)
                func_name = m.group(2)
                raw_params = m.group(3).strip()
                params = [p.strip() for p in raw_params.split(',') if p.strip()]
                is_isr = "ISR" in ret_type or "ISR" in func_name or "interrupt" in func_name.lower()

                current_func = FunctionInfo(
                    name=func_name,
                    return_type=ret_type,
                    parameters=params,
                    start_line=idx,
                    end_line=idx,
                    line_count=1,
                    is_isr=is_isr
                )

        if current_func:
            current_func.end_line = len(lines)
            current_func.line_count = max(1, current_func.end_line - current_func.start_line + 1)
            functions.append(current_func)

        return functions
