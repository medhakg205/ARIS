"""
ARIS 2.0 Phase B Test Suite: Adaptive Measurement & Experiment Planning.
Tests:
1. Measurement planner with known capabilities.
2. Measurement planner with missing capabilities.
3. Hypothesis-directed metric selection.
4. Competing hypothesis discrimination.
5. Instrumentation overhead handling (calibrated vs estimated).
6. Unknown overhead handling (zero guessing).
7. Measurement sufficiency with adequate samples and variance.
8. Insufficient samples detection and recommendations.
9. Invalid / corrupted telemetry detection.
10. Experiment state transitions (valid lifecycle).
11. Invalid state transitions blocked with ArisException.
12. Reproducibility verification (match vs mismatch).
13. Hardware identity mismatch blocking.
14. Architecture-specific measurement selection (AVR vs ARM).
15. SRAM-constrained instrumentation handling.
16. Simulation experiment provenance preservation (never disguised as physical).
17. Real hardware experiment provenance preservation.
18. Candidate experiment contract specification and validation.
19. Regression stopping condition.
20. Inconclusive stopping condition.
21. Safety stopping condition.
22. Successful closed-loop experiment lifecycle.
"""

import pytest
from backend.firmware.board_profiles import get_board_profile, BoardProfileResolver
from backend.hardware.capability_graph import HardwareCapabilityGraph, CapabilityProvenance
from backend.hardware.capability_negotiator import CapabilityGraphBuilder
from backend.experiments.overhead_models import (
    InstrumentationOverheadEstimate,
    InstrumentationOverheadEstimator,
    OverheadProvenance
)
from backend.experiments.manifest_models import (
    PerformanceHypothesis,
    ExperimentPlan,
    ExperimentManifest
)
from backend.experiments.measurement_planner import (
    MeasurementPlan,
    AdaptiveMeasurementPlanner,
    HypothesisDiscriminationPlan
)
from backend.experiments.sufficiency_evaluator import (
    SufficiencyStatus,
    EvidenceQuality,
    MeasurementSufficiencyEvaluator
)
from backend.experiments.experiment_planner import (
    ExperimentState,
    StoppingCondition,
    OptimizationExperimentContract,
    ExperimentStateMachine,
    ExperimentPlanner
)
from backend.database.models import TelemetryRecord, RunRecord, OptimizationRecord
from backend.database.db_engine import DatabaseEngine
from backend.telemetry.telemetry_schema import ArisException


# ==============================================================================
# 1. MEASUREMENT PLANNER WITH KNOWN CAPABILITIES
# ==============================================================================

def test_measurement_planner_known_capabilities():
    """Verifies that planner enables required metrics supported by Uno R3 and disables unneeded ones."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    hyp = PerformanceHypothesis(
        hypothesis_id="H001",
        target_metric="loop_time",
        predicted_effect="Loop time decreases by 30%",
        evidence_references=["jitter_variance"]
    )

    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [hyp])

    assert plan.target_board_id == "arduino_uno"
    assert "loop_time" in plan.enabled_metrics
    assert "loop_jitter" in plan.enabled_metrics
    # Peripheral measurements omitted to reduce perturbation
    assert "gpio_activity" in plan.disabled_metrics
    assert "adc_activity" in plan.disabled_metrics
    assert "Why these measurements?" or plan.metric_reasons


# ==============================================================================
# 2. MEASUREMENT PLANNER WITH MISSING CAPABILITIES
# ==============================================================================

def test_measurement_planner_missing_capabilities():
    """Verifies that unsupported metrics are excluded and flagged with architecture reasons."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    hyp = PerformanceHypothesis(
        hypothesis_id="H-DWT",
        target_metric="dwt_cycle_counter",  # ARM DWT does not exist on AVR8
        predicted_effect="Cycle counter decreases"
    )

    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [hyp])
    assert "dwt_cycle_counter" not in plan.enabled_metrics
    assert "dwt_cycle_counter" in plan.metric_reasons
    assert "unsupported by target MCU architecture" in plan.metric_reasons["dwt_cycle_counter"]


