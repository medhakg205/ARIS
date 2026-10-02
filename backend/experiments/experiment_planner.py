"""
ARIS Experiment Planner & Experiment State Machine.
Defines:
- ExperimentState: Formal state machine enum:
  PLANNED -> PRECHECKING -> BASELINE_READY -> INSTRUMENTATION_READY ->
  RUNNING_BASELINE -> BASELINE_COLLECTED -> RUNNING_CANDIDATE -> CANDIDATE_COLLECTED ->
  EVALUATING -> SUFFICIENT / INCONCLUSIVE -> IMPROVEMENT / REGRESSION / FAILED / ABORTED / COMPLETED
- StoppingCondition: Explicit stopping conditions:
  STOP_SUCCESS, STOP_REGRESSION, STOP_INCONCLUSIVE, STOP_SAFETY,
  STOP_IDENTITY_MISMATCH, STOP_TIMEOUT, STOP_MEASUREMENT_INVALID
- OptimizationExperimentContract: Explicit contract tying change to hypotheses, required evidence,
  target metric, non-regression invariants, and acceptance criteria.
- ExperimentPlanner: Comprehensive planner producing verified, reproducible ExperimentPlan entities.
- ExperimentStateMachine: Enforces valid state transitions and blocks invalid lifecycle transitions.
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from backend.hardware.capability_graph import HardwareCapabilityGraph
from backend.experiments.manifest_models import (
    PerformanceHypothesis,
    ExperimentPlan,
    ExperimentManifest
)
from backend.experiments.measurement_planner import (
    MeasurementPlan,
    AdaptiveMeasurementPlanner
)
from backend.experiments.sufficiency_evaluator import (
    SufficiencyReport,
    EvidenceQuality
)
from backend.telemetry.telemetry_schema import ArisException


class ExperimentState(str, Enum):
    PLANNED = "PLANNED"
    PRECHECKING = "PRECHECKING"
    BASELINE_READY = "BASELINE_READY"
    INSTRUMENTATION_READY = "INSTRUMENTATION_READY"
    RUNNING_BASELINE = "RUNNING_BASELINE"
    BASELINE_COLLECTED = "BASELINE_COLLECTED"
    RUNNING_CANDIDATE = "RUNNING_CANDIDATE"
    CANDIDATE_COLLECTED = "CANDIDATE_COLLECTED"
    EVALUATING = "EVALUATING"
    SUFFICIENT = "SUFFICIENT"
    INCONCLUSIVE = "INCONCLUSIVE"
    IMPROVEMENT = "IMPROVEMENT"
    REGRESSION = "REGRESSION"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    COMPLETED = "COMPLETED"


class StoppingCondition(str, Enum):
    STOP_SUCCESS = "STOP_SUCCESS"
    STOP_REGRESSION = "STOP_REGRESSION"
    STOP_INCONCLUSIVE = "STOP_INCONCLUSIVE"
    STOP_SAFETY = "STOP_SAFETY"
    STOP_IDENTITY_MISMATCH = "STOP_IDENTITY_MISMATCH"
    STOP_TIMEOUT = "STOP_TIMEOUT"
    STOP_MEASUREMENT_INVALID = "STOP_MEASUREMENT_INVALID"


class OptimizationExperimentContract(BaseModel):
    """
    Formal optimization experiment contract.
    Contains: what is changed, why, target metric, invariants, and acceptance criteria.
    """
    candidate_id: str
    target_file: str
    what_is_changed: str
    why_it_is_changed: str
    target_metric: str
    expected_improvement_pct: float
    must_not_regress_metrics: List[str] = Field(default_factory=lambda: ["sram_used", "runtime_fault"])
    required_hardware_capabilities: List[str] = Field(default_factory=list)
    acceptance_criteria: Dict[str, Any] = Field(default_factory=dict)
    safety_constraints: List[str] = Field(default_factory=list)


# Valid directed transitions in the ARIS Experiment State Machine
VALID_TRANSITIONS: Dict[ExperimentState, Set[ExperimentState]] = {
    ExperimentState.PLANNED: {ExperimentState.PRECHECKING, ExperimentState.ABORTED},
    ExperimentState.PRECHECKING: {ExperimentState.BASELINE_READY, ExperimentState.FAILED, ExperimentState.ABORTED},
    ExperimentState.BASELINE_READY: {ExperimentState.INSTRUMENTATION_READY, ExperimentState.RUNNING_BASELINE, ExperimentState.ABORTED},
    ExperimentState.INSTRUMENTATION_READY: {ExperimentState.RUNNING_BASELINE, ExperimentState.ABORTED},
    ExperimentState.RUNNING_BASELINE: {ExperimentState.BASELINE_COLLECTED, ExperimentState.FAILED, ExperimentState.ABORTED},
    ExperimentState.BASELINE_COLLECTED: {ExperimentState.RUNNING_CANDIDATE, ExperimentState.INCONCLUSIVE, ExperimentState.ABORTED},
    ExperimentState.RUNNING_CANDIDATE: {ExperimentState.CANDIDATE_COLLECTED, ExperimentState.FAILED, ExperimentState.ABORTED},
    ExperimentState.CANDIDATE_COLLECTED: {ExperimentState.EVALUATING, ExperimentState.FAILED, ExperimentState.ABORTED},
    ExperimentState.EVALUATING: {ExperimentState.SUFFICIENT, ExperimentState.INCONCLUSIVE, ExperimentState.FAILED, ExperimentState.ABORTED},
    ExperimentState.SUFFICIENT: {ExperimentState.IMPROVEMENT, ExperimentState.REGRESSION, ExperimentState.INCONCLUSIVE, ExperimentState.COMPLETED},
    ExperimentState.INCONCLUSIVE: {ExperimentState.COMPLETED, ExperimentState.ABORTED},
    ExperimentState.IMPROVEMENT: {ExperimentState.COMPLETED},
    ExperimentState.REGRESSION: {ExperimentState.COMPLETED, ExperimentState.FAILED},
    ExperimentState.FAILED: set(),
    ExperimentState.ABORTED: set(),
    ExperimentState.COMPLETED: set()
}


class ExperimentStateMachine:
    """
    Enforces valid state transitions and guarantees strict pre-validation checks.
    """

    @classmethod
    def transition(
        cls,
        current_state: ExperimentState,
        next_state: ExperimentState,
        candidate_data_present: bool = False
    ) -> ExperimentState:
        """
        Validates and transitions state.
        Raises ArisException if transition is invalid or if candidate validation is attempted without candidate data.
        """
        # Rule: Do not allow candidate validation before candidate data exists
        if next_state in (ExperimentState.IMPROVEMENT, ExperimentState.REGRESSION, ExperimentState.COMPLETED) and not candidate_data_present:
            if current_state in (ExperimentState.PLANNED, ExperimentState.PRECHECKING, ExperimentState.RUNNING_BASELINE, ExperimentState.BASELINE_COLLECTED):
                raise ArisException(
                    error_code="ARIS_VALIDATION_FAILED",
                    message="Cannot mark experiment as validated or completed before candidate telemetry has been executed and collected.",
                    details={"current_state": current_state.value, "attempted_state": next_state.value},
                    recoverable=False,
                    status_code=400
                )

        allowed = VALID_TRANSITIONS.get(current_state, set())
        if next_state not in allowed:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Invalid experiment state transition from '{current_state.value}' to '{next_state.value}'.",
                details={
                    "current_state": current_state.value,
                    "target_state": next_state.value,
                    "allowed_transitions": [s.value for s in allowed]
                },
                recoverable=False,
                status_code=400
            )

        return next_state


class ExperimentPlanner:
    """
    Deterministic Experiment Planner.
    Coordinates HardwareCapabilityGraph, Hypotheses, MeasurementPlan, and Safety constraints.
    """

    @classmethod
    def create_plan(
        cls,
        experiment_id: str,
        objective: str,
        hypotheses: List[PerformanceHypothesis],
        graph: HardwareCapabilityGraph,
        measurement_plan: MeasurementPlan,
        firmware_id: str,
        candidate_id: Optional[str] = None,
        candidate_contract: Optional[OptimizationExperimentContract] = None,
        reproducibility_params: Optional[Dict[str, Any]] = None,
        safety_constraints: Optional[List[str]] = None
    ) -> ExperimentPlan:
        """
        Generates a validated ExperimentPlan.
        """
        # Validate that required hardware identity matches graph
        if not graph.board_id:
            raise ArisException(
                error_code="ARIS_BOARD_NOT_FOUND",
                message="Cannot create experiment plan: board identity is missing in capability graph.",
                details={"experiment_id": experiment_id},
                recoverable=False,
                status_code=400
            )

        # Build acceptance criteria from candidate contract if present
        acceptance: Dict[str, Any] = {}
        if candidate_contract:
            target_metric = candidate_contract.target_metric
            exp_imp = candidate_contract.expected_improvement_pct
            # Standard criteria: min 5% improvement or half of expected
            min_imp = max(5.0, exp_imp * 0.5)
            acceptance[f"{target_metric}_min_improvement_pct"] = min_imp
            for inv_m in candidate_contract.must_not_regress_metrics:
                acceptance[f"{inv_m}_max_regression_pct"] = 0.0

        # Safety constraints
        constraints: Dict[str, Any] = {
            "board_id": graph.board_id,
            "architecture": graph.architecture,
            "mcu": graph.mcu,
            "fqbn": graph.fqbn,
            "safety_rules": safety_constraints or ["Watchdog enabled", "Max loop latency < 100ms", "SRAM headroom > 64B"]
        }

        repro = reproducibility_params or {}
        repro["planned_toolchain"] = graph.compiler_toolchain.value or "avr-gcc"
        repro["planned_architecture"] = graph.architecture

        target_hyp_id = hypotheses[0].hypothesis_id if hypotheses else "HYP-DEFAULT"

        return ExperimentPlan(
            plan_id=experiment_id,
            objective=objective,
            target_hypothesis_id=target_hyp_id,
            required_metrics=measurement_plan.enabled_metrics,
            required_instrumentation=measurement_plan.required_capabilities,
            hardware_constraints=constraints,
            sample_count=measurement_plan.sample_count,
            duration_seconds=measurement_plan.duration_seconds,
            acceptance_criteria=acceptance,
            reproducibility_params=repro
        )

    @classmethod
    def verify_reproducibility(
        cls,
        plan: ExperimentPlan,
        current_graph: HardwareCapabilityGraph,
        current_manifest: Optional[ExperimentManifest] = None
    ) -> tuple[bool, List[str]]:
        """
        Verifies whether current physical environment matches the planned experiment.
        Returns (is_reproducible, list_of_mismatches).
        """
        mismatches: List[str] = []

        planned_board = plan.hardware_constraints.get("board_id")
        if planned_board and planned_board != current_graph.board_id:
            mismatches.append(f"Board identity mismatch: planned '{planned_board}', current target is '{current_graph.board_id}'")

        planned_arch = plan.hardware_constraints.get("architecture")
        if planned_arch and planned_arch != current_graph.architecture:
            mismatches.append(f"Architecture mismatch: planned '{planned_arch}', current target is '{current_graph.architecture}'")

        planned_mcu = plan.hardware_constraints.get("mcu")
        if planned_mcu and current_graph.mcu and planned_mcu.lower() != current_graph.mcu.lower():
            mismatches.append(f"MCU mismatch: planned '{planned_mcu}', current target is '{current_graph.mcu}'")

        if current_manifest:
            planned_toolchain = plan.reproducibility_params.get("planned_toolchain")
            if planned_toolchain and current_manifest.compiler_toolchain != planned_toolchain:
                mismatches.append(f"Toolchain mismatch: planned '{planned_toolchain}', current manifest is '{current_manifest.compiler_toolchain}'")

        return len(mismatches) == 0, mismatches
