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
from backend.telemetry.telemetry_schema import ArisException, TelemetrySample
from backend.simulator.simulated_hardware import SimulatedHardware


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


def test_simulated_telemetry_uses_ingestion_pipeline_and_preserves_demo_provenance(temp_db, ingestor):
    """Simulator telemetry is stored as demo data before BaselineEngine aggregates it."""
    run_id = "ARIS-DEMO-BASELINE"
    temp_db.save_run(RunRecord(
        run_id=run_id,
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=True,
        is_demo=True,
    ))

    simulator = SimulatedHardware(ingestor, board_id="arduino_uno")
    simulator.run_id = run_id
    for sample in simulator.generate_telemetry_snapshot():
        ingestor._validate_and_store_sample(sample)

    stored_samples = temp_db.get_telemetry_by_run(run_id)
    assert len(stored_samples) == 20
    assert all(sample.is_demo for sample in stored_samples)

    physical_run_id = "ARIS-PHYSICAL-INGEST"
    temp_db.save_run(RunRecord(
        run_id=physical_run_id,
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=False,
        is_demo=False,
    ))
    ingestor._validate_and_store_sample(TelemetrySample(
        protocol_version="1.0",
        run_id=physical_run_id,
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=100,
        sequence=1,
        metric="loop_time",
        value=10.0,
        unit="ms",
        classification="MEASURED",
        confidence=1.0,
    ))
    physical_samples = temp_db.get_telemetry_by_run(physical_run_id)
    assert len(physical_samples) == 1
    assert physical_samples[0].is_demo is False

    baseline = BaselineEngine(temp_db).generate_baseline(run_id, min_samples_required=5)
    assert baseline.run_id == run_id
    assert "loop_time" in baseline.metrics


def test_unknown_run_telemetry_is_rejected_without_creating_physical_provenance(temp_db, ingestor):
    """Unknown run telemetry is rejected instead of being implicitly classified as physical."""
    run_id = "ARIS-UNKNOWN-TELEMETRY"
    received_samples = []
    ingestor.subscribe(received_samples.append)

    accepted = ingestor._validate_and_store_sample(TelemetrySample(
        protocol_version="1.0",
        run_id=run_id,
        board_id="arduino_uno",
        mcu="atmega328p",
        timestamp_ms=100,
        sequence=1,
        metric="loop_time",
        value=10.0,
        unit="ms",
        classification="MEASURED",
        confidence=1.0,
    ))

    assert accepted is False
    assert temp_db.get_run(run_id) is None
    assert temp_db.get_telemetry_by_run(run_id) == []
    assert received_samples == []
    assert ingestor.total_packets_valid == 0
    assert ingestor.total_packets_rejected == 1
    assert ingestor.last_error is not None
    assert ingestor.last_error.startswith("ARIS_TELEMETRY_INVALID:")


def test_synthetic_run_with_insufficient_samples_does_not_generate_telemetry(temp_db):
    """Baseline generation reports missing simulator evidence instead of fabricating it."""
    run_id = "ARIS-DEMO-INSUFFICIENT"
    temp_db.save_run(RunRecord(
        run_id=run_id,
        board_id="arduino_uno",
        status="COMPLETED",
        is_simulated=True,
        is_demo=True,
    ))

    with pytest.raises(ArisException) as exc:
        BaselineEngine(temp_db).generate_baseline(run_id, min_samples_required=5)

    assert exc.value.error_code == "ARIS_VALIDATION_FAILED"
    assert exc.value.details == {
        "run_id": run_id,
        "sample_count": 0,
        "min_required": 5,
    }
    assert temp_db.get_telemetry_by_run(run_id) == []
