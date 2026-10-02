"""
ARIS Physical Hardware Closed-Loop Experiment Evidence Package.
Defines machine-readable, tamper-evident evidence packages capturing:
- Experiment ID & Lineage
- Physical Board Identity & FQBN
- Hardware Capability Graph snapshot
- Baseline & Candidate firmware hashes
- Build & toolchain metadata
- Baseline & Candidate statistical metrics
- Prediction & Calibration state
- Prediction Error breakdown
- Multi-objective validation outcome
- Rollback execution & post-rollback verification
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class BuildMetadataSnapshot(BaseModel):
    toolchain: str                       # e.g. "arduino-cli 1.1.2"
    compiler: str                        # e.g. "avr-gcc 7.3.0"
    fqbn: str                            # e.g. "arduino:avr:uno"
    binary_size_bytes: int = 0
    flash_utilization_pct: float = 0.0
    sram_utilization_bytes: int = 0
    sram_utilization_pct: float = 0.0
    firmware_hash: str                   # SHA-256 of binary


class HandshakeVerificationSnapshot(BaseModel):
    handshake_success: bool
    runtime_version: str
    protocol_version: str
    board_id: str
    mcu: str
    architecture: str
    clock_hz: int
    identity_verified: bool
    frame_type: str = "ACK"


class RollbackVerificationRecord(BaseModel):
    rollback_executed: bool = False
    rollback_status: str = "NONE"        # "NONE", "ROLLBACK_SUCCESS", "ROLLBACK_FAILED"
    baseline_firmware_restored: bool = False
    baseline_handshake_verified: bool = False
    post_rollback_telemetry_resumed: bool = False
    notes: Optional[str] = None


class PhysicalExperimentEvidencePackage(BaseModel):
    """
    Authoritative, machine-readable evidence package capturing the entire
    physical closed-loop lifecycle without omissions or synthetic defaults.
    """
    evidence_package_id: str
    experiment_id: str
    execution_mode: str = "REAL_HARDWARE"  # "REAL_HARDWARE" or "SIMULATION"

    # Physical Hardware Identity
    serial_port: str
    board_id: str
    display_name: str
    fqbn: str
    mcu: str
    architecture: str
    clock_hz: int

    # Capability Graph Summary
    flash_total_bytes: int
    sram_total_bytes: int
    toolchain_name: str

    # Firmware & Code Lineage
    baseline_firmware_id: str
    baseline_firmware_hash: str
    candidate_firmware_id: str
    candidate_firmware_hash: str

    # Build Verification
    baseline_build: BuildMetadataSnapshot
    candidate_build: BuildMetadataSnapshot

    # Runtime Handshakes
    baseline_handshake: HandshakeVerificationSnapshot
    candidate_handshake: HandshakeVerificationSnapshot

    # Experiment Plan & Measurement Conditions
    sample_count: int
    duration_seconds: float
    instrumentation_mode: str
    target_metric: str

    # Empirical Physical Measurements
    baseline_statistics: Dict[str, Any]
    candidate_statistics: Dict[str, Any]

    # Predictions & Empirical Delta
    raw_prediction_delta_pct: float
    calibrated_prediction_delta_pct: float
    actual_measured_delta_pct: float

    # Quantitative Prediction Error (distinguishing pp and %)
    raw_prediction_error_pp: float
    calibrated_prediction_error_pp: float

    # Multi-Objective Outcomes
    multi_objective_deltas: Dict[str, float] = Field(default_factory=dict)
    validation_status: str              # "IMPROVEMENT", "REGRESSION", "NO_SIGNIFICANT_CHANGE", "INCONCLUSIVE"
    validation_reason: str

    # Calibration & Memory Impact
    experiment_memory_updated: bool = False
    calibration_updated: bool = False

    # Rollback Verification
    rollback: RollbackVerificationRecord = Field(default_factory=RollbackVerificationRecord)

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)
