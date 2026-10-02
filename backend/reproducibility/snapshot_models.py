"""
ARIS Reproducible Experiment Snapshot, Condition Fingerprint & Decision Models.
Provides immutable, cryptographic-grade audit records for experimental reproducibility:
- ExperimentSnapshot: Full hardware, software, measurement, and environment state.
- ConditionFingerprint: Deterministic SHA-256 fingerprint for compatibility checking.
- ReproductionClassification: EXACT, COMPATIBLE, CONDITIONALLY_REPRODUCIBLE, or INCOMPATIBLE.
- BaselineRepeatabilityRecord: Run-to-run variation, stability flags, CV%.
- CandidateRepeatabilityRecord: Multi-run stability metrics for candidates.
- TelemetryQualityReport: Sample loss, sequence gaps, framing errors, effective Hz.
- ExperimentDecisionRecord: Formal, evidence-traced acceptance/rejection verdicts.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class ReproductionClassification(str, Enum):
    EXACT_REPRODUCTION = "EXACT_REPRODUCTION"
    COMPATIBLE_REPRODUCTION = "COMPATIBLE_REPRODUCTION"
    CONDITIONALLY_REPRODUCIBLE = "CONDITIONALLY_REPRODUCIBLE"
    INCOMPATIBLE_HARDWARE = "INCOMPATIBLE_HARDWARE"
    INCOMPATIBLE_FIRMWARE = "INCOMPATIBLE_FIRMWARE"
    INCOMPATIBLE_TOOLCHAIN = "INCOMPATIBLE_TOOLCHAIN"
    INCOMPATIBLE_INSTRUMENTATION = "INCOMPATIBLE_INSTRUMENTATION"
    INCOMPATIBLE_CONFIGURATION = "INCOMPATIBLE_CONFIGURATION"


class ExperimentDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    ROLLED_BACK = "ROLLED_BACK"
    ABORTED = "ABORTED"


class HardwareSnapshot(BaseModel):
    board_id: str
    display_name: str
    mcu: str
    architecture: str
    fqbn: str
    clock_hz: int
    flash_bytes: int
    sram_bytes: int
    usb_vid_pid: Optional[str] = None
    hardware_profile_hash: str


class SoftwareSnapshot(BaseModel):
    firmware_hash: str
    candidate_hash: str
    runtime_version: str
    protocol_version: str
    compiler: str
    compiler_version: str
    core_platform_version: str
    build_flags: str = ""


class MeasurementSnapshot(BaseModel):
    instrumentation_mode: str
    metrics: List[str]
    sample_count_target: int
    sampling_interval_ms: int
    duration_seconds: float
    estimated_overhead_us: float = 0.0


class ExperimentSnapshot(BaseModel):
    """
    Immutable representation of an experiment at initialization.
    Cryptographically captures exact conditions.
    """
    snapshot_id: str
    experiment_id: str
    execution_mode: str = "REAL_HARDWARE"  # "REAL_HARDWARE" or "SIMULATION"
    hardware: HardwareSnapshot
    software: SoftwareSnapshot
    measurement: MeasurementSnapshot
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_sha256(self) -> str:
        dump = self.model_dump_json(exclude={"snapshot_id", "created_at"})
        return hashlib.sha256(dump.encode("utf-8")).hexdigest()


class ConditionFingerprint(BaseModel):
    """
    Deterministic fingerprint summarizing hardware, software, and measurement
    conditions to decide comparability and reproducibility.
    """
    fingerprint_hash: str
    board_id: str
    mcu: str
    architecture: str
    fqbn: str
    firmware_hash: str
    candidate_hash: str
    toolchain_signature: str
    instrumentation_mode: str

    @classmethod
    def generate(cls, snapshot: ExperimentSnapshot) -> "ConditionFingerprint":
        parts = [
            snapshot.hardware.board_id,
            snapshot.hardware.mcu,
            snapshot.hardware.architecture,
            snapshot.hardware.fqbn,
            snapshot.software.firmware_hash,
            snapshot.software.candidate_hash,
            f"{snapshot.software.compiler}:{snapshot.software.compiler_version}",
            snapshot.measurement.instrumentation_mode
        ]
        fp_str = "|".join(parts)
        h = hashlib.sha256(fp_str.encode("utf-8")).hexdigest()
        return cls(
            fingerprint_hash=h,
            board_id=snapshot.hardware.board_id,
            mcu=snapshot.hardware.mcu,
            architecture=snapshot.hardware.architecture,
            fqbn=snapshot.hardware.fqbn,
            firmware_hash=snapshot.software.firmware_hash,
            candidate_hash=snapshot.software.candidate_hash,
            toolchain_signature=f"{snapshot.software.compiler}:{snapshot.software.compiler_version}",
            instrumentation_mode=snapshot.measurement.instrumentation_mode
        )


class BaselineRepeatabilityRecord(BaseModel):
    """
    Quantifies stability across multiple baseline runs (RUN 1, RUN 2, RUN 3).
    """
    baseline_id: str
    run_ids: List[str]
    sample_count_total: int
    metric_means: Dict[str, float]
    metric_std_devs: Dict[str, float]
    coefficient_of_variation_pct: Dict[str, float]  # (std_dev / mean) * 100
    is_stable: bool = True
    stability_status: str = "BASELINE_STABLE"  # "BASELINE_STABLE", "BASELINE_UNSTABLE"
    instability_reasons: List[str] = Field(default_factory=list)


class CandidateRepeatabilityRecord(BaseModel):
    """
    Quantifies candidate stability across multiple runs.
    """
    candidate_id: str
    run_ids: List[str]
    sample_count_total: int
    metric_means: Dict[str, float]
    metric_std_devs: Dict[str, float]
    outlier_count: int = 0
    is_stable: bool = True


class OutlierAuditItem(BaseModel):
    """Specific telemetry sample flagged as outlier with explainable rationale."""
    sample_id: str
    sequence: int
    timestamp_ms: int
    metric: str
    value: float
    detection_method: str = "IQR_3X"  # or "Z_SCORE_3"
    threshold_value: float
    reason: str
    excluded_from_primary_stats: bool = False  # Always retained for audit


class TelemetryQualityReport(BaseModel):
    """
    Empirical telemetry data quality audit feeding EvidenceQuality.
    """
    total_samples_received: int
    valid_samples: int
    rejected_samples: int
    sequence_gaps: int = 0
    timestamp_anomalies: int = 0
    duplicate_samples: int = 0
    malformed_frames: int = 0
    effective_sampling_rate_hz: float = 0.0
    telemetry_duration_seconds: float = 0.0
    quality_score: float = 1.0  # 0.0 to 1.0
    outliers_detected: List[OutlierAuditItem] = Field(default_factory=list)


class ExperimentDecisionRecord(BaseModel):
    """
    Immutable post-experiment verdict grounded strictly in empirical evidence.
    """
    decision_id: str
    experiment_id: str
    baseline_run_id: str
    candidate_run_id: str
    decision: ExperimentDecision
    primary_metric: str
    measured_delta_pct: float
    statistical_significance_flag: str  # "STATISTICALLY_SIGNIFICANT", "NOT_SIGNIFICANT", "INCONCLUSIVE"
    practical_significance_flag: str    # "PRACTICALLY_SIGNIFICANT", "PRACTICALLY_INSIGNIFICANT"
    decision_rationale: str
    rollback_status: str = "NONE"
    calibration_updated: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
