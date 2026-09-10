"""
Unit tests for ARIS Static Firmware Analysis & Canonical Rules.
Verifies detection of:
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
"""

import pytest
from backend.analysis.rules import (
    RuleEvaluator,
    RULE_ARIS_001,
    RULE_ARIS_002,
    RULE_ARIS_003,
    RULE_ARIS_004,
    RULE_ARIS_005,
    RULE_ARIS_006,
    RULE_ARIS_007,
    RULE_ARIS_008,
    RULE_ARIS_009,
    RULE_ARIS_010
)
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.firmware.firmware_manager import FirmwareManager


def test_aris_001_blocking_delay():
    code = "void loop() { digitalWrite(13, HIGH); delay(100); }"
    findings = RuleEvaluator.check_aris_001_blocking_delay(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_001
    assert findings[0].severity == "CRITICAL"
    assert findings[0].evidence["duration"] == 100


def test_aris_002_excessive_serial():
    code = "void loop() { Serial.println(\"heartbeat\"); }"
    findings = RuleEvaluator.check_aris_002_excessive_serial_logging(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_002


def test_aris_003_excessive_polling():
    code = "void loop() { while(digitalRead(2) == LOW); }"
    findings = RuleEvaluator.check_aris_003_excessive_polling(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_003


def test_aris_004_large_local_allocation():
    code = "void loop() { char buffer[128]; }"
    findings = RuleEvaluator.check_aris_004_large_local_allocation(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_004
    assert findings[0].evidence["allocated_bytes"] == 128


def test_aris_005_high_loop_jitter():
    code = "void loop() { if (analogRead(A0) > 500) { delay(50); } }"
    findings = RuleEvaluator.check_aris_005_high_loop_jitter(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_005


def test_aris_006_high_interrupt_frequency():
    code = "void setup() { attachInterrupt(digitalPinToInterrupt(2), isrFunc, RISING); }"
    findings = RuleEvaluator.check_aris_006_high_interrupt_frequency(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_006


def test_aris_007_redundant_gpio():
    code = "void loop() {\n  digitalWrite(13, HIGH);\n  digitalWrite(13, HIGH);\n}"
    findings = RuleEvaluator.check_aris_007_redundant_gpio(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_007


def test_aris_008_repeated_computation():
    code = "void loop() { float v = sin(1.57) * 100.0; }"
    findings = RuleEvaluator.check_aris_008_repeated_computation(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_008


def test_aris_009_memory_pressure():
    code = "void loop() { String msg = \"data\"; }"
    findings = RuleEvaluator.check_aris_009_memory_pressure(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_009


def test_aris_010_long_critical_section():
    code = "void loop() { cli(); delay(10); sei(); }"
    findings = RuleEvaluator.check_aris_010_long_critical_section(code, "test.ino")
    assert len(findings) == 1
    assert findings[0].rule_id == RULE_ARIS_010


def test_static_analyzer_consolidated():
    sketch = """
    void setup() {
        Serial.begin(115200);
        pinMode(13, OUTPUT);
    }
    void loop() {
        digitalWrite(13, HIGH);
        delay(25);
        Serial.println("Tick");
    }
    """
    analyzer = StaticAnalyzer()
    res = analyzer.analyze_source(sketch, "arduino_uno")
    assert res.board_id == "arduino_uno"
    assert res.function_count == 2
    rule_ids = {f.rule_id for f in res.findings}
    assert RULE_ARIS_001 in rule_ids
    assert RULE_ARIS_002 in rule_ids