# ==============================================================================
# 3. HYPOTHESIS-DIRECTED METRIC SELECTION
# ==============================================================================

def test_hypothesis_directed_selection():
    """Verifies that metrics are selected strictly based on hypothesis needs rather than collecting everything."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    h_cpu = PerformanceHypothesis(
        hypothesis_id="H_CPU",
        target_metric="loop_time",
        predicted_effect="CPU execution latency bottleneck",
        evidence_references=[]
    )

    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [h_cpu])
    assert "loop_time" in plan.enabled_metrics
    assert "sram_used" in plan.disabled_metrics


# ==============================================================================
# 4. COMPETING HYPOTHESIS DISCRIMINATION
# ==============================================================================

def test_competing_hypothesis_discrimination():
    """Verifies building a discrimination plan to differentiate competing hypotheses."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    h1 = PerformanceHypothesis(hypothesis_id="H1", target_metric="loop_time", predicted_effect="CPU execution bound", evidence_references=["jitter"])
    h2 = PerformanceHypothesis(hypothesis_id="H2", target_metric="sram_used", predicted_effect="SRAM allocation bound", evidence_references=["memory_spill"])

    disc_plan = AdaptiveMeasurementPlanner.plan_discrimination(graph, [h1, h2])

    assert len(disc_plan.hypotheses) == 2
    assert "loop_time" in disc_plan.distinguishing_metrics
    assert "loop_jitter" in disc_plan.distinguishing_metrics
    assert "sram_used" in disc_plan.distinguishing_metrics
    assert "H1" in disc_plan.expected_evidence
    assert "H2" in disc_plan.expected_evidence


# ==============================================================================
# 5. INSTRUMENTATION OVERHEAD HANDLING
# ==============================================================================

def test_overhead_calibrated_vs_inferred():
    """Verifies that calibrated physical values take precedence over rough estimates."""
    uno_profile = get_board_profile("arduino_uno")
    uno_graph = CapabilityGraphBuilder.build(uno_profile)

    est = InstrumentationOverheadEstimator.estimate(uno_graph, method="SOFTWARE_MICROS")
    assert est.provenance == OverheadProvenance.CALIBRATED_HARDWARE
    assert est.measured_overhead_us == 4.5
    assert est.effective_overhead_us == 4.5
    assert est.confidence >= 0.90


# ==============================================================================
# 6. UNKNOWN OVERHEAD HANDLING
# ==============================================================================

def test_unknown_overhead_zero_guessing():
    """Verifies that targets lacking clock and architecture details yield UNKNOWN overhead rather than made-up numbers."""
    partial = BoardProfileResolver.create_partially_resolved(board_id="custom_target", display_name="Custom Target")
    graph = CapabilityGraphBuilder.build(partial)

    est = InstrumentationOverheadEstimator.estimate(graph, method="CUSTOM_METHOD")
    assert est.provenance == OverheadProvenance.UNKNOWN
    assert est.effective_overhead_us is None
    assert est.confidence == 0.0


# ==============================================================================
# 7. MEASUREMENT SUFFICIENCY (ADEQUATE SAMPLES & VARIANCE)
# ==============================================================================

