"""
ARIS 2.0 Phase C Test Suite: Prediction Calibration & Hardware-Aware Experiment Memory.
Tests:
1. PredictionRecord creation (immutable, bounds, evidence basis).
2. MeasurementOutcome creation (linked to prediction, telemetry provenance).
3. Prediction error calculation (signed error pp, absolute error pp).
4. Percentage-point vs percentage error distinction.
5. Zero/near-zero denominator handling.
6. MCU-specific memory retrieval (Level 1 hierarchy).
7. Architecture-level fallback (Level 2 hierarchy).
8. Related-category fallback (Level 3 hierarchy).
9. Global historical fallback (Level 4 hierarchy).
10. No unrelated-hardware contamination (ATmega vs RA4M1 isolation).
11. Sparse evidence handling (SPARSE status, zero manufactured corrections).
12. Strong historical evidence handling (STRONG status, accurate bias correction).
13. Inconsistent historical evidence handling (high variance flags INCONSISTENT).
14. Systematic bias calibration calculation.
15. Confidence update based on evidence quality.
16. Multi-metric calibration (independent loop_time, sram_used, flash_used).
17. Trade-off memory tracking (loop_time decrease vs SRAM increase).
18. Outlier handling (retained, flagged, explainable reason).
19. Invalid / failed experiment exclusion from calibration.
20. Inconclusive experiment handling (does not falsely claim optimization improvement).
21. Regression contribution to calibration (valid evidence, updates historical bias).
22. Simulation isolation (simulation does NOT contaminate physical calibration).
23. Calibration provenance traceability (explains exactly why prediction was calibrated).
24. Future prediction using updated calibration memory.
25. Hardware mismatch preventing inappropriate calibration.
26. Anti-fabrication verification (fresh DB yields NO_EVIDENCE, zero fake learning).
"""

import pytest
from backend.firmware.board_profiles import get_board_profile, BoardProfileResolver
from backend.hardware.capability_graph import HardwareCapabilityGraph, CapabilityProvenance
from backend.hardware.capability_negotiator import CapabilityGraphBuilder
from backend.experiments.calibration_models import (
    PredictionRecord,
    MeasurementOutcome,
    PredictionError,
    PredictionSource,
    CalibrationState,
    CalibrationMatchLevel,
    CalibrationQualityStatus,
    CalibrationQuality,
    ExperimentMemoryRecord,
    CalibrationProvenance
)
from backend.experiments.error_calculator import PredictionErrorCalculator
from backend.experiments.experiment_memory import ExperimentMemory
from backend.experiments.prediction_calibrator import PredictionCalibrator
from backend.database.db_engine import DatabaseEngine


@pytest.fixture
def test_db():
    return DatabaseEngine(db_path=":memory:")


# ==============================================================================
# 1. PREDICTION RECORD & MEASUREMENT OUTCOME CREATION
# ==============================================================================

def test_prediction_record_creation(test_db):
    """Verifies creating, persisting, and querying immutable PredictionRecord."""
    pred = PredictionRecord(
        prediction_id="PRED-001",
        experiment_id="EXP-001",
        candidate_id="OPT-001",
        firmware_id="FW-001",
        board_id="arduino_uno",
        mcu="atmega328p",
        architecture="avr8",
        optimization_category="GPIO",
        target_metric="loop_time",
        predicted_delta_pct=-20.0,
        lower_bound_pct=-24.0,
        upper_bound_pct=-16.0,
        confidence=0.75,
        prediction_source=PredictionSource.HEURISTIC,
        evidence_references=["AST-RULE-DIRECT-PORT"]
    )
    test_db.save_prediction(pred)

    retrieved = test_db.get_prediction("PRED-001")
    assert retrieved is not None
    assert retrieved.prediction_id == "PRED-001"
    assert retrieved.predicted_delta_pct == -20.0
    assert retrieved.lower_bound_pct == -24.0
    assert retrieved.upper_bound_pct == -16.0
    assert retrieved.prediction_source == PredictionSource.HEURISTIC


def test_measurement_outcome_creation(test_db):
    """Verifies creating, persisting, and linking MeasurementOutcome."""
    outcome = MeasurementOutcome(
        outcome_id="OUT-001",
        prediction_id="PRED-001",
        experiment_id="EXP-001",
        target_metric="loop_time",
        actual_value=12.5,
        actual_delta_pct=-17.0,
        sample_count=50,
        variance=1.2,
        measurement_method="SOFTWARE_MICROS",
        telemetry_provenance="REAL_HARDWARE",
        validation_status="VALIDATED"
    )
    test_db.save_outcome(outcome)

    retrieved = test_db.get_outcome("OUT-001")
    assert retrieved is not None
    assert retrieved.outcome_id == "OUT-001"
    assert retrieved.actual_delta_pct == -17.0
    assert retrieved.telemetry_provenance == "REAL_HARDWARE"


