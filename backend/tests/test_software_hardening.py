"""
Tests for Phase H software hardening passes:
1. Canonical error codes coverage for ARIS_FLASH_UNVERIFIED and ARIS_BOARD_IDENTITY_MISMATCH.
2. verify_upload rejecting empty/blank port strings.
3. Candidate generation engine tracking missing peripherals and failing hardware constraints.
4. save_ide_sketch endpoint rejecting non-sketch file extensions (.exe, .py, etc.).
5. ExperimentEngine state machine transitions rejecting illegal operations on completed experiments.
"""

import os
import pytest
from backend.telemetry.telemetry_schema import CANONICAL_ERROR_CODES, ArisErrorResponse
from backend.firmware.build_flasher import BuildFlasher
from backend.hardware.capability_graph import (
    HardwareCapabilityGraph,
    CapabilityItem,
    CapabilityProvenance
)
from backend.optimization.candidate_generation_engine import CandidateGenerationEngine
from backend.api.routes_firmware import save_ide_sketch, SaveIDESketchRequest
from backend.database.db_engine import DatabaseEngine
from backend.analysis.baseline_engine import BaselineEngine
from backend.experiments.experiment_engine import ExperimentEngine
from backend.telemetry.telemetry_schema import ArisException
from backend.database.models import RunRecord, OptimizationRecord


def test_canonical_error_codes_includes_new_codes():
    assert "ARIS_FLASH_UNVERIFIED" in CANONICAL_ERROR_CODES
    assert "ARIS_BOARD_IDENTITY_MISMATCH" in CANONICAL_ERROR_CODES

    err = ArisErrorResponse(
        error_code="ARIS_FLASH_UNVERIFIED",
        message="Flash could not be verified on target MCU."
    )
    assert err.error_code == "ARIS_FLASH_UNVERIFIED"

    err2 = ArisErrorResponse(
        error_code="ARIS_BOARD_IDENTITY_MISMATCH",
        message="Physical board identity does not match experiment plan."
    )
    assert err2.error_code == "ARIS_BOARD_IDENTITY_MISMATCH"


def test_verify_upload_empty_port_returns_false():
    flasher = BuildFlasher()
    # Empty string or None must return False, not True
    assert flasher.verify_upload(board_id="uno", port="") is False
    assert flasher.verify_upload(board_id="uno", port=None) is False
    # Mock / simulated ports must return True
    assert flasher.verify_upload(board_id="uno", port="SIMULATED") is True
    assert flasher.verify_upload(board_id="uno", port="COM_MOCK") is True


def test_candidate_generation_missing_peripheral_fails_constraint():
    # Build a capability graph without timers peripheral
    graph = HardwareCapabilityGraph(
        board_id="uno",
        display_name="Arduino Uno",
        fqbn="arduino:avr:uno",
        architecture="avr8",
        mcu="atmega328p",
        clock=CapabilityItem(name="clock", available=True, value=16000000, unit="Hz"),
        flash_memory=CapabilityItem(name="flash_memory", available=True, value=32256, unit="bytes"),
        sram_memory=CapabilityItem(name="sram_memory", available=True, value=2048, unit="bytes"),
        timers=CapabilityItem(name="timers", available=False)  # Timers explicitly unavailable
    )

    finding = {
        "finding_id": "FIND-TIME-01",
        "rule_id": "ARIS-001",  # Requires 'timers'
        "evidence": {"duration": 50},
        "source_file": "test.ino",
        "source_line": 42
    }
    candidate = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=finding,
        capability_graph=graph
    )
    assert candidate is not None
    # Candidate should fail hardware constraint checks because timers peripheral is missing/unavailable
    assert candidate.hardware_constraint_checks_passed is False
    assert candidate.status.value in ("REJECTED_UNSUPPORTED", "UNSUPPORTED_ON_TARGET", "BLOCKED_HARDWARE")


def test_save_ide_sketch_extension_validation(tmp_path):
    bad_file = tmp_path / "malicious.py"
    bad_file.write_text("print('hello')", encoding="utf-8")

    req = SaveIDESketchRequest(
        path=str(bad_file),
        source_code="print('evil')"
    )
    res = save_ide_sketch(req)
    assert res["success"] is False
    assert "Invalid sketch file extension" in res["error"]

    good_file = tmp_path / "sketch.ino"
    good_file.write_text("void setup() {}", encoding="utf-8")

    req2 = SaveIDESketchRequest(
        path=str(good_file),
        source_code="void setup() { /* updated */ }"
    )
    res2 = save_ide_sketch(req2)
    assert res2["success"] is True
    assert os.path.exists(res2["backup_path"])
    assert "/* updated */" in good_file.read_text(encoding="utf-8")


