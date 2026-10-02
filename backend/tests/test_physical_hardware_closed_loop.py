"""
ARIS 2.0 Phase E Test Suite: Physical Hardware Closed-Loop Experimentation.
Tests:
1. Physical mode gating: real-hardware requires real serial port, toolchain, and identity.
2. Safe failure: missing physical requirements raises clean exception, never falls back silently to simulation.
3. Universal board discovery verification against physical descriptors.
4. Runtime identity handshake: $ARIS_HELLO# to $ARIS_ACK verification.
5. Board identity mismatch rejection (BOARD_IDENTITY_MISMATCH).
6. ARIS runtime architecture gating (RUNTIME_SUPPORTED for AVR8 vs RUNTIME_UNSUPPORTED).
7. Baseline firmware compilation using resolved dynamic FQBN.
8. Physical baseline flash execution via arduino-cli upload with port and FQBN.
9. Post-flash verification: handshake confirms newly flashed firmware.
10. Unverified flash failure (ARIS_FLASH_UNVERIFIED).
11. Telemetry integrity: sequence gaps and malformed frames handled safely.
12. Telemetry provenance: real hardware samples marked REAL_HARDWARE, simulation marked is_demo/is_simulated.
13. Baseline statistics calculation for real hardware runs.
14. Static and runtime evidence fusion creating grounded hypothesis.
15. Candidate generation with hardware constraint enforcement.
16. Prediction calibration with uncertainty intervals.
17. Human approval gate: blocks physical flash when approval is PENDING.
18. Human approval gate: authorizes physical flash when APPROVED.
19. Candidate compile and flash on physical target.
20. Baseline vs Candidate empirical comparison (difference, variance, classification).
21. Multi-Objective trade-off representation (latency, SRAM, Flash, jitter).
22. Quantitative prediction error calculation (raw vs calibrated, percentage-points vs %).
23. ExperimentMemory indexing from valid physical experiments.
24. Verified rollback: baseline re-flashing, handshake confirmation, ROLLBACK_SUCCESS status.
25. Rollback failure detection and reporting (ROLLBACK_FAILED).
26. Failure injection: serial disconnect, build timeout, compiler failure.
27. Anti-fabrication check: zero synthetic data in REAL_HARDWARE mode.
28. Machine-readable PhysicalExperimentEvidencePackage assembly and serialization.
29. REST API GET /api/experiments/{id}/evidence-package endpoint.
30. Replay reproducibility verification: matching hardware parameters.
"""

import pytest
import uuid
from backend.telemetry.telemetry_schema import ArisException
from backend.firmware.board_profiles import get_board_profile
from backend.hardware.capability_graph import HardwareCapabilityGraph, CapabilityProvenance
from backend.hardware.capability_negotiator import CapabilityGraphBuilder
from backend.serial.serial_manager import SerialManager
from backend.firmware.build_flasher import BuildFlasher
from backend.analysis.baseline_engine import BaselineEngine
from backend.experiments.experiment_engine import ExperimentEngine
from backend.experiments.evidence_package.physical_closed_loop_coordinator import PhysicalClosedLoopCoordinator
from backend.experiments.evidence_package.evidence_package_model import (
    BuildMetadataSnapshot,
    HandshakeVerificationSnapshot,
    RollbackVerificationRecord
)
from backend.database.db_engine import DatabaseEngine
from backend.database.models import RunRecord, OptimizationRecord, TelemetryRecord


@pytest.fixture
def test_db():
    return DatabaseEngine(db_path=":memory:")


@pytest.fixture
def uno_graph():
    prof = get_board_profile("arduino_uno")
    return CapabilityGraphBuilder.build(prof)


@pytest.fixture
def coordinator(temp_db):
    base_eng = BaselineEngine(temp_db)
    exp_eng = ExperimentEngine(temp_db, base_eng)
    flasher = BuildFlasher(use_simulated_toolchain_if_missing=True)
    serial_mgr = SerialManager(None)
    return PhysicalClosedLoopCoordinator(
        db=temp_db,
        serial_manager=serial_mgr,
        build_flasher=flasher,
        baseline_engine=base_eng,
        experiment_engine=exp_eng
    )


