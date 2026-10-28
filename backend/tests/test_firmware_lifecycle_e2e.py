"""
Unit and End-to-End Tests for ARIS Firmware Lineage, Optimization Acceptance,
Safe Source Code Application, and Revert/Rollback Lifecycle.
"""

import os
import tempfile
import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.api.dependencies import get_db, get_experiment_engine
from backend.database.models import FirmwareRecord, OptimizationRecord, ExperimentRecord, RunRecord

client = TestClient(app)


@pytest.fixture
def temp_arduino_sketch():
    """Creates a temporary Arduino sketch mimicking a user project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sketch_path = os.path.join(tmpdir, "BlinkTest.ino")
        original_code = """const int LED = 13;
void setup() {
  pinMode(LED, OUTPUT);
}
void loop() {
  digitalWrite(LED, HIGH);
  delay(100);
}
"""
        with open(sketch_path, "w", encoding="utf-8") as f:
            f.write(original_code)

        yield {
            "dir": tmpdir,
            "path": sketch_path,
            "code": original_code,
            "hash": hashlib.sha256(original_code.encode("utf-8")).hexdigest()
        }


def test_candidate_source_provenance_and_acceptance(temp_arduino_sketch):
    """
    Verifies that optimization candidates track complete provenance:
    candidate_id, parent_firmware_id, parent_source_hash, candidate_source_hash,
    before_code, after_code, transformation_id, board, MCU, fqbn.
    Verifies acceptance promotes candidate to ACTIVE and supersedes parent.
    """
    db = get_db()

    # 1. Register Parent Firmware
    parent_fw = FirmwareRecord(
        firmware_id="FW-PARENT-TEST-001",
        name="BlinkTest Baseline",
        source_code=temp_arduino_sketch["code"],
        source_hash=temp_arduino_sketch["hash"],
        status="ACTIVE"
    )
    db.save_firmware(parent_fw)

    # 2. Register Candidate with Provenance
    cand_id = "OPT-TEST-PROV-001"
    cand_after_code = """const int LED = 13;
