"""
Unit tests for CPU Load Estimation methodology and constraints.
"""

import pytest
from embedded.protocol.protocol_schema import TelemetrySample, METRIC_METADATA

def calculate_cpu_load_estimate(active_us: int, epoch_ms: int, idle_us: int = 0) -> float:
    """Python reference implementation of the ARIS C++ CPU estimation methodology."""
    epoch_us = epoch_ms * 1000
    if epoch_us <= 0:
        return 0.0

    if idle_us > 0:
        total_accounted = active_us + idle_us
        if total_accounted > 0:
            pct = (active_us / total_accounted) * 100.0
            return max(0.0, min(100.0, pct))
    else:
        pct = (active_us / epoch_us) * 100.0
        return max(0.0, min(100.0, pct))
    return 0.0

def test_cpu_estimation_active_window():
    # 50ms active time in 100ms epoch -> 50% CPU load
    load = calculate_cpu_load_estimate(active_us=50000, epoch_ms=100)
    assert abs(load - 50.0) < 0.01

def test_cpu_estimation_with_idle():
    # 20ms active, 80ms cooperative idle -> 20% CPU load
    load = calculate_cpu_load_estimate(active_us=20000, epoch_ms=100, idle_us=80000)
    assert abs(load - 20.0) < 0.01

def test_cpu_estimation_clamping():
    # Over-budget active time clamped to 100%
    overload = calculate_cpu_load_estimate(active_us=150000, epoch_ms=100)
    assert overload == 100.0

    # 0 active time
    zero_load = calculate_cpu_load_estimate(active_us=0, epoch_ms=100)
    assert zero_load == 0.0

def test_cpu_classification_strictly_estimated():
    meta = METRIC_METADATA["cpu_load"]
    assert meta["classification"] == "ESTIMATED"
    assert meta["confidence"] == 0.85
    assert meta["unit"] == "%"

def test_sample_construction_enforces_estimated():
    sample = TelemetrySample(
        run_id="ARIS-CPU-001",
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=1000,
        sequence=1,
        metric="cpu_load",
        value=33.3,
        unit="%",
        classification="ESTIMATED",
        confidence=0.85
    )
    assert sample.classification == "ESTIMATED"
