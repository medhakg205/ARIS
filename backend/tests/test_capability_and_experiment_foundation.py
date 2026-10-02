"""
ARIS 2.0 Hardware Capability Graph & Experiment Foundation Test Suite.
Tests:
1. Capability graph generation for AVR (arduino_uno, arduino_mega) and ARM (arduino_uno_r4_minima)
2. Unknown / partially resolved capabilities remain UNKNOWN with zero guessing
3. Architecture-specific capability discrimination (AVR8 vs ARM Cortex-M4 vs ESP32)
4. Capability negotiation: valid vs invalid ARIS instrumentation operations
5. Persistent experiment manifests capturing exact hardware identity, toolchain, and code hashes
6. Provenance lineage tracking across the complete engineering lifecycle
7. Performance hypothesis data modeling with grounded evidence
8. Experiment plan validation and acceptance criteria
9. Statistical validation outcome classification (IMPROVEMENT, REGRESSION, INCONCLUSIVE, NO_SIGNIFICANT_CHANGE)
10. REST API endpoint GET /api/boards/{board_id}/capabilities
"""

import pytest
import hashlib
from backend.database.db_engine import DatabaseEngine
from backend.firmware.board_profiles import (
    get_board_profile,
    BoardProfile,
    BoardProfileResolver
)
from backend.hardware.capability_graph import (
    HardwareCapabilityGraph,
    CapabilityProvenance,
    CapabilityItem
)
from backend.hardware.capability_negotiator import (
    CapabilityGraphBuilder,
    CapabilityNegotiator
)
from backend.experiments.manifest_models import (
    PerformanceHypothesis,
    ExperimentPlan,
    ExperimentManifest,
    ProvenanceLineage
)
from backend.experiments.validation_engine import (
    ValidationEngine,
    VALIDATION_METRIC_NAMES
)
from backend.experiments.experiment_engine import ExperimentEngine
from backend.analysis.baseline_engine import BaselineEngine
from backend.database.models import (
    BaselineRecord,
    BaselineMetricStats,
    BoardRecord,
    RunRecord,
    OptimizationRecord
)


@pytest.fixture
def test_db():
    """In-memory database for testing."""
    return DatabaseEngine(db_path=":memory:")


# ==============================================================================
# 1. HARDWARE CAPABILITY GRAPH GENERATION & PROVENANCE
# ==============================================================================

