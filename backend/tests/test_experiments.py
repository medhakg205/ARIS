"""
Unit tests for ARIS Closed-Loop Experiment Engine.
Verifies:
- Experiment creation tying baseline run to optimization candidate
- Retention of both baseline and candidate data
- Closed-loop execution lifecycle
"""

import pytest
from backend.experiments.experiment_engine import ExperimentEngine
from backend.analysis.baseline_engine import BaselineEngine
from backend.database.models import RunRecord, OptimizationRecord, TelemetryRecord


def test_closed_loop_experiment_lifecycle(temp_db):
    """Verify closed-loop experiment workflow from baseline to validation."""
    base_eng = BaselineEngine(temp_db)
    exp_eng = ExperimentEngine(temp_db, base_eng)

    # 1. Setup baseline run with samples
    base_run_id = "ARIS-BASE-RUN"
    temp_db.save_run(RunRecord(run_id=base_run_id, board_id="arduino_uno", status="COMPLETED"))
    for i in range(1, 10):
        temp_db.save_telemetry_sample(TelemetryRecord(
            protocol_version="1.0",
            run_id=base_run_id,
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=i * 100,
            sequence=i,
            metric="loop_time",
            value=100.0,
            unit="ms",
            classification="MEASURED",
            confidence=1.0
        ))

    # 2. Setup optimization candidate
    opt_id = "OPT-001"
    temp_db.save_optimization(OptimizationRecord(
        optimization_id=opt_id,
        finding_id="FIND-001",
        run_id=base_run_id,
        title="Remove delay",
        problem="Blocking delay",
        source_location={"file": "main.ino", "line": 42},
        before_code="delay(100);",
        after_code="millis() timer",
        reason="Frees MCU",
        hardware_consideration="Restores timers",
        expected_effect={"loop_time_delta_ms": -98.0},
        risk="LOW",
        confidence=0.9,
        validation_required=True,
        status="PROPOSED"
    ))

    # 3. Create experiment
    exp = exp_eng.create_experiment(
        title="Test Delay Elimination",
        board_id="arduino_uno",
        baseline_run_id=base_run_id,
        optimization_id=opt_id
    )
    assert exp.status == "CREATED"
    assert exp.baseline_run_id == base_run_id

    # 4. Setup candidate run with optimized samples
    cand_run_id = "ARIS-CAND-RUN"
    temp_db.save_run(RunRecord(run_id=cand_run_id, board_id="arduino_uno", status="COMPLETED"))
    for i in range(1, 10):
        temp_db.save_telemetry_sample(TelemetryRecord(
            protocol_version="1.0",
            run_id=cand_run_id,
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=i * 100,
            sequence=i,
            metric="loop_time",
            value=2.0,  # Improved loop time!
            unit="ms",
            classification="MEASURED",
            confidence=1.0
        ))

    # 5. Bind candidate and validate
    exp_eng.bind_candidate_run(exp.experiment_id, cand_run_id)
    report = exp_eng.validate_experiment(exp.experiment_id)

    assert report.validation_status in ["VALIDATED", "PARTIALLY_VALIDATED"]
    assert report.percentage_change["loop_time"] <= -90.0

    # 6. Verify optimization candidate transitioned to VALIDATED
    updated_opt = temp_db.get_optimization(opt_id)
    assert updated_opt.status == "VALIDATED"
