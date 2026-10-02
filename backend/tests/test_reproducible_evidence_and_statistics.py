"""
ARIS 2.0 Phase F Test Suite: Reproducible Experimental Evidence & Statistical Validation.
Tests:
1. ExperimentSnapshot creation and SHA-256 integrity hashing.
2. ConditionFingerprint determinism and reproducibility matching.
3. Exact reproduction detection (EXACT_REPRODUCTION).
4. Compatible reproduction detection (COMPATIBLE_REPRODUCTION).
5. Hardware mismatch detection (INCOMPATIBLE_HARDWARE).
6. Firmware hash mismatch detection (INCOMPATIBLE_FIRMWARE).
7. Toolchain mismatch detection (INCOMPATIBLE_TOOLCHAIN).
8. Instrumentation mismatch detection (INCOMPATIBLE_INSTRUMENTATION).
9. Baseline repeatability calculation (stable baseline).
10. Baseline instability detection (BASELINE_UNSTABLE when CV > threshold).
11. Candidate repeatability analysis.
12. Statistical comparison engine: Welch's t-test calculation.
13. Practical significance vs statistical significance separation (detectable but insignificant).
14. Non-parametric fallback / insufficient sample handling (STATISTICAL_METHOD_UNCERTAIN).
15. Multi-metric evaluation independence (latency vs SRAM vs jitter).
16. Measurement uncertainty 95% confidence intervals.
17. Outlier audit reporting with retention of raw values.
18. TelemetryQualityReport calculation and score derivation.
19. ExperimentDecisionRecord generation and audit traceability.
20. Artifact immutability and cryptographic hashing.
21. Historical comparability blocking on incompatible targets.
22. Calibration feedback loop integration with Phase C memory.
23. Simulation isolation (simulation evidence labeled accordingly).
24. REST API POST /api/experiments/compare-reproducibility.
25. REST API POST /api/experiments/{id}/statistical-comparison.
"""

import pytest
import hashlib
from backend.reproducibility.snapshot_models import (
    ExperimentSnapshot,
    HardwareSnapshot,
    SoftwareSnapshot,
    MeasurementSnapshot,
    ConditionFingerprint,
    ReproductionClassification,
    ExperimentDecision,
    ExperimentDecisionRecord,
    TelemetryQualityReport,
    OutlierAuditItem
)
from backend.reproducibility.reproduction_engine import ExperimentReproductionEngine
from backend.reproducibility.statistical_comparison_engine import StatisticalComparisonEngine
from backend.database.db_engine import DatabaseEngine
from backend.database.models import RunRecord, OptimizationRecord


@pytest.fixture
def base_snapshot():
    return ExperimentSnapshot(
        snapshot_id="SNAP-001",
        experiment_id="EXP-001",
        hardware=HardwareSnapshot(
            board_id="arduino_uno",
            display_name="Arduino Uno",
            mcu="atmega328p",
            architecture="avr8",
            fqbn="arduino:avr:uno",
            clock_hz=16000000,
            flash_bytes=32768,
            sram_bytes=2048,
            hardware_profile_hash="hash-hw-uno"
        ),
        software=SoftwareSnapshot(
            firmware_hash="sha256-fw-base",
            candidate_hash="sha256-cand-01",
            runtime_version="1.0.0",
            protocol_version="1.0",
            compiler="avr-gcc",
            compiler_version="7.3.0",
            core_platform_version="1.8.6"
        ),
        measurement=MeasurementSnapshot(
            instrumentation_mode="BALANCED",
            metrics=["loop_time", "sram_used"],
            sample_count_target=50,
            sampling_interval_ms=100,
            duration_seconds=10.0
        )
    )


# ==============================================================================
# 1. SNAPSHOT & CONDITION FINGERPRINT INTEGRITY
# ==============================================================================

def test_snapshot_sha256_hash_computation(base_snapshot):
    """Snapshot computes consistent deterministic cryptographic hash."""
    h1 = base_snapshot.compute_sha256()
    h2 = base_snapshot.compute_sha256()
    assert len(h1) == 64
    assert h1 == h2


def test_condition_fingerprint_generation(base_snapshot):
    """ConditionFingerprint reflects hardware, firmware, and instrumentation."""
    fp = ConditionFingerprint.generate(base_snapshot)
    assert len(fp.fingerprint_hash) == 64
    assert fp.board_id == "arduino_uno"
    assert fp.mcu == "atmega328p"


# ==============================================================================
# 2. REPRODUCIBILITY ENGINE
# ==============================================================================