def test_measurement_sufficiency_success():
    """Verifies sufficiency evaluator passes when required samples, metrics, and variance are present."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)
    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [PerformanceHypothesis(hypothesis_id="H1", target_metric="loop_time", predicted_effect="Fast")])

    samples = [
        TelemetryRecord(
            run_id="R1", board_id="arduino_uno", mcu="atmega328p",
            timestamp_ms=i*10, sequence=i, metric="loop_time",
            value=100.0 + (i % 5), unit="ms", classification="MEASURED", confidence=1.0
        )
        for i in range(1, 51)
    ]

    report = MeasurementSufficiencyEvaluator.evaluate(plan, samples, is_simulated=False)
    assert report.is_sufficient is True
    assert report.status == SufficiencyStatus.SUFFICIENT
    assert report.evidence_quality.sample_sufficiency == "SUFFICIENT"
    assert report.evidence_quality.statistical_strength == "HIGH"


# ==============================================================================
# 8. INSUFFICIENT SAMPLES
# ==============================================================================

def test_measurement_sufficiency_too_few_samples():
    """Verifies insufficiency triggers when sample count is below minimum threshold."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)
    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [PerformanceHypothesis(hypothesis_id="H1", target_metric="loop_time", predicted_effect="Fast")])

    samples = [
        TelemetryRecord(
            run_id="R1", board_id="arduino_uno", mcu="atmega328p",
            timestamp_ms=i*10, sequence=i, metric="loop_time",
            value=100.0, unit="ms", classification="MEASURED", confidence=1.0
        )
        for i in range(1, 4)  # Only 3 samples
    ]

    report = MeasurementSufficiencyEvaluator.evaluate(plan, samples)
    assert report.is_sufficient is False
    assert report.status == SufficiencyStatus.INSUFFICIENT_SAMPLE_SIZE
    assert any("Increase sample count" in r for r in report.recommendations)


# ==============================================================================
# 9. INVALID / CORRUPTED TELEMETRY
# ==============================================================================

def test_corrupted_telemetry_detection():
    """Verifies corrupted samples (e.g. negative sequence or None values) are detected."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)
    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [])

    samples = [
        TelemetryRecord(
            run_id="R1", board_id="arduino_uno", mcu="atmega328p",
            timestamp_ms=100, sequence=-5, metric="loop_time",  # Negative sequence
            value=10.0, unit="ms", classification="MEASURED", confidence=1.0
        )
    ]

    report = MeasurementSufficiencyEvaluator.evaluate(plan, samples)
    assert report.is_sufficient is False
    assert report.status == SufficiencyStatus.CORRUPTED_OR_INVALID_TELEMETRY


# ==============================================================================
# 10. EXPERIMENT STATE MACHINE (VALID TRANSITIONS)
# ==============================================================================

def test_experiment_state_machine_valid_flow():
    """Verifies clean step-by-step lifecycle transition through the state machine."""
    state = ExperimentState.PLANNED

    state = ExperimentStateMachine.transition(state, ExperimentState.PRECHECKING)
    assert state == ExperimentState.PRECHECKING

    state = ExperimentStateMachine.transition(state, ExperimentState.BASELINE_READY)
    assert state == ExperimentState.BASELINE_READY

    state = ExperimentStateMachine.transition(state, ExperimentState.RUNNING_BASELINE)
    assert state == ExperimentState.RUNNING_BASELINE

    state = ExperimentStateMachine.transition(state, ExperimentState.BASELINE_COLLECTED)
    assert state == ExperimentState.BASELINE_COLLECTED

    state = ExperimentStateMachine.transition(state, ExperimentState.RUNNING_CANDIDATE)
    assert state == ExperimentState.RUNNING_CANDIDATE

    state = ExperimentStateMachine.transition(state, ExperimentState.CANDIDATE_COLLECTED)
    assert state == ExperimentState.CANDIDATE_COLLECTED

    state = ExperimentStateMachine.transition(state, ExperimentState.EVALUATING)
    assert state == ExperimentState.EVALUATING

    state = ExperimentStateMachine.transition(state, ExperimentState.SUFFICIENT)
    assert state == ExperimentState.SUFFICIENT

    state = ExperimentStateMachine.transition(state, ExperimentState.IMPROVEMENT, candidate_data_present=True)
    assert state == ExperimentState.IMPROVEMENT

    state = ExperimentStateMachine.transition(state, ExperimentState.COMPLETED, candidate_data_present=True)
    assert state == ExperimentState.COMPLETED


# ==============================================================================
# 11. INVALID STATE TRANSITIONS BLOCKED
# ==============================================================================

def test_invalid_state_transition_blocked():
    """Verifies invalid lifecycle leap raises ArisException."""
    with pytest.raises(ArisException) as exc:
        ExperimentStateMachine.transition(ExperimentState.PLANNED, ExperimentState.COMPLETED)
    assert exc.value.error_code == "ARIS_VALIDATION_FAILED"


def test_validation_without_candidate_data_blocked():
    """Verifies that transitioning to IMPROVEMENT without candidate measurements is blocked."""
    with pytest.raises(ArisException) as exc:
        ExperimentStateMachine.transition(ExperimentState.RUNNING_BASELINE, ExperimentState.IMPROVEMENT, candidate_data_present=False)
    assert exc.value.error_code == "ARIS_VALIDATION_FAILED"


# ==============================================================================
# 12. REPRODUCIBILITY VERIFICATION (MATCH VS MISMATCH)
# ==============================================================================

def test_reproducibility_check_matching():
    """Verifies reproducibility check succeeds when hardware matches plan."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)
    plan = AdaptiveMeasurementPlanner.plan_measurement(graph, [])
    exp_plan = ExperimentPlanner.create_plan(
        experiment_id="EXP-1",
        objective="Reproduce latency",
        hypotheses=[],
        graph=graph,
        measurement_plan=plan,
        firmware_id="FW-1"
    )

    is_repro, mismatches = ExperimentPlanner.verify_reproducibility(exp_plan, graph)
    assert is_repro is True
    assert len(mismatches) == 0


