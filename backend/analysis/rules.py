"""
ARIS Canonical Analysis Rules Definition & Rule Engines.
Implements the 10 canonical ARIS analysis rules:
- ARIS-001: blocking delay
- ARIS-002: excessive serial logging
- ARIS-003: excessive polling
- ARIS-004: large local allocation
- ARIS-005: high loop jitter
- ARIS-006: high interrupt frequency
- ARIS-007: redundant GPIO activity
- ARIS-008: repeated computation
- ARIS-009: memory pressure
- ARIS-010: long critical section
Adheres strictly to the Finding Schema.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# Canonical Severity Levels
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# Canonical Rule IDs
RULE_ARIS_001 = "ARIS-001"  # blocking delay
RULE_ARIS_002 = "ARIS-002"  # excessive serial logging
RULE_ARIS_003 = "ARIS-003"  # excessive polling
RULE_ARIS_004 = "ARIS-004"  # large local allocation
RULE_ARIS_005 = "ARIS-005"  # high loop jitter
RULE_ARIS_006 = "ARIS-006"  # high interrupt frequency
RULE_ARIS_007 = "ARIS-007"  # redundant GPIO activity
RULE_ARIS_008 = "ARIS-008"  # repeated computation
RULE_ARIS_009 = "ARIS-009"  # memory pressure
RULE_ARIS_010 = "ARIS-010"  # long critical section


class Finding(BaseModel):
    """
    Standard Finding schema conforming to the specification.
    """
    finding_id: str
    rule_id: str
    severity: str
    title: str
    description: str
    source_file: str = "main.ino"
    source_line: int
    runtime_correlation: str = "NONE"  # "NONE", "LOW", "MEDIUM", "HIGH"
    confidence: float
    evidence: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str


class RuleEvaluator:
    """
    Evaluates source code and normalized firmware structures against the 10 ARIS rules.
    """

    @staticmethod
    def evaluate_all(source_code: str, source_file: str = "main.ino") -> List[Finding]:
        """
        Runs all 10 canonical rule checks on the provided firmware source code.
        """
        findings: List[Finding] = []
        findings.extend(RuleEvaluator.check_aris_001_blocking_delay(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_002_excessive_serial_logging(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_003_excessive_polling(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_004_large_local_allocation(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_005_high_loop_jitter(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_006_high_interrupt_frequency(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_007_redundant_gpio(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_008_repeated_computation(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_009_memory_pressure(source_code, source_file))
        findings.extend(RuleEvaluator.check_aris_010_long_critical_section(source_code, source_file))
        return findings

    @staticmethod
    def check_aris_001_blocking_delay(code: str, source_file: str) -> List[Finding]:
        """ARIS-001: Detects blocking delay() or delayMicroseconds() calls."""
        findings = []
        pattern = re.compile(r'\b(delay|delayMicroseconds)\s*\(\s*([0-9]+)\s*\)')
        for line_num, line in enumerate(code.splitlines(), 1):
            for match in pattern.finditer(line):
                fn = match.group(1)
                duration = int(match.group(2))
                sev = "CRITICAL" if (fn == "delay" and duration >= 50) else "HIGH" if (fn == "delay" and duration > 5) else "MEDIUM"
                findings.append(Finding(
                    finding_id=f"FIND-001-{line_num}",
                    rule_id=RULE_ARIS_001,
                    severity=sev,
                    title="Blocking delay detected",
                    description=f"Invocation of '{fn}({duration})' blocks CPU execution and stalls real-time loop scheduling.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.95,
                    evidence={"call": match.group(0), "duration": duration, "unit": "ms" if fn == "delay" else "us"},
                    recommended_action="Replace blocking delay with a non-blocking millis() timer state machine."
                ))
        return findings

    @staticmethod
    def check_aris_002_excessive_serial_logging(code: str, source_file: str) -> List[Finding]:
        """ARIS-002: Detects unthrottled Serial.print() / Serial.println() calls inside loop()."""
        findings = []
        in_loop = False
        pattern = re.compile(r'\bSerial\.(print|println|write)\s*\(')
        for line_num, line in enumerate(code.splitlines(), 1):
            if "void loop" in line:
                in_loop = True
            if in_loop and pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-002-{line_num}",
                    rule_id=RULE_ARIS_002,
                    severity="HIGH",
                    title="Excessive serial logging in hot path",
                    description="Serial print statements inside the execution loop fill the UART hardware TX buffer and stall the processor.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.88,
                    evidence={"line": line.strip()},
                    recommended_action="Throttle serial output using a periodic epoch interval or reduce logging verbosity."
                ))
        return findings

    @staticmethod
    def check_aris_003_excessive_polling(code: str, source_file: str) -> List[Finding]:
        """ARIS-003: Detects busy-wait polling loops (e.g. while(digitalRead(...)))."""
        findings = []
        pattern = re.compile(r'\bwhile\s*\([^)]*(digitalRead|analogRead)[^)]*\)\s*;?')
        for line_num, line in enumerate(code.splitlines(), 1):
            if pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-003-{line_num}",
                    rule_id=RULE_ARIS_003,
                    severity="HIGH",
                    title="Excessive polling / busy-waiting detected",
                    description="Tight while loop continuously polling pin states consumes 100% CPU time without yielding.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.85,
                    evidence={"line": line.strip()},
                    recommended_action="Migrate pin monitoring to external pin-change interrupts (PCINT) or state change detection."
                ))
        return findings

    @staticmethod
    def check_aris_004_large_local_allocation(code: str, source_file: str) -> List[Finding]:
        """ARIS-004: Detects large local array allocations exceeding 32 bytes on the AVR stack."""
        findings = []
        pattern = re.compile(r'\b(char|byte|uint8_t|int|uint16_t|long|float)\s+([a-zA-Z0-9_]+)\s*\[\s*([0-9]+)\s*\]')
        for line_num, line in enumerate(code.splitlines(), 1):
            m = pattern.search(line)
            if m:
                type_name = m.group(1)
                size_items = int(m.group(3))
                item_size = 4 if type_name in ["long", "float"] else 2 if type_name in ["int", "uint16_t"] else 1
                total_bytes = size_items * item_size
                if total_bytes >= 32:
                    findings.append(Finding(
                        finding_id=f"FIND-004-{line_num}",
                        rule_id=RULE_ARIS_004,
                        severity="HIGH" if total_bytes > 64 else "MEDIUM",
                        title="Large local stack allocation",
                        description=f"Local array '{m.group(2)}' allocates {total_bytes} bytes on the call stack, risking stack-heap collision.",
                        source_file=source_file,
                        source_line=line_num,
                        runtime_correlation="NONE",
                        confidence=0.90,
                        evidence={"variable": m.group(2), "allocated_bytes": total_bytes},
                        recommended_action="Relocate large buffers to static/global memory or PROGMEM if constants."
                    ))
        return findings

    @staticmethod
    def check_aris_005_high_loop_jitter(code: str, source_file: str) -> List[Finding]:
        """ARIS-005: Detects conditional branching with variable timing leading to high loop jitter."""
        findings = []
        pattern = re.compile(r'\bif\s*\(.*?\)\s*\{\s*delay\(')
        for line_num, line in enumerate(code.splitlines(), 1):
            if pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-005-{line_num}",
                    rule_id=RULE_ARIS_005,
                    severity="MEDIUM",
                    title="Potential high loop jitter",
                    description="Conditional blocking delays inside branches cause non-deterministic loop execution durations.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.82,
                    evidence={"line": line.strip()},
                    recommended_action="Decouple periodic scheduling from conditional branch paths using a hardware timer."
                ))
        return findings

    @staticmethod
    def check_aris_006_high_interrupt_frequency(code: str, source_file: str) -> List[Finding]:
        """ARIS-006: Detects manual timer/external interrupt configurations that fire at high frequency."""
        findings = []
        pattern = re.compile(r'\b(attachInterrupt|ISR\s*\()\s*')
        for line_num, line in enumerate(code.splitlines(), 1):
            if pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-006-{line_num}",
                    rule_id=RULE_ARIS_006,
                    severity="MEDIUM",
                    title="Interrupt service routine detected",
                    description="Instrumented ISR detected. Requires runtime monitoring to verify interrupt rate does not saturate CPU.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.80,
                    evidence={"line": line.strip()},
                    recommended_action="Ensure ISR body is minimal (flag set only) and defer processing to main loop."
                ))
        return findings

    @staticmethod
    def check_aris_007_redundant_gpio(code: str, source_file: str) -> List[Finding]:
        """ARIS-007: Detects redundant or slow repeated digitalWrite calls."""
        findings = []
        pattern = re.compile(r'\bdigitalWrite\s*\(\s*([a-zA-Z0-9_]+)\s*,\s*([a-zA-Z0-9_]+)\s*\)')
        calls = []
        for line_num, line in enumerate(code.splitlines(), 1):
            m = pattern.search(line)
            if m:
                calls.append((line_num, m.group(1), m.group(2)))

        # Look for identical pin writes in sequence
        for i in range(len(calls) - 1):
            if calls[i][1] == calls[i+1][1] and calls[i][2] == calls[i+1][2]:
                findings.append(Finding(
                    finding_id=f"FIND-007-{calls[i+1][0]}",
                    rule_id=RULE_ARIS_007,
                    severity="LOW",
                    title="Redundant GPIO write detected",
                    description=f"Pin '{calls[i][1]}' is repeatedly written with the same state without intermediate changes.",
                    source_file=source_file,
                    source_line=calls[i+1][0],
                    runtime_correlation="NONE",
                    confidence=0.85,
                    evidence={"pin": calls[i][1], "value": calls[i][2]},
                    recommended_action="Cache output pin state in a variable and write only on state change, or use direct PORT registers."
                ))
        return findings

    @staticmethod
    def check_aris_008_repeated_computation(code: str, source_file: str) -> List[Finding]:
        """ARIS-008: Detects repeated complex floating point operations or trigonometry in loop."""
        findings = []
        pattern = re.compile(r'\b(sin|cos|tan|pow|sqrt)\s*\(')
        in_loop = False
        for line_num, line in enumerate(code.splitlines(), 1):
            if "void loop" in line:
                in_loop = True
            if in_loop and pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-008-{line_num}",
                    rule_id=RULE_ARIS_008,
                    severity="MEDIUM",
                    title="Repeated complex floating-point computation in loop",
                    description="ATmega microcontrollers lack a hardware FPU. Software emulated math functions consume hundreds of clock cycles per loop iteration.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.86,
                    evidence={"line": line.strip()},
                    recommended_action="Pre-compute values into a PROGMEM lookup table (LUT) or use fixed-point integer arithmetic."
                ))
        return findings

    @staticmethod
    def check_aris_009_memory_pressure(code: str, source_file: str) -> List[Finding]:
        """ARIS-009: Detects dynamic memory allocation (malloc/String) on memory-constrained AVR devices."""
        findings = []
        pattern = re.compile(r'\b(malloc|free|new |delete |String\s+[a-zA-Z0-9_]+\s*=)')
        for line_num, line in enumerate(code.splitlines(), 1):
            m = pattern.search(line)
            if m:
                findings.append(Finding(
                    finding_id=f"FIND-009-{line_num}",
                    rule_id=RULE_ARIS_009,
                    severity="HIGH",
                    title="Dynamic memory allocation / heap fragmentation risk",
                    description=f"Usage of '{m.group(1).strip()}' causes heap fragmentation on 8-bit AVR microcontrollers with 2KB SRAM.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.92,
                    evidence={"call": m.group(0)},
                    recommended_action="Replace dynamic String objects or malloc() with static fixed-length char arrays."
                ))
        return findings

    @staticmethod
    def check_aris_010_long_critical_section(code: str, source_file: str) -> List[Finding]:
        """ARIS-010: Detects extended critical sections (cli() or noInterrupts())."""
        findings = []
        cli_pattern = re.compile(r'\b(cli\(\)|noInterrupts\(\))')
        for line_num, line in enumerate(code.splitlines(), 1):
            if cli_pattern.search(line):
                findings.append(Finding(
                    finding_id=f"FIND-010-{line_num}",
                    rule_id=RULE_ARIS_010,
                    severity="HIGH",
                    title="Global interrupts disabled (critical section)",
                    description="Disabling interrupts stops hardware timer ticks (millis()/micros()) and can cause missed serial data.",
                    source_file=source_file,
                    source_line=line_num,
                    runtime_correlation="NONE",
                    confidence=0.88,
                    evidence={"line": line.strip()},
                    recommended_action="Ensure interrupts are disabled for the minimum possible number of instructions and restored immediately with sei()."
                ))
        return findings