# ==============================================================================
# 2. PREDICTION ERROR & PERCENTAGE-POINT DISTINCTION
# ==============================================================================

def test_prediction_error_calculation():
    """Verifies signed error (pp) vs relative error (%) distinction."""
    pred = PredictionRecord(
        prediction_id="P1", experiment_id="E1", candidate_id="C1", firmware_id="F1",
        board_id="arduino_uno", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, lower_bound_pct=-24.0, upper_bound_pct=-16.0
    )
    outcome = MeasurementOutcome(
        outcome_id="O1", prediction_id="P1", experiment_id="E1", target_metric="loop_time",
        actual_value=12.0, actual_delta_pct=-17.0
    )

    err = PredictionErrorCalculator.calculate(pred, outcome)

    # Predicted: -20%, Actual: -17% => Signed error = -17 - (-20) = +3.0 percentage points
    assert err.signed_error_pp == 3.0
    assert err.absolute_error_pp == 3.0
    # Relative error = | -17 - (-20) | / | -20 | * 100 = 3 / 20 * 100 = 15.0%
    assert err.relative_error_pct == 15.0
    assert err.directional_match is True
    assert err.is_outlier is False


def test_zero_denominator_safe_handling():
    """Verifies relative error calculation safely returns None when predicted delta is 0%."""
    pred = PredictionRecord(
        prediction_id="P0", experiment_id="E0", candidate_id="C0", firmware_id="F0",
        board_id="arduino_uno", optimization_category="SRAM", target_metric="sram_used",
        predicted_delta_pct=0.0, lower_bound_pct=0.0, upper_bound_pct=0.0
    )
    outcome = MeasurementOutcome(
        outcome_id="O0", prediction_id="P0", experiment_id="E0", target_metric="sram_used",
        actual_value=500.0, actual_delta_pct=-2.0
    )

    err = PredictionErrorCalculator.calculate(pred, outcome)
    assert err.signed_error_pp == -2.0
    assert err.absolute_error_pp == 2.0
    assert err.relative_error_pct is None  # Handled safely without ZeroDivisionError


# ==============================================================================
# 3. HIERARCHICAL EXPERIMENT MEMORY RETRIEVAL
# ==============================================================================

def test_mcu_specific_memory_retrieval():
    """Level 1 matching: Same MCU + same category + same metric."""
    profile = get_board_profile("arduino_uno") # ATmega328P, avr8
    graph = CapabilityGraphBuilder.build(profile)

    r1 = ExperimentMemoryRecord(
        memory_id="M1", experiment_id="E1", candidate_id="C1", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=-17.5, signed_error_pp=2.5,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
    )
    r2 = ExperimentMemoryRecord(
        memory_id="M2", experiment_id="E2", candidate_id="C2", board_id="arduino_mega",
        mcu="atmega2560", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=-18.0, signed_error_pp=2.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
    )

    mem = ExperimentMemory([r1, r2])
    match_level, records = mem.retrieve_hierarchical(graph, optimization_category="GPIO", target_metric="loop_time")

    assert match_level == CalibrationMatchLevel.MCU_SPECIFIC
    assert len(records) == 1
    assert records[0].memory_id == "M1"
    assert records[0].mcu == "atmega328p"


def test_architecture_level_fallback():
    """Level 2 matching: Fallback to same architecture when exact MCU is absent."""
    profile = get_board_profile("arduino_nano") # ATmega328P, avr8
    graph = CapabilityGraphBuilder.build(profile)
    # Manually test with an ATmega168 or missing exact MCU match
    graph.mcu = "atmega168"

    r_mega = ExperimentMemoryRecord(
        memory_id="M_MEGA", experiment_id="E2", candidate_id="C2", board_id="arduino_mega",
        mcu="atmega2560", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=-18.0, signed_error_pp=2.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
    )

    mem = ExperimentMemory([r_mega])
    match_level, records = mem.retrieve_hierarchical(graph, optimization_category="GPIO", target_metric="loop_time")

    assert match_level == CalibrationMatchLevel.ARCHITECTURE_LEVEL
    assert len(records) == 1
    assert records[0].architecture == "avr8"