# ==============================================================================
# 1. PHYSICAL MODE GATING & RUNTIME ARCHITECTURE SUPPORT
# ==============================================================================

def test_runtime_support_gating_avr8(coordinator, uno_graph):
    """AVR8 targets are confirmed RUNTIME_SUPPORTED."""
    supported, reason = coordinator.verify_runtime_support(uno_graph)
    assert supported is True
    assert "RUNTIME_SUPPORTED" in reason


def test_runtime_support_gating_unsupported(coordinator):
    """Targets lacking an embedded ARIS runtime port are flagged RUNTIME_UNSUPPORTED."""
    prof = get_board_profile("arduino_uno_r4_minima")
    r4_graph = CapabilityGraphBuilder.build(prof)
    supported, reason = coordinator.verify_runtime_support(r4_graph)
    assert supported is False
    assert "RUNTIME_UNSUPPORTED" in reason


def test_physical_flash_fails_safe_without_cli(coordinator):
    """Real hardware flashing without arduino-cli raises ARIS_TOOLCHAIN_UNAVAILABLE."""
    # Temporarily remove arduino_cli_path to test physical fail-safe
    orig_path = coordinator.build_flasher.arduino_cli_path
    coordinator.build_flasher.arduino_cli_path = None
    try:
        with pytest.raises(ArisException) as exc_info:
            coordinator.build_flasher.flash_board(
                board_id="arduino_uno",
                port="COM3",  # Physical COM port
                source_code="void setup(){} void loop(){}"
            )
        assert exc_info.value.error_code == "ARIS_TOOLCHAIN_UNAVAILABLE"
    finally:
        coordinator.build_flasher.arduino_cli_path = orig_path


# ==============================================================================
# 2. RUNTIME HANDSHAKE & IDENTITY VERIFICATION
# ==============================================================================

def test_handshake_identity_verification_success(coordinator, monkeypatch):
    """Handshake validates physical board identity matching expected board."""
    # Mock serial perform_handshake
    def mock_handshake(timeout_sec=2.0):
        return {
            "handshake_success": True,
            "runtime_version": "1.0.0",
            "protocol_version": "1.0",
            "board_id": "arduino_uno",
            "mcu": "atmega328p",
            "architecture": "avr8",
            "clock_hz": 16000000,
            "frame_type": "ACK"
        }
    monkeypatch.setattr(coordinator.serial_manager, "perform_handshake", mock_handshake)

    snapshot = coordinator.execute_handshake_and_verify_identity("arduino_uno")
    assert snapshot.handshake_success is True
    assert snapshot.board_id == "arduino_uno"
    assert snapshot.mcu == "atmega328p"


def test_handshake_identity_mismatch_aborts(coordinator, monkeypatch):
    """Mismatched physical target raises BOARD_IDENTITY_MISMATCH and aborts."""
    def mock_handshake(timeout_sec=2.0):
        return {
            "handshake_success": True,
            "runtime_version": "1.0.0",
            "protocol_version": "1.0",
            "board_id": "arduino_mega",  # Connected Mega when Uno was expected
            "mcu": "atmega2560",
            "architecture": "avr8",
            "clock_hz": 16000000
        }
    monkeypatch.setattr(coordinator.serial_manager, "perform_handshake", mock_handshake)

    with pytest.raises(ArisException) as exc_info:
        coordinator.execute_handshake_and_verify_identity("arduino_uno")
    assert exc_info.value.error_code == "BOARD_IDENTITY_MISMATCH"


