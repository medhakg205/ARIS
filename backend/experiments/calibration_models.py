"""
ARIS Prediction Calibration & Hardware-Aware Experiment Memory Models.
Defines:
- PredictionSource: Enum (RAW_MODEL, HEURISTIC, HISTORICAL_CALIBRATION, HYBRID)
- CalibrationState: Enum (UNCHECKED, PENDING_PHYSICAL, CALIBRATED, REJECTED)
- CalibrationMatchLevel: Enum (MCU_SPECIFIC, ARCHITECTURE_LEVEL, RELATED_CATEGORY, GLOBAL, NONE)
- CalibrationQualityStatus: Enum (NO_EVIDENCE, SPARSE, PRELIMINARY, SUPPORTED, STRONG, INCONSISTENT)
- PredictionRecord: Persistent model capturing what was predicted, bounds, confidence, and basis.
- MeasurementOutcome: Immutable actual physical measurement linked to a PredictionRecord.
- PredictionError: Quantitative comparison distinguishing signed error, absolute error, relative error, and pp difference.
- CalibrationQuality: Meta-assessment of historical evidence volume and consistency.
- ExperimentMemoryRecord: Indexed historical unit with hardware, toolchain, candidate, and trade-off traits.
- CalibrationProvenance: Explains exactly why a calibrated prediction was adjusted.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PredictionSource(str, Enum):
    RAW_MODEL = "RAW_MODEL"
    HEURISTIC = "HEURISTIC"
    HISTORICAL_CALIBRATION = "HISTORICAL_CALIBRATION"
    HYBRID = "HYBRID"


class CalibrationState(str, Enum):
    UNCHECKED = "UNCHECKED"
    PENDING_PHYSICAL = "PENDING_PHYSICAL"
    CALIBRATED = "CALIBRATED"
    REJECTED = "REJECTED"


class CalibrationMatchLevel(str, Enum):
    MCU_SPECIFIC = "MCU_SPECIFIC"
    ARCHITECTURE_LEVEL = "ARCHITECTURE_LEVEL"
    RELATED_CATEGORY = "RELATED_CATEGORY"
    GLOBAL = "GLOBAL"
    NONE = "NONE"


class CalibrationQualityStatus(str, Enum):
    NO_EVIDENCE = "NO_EVIDENCE"
    SPARSE = "SPARSE"
    PRELIMINARY = "PRELIMINARY"
    SUPPORTED = "SUPPORTED"
    STRONG = "STRONG"
    INCONSISTENT = "INCONSISTENT"


class PredictionRecord(BaseModel):
    """
    Immutable representation of an optimization performance prediction.
    Never overwritten by actual measurements.
    """
    prediction_id: str
    experiment_id: str
    candidate_id: str
    firmware_id: str
    baseline_id: Optional[str] = None
    board_id: str
    mcu: Optional[str] = None
    architecture: Optional[str] = None
    fqbn: Optional[str] = None
    hardware_profile_hash: Optional[str] = None
    optimization_category: str                  # e.g. "GPIO", "TIMER", "LOOP", "MEMORY"
    target_metric: str                          # e.g. "loop_time", "sram_used"
    predicted_value: Optional[float] = None     # Absolute predicted value (e.g. 14.5 ms)
    predicted_delta_pct: float                  # Predicted change percentage (e.g. -20.0%)
    lower_bound_pct: float                      # Lower bound of interval (e.g. -24.0%)
    upper_bound_pct: float                      # Upper bound of interval (e.g. -16.0%)
    confidence: float = 0.5                     # Confidence factor 0.0 to 1.0
    prediction_source: PredictionSource = PredictionSource.HEURISTIC
    evidence_references: List[str] = Field(default_factory=list)
    calibration_state: CalibrationState = CalibrationState.UNCHECKED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MeasurementOutcome(BaseModel):
    """
    Immutable physical measurement outcome associated with a PredictionRecord.
    """
    outcome_id: str
    prediction_id: str
    experiment_id: str
    target_metric: str
    actual_value: float                         # Measured value on target
    actual_delta_pct: float                     # Measured change from baseline ((cand - base) / base) * 100
    confidence_interval: Optional[List[float]] = None # [min, max]
    sample_count: int = 50
    variance: float = 0.0
    measurement_method: str = "SOFTWARE_MICROS"
    instrumentation_config: str = "BALANCED"
    measurement_overhead_us: Optional[float] = None
    telemetry_provenance: str = "REAL_HARDWARE" # "REAL_HARDWARE" or "SIMULATION"
    validation_status: str = "VALIDATED"        # "VALIDATED", "REGRESSION", "INCONCLUSIVE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PredictionError(BaseModel):
    """
    Quantitative analysis of prediction error against actual measurement.
    Strictly distinguishes percentage points (pp) from relative percent error.
    """
    error_id: str
    prediction_id: str
    outcome_id: str
    target_metric: str
    predicted_delta_pct: float
    actual_delta_pct: float
    signed_error_pp: float                      # actual - predicted in percentage points (e.g. -17 - (-20) = +3.0 pp)
    absolute_error_pp: float                    # abs(actual - predicted) in percentage points
    relative_error_pct: Optional[float] = None  # abs(actual - predicted) / abs(predicted) * 100 (safely handles 0)
    directional_match: bool = True              # Both improved or both regressed
    is_outlier: bool = False
    outlier_reason: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CalibrationQuality(BaseModel):
    """
    Quality metadata for historical calibration evidence.
    """
    quality_id: str
    target_metric: str
    optimization_category: str
    match_level: CalibrationMatchLevel
    relevant_experiment_count: int = 0
    mean_absolute_error_pp: float = 0.0
    signed_bias_pp: float = 0.0                 # Systematic over/under prediction bias
    error_variance: float = 0.0
    consistency: float = 1.0                    # 0.0 to 1.0
    status: CalibrationQualityStatus = CalibrationQualityStatus.NO_EVIDENCE
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    minimum_evidence_requirement: int = 3


class ExperimentMemoryRecord(BaseModel):
    """
    Indexed historical experiment outcome stored in ExperimentMemory.
    Captures hardware profile context, trade-offs, and toolchain info.
    """
    memory_id: str
    experiment_id: str
    candidate_id: str
    board_id: str
    mcu: str
    architecture: str
    fqbn: Optional[str] = None
    compiler_toolchain: str = "avr-gcc"
    optimization_category: str
    target_metric: str
    predicted_delta_pct: float
    actual_delta_pct: float
    signed_error_pp: float
    telemetry_provenance: str = "REAL_HARDWARE" # "REAL_HARDWARE" or "SIMULATION"
    validation_status: str                      # "VALIDATED", "REGRESSION", "INCONCLUSIVE"
    trade_off_metrics: Dict[str, float] = Field(default_factory=dict) # e.g. {"sram_used": +4.2}
    is_outlier: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CalibrationProvenance(BaseModel):
    """
    Full traceability explaining why and how a prediction was calibrated.
    """
    calibrated_prediction_id: str
    raw_predicted_delta_pct: float
    calibrated_predicted_delta_pct: float
    applied_bias_correction_pp: float
    match_level: CalibrationMatchLevel
    contributing_memory_ids: List[str] = Field(default_factory=list)
    quality_status: CalibrationQualityStatus
    explanation: str
