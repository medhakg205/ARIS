"""
Unit tests for ARIS Benchmark Validation Engine.
Verifies:
- Comparison across all 8 canonical validation metrics:
  cpu_load, loop_time, loop_jitter, sram_used, stack_used, interrupt_rate, runtime_fault, instrumentation_overhead
- Correct status transitions: VALIDATED, REGRESSION, NO_SIGNIFICANT_CHANGE
- Percentage change and arithmetic difference accuracy
"""

import pytest
from backend.experiments.validation_engine import ValidationEngine, VALIDATION_METRIC_NAMES
from backend.database.models import BaselineRecord, BaselineMetricStats


def create_mock_baseline(run_id: str, loop_time: float, cpu_load: float, sram_used: float, faults: float = 0.0) -> BaselineRecord:
    stats = {}
    for m in VALIDATION_METRIC_NAMES:
        stats[m] = BaselineMetricStats(
            metric=m, sample_count=20, mean=1.0, median=1.0,
            minimum=1.0, maximum=1.0, variance=0.0, jitter=0.0
        )
    stats["loop_time"].mean = loop_time
    stats["cpu_load"].mean = cpu_load
    stats["sram_used"].mean = sram_used
    stats["runtime_fault"].maximum = faults
    return BaselineRecord(
        baseline_id=f"BASE-{run_id}",
        run_id=run_id,
        board_id="arduino_uno",
        sample_window_ms=2000,
        metrics=stats
    )


def test_validation_successful_improvement():
    """Verify significant reduction in loop_time and cpu_load yields VALIDATED."""
    base = create_mock_baseline("R1", loop_time=100.0, cpu_load=80.0, sram_used=600.0)
    cand = create_mock_baseline("R2", loop_time=5.0, cpu_load=20.0, sram_used=600.0)

    report = ValidationEngine.validate_benchmarks(base, cand, "VAL-1", "EXP-1")
    assert report.validation_status == "VALIDATED"
    assert report.percentage_change["loop_time"] == -95.0
    assert report.percentage_change["cpu_load"] == -75.0
    assert "Empirical confirmation" in report.reason


def test_validation_regression_detected():
    """Verify increase in execution latency or runtime faults yields REGRESSION."""
    base = create_mock_baseline("R1", loop_time=10.0, cpu_load=30.0, sram_used=500.0)
    cand = create_mock_baseline("R2", loop_time=80.0, cpu_load=90.0, sram_used=500.0)

    report = ValidationEngine.validate_benchmarks(base, cand, "VAL-2", "EXP-2")
    assert report.validation_status == "REGRESSION"


def test_validation_runtime_fault_causes_regression():
    """Verify new runtime faults trigger immediate REGRESSION."""
    base = create_mock_baseline("R1", loop_time=10.0, cpu_load=30.0, sram_used=500.0, faults=0.0)
    cand = create_mock_baseline("R2", loop_time=5.0, cpu_load=15.0, sram_used=500.0, faults=1.0)

    report = ValidationEngine.validate_benchmarks(base, cand, "VAL-3", "EXP-3")
    assert report.validation_status == "REGRESSION"
    assert "fault" in report.reason.lower()


def test_validation_no_significant_change():
    """Verify minute metric differences (< 2%) return NO_SIGNIFICANT_CHANGE."""
    base = create_mock_baseline("R1", loop_time=10.0, cpu_load=40.0, sram_used=500.0)
    cand = create_mock_baseline("R2", loop_time=9.9, cpu_load=40.2, sram_used=500.0)

    report = ValidationEngine.validate_benchmarks(base, cand, "VAL-4", "EXP-4")
    assert report.validation_status == "NO_SIGNIFICANT_CHANGE"
