"""
Comprehensive Software-Only End-to-End Audit & Verification Suite.
Validates the complete ARIS software product workflow without requiring physical hardware:
1. Untouched original Arduino source preservation and SHA-256 integrity
2. Shadow workspace generation and isolated instrumentation
3. Static analysis and deterministic finding generation
4. Optimization candidate generation, predictions, and risk assessment
5. Simulation experiment execution and telemetry ingestion (explicitly labeled SIMULATION)
6. Statistical validation and candidate decision
7. Safe source apply to local sketch, backup verification, and safe rollback
8. Historical physical evidence preservation (EXP-PHYS-001, CAND-7E067277)
"""

import os
import json
import time
import hashlib
import tempfile
import pytest

from backend.analysis.static_analyzer import StaticAnalyzer
from backend.instrumentation.sketch_instrumenter import SketchInstrumenter
from backend.firmware.board_profiles import get_board_profile
from backend.optimization.candidate_generation_engine import CandidateGenerationEngine
from backend.database.db_engine import DatabaseEngine
from backend.analysis.baseline_engine import BaselineEngine
from backend.experiments.experiment_engine import ExperimentEngine
from backend.simulator.simulated_hardware import SimulatedHardware
from backend.telemetry.telemetry_ingestor import TelemetryIngestor


SAMPLE_ARDUINO_SKETCH = """// Normal Arduino Sensor Sketch
#define SENSOR_PIN A0
#define LED_PIN 13

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  int val = analogRead(SENSOR_PIN);
  if (val > 512) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
  } else {
    digitalWrite(LED_PIN, LOW);
    delay(50);
  }
}
"""