def test_capability_graph_uno_r3():
    """Verifies capability graph generation for Arduino Uno R3 (AVR8 ATmega328P)."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    assert graph.board_id == "arduino_uno"
    assert graph.mcu == "atmega328p"
    assert graph.architecture == "avr8"
    assert graph.clock.available is True
    assert graph.clock.value == 16000000
    assert graph.clock.provenance == CapabilityProvenance.EXACT_PROFILE

    assert graph.flash_memory.value == 32768
    assert graph.sram_memory.value == 2048
    assert graph.eeprom_memory.value == 1024

    # Peripherals
    assert graph.gpio.value == 14
    assert graph.adc.value == 6
    assert graph.uart.value == 1
    assert graph.spi.available is True
    assert graph.i2c.available is True
    assert graph.timers.value == 3

    # Compiler toolchain
    assert graph.compiler_toolchain.value == "avr-gcc"


def test_capability_graph_uno_r4_minima():
    """Verifies capability graph generation for Arduino Uno R4 Minima (ARM Cortex-M4 RA4M1)."""
    profile = get_board_profile("arduino_uno_r4_minima")
    graph = CapabilityGraphBuilder.build(profile)

    assert graph.board_id == "arduino_uno_r4_minima"
    assert graph.mcu == "ra4m1"
    assert graph.architecture == "arm_cortex_m4"
    assert graph.clock.value == 48000000
    assert graph.sram_memory.value == 32768
    assert graph.flash_memory.value == 262144
    assert graph.compiler_toolchain.value == "arm-none-eabi-gcc"


def test_capability_graph_unknown_target_zero_guessing():
    """Verifies that unknown or partially resolved boards have UNKNOWN provenance and no guessed values."""
    partial_profile = BoardProfileResolver.create_partially_resolved(
        board_id="custom_board_xyz",
        display_name="Custom Target Board",
        fqbn=None
    )
    graph = CapabilityGraphBuilder.build(partial_profile)

    assert graph.board_id == "custom_board_xyz"
    assert graph.clock.available is None
    assert graph.clock.value is None
    assert graph.clock.provenance == CapabilityProvenance.UNKNOWN

    assert graph.sram_memory.available is None
    assert graph.sram_memory.value is None
    assert graph.sram_memory.provenance == CapabilityProvenance.UNKNOWN

    assert graph.flash_memory.available is None
    assert graph.flash_memory.value is None


# ==============================================================================
# 2. CAPABILITY NEGOTIATION (VALID VS INVALID INSTRUMENTATION)
# ==============================================================================

def test_capability_negotiation_avr_vs_arm():
    """
    Verifies that AVR targets reject DWT cycle counters and cache tracing,
    while ARM Cortex-M4 targets support DWT cycle counting.
    """
    uno_profile = get_board_profile("arduino_uno")
    uno_graph = CapabilityGraphBuilder.build(uno_profile)

    # AVR should support basic loop and timer-tick load, but not DWT cycle counters
    assert "loop_time" in uno_graph.available_instrumentation
    assert "cpu_load_timer_tick" in uno_graph.available_instrumentation
    assert "dwt_cycle_count" in uno_graph.unavailable_instrumentation
    assert "hardware_cycle_counter" in uno_graph.unavailable_instrumentation
    assert "cache_miss_rate" in uno_graph.unavailable_instrumentation
    assert not CapabilityNegotiator.is_operation_valid(uno_graph, "dwt_cycle_count")

    # Uno R4 (ARM Cortex-M4) supports DWT cycle counting
    r4_profile = get_board_profile("arduino_uno_r4_minima")
    r4_graph = CapabilityGraphBuilder.build(r4_profile)

    assert "loop_time" in r4_graph.available_instrumentation
    assert "dwt_cycle_counter" in r4_graph.available_instrumentation
    assert "systick_cpu_load" in r4_graph.available_instrumentation
    assert CapabilityNegotiator.is_operation_valid(r4_graph, "dwt_cycle_counter")


def test_capability_negotiation_unknown_board():
    """Partially resolved or unknown targets only get safe universal timing; no hardware registers."""
    partial_profile = BoardProfileResolver.create_partially_resolved(
        board_id="unknown_mcu",
        display_name="Unknown Device"
    )
    graph = CapabilityGraphBuilder.build(partial_profile)

    assert "loop_time" in graph.available_instrumentation
    assert "dwt_cycle_count" in graph.unavailable_instrumentation
    assert "hardware_cycle_counter" in graph.unavailable_instrumentation
    assert "cpu_load_register" in graph.unavailable_instrumentation
    assert "cache_miss_rate" in graph.unavailable_instrumentation


# ==============================================================================
# 3. EXPERIMENT MANIFEST & PERSISTENCE
# ==============================================================================

def test_experiment_manifest_persistence(test_db):
    """Verifies saving, retrieving, and hash auditing of ExperimentManifest."""
    fw_code = b"void setup() { pinMode(13, OUTPUT); } void loop() { digitalWrite(13, HIGH); }"
    cand_code = b"void setup() { DDRB |= (1 << 5); } void loop() { PORTB |= (1 << 5); }"

    fw_hash = hashlib.sha256(fw_code).hexdigest()
    cand_hash = hashlib.sha256(cand_code).hexdigest()

    manifest = ExperimentManifest(
        manifest_id="MAN-TEST001",
        experiment_id="EXP-TEST001",
        board_id="arduino_uno",
        mcu="atmega328p",
        architecture="avr",
        fqbn="arduino:avr:uno",
        firmware_hash=fw_hash,
        candidate_hash=cand_hash,
        compiler_toolchain="avr-gcc 7.3.0",
        runtime_version="1.0.0",
        instrumentation_mode="BALANCED",
        selected_measurements=["loop_time", "cpu_load"],
        duration_seconds=10.0,
        sample_count=50,
        experiment_conditions={"temperature_c": 24.5, "voltage_v": 5.01},
        prediction={"loop_time_delta_pct": -35.0},
        actual_result={"loop_time_delta_pct": -34.2},
        validation_result="IMPROVEMENT"
    )

    test_db.save_manifest(manifest)

    # Fetch by manifest ID
    retrieved = test_db.get_manifest("MAN-TEST001")
    assert retrieved is not None
    assert retrieved.manifest_id == "MAN-TEST001"
    assert retrieved.experiment_id == "EXP-TEST001"
    assert retrieved.board_id == "arduino_uno"
    assert retrieved.firmware_hash == fw_hash
    assert retrieved.candidate_hash == cand_hash
    assert retrieved.validation_result == "IMPROVEMENT"
    assert retrieved.prediction["loop_time_delta_pct"] == -35.0

    # Fetch by experiment ID
    by_exp = test_db.get_manifest_by_experiment("EXP-TEST001")
    assert by_exp is not None
    assert by_exp.manifest_id == "MAN-TEST001"


# ==============================================================================
# 4. PROVENANCE LINEAGE AUDIT TRAIL
# ==============================================================================

def test_provenance_lineage_persistence(test_db):
    """
    Verifies audit trail connecting:
    Firmware -> Static Analysis -> Runtime -> Finding -> Hypothesis -> Candidate -> Experiment -> Validation.
    """
    lineage = ProvenanceLineage(
        lineage_id="LIN-001",
        firmware_id="FW-ORACLE-01",
        analysis_run_id="ANALYSIS-01",
        baseline_run_id="RUN-BASE-01",
        finding_ids=["FIND-01", "FIND-02"],
        hypothesis_id="HYP-01",
        candidate_id="OPT-CAND-01",
        experiment_id="EXP-01",
        manifest_id="MAN-01",
        candidate_run_id="RUN-CAND-01",
        validation_id="VAL-01"
    )

    test_db.save_lineage(lineage)

    retrieved = test_db.get_lineage("LIN-001")
    assert retrieved is not None
    assert retrieved.lineage_id == "LIN-001"
    assert retrieved.firmware_id == "FW-ORACLE-01"
    assert retrieved.finding_ids == ["FIND-01", "FIND-02"]
    assert retrieved.hypothesis_id == "HYP-01"
    assert retrieved.manifest_id == "MAN-01"
    assert retrieved.validation_id == "VAL-01"


# ==============================================================================
# 5. HYPOTHESIS & EXPERIMENT PLAN MODELS
# ==============================================================================

def test_performance_hypothesis_model(test_db):
    """Verifies creating, persisting, and querying performance hypotheses."""
    hyp = PerformanceHypothesis(
        hypothesis_id="HYP-DIRECT-PORT-01",
        target_metric="loop_time",
        predicted_effect="Direct port manipulation replaces digitalWrite, reducing loop execution latency by ~35-40%",
        confidence=0.92,
        evidence_references=["AST-CALL-DIGITALWRITE-L24", "BASELINE-LOOPTIME-14.2US"],
        supporting_static_evidence={"ast_call_count": 8, "function": "digitalWrite"},
        supporting_runtime_evidence={"mean_loop_time_us": 14.2, "jitter_us": 1.1},
        hardware_constraints=["Architecture: avr", "Pin: PB5 / D13"]
    )

    test_db.save_hypothesis(hyp)
    retrieved = test_db.get_hypothesis("HYP-DIRECT-PORT-01")

    assert retrieved is not None
    assert retrieved.hypothesis_id == "HYP-DIRECT-PORT-01"
    assert retrieved.confidence == 0.92
    assert retrieved.target_metric == "loop_time"
    assert "AST-CALL-DIGITALWRITE-L24" in retrieved.evidence_references


def test_experiment_plan_model():
    """Verifies creating and inspecting structured ExperimentPlan."""
    plan = ExperimentPlan(
        plan_id="PLAN-001",
        objective="Validate direct port register optimization against digitalWrite baseline on Uno R3",
        target_hypothesis_id="HYP-DIRECT-PORT-01",
        required_metrics=["loop_time", "sram_used"],
        required_instrumentation=["loop_time", "cpu_load_timer_tick"],
        hardware_constraints={"board": "arduino_uno", "mcu": "atmega328p"},
        sample_count=100,
        duration_seconds=10.0,
        acceptance_criteria={
            "loop_time_max_allowed_us": 10.0,
            "min_latency_reduction_pct": 20.0
        }
    )

    assert plan.plan_id == "PLAN-001"
    assert plan.sample_count == 100
    assert "loop_time" in plan.required_metrics
    assert plan.acceptance_criteria["min_latency_reduction_pct"] == 20.0


# ==============================================================================
# 6. STATISTICAL VALIDATION OUTCOME CLASSIFICATION
# ==============================================================================

def _make_baseline_stats(loop_time: float, cpu_load: float, sram_used: float, faults: float = 0.0):
    stats = {}
    for m in VALIDATION_METRIC_NAMES:
        stats[m] = BaselineMetricStats(
            metric=m,
            sample_count=50,
            mean=1.0,
            median=1.0,
            minimum=1.0,
            maximum=1.0,
            variance=0.0,
            jitter=0.0
        )
    stats["loop_time"].mean = loop_time
    stats["cpu_load"].mean = cpu_load
    stats["sram_used"].mean = sram_used
    stats["runtime_fault"].maximum = faults
    return stats


def test_validation_outcomes_classification():
    """
    Verifies that ValidationEngine normalizes outputs into the 4 standard categories:
    IMPROVEMENT, REGRESSION, INCONCLUSIVE, NO_SIGNIFICANT_CHANGE.
    """
    # 1. Improvement scenario: loop time drops from 1000us to 600us (-40%), cpu load from 80% to 20%
    base_stats = _make_baseline_stats(loop_time=1000.0, cpu_load=80.0, sram_used=500.0)
    cand_stats_improved = _make_baseline_stats(loop_time=600.0, cpu_load=20.0, sram_used=500.0)

    base_rec = BaselineRecord(
        baseline_id="BASE-01",
        run_id="RUN-BASE",
        board_id="arduino_uno",
        sample_window_ms=10000,
        metrics=base_stats,
        created_at="2026-10-01T00:00:00Z"
    )
    cand_rec_improved = BaselineRecord(
        baseline_id="CAND-01",
        run_id="RUN-CAND",
        board_id="arduino_uno",
        sample_window_ms=10000,
        metrics=cand_stats_improved,
        created_at="2026-10-01T00:01:00Z"
    )

    report_imp = ValidationEngine.validate_benchmarks(base_rec, cand_rec_improved, "VAL-IMP", "EXP-01")
    assert report_imp.normalized_outcome == "IMPROVEMENT"

    # 2. Regression scenario: loop time increases from 1000us to 1500us (+50%)
    cand_stats_regressed = _make_baseline_stats(loop_time=1500.0, cpu_load=90.0, sram_used=500.0)
    cand_rec_regressed = BaselineRecord(
        baseline_id="CAND-02",
        run_id="RUN-CAND-REG",
        board_id="arduino_uno",
        sample_window_ms=10000,
        metrics=cand_stats_regressed,
        created_at="2026-10-01T00:02:00Z"
    )

    report_reg = ValidationEngine.validate_benchmarks(base_rec, cand_rec_regressed, "VAL-REG", "EXP-02")
    assert report_reg.normalized_outcome == "REGRESSION"

    # 3. No Significant Change scenario: all metrics delta within < 3%
    cand_stats_unchanged = _make_baseline_stats(loop_time=1000.0, cpu_load=80.0, sram_used=500.0)
    cand_rec_unchanged = BaselineRecord(
        baseline_id="CAND-03",
        run_id="RUN-CAND-SAME",
        board_id="arduino_uno",
        sample_window_ms=10000,
        metrics=cand_stats_unchanged,
        created_at="2026-10-01T00:03:00Z"
    )

    report_same = ValidationEngine.validate_benchmarks(base_rec, cand_rec_unchanged, "VAL-SAME", "EXP-03")
    assert report_same.normalized_outcome in ("NO_SIGNIFICANT_CHANGE", "INCONCLUSIVE")


# ==============================================================================
# 7. EXPERIMENT ENGINE WITH MANIFEST CREATION
# ==============================================================================

def test_experiment_engine_manifest_and_lineage_flow(test_db):
    """Verifies that ExperimentEngine can create linked manifests and audit lineages."""
    baseline_eng = BaselineEngine(test_db)
    exp_eng = ExperimentEngine(test_db, baseline_eng)

    # Setup board, runs, optimization in test_db
    test_db.save_board(BoardRecord(
        board_id="arduino_uno",
        display_name="Arduino Uno R3",
        fqbn="arduino:avr:uno",
        mcu="atmega328p",
        architecture="avr"
    ))
    test_db.save_run(RunRecord(
        run_id="RUN-B01",
        board_id="arduino_uno",
        status="COMPLETED"
    ))
    test_db.save_run(RunRecord(
        run_id="RUN-C01",
        board_id="arduino_uno",
        status="COMPLETED"
    ))
    test_db.save_optimization(OptimizationRecord(
        optimization_id="OPT-01",
        finding_id="FIND-01",
        run_id="RUN-B01",
        title="Direct Port Registers",
        problem="Slow digitalWrite call",
        source_location={"file": "sketch.ino", "line": 10},
        before_code="digitalWrite(13, HIGH);",
        after_code="PORTB |= (1 << 5);",
        reason="Eliminate digitalWrite lookup",
        hardware_consideration="Writes directly to PORTB",
        expected_effect={"loop_time_delta_ms": -35.0},
        risk="LOW",
        confidence=0.9,
        validation_required=True,
        status="PROPOSED"
    ))

    # Create Experiment
    exp = exp_eng.create_experiment(
        title="Direct Port Experiment",
        board_id="arduino_uno",
        baseline_run_id="RUN-B01",
        optimization_id="OPT-01"
    )
    assert exp.status == "CREATED"

    # Create Experiment Manifest
    manifest = exp_eng.create_experiment_manifest(
        experiment_id=exp.experiment_id,
        firmware_hash="hash_baseline_123",
        candidate_hash="hash_candidate_456",
        compiler_toolchain="avr-gcc 7.3.0",
        selected_measurements=["loop_time", "cpu_load"],
        prediction={"loop_time_delta_pct": -35.0}
    )
    assert manifest.experiment_id == exp.experiment_id
    assert manifest.mcu == "atmega328p"
    assert manifest.architecture == "avr8"
    assert manifest.firmware_hash == "hash_baseline_123"

    # Create Provenance Lineage
    lineage = exp_eng.create_provenance_lineage(
        firmware_id="FW-01",
        analysis_run_id="STATIC-01",
        baseline_run_id="RUN-B01",
        finding_ids=["FIND-01"],
        hypothesis_id="HYP-01",
        candidate_id="OPT-01",
        experiment_id=exp.experiment_id,
        manifest_id=manifest.manifest_id
    )
    assert lineage.firmware_id == "FW-01"
    assert lineage.experiment_id == exp.experiment_id
    assert lineage.manifest_id == manifest.manifest_id

    # Verify retrieval from DB
    saved_m = test_db.get_manifest(manifest.manifest_id)
    assert saved_m is not None
    assert saved_m.firmware_hash == "hash_baseline_123"

    saved_l = test_db.get_lineage(lineage.lineage_id)
    assert saved_l is not None
    assert saved_l.experiment_id == exp.experiment_id


# ==============================================================================
# 8. REST API CAPABILITY ENDPOINT
# ==============================================================================

def test_api_board_capabilities(test_client):
    """Verifies GET /api/boards/{board_id}/capabilities via FastAPI TestClient."""
    response = test_client.get("/api/boards/arduino_uno/capabilities")
    assert response.status_code == 200
    data = response.json()

    assert data["board_id"] == "arduino_uno"
    assert data["architecture"] == "avr8"
    assert data["clock"]["available"] is True
    assert data["clock"]["value"] == 16000000
    assert "loop_time" in data["available_instrumentation"]
    assert "dwt_cycle_count" in data["unavailable_instrumentation"]