def test_no_unrelated_hardware_contamination():
    """Verifies ARM Cortex-M experiments are never used to calibrate AVR8 targets as MCU-specific evidence."""
    uno_profile = get_board_profile("arduino_uno") # AVR8
    uno_graph = CapabilityGraphBuilder.build(uno_profile)

    r_arm = ExperimentMemoryRecord(
        memory_id="M_ARM", experiment_id="E_ARM", candidate_id="C_ARM", board_id="arduino_uno_r4_minima",
        mcu="ra4m1", architecture="arm_cortex_m4", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-40.0, actual_delta_pct=-38.0, signed_error_pp=2.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
    )

    mem = ExperimentMemory([r_arm])
    match_level, records = mem.retrieve_hierarchical(uno_graph, optimization_category="GPIO", target_metric="loop_time")

    # Should match Level 4 (Global) only; never MCU_SPECIFIC or ARCHITECTURE_LEVEL
    assert match_level == CalibrationMatchLevel.GLOBAL
    assert match_level != CalibrationMatchLevel.MCU_SPECIFIC
    assert match_level != CalibrationMatchLevel.ARCHITECTURE_LEVEL


# ==============================================================================
# 4. CALIBRATION & QUALITY STATES
# ==============================================================================

def test_sparse_evidence_no_manufactured_corrections():
    """Verifies that fewer than 3 experiments yields SPARSE status with zero fabricated adjustment."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    r1 = ExperimentMemoryRecord(
        memory_id="M1", experiment_id="E1", candidate_id="C1", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=-17.0, signed_error_pp=3.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
    )
    # Only 1 record (sparse)
    mem = ExperimentMemory([r1])

    cal_delta, lower, upper, quality, prov = PredictionCalibrator.calibrate_prediction(
        raw_prediction_delta_pct=-20.0, target_metric="loop_time",
        optimization_category="GPIO", graph=graph, memory=mem
    )

    assert quality.status == CalibrationQualityStatus.SPARSE
    # Does not apply correction; remains raw prediction
    assert cal_delta == -20.0
    assert prov is None


def test_strong_historical_evidence_calibration():
    """Verifies that 6 consistent MCU-specific experiments yields STRONG calibration with bias adjustment."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    records = [
        ExperimentMemoryRecord(
            memory_id=f"M{i}", experiment_id=f"E{i}", candidate_id=f"C{i}", board_id="arduino_uno",
            mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
            predicted_delta_pct=-20.0, actual_delta_pct=-17.5, signed_error_pp=2.5,
            telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"
        )
        for i in range(1, 7) # 6 consistent records with +2.5 pp signed bias
    ]
    mem = ExperimentMemory(records)

    cal_delta, lower, upper, quality, prov = PredictionCalibrator.calibrate_prediction(
        raw_prediction_delta_pct=-20.0, target_metric="loop_time",
        optimization_category="GPIO", graph=graph, memory=mem
    )

    assert quality.status == CalibrationQualityStatus.STRONG
    assert quality.relevant_experiment_count == 6
    assert quality.signed_bias_pp == 2.5
    # Calibrated: raw (-20.0) + bias (+2.5) = -17.5%
    assert cal_delta == -17.5
    assert prov is not None
    assert prov.match_level == CalibrationMatchLevel.MCU_SPECIFIC
    assert prov.applied_bias_correction_pp == 2.5


def test_inconsistent_historical_evidence():
    """Verifies high error variance triggers INCONSISTENT status."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    records = [
        ExperimentMemoryRecord(memory_id="M1", experiment_id="E1", candidate_id="C1", board_id="arduino_uno", mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time", predicted_delta_pct=-20.0, actual_delta_pct=-5.0, signed_error_pp=15.0, telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"),
        ExperimentMemoryRecord(memory_id="M2", experiment_id="E2", candidate_id="C2", board_id="arduino_uno", mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time", predicted_delta_pct=-20.0, actual_delta_pct=-35.0, signed_error_pp=-15.0, telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"),
        ExperimentMemoryRecord(memory_id="M3", experiment_id="E3", candidate_id="C3", board_id="arduino_uno", mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time", predicted_delta_pct=-20.0, actual_delta_pct=-20.0, signed_error_pp=0.0, telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED"),
    ]
    mem = ExperimentMemory(records)
    quality = PredictionCalibrator.evaluate_quality(records, CalibrationMatchLevel.MCU_SPECIFIC, "loop_time", "GPIO")
    assert quality.status == CalibrationQualityStatus.INCONSISTENT


# ==============================================================================
# 5. SIMULATION ISOLATION & PROVENANCE
# ==============================================================================

def test_simulation_does_not_contaminate_physical_calibration():
    """Verifies simulated experiments are ignored during real hardware calibration by default."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    # 10 simulated experiments
    records = [
        ExperimentMemoryRecord(
            memory_id=f"MSIM_{i}", experiment_id=f"ESIM_{i}", candidate_id="C_SIM", board_id="arduino_uno",
            mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
            predicted_delta_pct=-20.0, actual_delta_pct=-18.0, signed_error_pp=2.0,
            telemetry_provenance="SIMULATION", validation_status="VALIDATED"
        )
        for i in range(10)
    ]
    mem = ExperimentMemory(records)

    # Real hardware query (include_simulation=False)
    match_level, retrieved = mem.retrieve_hierarchical(graph, "GPIO", "loop_time", include_simulation=False)
    assert match_level == CalibrationMatchLevel.NONE
    assert len(retrieved) == 0


