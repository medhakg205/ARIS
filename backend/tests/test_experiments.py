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
from backend.simulator.simulated_hardware import SimulatedHardware


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


def test_simulated_runs_flow_through_ingestion_baseline_and_experiment_validation(temp_db, ingestor):
    """Simulated baseline and candidate telemetry use the real provenance and validation pipeline."""
    baseline_run_id = "ARIS-SIM-BASELINE"
    candidate_run_id = "ARIS-SIM-CANDIDATE"
    optimization_id = "OPT-SIM-PIPELINE"

    temp_db.save_run(RunRecord(
        run_id=baseline_run_id,
        board_id="arduino_uno",
        status="COMPLETED",
        is_simulated=True,
        is_demo=True,
    ))
    temp_db.save_run(RunRecord(
        run_id=candidate_run_id,
        board_id="arduino_uno",
        status="COMPLETED",
        is_simulated=True,
        is_demo=True,
    ))
    temp_db.save_optimization(OptimizationRecord(
        optimization_id=optimization_id,
        finding_id="FIND-SIM-PIPELINE",
        run_id=baseline_run_id,
        title="Replace blocking delay",
        problem="Blocking delay",
        source_location={"file": "main.ino", "line": 42},
        before_code="delay(100);",
        after_code="millis() timer",
        reason="Frees MCU time for concurrent work.",
        hardware_consideration="Preserves AVR timer availability.",
        expected_effect={"loop_time_delta_ms": -98.0},
        risk="LOW",
        confidence=0.9,
        validation_required=True,
        status="PROPOSED",
    ))

    baseline_engine = BaselineEngine(temp_db)
    experiment_engine = ExperimentEngine(temp_db, baseline_engine)
    experiment = experiment_engine.create_experiment(
        title="Simulated candidate validation",
        board_id="arduino_uno",
        baseline_run_id=baseline_run_id,
        optimization_id=optimization_id,
    )

    simulator = SimulatedHardware(ingestor, board_id="arduino_uno")
    simulator.set_mode("blocking_delay", delay_ms=100)
    simulator.run_id = baseline_run_id
    for sample in simulator.generate_telemetry_snapshot():
        assert ingestor._validate_and_store_sample(sample) is True

    baseline_samples = temp_db.get_telemetry_by_run(baseline_run_id)
    assert baseline_samples
    assert all(sample.is_demo for sample in baseline_samples)

    simulator.set_mode("optimized")
    simulator.run_id = candidate_run_id
    for sample in simulator.generate_telemetry_snapshot():
        assert ingestor._validate_and_store_sample(sample) is True

    candidate_samples = temp_db.get_telemetry_by_run(candidate_run_id)
    assert candidate_samples
    assert all(sample.is_demo for sample in candidate_samples)

    experiment_engine.bind_candidate_run(experiment.experiment_id, candidate_run_id)
    report = experiment_engine.validate_experiment(experiment.experiment_id)

    baseline_run = temp_db.get_run(baseline_run_id)
    candidate_run = temp_db.get_run(candidate_run_id)
    completed_experiment = experiment_engine.get_experiment(experiment.experiment_id)
    validation_result = temp_db.get_validation_result(completed_experiment.validation_id)

    assert baseline_run is not None and baseline_run.baseline_id is not None
    assert candidate_run is not None and candidate_run.baseline_id is not None
    assert completed_experiment.status == "COMPLETED"
    assert completed_experiment.validation_id is not None
    assert validation_result is not None
    assert validation_result.validation_status == report.validation_status
    assert report.validation_status in {
        "VALIDATED",
        "PARTIALLY_VALIDATED",
        "NO_SIGNIFICANT_CHANGE",
        "REGRESSION",
        "REJECTED",
        "INCONCLUSIVE",
    }
    assert all(sample.is_demo for sample in baseline_samples)
    assert all(sample.is_demo for sample in candidate_samples)


def test_rollback_experiment(temp_db):
    """Verify that rollback transitions experiment, candidate run, and optimization candidate to ROLLED_BACK."""
    base_eng = BaselineEngine(temp_db)
    exp_eng = ExperimentEngine(temp_db, base_eng)

    base_run_id = "ARIS-ROLLBACK-BASE"
    temp_db.save_run(RunRecord(run_id=base_run_id, board_id="arduino_uno", status="COMPLETED"))

    opt_id = "OPT-ROLLBACK-01"
    temp_db.save_optimization(OptimizationRecord(
        optimization_id=opt_id,
        finding_id="FIND-001",
        run_id=base_run_id,
        title="Candidate to rollback",
        problem="Test bottleneck",
        source_location={"file": "main.ino", "line": 10},
        before_code="delay(50);",
        after_code="millis();",
        reason="Test",
        hardware_consideration="None",
        expected_effect={"latency_delta_ms": -45.0},
        status="PROPOSED"
    ))

    exp = exp_eng.create_experiment(
        title="Rollback Test Experiment",
        board_id="arduino_uno",
        baseline_run_id=base_run_id,
        optimization_id=opt_id
    )

    cand_run_id = "ARIS-ROLLBACK-CAND"
    temp_db.save_run(RunRecord(run_id=cand_run_id, board_id="arduino_uno", status="RUNNING"))
    exp_eng.bind_candidate_run(exp.experiment_id, cand_run_id)

    # Trigger rollback
    result = exp_eng.rollback_experiment(exp.experiment_id)
    assert result["status"] == "ROLLED_BACK"

    # Verify persistent states
    updated_exp = temp_db.get_experiment(exp.experiment_id)
    assert updated_exp.status == "ROLLED_BACK"

    updated_cand_run = temp_db.get_run(cand_run_id)
    assert updated_cand_run.status == "ROLLED_BACK"

    updated_opt = temp_db.get_optimization(opt_id)
    assert updated_opt.status == "ROLLED_BACK"

