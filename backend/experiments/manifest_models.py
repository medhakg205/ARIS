"""
ARIS Hardware Experiment Foundation & Manifest System.
Defines models and schemas for:
- Competing Performance Hypotheses (Evidence references, predicted effect, confidence, constraints)
- Experiment Plan (Objective, target hypothesis, required metrics, acceptance criteria)
- Reproducible Experiment Manifest (Hardware identity, firmware & candidate hashes, conditions, results)
- Provenance Lineage tracking: Firmware -> Static Analysis -> Runtime -> Finding -> Hypothesis -> Candidate -> Experiment -> Validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class PerformanceHypothesis(BaseModel):
    """
    Model for competing performance hypotheses.
    Grounds predicted effect in static & runtime evidence without AI hallucinations.
    """
    hypothesis_id: str
    target_metric: str                  # e.g. "loop_time", "sram_used", "cpu_load"
    predicted_effect: str               # e.g. "Loop execution latency decreases by ~30-40%"
    confidence: float = 0.85            # 0.0 to 1.0 confidence rating
    evidence_references: List[str] = Field(default_factory=list) # IDs of findings, metrics, or logs
    supporting_static_evidence: Dict[str, Any] = Field(default_factory=dict)
    supporting_runtime_evidence: Dict[str, Any] = Field(default_factory=dict)
    hardware_constraints: List[str] = Field(default_factory=list) # e.g. ["Requires 16MHz clock", "SRAM > 1KB"]
    status: str = "PROPOSED"            # "PROPOSED", "ACCEPTED", "REJECTED", "TESTED"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExperimentPlan(BaseModel):
    """
    Formal plan for executing an optimization experiment.
    Defines explicit acceptance criteria and required hardware instrumentation.
    """
    plan_id: str
    objective: str
    target_hypothesis_id: str
    required_metrics: List[str]
    required_instrumentation: List[str]
    hardware_constraints: Dict[str, Any] = Field(default_factory=dict)
    sample_count: int = 50
    duration_seconds: float = 10.0
    acceptance_criteria: Dict[str, Any] = Field(default_factory=dict) # e.g. {"loop_time_max_pct_change": -5.0}
    reproducibility_params: Dict[str, Any] = Field(default_factory=dict)


class ExperimentManifest(BaseModel):
    """
    Persistent, fully reproducible experiment manifest capturing exact hardware,
    toolchain, code hash, measurement condition, and outcome states.
    """
    manifest_id: str
    experiment_id: str
    board_id: str
    mcu: Optional[str] = None
    architecture: Optional[str] = None
    fqbn: Optional[str] = None

    # Code hashes for exact reproducibility
    firmware_hash: str                  # SHA-256 of baseline sketch / binary
    candidate_hash: str                 # SHA-256 of candidate sketch / binary
    compiler_toolchain: str             # e.g. "avr-gcc 7.3.0"
    runtime_version: str = "1.0.0"
    instrumentation_mode: str = "BALANCED"

    # Execution parameters
    selected_measurements: List[str] = Field(default_factory=list)
    duration_seconds: float = 10.0
    sample_count: int = 50
    experiment_conditions: Dict[str, Any] = Field(default_factory=dict)

    # Outcomes
    prediction: Dict[str, Any] = Field(default_factory=dict)
    actual_result: Dict[str, Any] = Field(default_factory=dict)
    validation_result: Optional[str] = None # "IMPROVEMENT", "REGRESSION", "INCONCLUSIVE", "NO_SIGNIFICANT_CHANGE"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProvenanceLineage(BaseModel):
    """
    Full audit lineage connecting:
    Firmware -> Static Analysis -> Runtime Run -> Finding -> Hypothesis -> Candidate -> Experiment -> Prediction -> Physical Run -> Validation.
    """
    lineage_id: str
    firmware_id: str
    analysis_run_id: Optional[str] = None
    baseline_run_id: Optional[str] = None
    finding_ids: List[str] = Field(default_factory=list)
    hypothesis_id: Optional[str] = None
    candidate_id: Optional[str] = None
    experiment_id: Optional[str] = None
    manifest_id: Optional[str] = None
    candidate_run_id: Optional[str] = None
    validation_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