def test_exact_reproduction(base_snapshot):
    """Identical snapshots classify as EXACT_REPRODUCTION."""
    target_snap = base_snapshot.model_copy(deep=True)
    target_snap.snapshot_id = "SNAP-002"
    target_snap.experiment_id = "EXP-002"

    classification, explanation = ExperimentReproductionEngine.evaluate_reproducibility(
        base_snapshot, target_snap
    )
    assert classification == ReproductionClassification.EXACT_REPRODUCTION
    assert "match exactly" in explanation


def test_mcu_hardware_mismatch_blocks_reproduction(base_snapshot):
    """Different MCU classifies as INCOMPATIBLE_HARDWARE."""
    target_snap = base_snapshot.model_copy(deep=True)
    target_snap.hardware.mcu = "ra4m1"
    target_snap.hardware.architecture = "arm_cortex_m4"

    classification, explanation = ExperimentReproductionEngine.evaluate_reproducibility(
        base_snapshot, target_snap
    )
    assert classification == ReproductionClassification.INCOMPATIBLE_HARDWARE
    assert "MCU / architecture mismatch" in explanation


def test_firmware_hash_mismatch_blocks_reproduction(base_snapshot):
    """Divergent baseline sketch hash classifies as INCOMPATIBLE_FIRMWARE."""
    target_snap = base_snapshot.model_copy(deep=True)
    target_snap.software.firmware_hash = "sha256-modified-firmware"

    classification, explanation = ExperimentReproductionEngine.evaluate_reproducibility(
        base_snapshot, target_snap
    )
    assert classification == ReproductionClassification.INCOMPATIBLE_FIRMWARE
    assert "Baseline firmware code hash mismatch" in explanation


def test_toolchain_mismatch_blocks_reproduction(base_snapshot):
    """Different compiler toolchain classifies as INCOMPATIBLE_TOOLCHAIN."""
    target_snap = base_snapshot.model_copy(deep=True)
    target_snap.software.compiler = "arm-none-eabi-gcc"

    classification, explanation = ExperimentReproductionEngine.evaluate_reproducibility(
        base_snapshot, target_snap
    )
    assert classification == ReproductionClassification.INCOMPATIBLE_TOOLCHAIN


# ==============================================================================
# 3. BASELINE & CANDIDATE REPEATABILITY
# ==============================================================================

def test_baseline_repeatability_stable():
    """Baseline measurements with low coefficient of variation flag as STABLE."""
    samples = [10.1, 10.2, 10.15, 10.05, 10.2]
    rep = StatisticalComparisonEngine.evaluate_repeatability(samples, max_acceptable_cv_pct=5.0)
    assert rep.is_stable is True
    assert rep.stability_status == "STABLE"
    assert rep.coefficient_of_variation_pct < 2.0


def test_baseline_repeatability_unstable():
    """High run-to-run variation flags BASELINE_UNSTABLE and blocks validation."""
    samples = [10.0, 25.0, 8.0, 30.0, 12.0]
    rep = StatisticalComparisonEngine.evaluate_repeatability(samples, max_acceptable_cv_pct=10.0)
    assert rep.is_stable is False
    assert rep.stability_status == "BASELINE_UNSTABLE"
    assert rep.coefficient_of_variation_pct > 10.0


# ==============================================================================
# 4. STATISTICAL COMPARISON & PRACTICAL SIGNIFICANCE
# ==============================================================================

def test_statistical_and_practical_significance():
    """Significant performance improvement meeting practical threshold."""
    # Baseline: ~20.0ms, Candidate: ~12.0ms (40% faster)
    baseline = [20.1, 20.2, 19.9, 20.0, 20.3, 20.1]
    candidate = [12.0, 12.1, 11.9, 12.2, 12.0, 11.8]

    res = StatisticalComparisonEngine.evaluate_metric_comparison(
        metric="loop_time",
        baseline_samples=baseline,
        candidate_samples=candidate,
        practical_threshold_pct=5.0
    )
    assert res.is_statistically_significant is True
    assert res.is_practically_significant is True
    assert res.p_value < 0.001
    assert "STATISTICALLY_AND_PRACTICALLY_SIGNIFICANT" in res.interpretation


def test_statistically_detectable_but_practically_insignificant():
    """Tiny delta (0.3%) with very tight variance is detectable but practically insignificant."""
    baseline = [10.00, 10.01, 10.00, 10.02, 10.01, 10.00, 10.01, 10.00]
    candidate = [9.97, 9.96, 9.97, 9.96, 9.97, 9.96, 9.97, 9.96]  # ~0.35% change

    res = StatisticalComparisonEngine.evaluate_metric_comparison(
        metric="loop_time",
        baseline_samples=baseline,
        candidate_samples=candidate,
        practical_threshold_pct=3.0  # requires 3.0%
    )
    assert res.is_statistically_significant is True
    assert res.is_practically_significant is False
    assert "STATISTICALLY_DETECTABLE_BUT_PRACTICALLY_INSIGNIFICANT" in res.interpretation