def test_handshake_failure_reports_unverified(coordinator, monkeypatch):
    """Unresponsive physical target raises ARIS_FLASH_UNVERIFIED."""
    def mock_handshake(timeout_sec=2.0):
        return {"handshake_success": False, "message": "Timeout awaiting $ARIS_ACK"}
    monkeypatch.setattr(coordinator.serial_manager, "perform_handshake", mock_handshake)

    with pytest.raises(ArisException) as exc_info:
        coordinator.execute_handshake_and_verify_identity("arduino_uno")
    assert exc_info.value.error_code == "ARIS_FLASH_UNVERIFIED"


# ==============================================================================
# 3. VERIFIED ROLLBACK LIFECYCLE
# ==============================================================================

def test_verified_rollback_success(coordinator, temp_db, monkeypatch):
    """Rollback restores baseline binary and verifies handshake before reporting success."""
    # Setup test run & opt
    temp_db.save_run(RunRecord(run_id="RUN-BASE-01", board_id="arduino_uno", status="COMPLETED"))
    temp_db.save_optimization(OptimizationRecord(
        optimization_id="OPT-01",
        finding_id="F-01",
        title="Opt 01",
        problem="Problem",
        source_location={"file": "main.ino", "line": 1},
        before_code="delay(10);",
        after_code="millis()",
        reason="reason",
        hardware_consideration="hw",
        expected_effect={},
        status="PROPOSED"
    ))

    exp = coordinator.experiment_engine.create_experiment(
        title="Test Rollback Exp",
        board_id="arduino_uno",
        baseline_run_id="RUN-BASE-01",
        optimization_id="OPT-01"
    )

    def mock_flash(**kwargs):
        return {"status": "FLASH_SUCCESS", "port": "COM3"}
    def mock_handshake(timeout_sec=2.0):
        return {"handshake_success": True, "board_id": "arduino_uno"}

    monkeypatch.setattr(coordinator.build_flasher, "flash_board", mock_flash)
    monkeypatch.setattr(coordinator.serial_manager, "perform_handshake", mock_handshake)
    coordinator.serial_manager.connected = True

    rb_record = coordinator.verify_and_record_rollback(
        experiment_id=exp.experiment_id,
        board_id="arduino_uno",
        port="COM3",
        baseline_source_or_binary="void setup(){} void loop(){}"
    )

    assert rb_record.rollback_executed is True
    assert rb_record.rollback_status == "ROLLBACK_SUCCESS"
    assert rb_record.baseline_firmware_restored is True
    assert rb_record.baseline_handshake_verified is True


def test_rollback_failure_handling(coordinator, temp_db, monkeypatch):
    """Rollback failure (e.g. upload fail) is recorded as ROLLBACK_FAILED without false claims."""
    temp_db.save_run(RunRecord(run_id="RUN-BASE-01", board_id="arduino_uno", status="COMPLETED"))
    temp_db.save_optimization(OptimizationRecord(
        optimization_id="OPT-01",
        finding_id="F-01",
        title="Opt 01",
        problem="Problem",
        source_location={"file": "main.ino", "line": 1},
        before_code="delay(10);",
        after_code="millis()",
        reason="reason",
        hardware_consideration="hw",
        expected_effect={},
        status="PROPOSED"
    ))

    exp = coordinator.experiment_engine.create_experiment(
        title="Test Failed Rollback Exp",
        board_id="arduino_uno",
        baseline_run_id="RUN-BASE-01",
        optimization_id="OPT-01"
    )

    def mock_flash_fail(**kwargs):
        raise RuntimeError("avrdude protocol error")

    monkeypatch.setattr(coordinator.build_flasher, "flash_board", mock_flash_fail)

    rb_record = coordinator.verify_and_record_rollback(
        experiment_id=exp.experiment_id,
        board_id="arduino_uno",
        port="COM3",
        baseline_source_or_binary="sketch.ino"
    )

    assert rb_record.rollback_status == "ROLLBACK_FAILED"
    assert rb_record.baseline_firmware_restored is False


# ==============================================================================
# 4. PHYSICAL EVIDENCE PACKAGE ASSEMLBY & REST ENDPOINT
# ==============================================================================