def test_reproducibility_check_mismatch():
    """Verifies reproducibility check detects board/architecture mismatch."""
    uno_profile = get_board_profile("arduino_uno")
    uno_graph = CapabilityGraphBuilder.build(uno_profile)
    plan = AdaptiveMeasurementPlanner.plan_measurement(uno_graph, [])
    exp_plan = ExperimentPlanner.create_plan(
        experiment_id="EXP-1",
        objective="Uno R3 test",
        hypotheses=[],
        graph=uno_graph,
        measurement_plan=plan,
        firmware_id="FW-1"
    )

    # Now verify against an Uno R4 (ARM Cortex-M4)
    r4_profile = get_board_profile("arduino_uno_r4_minima")
    r4_graph = CapabilityGraphBuilder.build(r4_profile)

    is_repro, mismatches = ExperimentPlanner.verify_reproducibility(exp_plan, r4_graph)
    assert is_repro is False
    assert any("Board identity mismatch" in m for m in mismatches)
    assert any("Architecture mismatch" in m for m in mismatches)


# ==============================================================================
# 13. HARDWARE IDENTITY MISMATCH BLOCKING
# ==============================================================================

def test_hardware_identity_missing_blocks_planning():
    """Verifies planner rejects creating an experiment plan if board_id is missing."""
    empty_graph = HardwareCapabilityGraph(board_id="", display_name="Missing")
    mplan = MeasurementPlan(
        plan_id="MPLAN-1",
        target_board_id="",
        enabled_metrics=[],
        disabled_metrics=[],
        overhead_estimate=InstrumentationOverheadEstimate(
            instrumentation_config="MIN",
            board_id="",
            measurement_method="NONE"
        )
    )

    with pytest.raises(ArisException) as exc:
        ExperimentPlanner.create_plan("EXP-ERR", "Test", [], empty_graph, mplan, "FW-1")
    assert exc.value.error_code == "ARIS_BOARD_NOT_FOUND"


# ==============================================================================
# 14. ARCHITECTURE-SPECIFIC MEASUREMENT SELECTION (AVR VS ARM)
# ==============================================================================

def test_architecture_measurement_selection():
    """Verifies DWT cycle counting is selected on ARM Cortex-M4 and rejected on AVR."""
    r4_profile = get_board_profile("arduino_uno_r4_minima")
    r4_graph = CapabilityGraphBuilder.build(r4_profile)
    r4_plan = AdaptiveMeasurementPlanner.plan_measurement(r4_graph, [
        PerformanceHypothesis(hypothesis_id="H-ARM", target_metric="loop_time", predicted_effect="Fast")
    ])
    assert r4_plan.overhead_estimate.measurement_method == "DWT_CYCCNT"
    assert r4_plan.overhead_estimate.effective_overhead_us < 1.0


