"""
ARIS Major End-to-End System Integration Test.
Formally verifies the entire closed-loop ARIS architectural pipeline:
Simulator
   ↓
Telemetry Ingestion
   ↓
Backend Database
   ↓
Static Firmware Analysis
   ↓
Static + Runtime Correlation
   ↓
AI Interface
   ↓
Optimization Candidate
   ↓
Experiment Engine
   ↓
Empirical Validation
"""

import pytest
import time
from backend.simulator.simulated_hardware import SimulatedHardware
from backend.telemetry.telemetry_ingestor import TelemetryIngestor
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.analysis.baseline_engine import BaselineEngine
from backend.correlation.correlation_engine import CorrelationEngine
from backend.analysis.ai_interface import AIInterface
from backend.experiments.experiment_engine import ExperimentEngine
from backend.database.models import RunRecord, FirmwareRecord


def test_full_pipeline_end_to_end(temp_db):
    """
    Executes the full closed-loop pipeline test:
    Simulator -> Telemetry -> Backend -> Analysis -> Correlation -> AI -> Optimization -> Experiment -> Validation.
    """
    print("\n--- STEP 1: INITIALIZE CORE SUBSYSTEMS ---")
    ingestor = TelemetryIngestor(temp_db)
    simulator = SimulatedHardware(ingestor, board_id="arduino_uno")
    static_analyzer = StaticAnalyzer(default_board_id="arduino_uno")
    baseline_engine = BaselineEngine(temp_db)
    experiment_engine = ExperimentEngine(temp_db, baseline_engine)

    print("\n--- STEP 2: FIRMWARE & BASELINE RUN SETUP ---")
    sample_sketch = """
    void setup() {
        pinMode(13, OUTPUT);
        Serial.begin(115200);
    }
    void loop() {
        digitalWrite(13, HIGH);
        delay(50);
        digitalWrite(13, LOW);
        delay(50);
    }
    """
    fw = FirmwareRecord(
        firmware_id="FW-E2E-001",
        name="BlinkDelayE2E",
        source_code=sample_sketch
    )
    temp_db.save_firmware(fw)

    baseline_run_id = "ARIS-RUN-BASELINE"
    temp_db.save_run(RunRecord(
        run_id=baseline_run_id,
        board_id="arduino_uno",
        firmware_id=fw.firmware_id,
        status="RUNNING",
        is_simulated=True,
        is_demo=True
    ))

    print("\n--- STEP 3: SIMULATE RUNTIME TELEMETRY (BASELINE) ---")
    # Simulate unoptimized execution with 100ms blocking delay
    simulator.set_board("arduino_uno")
    simulator.set_mode("blocking_delay", delay_ms=100)
    simulator.run_id = baseline_run_id

    # Emit 10 snapshots into the ingestion pipeline
    for _ in range(10):
        snapshots = simulator.generate_telemetry_snapshot()
        for sample in snapshots:
            ingestor._validate_and_store_sample(sample)

    assert ingestor.total_packets_valid >= 200
    telemetry_items = temp_db.get_telemetry_by_run(baseline_run_id)
    assert len(telemetry_items) >= 200

    print("\n--- STEP 4: STATIC ANALYSIS ---")
    static_res = static_analyzer.analyze_source(sample_sketch, board_id="arduino_uno")
    assert static_res.function_count == 2
    assert any(f.rule_id == "ARIS-001" for f in static_res.findings)
    delay_finding = next(f for f in static_res.findings if f.rule_id == "ARIS-001")

    print("\n--- STEP 5: BASELINE GENERATION ---")
    baseline = baseline_engine.generate_baseline(baseline_run_id, min_samples_required=5)
    assert "loop_time" in baseline.metrics
    assert baseline.metrics["loop_time"].mean >= 90.0

    print("\n--- STEP 6: STATIC + RUNTIME CORRELATION ---")
    correlated_findings = CorrelationEngine.correlate(static_res.findings, baseline)
    corr_finding = next(f for f in correlated_findings if f.rule_id == "ARIS-001")
    assert corr_finding.runtime_correlation == "HIGH"
    assert corr_finding.confidence >= 0.95
    assert "runtime_loop_time_mean_ms" in corr_finding.evidence

    print("\n--- STEP 7: AI INTERFACE & CANDIDATE SYNTHESIS ---")
    ai_context = AIInterface.build_context(
        board_profile=simulator.profile.to_dict(),
        firmware_source=sample_sketch,
        static_findings=[f.model_dump() for f in static_res.findings],
        runtime_metrics={k: v.mean for k, v in baseline.metrics.items()},
        baseline_metrics={k: v.model_dump() for k, v in baseline.metrics.items()},
        runtime_static_correlations=[f.model_dump() for f in correlated_findings]
    )
    assert len(ai_context.runtime_static_correlations) >= 1

    candidate = AIInterface.generate_candidate_for_finding(
        finding=corr_finding.model_dump(),
        source_code=sample_sketch,
        board_id="arduino_uno"
    )
    assert candidate.status == "PROPOSED"
    assert "millis()" in candidate.after_code

    # Store candidate
    from backend.database.models import OptimizationRecord
    opt_record = OptimizationRecord(
        optimization_id=candidate.optimization_id,
        finding_id=candidate.finding_id,
        run_id=baseline_run_id,
        title=candidate.title,
        problem=candidate.problem,
        source_location=candidate.source_location,
        before_code=candidate.before_code,
        after_code=candidate.after_code,
        reason=candidate.reason,
        hardware_consideration=candidate.hardware_consideration,
        expected_effect=candidate.expected_effect,
        risk=candidate.risk,
        confidence=candidate.confidence,
        validation_required=candidate.validation_required,
        status="APPROVED"  # Simulate user approval
    )
    temp_db.save_optimization(opt_record)

    print("\n--- STEP 8: EXPERIMENT SETUP ---")
    experiment = experiment_engine.create_experiment(
        title="E2E Delay Elimination Experiment",
        board_id="arduino_uno",
        baseline_run_id=baseline_run_id,
        optimization_id=candidate.optimization_id
    )

    print("\n--- STEP 9: CANDIDATE RUN (OPTIMIZED SIMULATION) ---")
    cand_run_id = "ARIS-RUN-CANDIDATE"
    temp_db.save_run(RunRecord(
        run_id=cand_run_id,
        board_id="arduino_uno",
        status="RUNNING",
        is_simulated=True,
        is_demo=True
    ))

    # Switch simulator to optimized mode (< 2ms loop latency)
    simulator.set_mode("optimized")
    simulator.run_id = cand_run_id
    for _ in range(10):
        snapshots = simulator.generate_telemetry_snapshot()
        for sample in snapshots:
            ingestor._validate_and_store_sample(sample)

    experiment_engine.bind_candidate_run(experiment.experiment_id, cand_run_id)

    print("\n--- STEP 10: CLOSED-LOOP VALIDATION & DECISION ---")
    validation_report = experiment_engine.validate_experiment(experiment.experiment_id)

    assert validation_report.validation_status in ["VALIDATED", "PARTIALLY_VALIDATED"]
    assert validation_report.percentage_change["loop_time"] <= -90.0

    # Verify persistent states
    stored_exp = experiment_engine.get_experiment(experiment.experiment_id)
    assert stored_exp.status == "COMPLETED"
    assert stored_exp.validation_id is not None

    stored_opt = temp_db.get_optimization(candidate.optimization_id)
    assert stored_opt.status == "VALIDATED"

    print("\n>>> FULL PIPELINE E2E INTEGRATION TEST PASSED WITH 100% SUCCESS! <<<")
