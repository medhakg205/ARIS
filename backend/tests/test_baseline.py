"""
Unit tests for ARIS Baseline Engine.
Verifies:
- Statistical calculation: mean, median, min, max, variance, jitter
- Multiple sample aggregation
- Minimum sample threshold enforcement
"""

import pytest
from backend.analysis.baseline_engine import BaselineEngine
from backend.database.models import RunRecord, TelemetryRecord
from backend.telemetry.telemetry_schema import ArisException


def test_baseline_generation(temp_db):
    """Verify mean, median, min, max, variance, and jitter calculations."""
    eng = BaselineEngine(temp_db)

    # 1. Create run
    run_id = "ARIS-TEST-BASE"
    temp_db.save_run(RunRecord(run_id=run_id, board_id="arduino_uno", status="RUNNING"))

    # 2. Insert telemetry series for loop_time: [10.0, 12.0, 11.0, 9.0, 13.0]
    values = [10.0, 12.0, 11.0, 9.0, 13.0]
    for i, v in enumerate(values, 1):
        temp_db.save_telemetry_sample(TelemetryRecord(
            protocol_version="1.0",
            run_id=run_id,
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=100 * i,
            sequence=i,
            metric="loop_time",
            value=v,
            unit="ms",
            classification="MEASURED",
            confidence=1.0
        ))

    base = eng.generate_baseline(run_id, min_samples_required=3)
    assert base.run_id == run_id
    assert "loop_time" in base.metrics

    stats = base.metrics["loop_time"]
    assert stats.sample_count == 5
    assert stats.mean == 11.0
    assert stats.median == 11.0
    assert stats.minimum == 9.0
    assert stats.maximum == 13.0
    assert stats.variance == 2.5
    assert stats.jitter > 0.0


def test_baseline_insufficient_samples_raises(temp_db):
    """Verify baseline generation raises ARIS_VALIDATION_FAILED on empty run."""
    eng = BaselineEngine(temp_db)
    run_id = "ARIS-EMPTY"
    temp_db.save_run(RunRecord(run_id=run_id, board_id="arduino_uno", status="RUNNING"))

    with pytest.raises(ArisException) as exc:
        eng.generate_baseline(run_id, min_samples_required=10)
    assert exc.value.error_code == "ARIS_VALIDATION_FAILED"