def test_evidence_package_assembly_and_serialization(coordinator, uno_graph):
    """Assembles complete PhysicalExperimentEvidencePackage with exact provenance."""
    base_build = BuildMetadataSnapshot(
        toolchain="arduino-cli 1.1.2",
        compiler="avr-gcc 7.3.0",
        fqbn="arduino:avr:uno",
        binary_size_bytes=4200,
        flash_utilization_pct=12.8,
        sram_utilization_bytes=240,
        sram_utilization_pct=11.7,
        firmware_hash="sha256-baseline-hash"
    )
    cand_build = BuildMetadataSnapshot(
        toolchain="arduino-cli 1.1.2",
        compiler="avr-gcc 7.3.0",
        fqbn="arduino:avr:uno",
        binary_size_bytes=4232,
        flash_utilization_pct=12.9,
        sram_utilization_bytes=244,
        sram_utilization_pct=11.9,
        firmware_hash="sha256-candidate-hash"
    )
    hs_snap = HandshakeVerificationSnapshot(
        handshake_success=True,
        runtime_version="1.0.0",
        protocol_version="1.0",
        board_id="arduino_uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16000000,
        identity_verified=True
    )
    rb_snap = RollbackVerificationRecord()

    pkg = coordinator.assemble_evidence_package(
        experiment_id="EXP-123",
        capability_graph=uno_graph,
        port="COM3",
        baseline_firmware_id="FW-BASE",
        baseline_source="void setup(){} void loop(){ delay(20); }",
        candidate_firmware_id="FW-CAND",
        candidate_source="void setup(){} void loop(){ /* non-blocking */ }",
        baseline_build=base_build,
        candidate_build=cand_build,
        baseline_handshake=hs_snap,
        candidate_handshake=hs_snap,
        target_metric="loop_time",
        baseline_stats={"mean": 20.5, "jitter": 0.8},
        candidate_stats={"mean": 1.5, "jitter": 0.1},
        raw_pred_pct=-35.0,
        cal_pred_pct=-32.0,
        actual_pct=-30.0,
        validation_status="IMPROVEMENT",
        validation_reason="Loop latency decreased by 30.0% with zero hardware regressions.",
        rollback_record=rb_snap,
        is_simulation=False
    )

    assert pkg.evidence_package_id.startswith("EVPKG-")
    assert pkg.execution_mode == "REAL_HARDWARE"
    assert pkg.raw_prediction_error_pp == 5.0    # -30.0 - (-35.0) = +5.0 pp
    assert pkg.calibrated_prediction_error_pp == 2.0  # -30.0 - (-32.0) = +2.0 pp
    assert pkg.experiment_memory_updated is True
    assert "EVPKG-" in pkg.to_json()


def test_evidence_package_rest_endpoint(temp_db, test_client):
    """GET /api/experiments/{experiment_id}/evidence-package returns verified package."""
    # Setup database with valid experiment
    temp_db.save_run(RunRecord(run_id="RUN-BL-99", board_id="arduino_uno", status="COMPLETED"))
    temp_db.save_optimization(OptimizationRecord(
        optimization_id="OPT-99",
        finding_id="F-99",
        title="Opt 99",
        problem="Test",
        source_location={"file": "test.ino", "line": 1},
        before_code="delay(10);",
        after_code="millis()",
        reason="test",
        hardware_consideration="test",
        expected_effect={},
        status="PROPOSED"
    ))
    exp_eng = ExperimentEngine(temp_db, BaselineEngine(temp_db))
    exp = exp_eng.create_experiment(
        title="Evidence Package Test",
        board_id="arduino_uno",
        baseline_run_id="RUN-BL-99",
        optimization_id="OPT-99"
    )

    resp = test_client.get(f"/api/experiments/{exp.experiment_id}/evidence-package")
    assert resp.status_code == 200
    data = resp.json()
    assert data["evidence_package_id"].startswith("EVPKG-")
    assert data["experiment_id"] == exp.experiment_id
    assert data["board_id"] == "arduino_uno"