def test_experiment_engine_transition_validation(temp_db):
    base_engine = BaselineEngine(temp_db)
    exp_engine = ExperimentEngine(temp_db, base_engine)

    # Setup dummy baseline run & optimization record
    base_run = RunRecord(
        run_id="RUN-BASE-01",
        board_id="arduino_uno",
        status="COMPLETED"
    )
    cand_run = RunRecord(
        run_id="RUN-CAND-01",
        board_id="arduino_uno",
        status="COMPLETED"
    )
    temp_db.save_run(base_run)
    temp_db.save_run(cand_run)

    from backend.database.models import TelemetryRecord
    for i in range(1, 10):
        temp_db.save_telemetry_sample(TelemetryRecord(
            protocol_version="1.0",
            run_id="RUN-BASE-01",
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
        temp_db.save_telemetry_sample(TelemetryRecord(
            protocol_version="1.0",
            run_id="RUN-CAND-01",
            board_id="arduino_uno",
            mcu="atmega328p",
            timestamp_ms=i * 100,
            sequence=i,
            metric="loop_time",
            value=2.0,
            unit="ms",
            classification="MEASURED",
            confidence=1.0
        ))

    opt = OptimizationRecord(
        optimization_id="OPT-01",
        finding_id="FIND-01",
        run_id="RUN-BASE-01",
        title="Test Optimization",
        problem="Test Problem",
        source_location={"file": "main.ino", "line": 1},
        before_code="delay(10);",
        after_code="millis()",
        reason="Speed",
        hardware_consideration="None",
        expected_effect={"loop_time_delta_ms": -10.0},
        risk="LOW",
        confidence=0.9,
        validation_required=True,
        status="PROPOSED"
    )
    temp_db.save_optimization(opt)

    exp = exp_engine.create_experiment(
        title="Test Exp",
        board_id="arduino_uno",
        baseline_run_id="RUN-BASE-01",
        optimization_id="OPT-01"
    )
    assert exp.status == "CREATED"

    # Bind candidate run
    exp = exp_engine.bind_candidate_run(exp.experiment_id, "RUN-CAND-01")
    assert exp.status == "RUNNING"

    # Validate experiment
    report = exp_engine.validate_experiment(exp.experiment_id)
    assert report is not None
    updated_exp = exp_engine.get_experiment(exp.experiment_id)
    assert updated_exp.status == "COMPLETED"

    # Attempting to re-validate completed experiment should raise ArisException
    with pytest.raises(ArisException) as exc_info:
        exp_engine.validate_experiment(exp.experiment_id)
    assert exc_info.value.error_code == "ARIS_VALIDATION_FAILED"
    assert "already completed" in exc_info.value.message

    # Attempting to re-bind candidate to completed experiment should raise ArisException
    with pytest.raises(ArisException) as exc_info2:
        exp_engine.bind_candidate_run(exp.experiment_id, "RUN-CAND-01")
    assert exc_info2.value.error_code == "ARIS_VALIDATION_FAILED"
    assert "already COMPLETED" in exc_info2.value.message


def test_simulation_evidence_never_contaminates_physical_calibration():
    """
    Mathematical proof that simulated experiment records cannot alter
    physical prediction calibration or generate false physical confidence.
    """
    from backend.experiments.experiment_memory import ExperimentMemory
    from backend.experiments.calibration_models import (
        ExperimentMemoryRecord,
        CalibrationMatchLevel,
        CalibrationQualityStatus
    )
    from backend.experiments.prediction_calibrator import PredictionCalibrator
    from backend.firmware.board_profiles import get_board_profile
    from backend.hardware.capability_negotiator import CapabilityGraphBuilder

    memory = ExperimentMemory()
    sim_rec = ExperimentMemoryRecord(
        memory_id="MEM-SIM-01",
        experiment_id="EXP-SIM-01",
        candidate_id="CAND-01",
        board_id="arduino_uno",
        mcu="atmega328p",
        architecture="avr8",
        optimization_category="GPIO",
        target_metric="loop_time",
        predicted_delta_pct=-50.0,
        actual_delta_pct=-20.0,
        signed_error_pp=30.0,
        validation_status="VALIDATED",
        telemetry_provenance="SIMULATED"
    )
    memory.add_record(sim_rec)

    prof = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(prof)

    # 1. Hierarchical retrieval with default include_simulation=False must find 0 records
    match_lvl, records = memory.retrieve_hierarchical(
        graph=graph,
        optimization_category="GPIO",
        target_metric="loop_time",
        include_simulation=False
    )
    assert match_lvl == CalibrationMatchLevel.NONE
    assert len(records) == 0

    # 2. Calibration must yield NO_EVIDENCE and leave raw prediction unaltered
    cal_delta, lower, upper, quality, prov = PredictionCalibrator.calibrate_prediction(
        raw_prediction_delta_pct=-50.0,
        target_metric="loop_time",
        optimization_category="GPIO",
        graph=graph,
        memory=memory,
        include_simulation=False
    )
    assert quality.status == CalibrationQualityStatus.NO_EVIDENCE
    assert cal_delta == -50.0
    assert prov is None

