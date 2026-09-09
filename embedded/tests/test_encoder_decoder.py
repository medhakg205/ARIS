"""
Unit tests for ARIS Telemetry Encoding, Serialization, and Protocol Parsing.
"""

import json
import pytest
from embedded.protocol.protocol_schema import TelemetrySample, PROTOCOL_VERSION
from embedded.protocol.protocol_parser import ProtocolParser
from embedded.telemetry.telemetry_encoder import TelemetryEncoder
from embedded.telemetry.telemetry_collector import TelemetryCollector

def test_json_encode_decode_roundtrip():
    collector = TelemetryCollector(board_id="arduino_uno", run_id="ARIS-EXP-001")
    sample = collector.create_sample("loop_time", 5.25, timestamp_ms=123456)

    json_str = TelemetryEncoder.encode_sample_to_json(sample)
    data = json.loads(json_str)

    assert data["protocol_version"] == "1.0"
    assert data["run_id"] == "ARIS-EXP-001"
    assert data["board_id"] == "arduino_uno"
    assert data["mcu"] == "atmega328p"
    assert data["timestamp_ms"] == 123456
    assert data["sequence"] == 1
    assert data["metric"] == "loop_time"
    assert data["value"] == 5.25
    assert data["unit"] == "ms"
    assert data["classification"] == "MEASURED"
    assert data["confidence"] == 1.0

    parser = ProtocolParser()
    parsed_sample = parser.parse_json_sample(json_str)
    assert parsed_sample == sample

def test_compact_aris1_frame_parsing():
    metrics = {
        "cpu_load": 42.5,
        "loop_time": 3.14,
        "loop_frequency": 318.5,
        "loop_jitter": 0.45,
        "sram_used": 512,
        "sram_free": 1536,
        "stack_used": 64,
        "stack_high_water_mark": 128,
        "interrupt_count": 15,
        "interrupt_rate": 150.0,
        "gpio_activity": 20,
        "adc_activity": 10,
        "uart_activity": 85,
        "spi_activity": 0,
        "i2c_activity": 0,
        "timer_activity": 50,
        "reset_event": 1,
        "watchdog_event": 0,
        "runtime_fault": 0,
        "instrumentation_overhead": 1.5
    }

    raw_frame = TelemetryEncoder.encode_compact_frame(
        run_id="ARIS-RUN-777",
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=500000,
        sequence=100,
        metrics=metrics
    )

    assert raw_frame.startswith("$ARIS1,")
    assert raw_frame.endswith("#")

    parser = ProtocolParser()
    samples = parser.parse_frame(raw_frame)

    assert len(samples) == 20
    metric_map = {s.metric: s for s in samples}

    # Verify key metrics
    assert metric_map["cpu_load"].value == 42.5
    assert metric_map["cpu_load"].classification == "ESTIMATED"
    assert metric_map["cpu_load"].confidence == 0.85

    assert metric_map["loop_time"].value == 3.14
    assert metric_map["loop_time"].classification == "MEASURED"

    assert metric_map["sram_free"].value == 1536.0
    assert metric_map["sram_free"].unit == "bytes"

    assert metric_map["instrumentation_overhead"].value == 1.5
    assert metric_map["instrumentation_overhead"].unit == "us"

def test_legacy_frame_parsing_backward_compatibility():
    parser = ProtocolParser(run_id="ARIS-LEGACY-001")
    legacy_line = "$ARIS,1,35.0,1400,120,4500,5,10,20#"
    samples = parser.parse_frame(legacy_line)

    assert len(samples) >= 7
    metric_names = [s.metric for s in samples]
    assert "cpu_load" in metric_names
    assert "loop_time" in metric_names
    assert "sram_free" in metric_names
    assert "stack_high_water_mark" in metric_names

    cpu_sample = next(s for s in samples if s.metric == "cpu_load")
    assert cpu_sample.classification == "ESTIMATED"
    assert cpu_sample.value == 35.0
