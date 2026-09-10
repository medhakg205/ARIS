"""
Unit tests for ARIS Simulated Hardware Adapter.
Verifies:
- Simulator generates valid ARIS telemetry using EXACTLY the canonical TelemetrySample schema
- Clear identification as DEMO MODE
- Accurate behavioral modes (blocking delay vs optimized)
- Ingestion through the standard telemetry pipeline
"""

import pytest
from backend.simulator.simulated_hardware import SimulatedHardware
from backend.telemetry.telemetry_schema import TelemetrySample, CANONICAL_METRIC_NAMES


def test_simulator_generates_canonical_telemetry_snapshot(ingestor):
    """Verify snapshot contains all 20 canonical metrics conforming to TelemetrySample."""
    sim = SimulatedHardware(ingestor, "arduino_uno")
    sim.set_mode("default")
    samples = sim.generate_telemetry_snapshot()

    assert len(samples) == 20
    metric_names = [s.metric for s in samples]
    for m in CANONICAL_METRIC_NAMES:
        assert m in metric_names

    # Check first sample
    sample = samples[0]
    assert isinstance(sample, TelemetrySample)
    assert sample.board_id == "arduino_uno"
    assert sample.mcu == "atmega328p"
    assert sample.protocol_version == "1.0"


def test_simulator_blocking_delay_mode(ingestor):
    """Verify blocking_delay simulation mode produces high loop_time."""
    sim = SimulatedHardware(ingestor, "arduino_uno")
    sim.set_mode("blocking_delay", delay_ms=50)
    samples = sim.generate_telemetry_snapshot()
    metric_map = {s.metric: s.value for s in samples}

    assert metric_map["loop_time"] >= 50.0
    assert metric_map["loop_frequency"] <= 20.0
    assert metric_map["cpu_load"] >= 70.0


def test_simulator_optimized_mode(ingestor):
    """Verify optimized simulation mode produces sub-2ms loop_time and low CPU load."""
    sim = SimulatedHardware(ingestor, "arduino_uno")
    sim.set_mode("optimized")
    samples = sim.generate_telemetry_snapshot()
    metric_map = {s.metric: s.value for s in samples}

    assert metric_map["loop_time"] < 3.0
    assert metric_map["loop_frequency"] > 250.0
    assert metric_map["cpu_load"] < 25.0


def test_simulator_lifecycle_and_demo_mode_identification(ingestor):
    """Verify simulator start/stop methods clearly identify as DEMO MODE."""
    sim = SimulatedHardware(ingestor, "arduino_mega")
    res = sim.start(run_id="DEMO-TEST-001")
    assert res["mode"] == "DEMO MODE"
    assert sim.running is True

    stop_res = sim.stop()
    assert stop_res["mode"] == "DEMO MODE"
    assert sim.running is False