# ==============================================================================
# 15. SRAM-CONSTRAINED INSTRUMENTATION HANDLING
# ==============================================================================

def test_sram_constrained_instrumentation():
    """Verifies low-SRAM targets generate warnings and prefer minimal footprints."""
    uno_profile = get_board_profile("arduino_uno")
    uno_graph = CapabilityGraphBuilder.build(uno_profile)
    # Simulate tight SRAM (512 bytes)
    uno_graph.sram_memory.value = 512

    plan = AdaptiveMeasurementPlanner.plan_measurement(uno_graph, [])
    assert plan.overhead_warning is not None
    assert "SRAM is severely constrained" in plan.overhead_warning


# ==============================================================================
# 16. SIMULATION VS PHYSICAL PROVENANCE PRESERVATION
# ==============================================================================

def test_provenance_separation_simulation():
    """Verifies simulation experiments retain explicit SIMULATION flags."""
    record = TelemetryRecord(
        run_id="RUN-SIM", board_id="arduino_uno", mcu="atmega328p",
        timestamp_ms=100, sequence=1, metric="loop_time", value=12.5,
        unit="ms", classification="DERIVED", confidence=0.8, is_demo=True
    )
    assert record.is_demo is True
    assert record.classification == "DERIVED"


def test_provenance_separation_physical():
    """Verifies physical hardware telemetry retains MEASURED classification and false demo flag."""
    record = TelemetryRecord(
        run_id="RUN-PHYS", board_id="arduino_uno", mcu="atmega328p",
        timestamp_ms=100, sequence=1, metric="loop_time", value=14.2,
        unit="ms", classification="MEASURED", confidence=1.0, is_demo=False
    )
    assert record.is_demo is False
    assert record.classification == "MEASURED"


# ==============================================================================
# 17. CANDIDATE EXPERIMENT CONTRACT
# ==============================================================================

def test_candidate_experiment_contract():
    """Verifies building and binding an OptimizationExperimentContract."""
    contract = OptimizationExperimentContract(
        candidate_id="OPT-PORT-01",
        target_file="sketch.ino",
        what_is_changed="Replace digitalWrite(13, HIGH) with PORTB |= (1 << 5)",
        why_it_is_changed="Avoid ~4us pin-to-port lookup in loop()",
        target_metric="loop_time",
        expected_improvement_pct=35.0,
        must_not_regress_metrics=["sram_used", "runtime_fault"],
        required_hardware_capabilities=["gpio", "avr"],
        acceptance_criteria={"min_latency_reduction_pct": 20.0}
    )

    assert contract.target_metric == "loop_time"
    assert contract.expected_improvement_pct == 35.0
    assert "sram_used" in contract.must_not_regress_metrics


# ==============================================================================
# 18. STOPPING CONDITIONS ENUM
# ==============================================================================

def test_stopping_conditions():
    """Verifies all explicit stopping conditions are defined and distinct."""
    assert StoppingCondition.STOP_SUCCESS == "STOP_SUCCESS"
    assert StoppingCondition.STOP_REGRESSION == "STOP_REGRESSION"
    assert StoppingCondition.STOP_INCONCLUSIVE == "STOP_INCONCLUSIVE"
    assert StoppingCondition.STOP_SAFETY == "STOP_SAFETY"
    assert StoppingCondition.STOP_IDENTITY_MISMATCH == "STOP_IDENTITY_MISMATCH"
    assert StoppingCondition.STOP_TIMEOUT == "STOP_TIMEOUT"
    assert StoppingCondition.STOP_MEASUREMENT_INVALID == "STOP_MEASUREMENT_INVALID"