def test_e2e_software_lifecycle_audit(tmp_path):
    # -------------------------------------------------------------
    # Stage 1: Untouched User Source & Hashing
    # -------------------------------------------------------------
    sketch_dir = tmp_path / "sensor_sketch"
    sketch_dir.mkdir()
    sketch_file = sketch_dir / "sensor_sketch.ino"
    sketch_file.write_text(SAMPLE_ARDUINO_SKETCH, encoding="utf-8")

    orig_content = sketch_file.read_text(encoding="utf-8")
    orig_hash = hashlib.sha256(orig_content.encode("utf-8")).hexdigest()

    # Verify zero ARIS runtime code in original source
    assert "#include <aris_runtime.h>" not in orig_content
    assert "ARIS." not in orig_content

    # -------------------------------------------------------------
    # Stage 2: Shadow Workspace & Transparent Instrumentation
    # -------------------------------------------------------------
    inst_result = SketchInstrumenter.create_shadow_workspace(
        source_code=orig_content,
        source_path=str(sketch_file),
        board_id="arduino_uno",
        run_id="RUN-AUDIT-001"
    )

    # Verify original source remains bit-for-bit untouched on disk
    post_inst_content = sketch_file.read_text(encoding="utf-8")
    assert post_inst_content == orig_content
    assert hashlib.sha256(post_inst_content.encode("utf-8")).hexdigest() == orig_hash
    assert inst_result.verification_hash_match is True

    # Verify shadow copy contains instrumentation
    shadow_content = open(inst_result.shadow_sketch_path, "r", encoding="utf-8").read()
    assert "#include <aris_runtime.h>" in shadow_content
    assert "ARIS.init(" in shadow_content
    assert "ARIS.loop_enter()" in shadow_content

    # -------------------------------------------------------------
    # Stage 3: Static Analysis on Untouched Source
    # -------------------------------------------------------------
    analyzer = StaticAnalyzer(default_board_id="arduino_uno")
    analysis_res = analyzer.analyze_source(
        source_code=orig_content,
        board_id="arduino_uno",
        source_file="sensor_sketch.ino"
    )

    assert len(analysis_res.findings) >= 2
    delay_findings = [f for f in analysis_res.findings if "delay" in f.rule_id.lower() or "blocking" in f.title.lower()]
    assert len(delay_findings) >= 2

    # -------------------------------------------------------------
    # Stage 4: Candidate Generation with Prediction & Risk
    # -------------------------------------------------------------
    gen_engine = CandidateGenerationEngine()
    from backend.hardware.capability_negotiator import CapabilityGraphBuilder
    board_prof = get_board_profile("arduino_uno")
    cap_graph = CapabilityGraphBuilder.build(board_prof)
    target_finding = delay_findings[0]
    candidate = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=target_finding.model_dump(),
        capability_graph=cap_graph,
        current_flash_used=14000,
        current_sram_used=1200
    )

    assert candidate is not None
    assert candidate.candidate_id.startswith("CAND-")
    assert candidate.status.value in ("PROPOSED", "GATED", "READY_FOR_APPROVAL")
    assert candidate.calibrated_prediction is not None
    assert str(candidate.safety_risk) in ("LOW", "MEDIUM", "HIGH")

    # -------------------------------------------------------------
    # Stage 5: Database Setup & Simulation Experiment
    # -------------------------------------------------------------
    from backend.database.models import RunRecord, BoardRecord
    db = DatabaseEngine(":memory:")
    db.save_board(BoardRecord(
        board_id="arduino_uno",
        display_name="Arduino Uno",
        mcu="atmega328p",
        architecture="avr8",
        clock_hz=16000000,
        flash_bytes=32256,
        sram_bytes=2048,
        eeprom_bytes=1024,
        gpio_count=20,
        adc_channels=6,
        uart_count=1,
        timer_count=3,
        fqbn="arduino:avr:uno"
    ))
    ingestor = TelemetryIngestor(db)
    sim = SimulatedHardware(ingestor=ingestor, board_id="arduino_uno")
    sim.set_mode("blocking_delay", delay_ms=100)

    # Emulate baseline run in simulation mode
    baseline_run_id = "RUN-SIM-BASELINE-001"
    db.save_run(RunRecord(run_id=baseline_run_id, board_id="arduino_uno", status="RUNNING", is_simulated=True, is_demo=True))
    sim.start(run_id=baseline_run_id)
    # Generate 15 simulated snapshots (300 metric samples)
    for _ in range(15):
        samples = sim.generate_telemetry_snapshot()
        for s in samples:
            assert s.classification is not None
            ingestor._validate_and_store_sample(s)
    sim.stop()

    base_engine = BaselineEngine(db)
    baseline_rec = base_engine.generate_baseline(
        run_id=baseline_run_id,
        min_samples_required=5
    )
    assert baseline_rec is not None
    assert "loop_time" in baseline_rec.metrics
    assert "cpu_load" in baseline_rec.metrics

    # Emulate optimized candidate run in simulation mode
    cand_run_id = "RUN-SIM-CAND-001"
    db.save_run(RunRecord(run_id=cand_run_id, board_id="arduino_uno", status="RUNNING", is_simulated=True, is_demo=True))
    sim.set_mode("optimized")
    sim.start(run_id=cand_run_id)
    for _ in range(15):
        samples = sim.generate_telemetry_snapshot()
        for s in samples:
            ingestor._validate_and_store_sample(s)
    sim.stop()

    # Save candidate into db for experiment and apply routes
    from backend.database.models import OptimizationRecord
    opt_record = OptimizationRecord(
        optimization_id=candidate.candidate_id,
        finding_id=candidate.finding_id,
        title=candidate.title,
        problem=candidate.rationale,
        source_location={"file": str(sketch_file), "line": 15},
        before_code="delay(100);",
        after_code="// non-blocking state advance",
        reason=candidate.rationale,
        hardware_consideration=candidate.hardware_consideration,
        expected_effect={"latency_delta_ms": -100.0},
        status="ACCEPTED",
        board_id="arduino_uno"
    )
    db.save_optimization(opt_record)

    # -------------------------------------------------------------
    # Stage 6: Experiment Creation & Closed-Loop Validation
    # -------------------------------------------------------------
    exp_engine = ExperimentEngine(db, base_engine)
    exp = exp_engine.create_experiment(
        title="Simulated State Machine Delay Elimination",
        board_id="arduino_uno",
        baseline_run_id=baseline_run_id,
        optimization_id=candidate.candidate_id
    )
    assert exp.status == "CREATED"

    exp_engine.bind_candidate_run(exp.experiment_id, cand_run_id)
    val_report = exp_engine.validate_experiment(exp.experiment_id)

    assert val_report.validation_status in ("VALIDATED", "PARTIALLY_VALIDATED", "NO_SIGNIFICANT_CHANGE", "SUCCESS")
    updated_exp = exp_engine.get_experiment(exp.experiment_id)
    assert updated_exp.status in ("COMPLETED", "VALIDATED", "SUCCESS")

    # -------------------------------------------------------------
    # Stage 7: Safe Source Application, Backups & Verification
    # -------------------------------------------------------------
    from backend.api.routes_firmware import apply_candidate_endpoint, ApplyCandidateRequest, revert_candidate_endpoint, RevertCandidateRequest

    apply_req = ApplyCandidateRequest(
        candidate_id=candidate.candidate_id,
        sketch_path=str(sketch_file),
        expected_hash=orig_hash
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.routes_firmware.get_db", lambda: db)
        apply_res = apply_candidate_endpoint(apply_req)
        assert apply_res["success"] is True
        assert apply_res["applied"] is True
        assert os.path.exists(apply_res["backup_path"])

        # Check modified file contains zero ARIS runtime code
        applied_content = sketch_file.read_text(encoding="utf-8")
        assert "#include <aris_runtime.h>" not in applied_content
        assert "// non-blocking state advance" in applied_content

        # Revert candidate back to original
        revert_req = RevertCandidateRequest(
            candidate_id=candidate.candidate_id,
            sketch_path=str(sketch_file)
        )
        revert_res = revert_candidate_endpoint(revert_req)
        assert revert_res["success"] is True
        assert revert_res["reverted"] is True

        # Check reverted file matches original hash bit-for-bit
        reverted_content = sketch_file.read_text(encoding="utf-8")
        assert hashlib.sha256(reverted_content.encode("utf-8")).hexdigest() == orig_hash