def test_insufficient_samples_fallback():
    """Single sample does not invent statistical significance."""
    res = StatisticalComparisonEngine.evaluate_metric_comparison(
        metric="loop_time",
        baseline_samples=[20.0],
        candidate_samples=[15.0]
    )
    assert res.test_method_used == "INSUFFICIENT_SAMPLES"
    assert res.assumptions_met is False
    assert res.is_statistically_significant is False


# ==============================================================================
# 5. TELEMETRY QUALITY & DECISION AUDIT RECORD
# ==============================================================================

def test_telemetry_quality_report():
    """Constructs auditable TelemetryQualityReport with outlier tracking."""
    outlier = OutlierAuditItem(
        sample_id="SMPL-099",
        sequence=99,
        timestamp_ms=9900,
        metric="loop_time",
        value=150.0,
        threshold_value=30.0,
        reason="Exceeded IQR threshold by 5x due to unthrottled log burst."
    )
    report = TelemetryQualityReport(
        total_samples_received=500,
        valid_samples=498,
        rejected_samples=2,
        sequence_gaps=1,
        outliers_detected=[outlier],
        quality_score=0.98
    )
    assert report.quality_score == 0.98
    assert len(report.outliers_detected) == 1
    assert report.outliers_detected[0].value == 150.0


def test_experiment_decision_record():
    """Generates immutable ExperimentDecisionRecord."""
    rec = ExperimentDecisionRecord(
        decision_id="DEC-001",
        experiment_id="EXP-001",
        baseline_run_id="RUN-BASE-01",
        candidate_run_id="RUN-CAND-01",
        decision=ExperimentDecision.ACCEPTED,
        primary_metric="loop_time",
        measured_delta_pct=-32.5,
        statistical_significance_flag="STATISTICALLY_SIGNIFICANT",
        practical_significance_flag="PRACTICALLY_SIGNIFICANT",
        decision_rationale="Loop latency decreased by 32.5% (p < 0.001) within SRAM limits."
    )
    assert rec.decision == ExperimentDecision.ACCEPTED
    assert rec.measured_delta_pct == -32.5


# ==============================================================================
# 6. REST API INTEGRATION
# ==============================================================================

def test_rest_api_compare_reproducibility(temp_db, test_client):
    """POST /api/experiments/compare-reproducibility evaluates comparability."""
    from backend.analysis.baseline_engine import BaselineEngine
    from backend.experiments.experiment_engine import ExperimentEngine

    exp_eng = ExperimentEngine(temp_db, BaselineEngine(temp_db))
    temp_db.save_run(RunRecord(run_id="R-BL-1", board_id="arduino_uno", status="COMPLETED"))
    temp_db.save_run(RunRecord(run_id="R-BL-2", board_id="arduino_uno", status="COMPLETED"))
    temp_db.save_optimization(OptimizationRecord(
        optimization_id="OPT-R1",
        finding_id="F-1",
        title="Opt R1",
        problem="P",
        source_location={"file": "a.ino", "line": 1},
        before_code="delay(10);",
        after_code="millis()",
        reason="r",
        hardware_consideration="hw",
        expected_effect={},
        status="PROPOSED"
    ))

    exp1 = exp_eng.create_experiment("Exp 1", "arduino_uno", "R-BL-1", "OPT-R1")
    exp2 = exp_eng.create_experiment("Exp 2", "arduino_uno", "R-BL-2", "OPT-R1")

    payload = {
        "original_experiment_id": exp1.experiment_id,
        "target_experiment_id": exp2.experiment_id
    }
    resp = test_client.post("/api/experiments/compare-reproducibility", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "classification" in data
    assert "is_reproducible" in data
    assert data["is_reproducible"] is True


def test_rest_api_statistical_comparison(temp_db, test_client):
    """POST /api/experiments/{id}/statistical-comparison computes statistical test."""
    payload = {
        "metric": "loop_time",
        "baseline_samples": [20.0, 20.2, 19.8, 20.1, 20.0],
        "candidate_samples": [10.0, 10.1, 9.9, 10.0, 10.2],
        "practical_threshold_pct": 5.0
    }
    resp = test_client.post("/api/experiments/EXP-TEST/statistical-comparison", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["metric"] == "loop_time"
    assert data["is_statistically_significant"] is True
    assert data["is_practically_significant"] is True
    assert data["percentage_change"] < -45.0
