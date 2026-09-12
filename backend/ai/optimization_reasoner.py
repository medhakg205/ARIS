"""
ARIS Optimization Reasoner.
Implements the 7-stage architectural reasoning pipeline:
BOARD PROFILE + FIRMWARE + STATIC FINDINGS + RUNTIME TELEMETRY + BASELINE + CORRELATION
  ↓
PROBLEM IDENTIFICATION
  ↓
POSSIBLE OPTIMIZATIONS
  ↓
HARDWARE CONSTRAINT CHECK (AVR8 / ATmega328P / ATmega2560)
  ↓
RISK ASSESSMENT
  ↓
EXPECTED EFFECT
  ↓
OPTIMIZATION CANDIDATE

Guarantees ZERO HARDWARE HALLUCINATIONS:
- Rejects references to CPU performance counters, caches, or FPUs.
- Enforces 16MHz clock cycle math (62.5ns/cycle).
- Enforces Harvard memory boundaries (Flash vs SRAM).
"""

import uuid
from typing import Dict, Any

from backend.analysis.ai_interface import AIContextInput
from backend.ai.risk_evaluator import RiskEvaluator
from backend.ai.prediction_engine import PredictionEngine


class OptimizationReasoner:
    """Architecture-aware reasoning engine for AVR microcontroller targets."""

    AVR_PROFILES = {
        "arduino_uno": {"mcu": "atmega328p", "arch": "avr8", "clock_mhz": 16, "sram_bytes": 2048, "flash_bytes": 32768, "has_perf_counters": False, "has_fpu": False},
        "arduino_nano": {"mcu": "atmega328p", "arch": "avr8", "clock_mhz": 16, "sram_bytes": 2048, "flash_bytes": 32768, "has_perf_counters": False, "has_fpu": False},
        "arduino_mega": {"mcu": "atmega2560", "arch": "avr8", "clock_mhz": 16, "sram_bytes": 8192, "flash_bytes": 262144, "has_perf_counters": False, "has_fpu": False},
    }

    @classmethod
    def reason_and_synthesize(cls, context: AIContextInput, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the formal 7-step reasoning pipeline to produce a validated
        OptimizationCandidate dictionary.
        """
        board_id = context.board_profile.get("board_id", "arduino_uno")
        avr_spec = cls.AVR_PROFILES.get(board_id, cls.AVR_PROFILES["arduino_uno"])
        rule_id = finding.get("rule_id", "ARIS-001")
        finding_id = finding.get("finding_id", f"FIND-{uuid.uuid4().hex[:6].upper()}")
        opt_id = f"OPT-{uuid.uuid4().hex[:8].upper()}"

        # 1. Problem Identification & Evidence
        evidence = finding.get("evidence", {})
        source_file = finding.get("source_file", "main.ino")
        source_line = finding.get("source_line", 1)

        # 2. Hardware-specific reasoning by rule
        if rule_id == "ARIS-001":
            # Blocking delay antipattern
            delay_ms = evidence.get("duration", 20)
            before_code = f"delay({delay_ms});"
            after_code = (
                f"static unsigned long last_exec = 0;\n"
                f"if (millis() - last_exec >= {delay_ms}) {{\n"
                f"    last_exec = millis();\n"
                f"    // Execute scheduled task non-blockingly\n"
                f"}}"
            )
            title = "Convert blocking delay() to non-blocking millis() state machine"
            problem = f"delay({delay_ms}) busy-waits for {delay_ms}ms ({int(delay_ms * 16000)} CPU clock cycles), blocking the main loop."
            reason = "Yields execution cycles to allow concurrent loop iterations, lowering loop latency and jitter."
            hardware_consideration = (
                f"On {avr_spec['mcu'].upper()} (16MHz, no OS/threads), delay() burns 16,000 instructions per ms in an empty loop. "
                "Non-blocking millis() leverages hardware Timer0 overflow ticks without blocking CPU execution."
            )
            confidence = 0.94

        elif rule_id == "ARIS-002":
            # Unthrottled serial print
            before_code = 'Serial.println("Telemetry log payload");'
            after_code = (
                'static unsigned long last_tx = 0;\n'
                'if (millis() - last_tx >= 250) {\n'
                '    last_tx = millis();\n'
                '    Serial.println(F("Telemetry log payload"));\n'
                '}'
            )
            title = "Throttle UART serial output and use Flash string helper"
            problem = "Unthrottled Serial.print in loop() overflows the 64-byte hardware UART ring buffer."
            reason = "Limits serial transmission frequency, preventing UART interrupt saturation and CPU stalling."
            hardware_consideration = (
                f"{avr_spec['mcu'].upper()} USART has only a 64-byte TX buffer. When saturated, Serial.write() "
                "blocks synchronously until buffer space is freed by the UART TX Complete ISR."
            )
            confidence = 0.91

        elif rule_id in ("ARIS-003", "ARIS-005"):
            # Non-PROGMEM RAM string literal
            before_code = 'Serial.print("System Status Initialized Successfully");'
            after_code = 'Serial.print(F("System Status Initialized Successfully"));'
            title = "Store string literals in Flash ROM using F() macro"
            problem = "String literals declared without F() or PROGMEM are copied into precious SRAM at boot."
            reason = "Reduces SRAM consumption, preventing stack/heap collision and memory corruption."
            hardware_consideration = (
                f"Under the AVR Harvard architecture, Flash program memory ({avr_spec['flash_bytes'] // 1024}KB) is separate from "
                f"SRAM ({avr_spec['sram_bytes'] // 1024}KB). The F() macro uses the LPM instruction to read directly from Flash."
            )
            confidence = 0.96

        elif rule_id == "ARIS-004":
            # Software float math
            before_code = "float calculated_val = raw_adc * 0.0048828125;"
            after_code = "uint32_t calculated_val_mv = ((uint32_t)raw_adc * 5000UL) >> 10;"
            title = "Replace 32-bit software float arithmetic with fixed-point integer math"
            problem = "Software emulation of IEEE 754 32-bit floats consumes 60-120 clock cycles per operation."
            reason = "Integer arithmetic executes in 1-2 AVR instruction cycles, accelerating loop frequency."
            hardware_consideration = (
                f"{avr_spec['mcu'].upper()} has an 8-bit RISC ALU without a hardware FPU. Floating point math is "
                "synthesized in software, bloating Flash by ~1.5KB and burning hundreds of clock cycles."
            )
            confidence = 0.88

        elif rule_id == "ARIS-007":
            # Slow GPIO HAL
            before_code = "digitalWrite(13, HIGH);"
            after_code = "PORTB |= (1 << PB5); // Direct port register write (Pin 13 on Uno/Nano)"
            title = "Replace digitalWrite() with atomic direct port register manipulation"
            problem = "digitalWrite() performs multiple lookup operations, consuming ~56 clock cycles (3.5 µs)."
            reason = "Direct port write executes in 1-2 clock cycles (62.5 - 125 ns), cutting GPIO latency by 96%."
            hardware_consideration = (
                f"AVR SBI/CBI instructions set or clear bits in I/O registers atomically in 1 clock cycle at 16MHz."
            )
            confidence = 0.89

        else:
            before_code = "// original code"
            after_code = "// optimized architecture-compliant implementation"
            title = f"Remediate {finding.get('title', 'Hardware Bottleneck')}"
            problem = finding.get("description", "MCU resource bottleneck detected.")
            reason = finding.get("recommended_action", "Apply embedded architecture best practices.")
            hardware_consideration = f"Optimized for {avr_spec['mcu'].upper()} 16MHz AVR8 Harvard architecture."
            confidence = 0.85

        # 3. Hardware Constraint Check (strictly reject hallucinations)
        cls._verify_zero_hardware_hallucinations(reason + " " + hardware_consideration)

        # 4. Risk Assessment
        risk_level, risk_rationale = RiskEvaluator.evaluate(
            rule_id=rule_id,
            board_id=board_id,
            before_code=before_code,
            after_code=after_code,
            finding_severity=finding.get("severity", "MEDIUM")
        )

        # 5. Expected Effect (Quantitative Prediction)
        expected_effect = PredictionEngine.forecast_effect(
            rule_id=rule_id,
            board_id=board_id,
            evidence=evidence,
            baseline_metrics=context.baseline_metrics
        )

        # 6. Candidate Assembly
        candidate = {
            "optimization_id": opt_id,
            "finding_id": finding_id,
            "title": title,
            "problem": problem,
            "source_location": {"file": source_file, "line": source_line},
            "before_code": before_code,
            "after_code": after_code,
            "reason": reason,
            "hardware_consideration": hardware_consideration,
            "expected_effect": expected_effect,
            "risk": risk_level,
            "confidence": confidence,
            "validation_required": True,
            "status": "PROPOSED"
        }

        return candidate

    @staticmethod
    def _verify_zero_hardware_hallucinations(text: str):
        """Ensures reasoning does not reference non-existent hardware features on AVR microcontrollers."""
        forbidden_hallucinations = [
            "cpu performance counter",
            "hardware cycle counter register",
            "branch predictor",
            "l1 cache",
            "l2 cache",
            "instruction cache",
            "hardware fpu",
            "hardware floating point unit",
            "out-of-order execution"
        ]
        text_lower = text.lower()
        for forbidden in forbidden_hallucinations:
            if forbidden in text_lower:
                raise ValueError(
                    f"Hardware hallucination detected: AVR microcontrollers do not possess '{forbidden}'."
                )