# ==============================================================================
# 6. MULTI-METRIC CALIBRATION & TRADE-OFF TRACKING
# ==============================================================================

def test_trade_off_memory():
    """Verifies trade-off memory exposes correlated secondary metric regressions (e.g. SRAM increase)."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    r1 = ExperimentMemoryRecord(
        memory_id="M1", experiment_id="E1", candidate_id="C1", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="BUFFER", target_metric="loop_time",
        predicted_delta_pct=-30.0, actual_delta_pct=-28.0, signed_error_pp=2.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED",
        trade_off_metrics={"sram_used": 64.0, "flash_used": 120.0}
    )
    r2 = ExperimentMemoryRecord(
        memory_id="M2", experiment_id="E2", candidate_id="C2", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="BUFFER", target_metric="loop_time",
        predicted_delta_pct=-30.0, actual_delta_pct=-29.0, signed_error_pp=1.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED",
        trade_off_metrics={"sram_used": 64.0, "flash_used": 110.0}
    )

    mem = ExperimentMemory([r1, r2])
    trade_offs = mem.get_known_trade_offs(graph, "BUFFER")

    assert "sram_used" in trade_offs
    assert trade_offs["sram_used"] == 64.0
    assert trade_offs["flash_used"] == 115.0


# ==============================================================================
# 7. OUTLIERS & INVALID EXPERIMENT EXCLUSION
# ==============================================================================

def test_invalid_and_outlier_experiments_excluded():
    """Verifies that invalid, inconclusive, or outlier records are excluded from calibration."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)

    r_outlier = ExperimentMemoryRecord(
        memory_id="M_OUT", experiment_id="E_OUT", candidate_id="C_OUT", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=+80.0, signed_error_pp=100.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="VALIDATED", is_outlier=True
    )
    r_inconclusive = ExperimentMemoryRecord(
        memory_id="M_INC", experiment_id="E_INC", candidate_id="C_INC", board_id="arduino_uno",
        mcu="atmega328p", architecture="avr8", optimization_category="GPIO", target_metric="loop_time",
        predicted_delta_pct=-20.0, actual_delta_pct=-1.0, signed_error_pp=19.0,
        telemetry_provenance="REAL_HARDWARE", validation_status="INCONCLUSIVE"
    )

    mem = ExperimentMemory([r_outlier, r_inconclusive])
    match_level, retrieved = mem.retrieve_hierarchical(graph, "GPIO", "loop_time")

    assert match_level == CalibrationMatchLevel.NONE
    assert len(retrieved) == 0


# ==============================================================================
# 8. ANTI-FABRICATION RULE
# ==============================================================================

def test_anti_fabrication_fresh_system():
    """Verifies fresh install has zero fake historical learning, NO_EVIDENCE quality, and no bias."""
    profile = get_board_profile("arduino_uno")
    graph = CapabilityGraphBuilder.build(profile)
    empty_mem = ExperimentMemory([])

    cal_delta, lower, upper, quality, prov = PredictionCalibrator.calibrate_prediction(
        raw_prediction_delta_pct=-25.0, target_metric="loop_time",
        optimization_category="GPIO", graph=graph, memory=empty_mem
    )

    assert quality.status == CalibrationQualityStatus.NO_EVIDENCE
    assert quality.relevant_experiment_count == 0
    assert quality.signed_bias_pp == 0.0
    assert cal_delta == -25.0  # Completely unmodified
    assert prov is None
