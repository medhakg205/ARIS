"""
Unit tests for ARIS Telemetry Protocol v1.0 Schema and Validation.
"""

import pytest
from pydantic import ValidationError
from embedded.protocol.protocol_schema import (
    TelemetrySample,
    PROTOCOL_VERSION,
    CANONICAL_METRIC_NAMES,
    METRIC_METADATA,
    VALID_CLASSIFICATIONS
)

def test_protocol_version_default():
    sample = TelemetrySample(
        run_id="ARIS-TEST-001",
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=1000,
        sequence=1,
        metric="loop_time",
        value=4.21,
        unit="ms",
        classification="MEASURED",
        confidence=1.0
    )
    assert sample.protocol_version == "1.0"

def test_canonical_metric_names_count():
    assert len(CANONICAL_METRIC_NAMES) == 20
    assert "cpu_load" in CANONICAL_METRIC_NAMES
    assert "loop_time" in CANONICAL_METRIC_NAMES
    assert "loop_frequency" in CANONICAL_METRIC_NAMES
    assert "loop_jitter" in CANONICAL_METRIC_NAMES
    assert "sram_used" in CANONICAL_METRIC_NAMES
    assert "sram_free" in CANONICAL_METRIC_NAMES
    assert "stack_used" in CANONICAL_METRIC_NAMES
    assert "stack_high_water_mark" in CANONICAL_METRIC_NAMES
    assert "interrupt_count" in CANONICAL_METRIC_NAMES
    assert "interrupt_rate" in CANONICAL_METRIC_NAMES
    assert "gpio_activity" in CANONICAL_METRIC_NAMES
    assert "adc_activity" in CANONICAL_METRIC_NAMES
    assert "uart_activity" in CANONICAL_METRIC_NAMES
    assert "spi_activity" in CANONICAL_METRIC_NAMES
    assert "i2c_activity" in CANONICAL_METRIC_NAMES
    assert "timer_activity" in CANONICAL_METRIC_NAMES
    assert "reset_event" in CANONICAL_METRIC_NAMES
    assert "watchdog_event" in CANONICAL_METRIC_NAMES
    assert "runtime_fault" in CANONICAL_METRIC_NAMES
    assert "instrumentation_overhead" in CANONICAL_METRIC_NAMES

def test_reject_non_canonical_metric_names():
    invalid_metrics = ["cpuUsage", "cpu_utilization", "cpuLoad", "loopTime", "free_ram", "jitter"]
    for bad_name in invalid_metrics:
        with pytest.raises(ValidationError):
            TelemetrySample(
                run_id="ARIS-TEST-001",
                board_id="arduino_uno",
                mcu="atmega328p",
                timestamp_ms=1000,
                sequence=1,
                metric=bad_name,
                value=10.0,
                unit="unit",
                classification="MEASURED",
                confidence=1.0
            )

def test_cpu_load_must_be_estimated():
    # Attempting to classify cpu_load as MEASURED must raise ValidationError
    with pytest.raises(ValidationError) as excinfo:
        TelemetrySample(
            run_id="ARIS-TEST-001",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=1000,
            sequence=1,
            metric="cpu_load",
            value=45.5,
            unit="%",
            classification="MEASURED",
            confidence=1.0
        )
    assert "NEVER be classified as MEASURED" in str(excinfo.value)

def test_cpu_load_valid_estimated():
    sample = TelemetrySample(
        run_id="ARIS-TEST-001",
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=1000,
        sequence=1,
        metric="cpu_load",
        value=45.5,
        unit="%",
        classification="ESTIMATED",
        confidence=0.85
    )
    assert sample.classification == "ESTIMATED"
    assert sample.value == 45.5
    assert sample.confidence == 0.85

def test_invalid_classification_rejected():
    with pytest.raises(ValidationError):
        TelemetrySample(
            run_id="ARIS-TEST-001",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=1000,
            sequence=1,
            metric="loop_time",
            value=2.5,
            unit="ms",
            classification="GUESSED",
            confidence=1.0
        )

def test_confidence_bounds():
    with pytest.raises(ValidationError):
        TelemetrySample(
            run_id="ARIS-TEST-001",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=1000,
            sequence=1,
            metric="loop_time",
            value=2.5,
            unit="ms",
            classification="MEASURED",
            confidence=1.5  # > 1.0 invalid
        )
    with pytest.raises(ValidationError):
        TelemetrySample(
            run_id="ARIS-TEST-001",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=1000,
            sequence=1,
            metric="loop_time",
            value=2.5,
            unit="ms",
            classification="MEASURED",
            confidence=-0.1  # < 0.0 invalid
        )