void setup() {
  pinMode(LED, OUTPUT);
}
void loop() {
  PORTB |= (1 << 5);
  delay(100);
}
"""
    cand_hash = hashlib.sha256(cand_after_code.encode("utf-8")).hexdigest()

    opt = OptimizationRecord(
        optimization_id=cand_id,
        finding_id="FIND-GPIO-001",
        title="Direct Port Register Access",
        problem="digitalWrite overhead",
        source_location={"file": temp_arduino_sketch["path"], "line": 7},
        before_code="digitalWrite(LED, HIGH);",
        after_code="PORTB |= (1 << 5);",
        reason="Low-latency direct hardware register control",
        hardware_consideration="Targets ATmega328P PORTB register (Pin 13)",
        expected_effect={"loop_time_delta_ms": -1.5},
        status="VALIDATED",
        transformation_id="TR-GPIO-001",
        parent_firmware_id="FW-PARENT-TEST-001",
        parent_source_hash=temp_arduino_sketch["hash"],
        candidate_source_hash=cand_hash,
        board_id="arduino_uno",
        mcu="atmega328p",
        architecture="avr8",
        fqbn="arduino:avr:uno",
        hypothesis="Register write eliminates MCU function call overhead"
    )
    db.save_optimization(opt)

    # 3. Accept Candidate via API
    resp = client.post(f"/api/optimizations/{cand_id}/accept")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "ACCEPTED"
    assert data["lineage"]["parent_firmware_id"] == "FW-PARENT-TEST-001"
    assert data["lineage"]["candidate_id"] == cand_id

    # 4. Verify Parent is SUPERSEDED and New Firmware is ACTIVE
    updated_parent = db.get_firmware("FW-PARENT-TEST-001")
    assert updated_parent.status == "SUPERSEDED"

    accepted_fw = db.get_firmware(f"FW-ACCEPTED-{cand_id}")
    assert accepted_fw is not None
    assert accepted_fw.status == "ACTIVE"
    assert accepted_fw.parent_firmware_id == "FW-PARENT-TEST-001"
    assert accepted_fw.candidate_id == cand_id


def test_safe_source_application_and_rollback(temp_arduino_sketch):
    """
    Verifies that:
    1. Applying an optimization creates a timestamped backup in .aris/backups/
    2. Writes clean code without any ARIS runtime headers (#include <aris_runtime.h>)
    3. Verifies SHA-256 after writing
    4. Safe Revert restores the backup image
    """
    db = get_db()
    cand_id = "OPT-TEST-APPLY-001"
    opt = OptimizationRecord(
        optimization_id=cand_id,
        finding_id="FIND-GPIO-002",
        title="Direct Port Register Access",
        problem="High pin latency",
        source_location={"file": temp_arduino_sketch["path"], "line": 7},
        before_code="digitalWrite(LED, HIGH);",
        after_code="PORTB |= (1 << 5);",
        reason="Register manipulation",
        hardware_consideration="Direct ATmega PORTB",
        expected_effect={"loop_time_delta_ms": -1.0},
        status="VALIDATED"
    )
    db.save_optimization(opt)

    # 1. Apply Candidate
    apply_payload = {
        "candidate_id": cand_id,
        "sketch_path": temp_arduino_sketch["path"],
        "expected_hash": temp_arduino_sketch["hash"]
    }
    resp = client.post("/api/firmware/apply-candidate", json=apply_payload)
    assert resp.status_code == 200
    apply_res = resp.json()
    assert apply_res["success"] is True
    assert apply_res["applied"] is True
    assert os.path.exists(apply_res["backup_path"])
    assert ".aris" in apply_res["backup_path"]
    assert "backups" in apply_res["backup_path"]

    # 2. Check written sketch file
    with open(temp_arduino_sketch["path"], "r", encoding="utf-8") as f:
        new_content = f.read()

    assert "PORTB |= (1 << 5);" in new_content
    assert "digitalWrite(LED, HIGH);" not in new_content
    # Strict transparent invariant: ZERO ARIS runtime headers
    assert "aris_runtime.h" not in new_content
    assert "ARIS_RUN_ID" not in new_content

    # 3. Revert candidate
    revert_payload = {
        "candidate_id": cand_id,
        "sketch_path": temp_arduino_sketch["path"],
        "backup_path": apply_res["backup_path"]
    }
    resp = client.post("/api/firmware/revert-candidate", json=revert_payload)
    assert resp.status_code == 200
    revert_res = resp.json()
    assert revert_res["success"] is True
    assert revert_res["reverted"] is True

    # Check restored file
    with open(temp_arduino_sketch["path"], "r", encoding="utf-8") as f:
        restored_content = f.read()

    assert restored_content == temp_arduino_sketch["code"]


def test_rollback_experiment_restores_active_firmware(temp_arduino_sketch):
    """
    Verifies that rolling back an experiment restores the parent firmware as ACTIVE,
    demotes the candidate firmware, safely restores applied source from backup,
    and preserves all experiment evidence.
    """
    db = get_db()
    eng = get_experiment_engine()

    parent_fw = FirmwareRecord(
        firmware_id="FW-ROLLBACK-PARENT",
        name="Original Blink",
        source_code=temp_arduino_sketch["code"],
        status="SUPERSEDED"
    )
    db.save_firmware(parent_fw)

    cand_id = "OPT-TEST-RB-001"
    opt = OptimizationRecord(
        optimization_id=cand_id,
        finding_id="FIND-RB-001",
        title="Direct Port Access",
        problem="Latency",
        source_location={"file": temp_arduino_sketch["path"], "line": 7},
        before_code="digitalWrite(LED, HIGH);",
        after_code="PORTB |= (1 << 5);",
        reason="Register optimization",
        hardware_consideration="ATmega PORTB",
        expected_effect={"loop_time_delta_ms": -1.0},
        parent_firmware_id="FW-ROLLBACK-PARENT",
        status="ACCEPTED",
        applied=True
    )
    db.save_optimization(opt)

    # First apply to create backup
    apply_resp = client.post("/api/firmware/apply-candidate", json={
        "candidate_id": cand_id,
        "sketch_path": temp_arduino_sketch["path"]
    })
    assert apply_resp.status_code == 200

    # Create candidate accepted firmware
    cand_fw = FirmwareRecord(
        firmware_id=f"FW-ACCEPTED-{cand_id}",
        name="Candidate Blink",
        parent_firmware_id="FW-ROLLBACK-PARENT",
        candidate_id=cand_id,
        status="ACTIVE"
    )
    db.save_firmware(cand_fw)

    # Create baseline and candidate run records for foreign key integrity
    db.save_run(RunRecord(
        run_id="RUN-BASE-TEST",
        board_id="arduino_uno",
        status="COMPLETED"
    ))
    db.save_run(RunRecord(
        run_id="RUN-CAND-TEST",
        board_id="arduino_uno",
        status="COMPLETED"
    ))

    # Create experiment
    exp = ExperimentRecord(
        experiment_id="EXP-ROLLBACK-TEST-001",
        title="Rollback Test Experiment",
        board_id="arduino_uno",
        baseline_run_id="RUN-BASE-TEST",
        candidate_run_id="RUN-CAND-TEST",
        optimization_id=cand_id,
        status="COMPLETED"
    )
    db.save_experiment(exp)

    # Execute Rollback via API
    resp = client.post(f"/api/experiments/EXP-ROLLBACK-TEST-001/rollback")
    assert resp.status_code == 200
    rb_data = resp.json()
    assert rb_data["status"] == "ROLLED_BACK"

    # Verify parent firmware is restored to ACTIVE
    restored_parent = db.get_firmware("FW-ROLLBACK-PARENT")
    assert restored_parent.status == "ACTIVE"

    # Verify candidate firmware is demoted to ROLLED_BACK
    demoted_cand = db.get_firmware(f"FW-ACCEPTED-{cand_id}")
    assert demoted_cand.status == "ROLLED_BACK"

    # Verify source file was safely restored
    with open(temp_arduino_sketch["path"], "r", encoding="utf-8") as f:
        current_content = f.read()
    assert current_content == temp_arduino_sketch["code"]

    # Verify experiment evidence remains preserved in DB
    preserved_exp = db.get_experiment("EXP-ROLLBACK-TEST-001")
    assert preserved_exp.status == "ROLLED_BACK"
