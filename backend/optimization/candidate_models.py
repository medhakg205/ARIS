"""
ARIS Hardware-Aware Optimization Candidate Models.
Defines extended Candidate model, Resource Budgets, Multi-Objective Vectors,
Experiment Costs, Information Value, and Human Approval records.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field

from backend.optimization.transformation_registry import TransformationCategory, ResourceImpactType


class CandidateStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED_RESOURCE = "BLOCKED_RESOURCE"
    BLOCKED_HARDWARE = "BLOCKED_HARDWARE"
    BLOCKED_SAFETY = "BLOCKED_SAFETY"
    BLOCKED_BUILD = "BLOCKED_BUILD"
    HIGH_UNCERTAINTY = "HIGH_UNCERTAINTY"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ROLLED_BACK = "ROLLED_BACK"


class CandidateReversibility(str, Enum):
    FULLY_REVERSIBLE = "FULLY_REVERSIBLE"
    MANUAL_INTERVENTION = "MANUAL_INTERVENTION"


class ApprovalDecision(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class HumanApprovalRecord(BaseModel):
    """Formal audit trail of human engineer authorization for hardware validation."""
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decided_by: str = "operator"
    timestamp: Optional[str] = None
    reason: Optional[str] = None
    pre_approval_checks_passed: bool = False
    notes: Optional[str] = None


class ResourceBudgetImpact(BaseModel):
    """Evaluated resource changes against board limits."""
    flash_delta_bytes: int = 0
    sram_delta_bytes: int = 0
    flash_headroom_bytes_remaining: int
    sram_headroom_bytes_remaining: int
    flash_utilization_pct: float
    sram_utilization_pct: float
    stack_margin_bytes: int
    violates_flash_budget: bool = False
    violates_sram_budget: bool = False
    violates_stack_budget: bool = False
    budget_explanation: str = ""


class MultiObjectiveDelta(BaseModel):
    """Multi-objective performance impact projections."""
    loop_time_delta_pct: float = 0.0      # Lower is better (negative delta)
    sram_delta_pct: float = 0.0           # Lower is better
    flash_delta_pct: float = 0.0          # Lower is better
    jitter_delta_pct: float = 0.0         # Lower is better

    def as_vector(self) -> Dict[str, float]:
        return {
            "loop_time_delta_pct": self.loop_time_delta_pct,
            "sram_delta_pct": self.sram_delta_pct,
            "flash_delta_pct": self.flash_delta_pct,
            "jitter_delta_pct": self.jitter_delta_pct,
        }


class UncertaintyBounds(BaseModel):
    """Statistical bounds and variance of prediction."""
    lower_bound_pct: float
    upper_bound_pct: float
    variance: float = 0.0
    confidence_score: float = 0.8
    is_high_uncertainty: bool = False


class ExperimentCost(BaseModel):
    """Resource and time cost to physically validate candidate on hardware."""
    estimated_compile_duration_s: float = 5.0
    estimated_flash_duration_s: float = 6.0
    recommended_measurement_samples: int = 50
    estimated_run_duration_s: float = 10.0
    total_cost_score: float = 1.0  # normalized cost rating
    wear_risk: str = "NEGLIGIBLE"   # Flash ROM write cycle count concern level


class InformationValue(BaseModel):
    """Value of experiment outcome in resolving competing hypotheses or reducing model uncertainty."""
    hypothesis_disambiguation_score: float = 0.5  # 0.0 to 1.0
    uncertainty_reduction_potential: float = 0.5
    composite_information_value: float = 0.5
    distinguishes_hypotheses: List[str] = Field(default_factory=list)


class CandidateDiff(BaseModel):
    """Structured code difference for audit and verification."""
    source_file: str
    start_line: int
    end_line: int
    original_code: str
    proposed_code: str
    unified_diff: str
    syntax_valid: bool = True
    preserves_semantics: bool = True


class HardwareAwareCandidate(BaseModel):
    """
    ARIS 2.0 Hardware-Aware Optimization Candidate.
    Fully connects hardware capability graph, evidence hypothesis, resource budgets,
    multi-objective metrics, uncertainty, and human approvals.
    """
    candidate_id: str
    finding_id: str
    hypothesis_id: Optional[str] = None
    lineage_id: Optional[str] = None
    transformation_id: str
    transformation_category: TransformationCategory
    title: str

    # Target Hardware Context
    board_id: str
    mcu: Optional[str] = None
    architecture: Optional[str] = None
    fqbn: Optional[str] = None
    hardware_profile_hash: Optional[str] = None

    # Source code & diff
    source_location: Dict[str, Any]
    diff: CandidateDiff

    # Multi-Objective Projected & Calibrated Impact
    raw_prediction: MultiObjectiveDelta
    calibrated_prediction: MultiObjectiveDelta
    uncertainty: UncertaintyBounds
    calibration_provenance_id: Optional[str] = None

    # Resource & Peripheral Constraints
    resource_impact: ResourceBudgetImpact
    required_peripherals: List[str] = Field(default_factory=list)
    hardware_constraint_checks_passed: bool = True
    incompatible_capabilities_detected: List[str] = Field(default_factory=list)

    # Rationale & Explainability
    rationale: str
    trade_offs_explained: Dict[str, str] = Field(default_factory=dict)
    hardware_consideration: str

    # Execution & Safety
    reversibility: CandidateReversibility = CandidateReversibility.FULLY_REVERSIBLE
    safety_risk: str = "LOW"
    status: CandidateStatus = CandidateStatus.ELIGIBLE
    blocked_reasons: List[str] = Field(default_factory=list)

    # Experiment & Value Metrics
    experiment_cost: ExperimentCost = Field(default_factory=ExperimentCost)
    information_value: InformationValue = Field(default_factory=InformationValue)
    contract_id: Optional[str] = None

    # Human Gate
    approval: HumanApprovalRecord = Field(default_factory=HumanApprovalRecord)

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
