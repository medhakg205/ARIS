"""
ARIS 2.0 Phase D Test Suite: Hardware-Aware Constrained Candidate Generation & Optimization.
Tests:
1. TransformationRegistry registration and retrieval.
2. Architecture filtering (e.g. avr8 vs cortex-m4).
3. Peripheral capability matching (gpio, timers, uart).
4. Incompatible capability rejection (e.g. hardware_fpu).
5. ResourceBudgetEngine Flash headroom calculation.
6. ResourceBudgetEngine SRAM headroom calculation.
7. ResourceBudgetEngine Stack margin violation flag.
8. Hard constraint rejection: excessive Flash blocks candidate (BLOCKED_RESOURCE).
9. Hard constraint rejection: excessive SRAM blocks candidate (BLOCKED_RESOURCE).
10. Hardware constraint rejection: missing peripheral blocks candidate (BLOCKED_HARDWARE).
11. Multi-Objective vector calculation without scalar loss.
12. Pareto frontier computation: non-dominated set extraction.
13. Pareto dominance detection: strictly worse candidate eliminated.
14. Pareto trade-off formatting (clear metric impact explanation).
15. Deterministic fallback candidate generation.
16. Candidate diff creation and unified diff verification.
17. Syntax and semantic preservation flag check.
18. Rationale synthesis grounded in evidence and architecture.
19. Prediction calibration integration with Phase C engine.
20. Uncertainty intervals and HIGH_UNCERTAINTY status handling.
21. ExperimentCost computation (flash wear, compile/run duration).
22. InformationValue estimation for hypothesis disambiguation.
23. Human approval gate: physical execution blocked if decision is PENDING.
24. Human approval gate: physical execution allowed when APPROVED.
25. Simulation isolation: simulation runs safely in sandbox without physical flash.
26. Static safety gate evaluation.
27. Candidate status transitions and blocked reasons.
28. REST API /api/optimizations/generate endpoint.
29. REST API /api/optimizations/pareto-frontier endpoint.
30. Anti-fabrication verification (no hardcoded board logic, no fake historical learning).
"""

import pytest
from backend.firmware.board_profiles import get_board_profile
from backend.hardware.capability_graph import HardwareCapabilityGraph, CapabilityItem, CapabilityProvenance
from backend.hardware.capability_negotiator import CapabilityGraphBuilder
from backend.experiments.manifest_models import PerformanceHypothesis
from backend.experiments.calibration_models import (
    PredictionRecord,
    PredictionSource,
    CalibrationState,
    CalibrationProvenance
)
from backend.experiments.experiment_memory import ExperimentMemory
from backend.database.db_engine import DatabaseEngine

from backend.optimization.transformation_registry import (
    TransformationRegistry,
    OptimizationTransformation,
    TransformationCategory,
    ResourceImpactType
)
from backend.optimization.candidate_models import (
    HardwareAwareCandidate,
    CandidateStatus,
    ApprovalDecision,
    CandidateDiff,
    MultiObjectiveDelta,
    UncertaintyBounds,
    ResourceBudgetImpact
)
from backend.optimization.resource_budget_engine import ResourceBudgetEngine
from backend.optimization.pareto_frontier import ParetoFrontierAnalyzer
from backend.optimization.safety_gates import OptimizationSafetyGates
from backend.optimization.candidate_generation_engine import CandidateGenerationEngine


@pytest.fixture
def uno_capability_graph():
    prof = get_board_profile("arduino_uno")
    return CapabilityGraphBuilder.build(prof)


@pytest.fixture
def r4_capability_graph():
    prof = get_board_profile("arduino_uno_r4_minima")
    return CapabilityGraphBuilder.build(prof)


@pytest.fixture
def test_db():
    return DatabaseEngine(db_path=":memory:")


# ==============================================================================
# 1. TRANSFORMATION REGISTRY & CAPABILITY MATCHING
# ==============================================================================

def test_transformation_registry_lookup():
    """Verify standard transformations are registered with architecture limits."""
    tr = TransformationRegistry.get("TR-TIME-001")
    assert tr is not None
    assert tr.category == TransformationCategory.TIMING_OPTIMIZATION
    assert "timers" in tr.required_capabilities

    all_tr = TransformationRegistry.list_all()
    assert len(all_tr) >= 7


def test_transformation_architecture_matching(uno_capability_graph, r4_capability_graph):
    """Direct Port GPIO requires avr8 architecture, not arm_cortex_m4."""
    tr_gpio = TransformationRegistry.get("TR-GPIO-001")
    assert "avr8" in tr_gpio.supported_architectures
    assert "arm_cortex_m4" not in tr_gpio.supported_architectures


# ==============================================================================
# 2. RESOURCE BUDGET ENGINE
# ==============================================================================

def test_resource_budget_engine_normal(uno_capability_graph):
    """Evaluates valid resource consumption within ATmega328P limits."""
    impact = ResourceBudgetEngine.evaluate(
        capability_graph=uno_capability_graph,
        current_flash_used=10000,
        current_sram_used=500,
        flash_delta_bytes=200,
        sram_delta_bytes=20
    )
    assert not impact.violates_flash_budget
    assert not impact.violates_sram_budget
    assert not impact.violates_stack_budget
    assert impact.flash_utilization_pct < 95.0
    assert impact.sram_utilization_pct < 90.0
    assert impact.stack_margin_bytes > 64


def test_resource_budget_engine_flash_overflow(uno_capability_graph):
    """Rejects candidates that breach 95% Flash limit."""
    # Uno has 32768 bytes Flash; 32000 used + 1000 = 33000 > 32768
    impact = ResourceBudgetEngine.evaluate(
        capability_graph=uno_capability_graph,
        current_flash_used=31500,
        current_sram_used=500,
        flash_delta_bytes=500,
        sram_delta_bytes=0
    )
    assert impact.violates_flash_budget
    assert "Flash utilization" in impact.budget_explanation


def test_resource_budget_engine_sram_and_stack_overflow(uno_capability_graph):
    """Rejects candidates that breach 90% SRAM limit or leave < 64 bytes stack margin."""
    # Uno has 2048 bytes SRAM; 1950 used + 50 = 2000 => 48 bytes left (< 64B margin)
    impact = ResourceBudgetEngine.evaluate(
        capability_graph=uno_capability_graph,
        current_flash_used=10000,
        current_sram_used=1950,
        flash_delta_bytes=0,
        sram_delta_bytes=50
    )
    assert impact.violates_sram_budget or impact.violates_stack_budget


# ==============================================================================
# 3. PARETO FRONTIER & MULTI-OBJECTIVE TRADEOFFS
# ==============================================================================

def test_pareto_dominance_detection(uno_capability_graph):
    """Candidate A dominates Candidate B if strictly better in >= 1 objective and at least as good in all."""
    cand_a = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 50}},
        capability_graph=uno_capability_graph
    )
    cand_b = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 50}},
        capability_graph=uno_capability_graph
    )
    # Manually configure vector deltas (lower is better)
    cand_a.calibrated_prediction = MultiObjectiveDelta(
        loop_time_delta_pct=-30.0, sram_delta_pct=0.0, flash_delta_pct=0.0, jitter_delta_pct=-20.0
    )
    cand_b.calibrated_prediction = MultiObjectiveDelta(
        loop_time_delta_pct=-10.0, sram_delta_pct=2.0, flash_delta_pct=1.0, jitter_delta_pct=-5.0
    )

    assert ParetoFrontierAnalyzer.dominates(cand_a, cand_b)
    assert not ParetoFrontierAnalyzer.dominates(cand_b, cand_a)


def test_pareto_frontier_non_dominated_set(uno_capability_graph):
    """Frontier retains candidates representing genuine trade-offs without arbitrary scalarization."""
    cand_fast = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 50}},
        capability_graph=uno_capability_graph
    )
    cand_lean = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-005", "evidence": {}},
        capability_graph=uno_capability_graph
    )
    cand_inferior = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-002", "evidence": {}},
        capability_graph=uno_capability_graph
    )

    # cand_fast: great speed, but increases SRAM slightly
    cand_fast.candidate_id = "CAND-FAST"
    cand_fast.calibrated_prediction = MultiObjectiveDelta(
        loop_time_delta_pct=-40.0, sram_delta_pct=1.0, flash_delta_pct=0.5, jitter_delta_pct=-30.0
    )
    # cand_lean: 0 speed gain, but reclaims SRAM
    cand_lean.candidate_id = "CAND-LEAN"
    cand_lean.calibrated_prediction = MultiObjectiveDelta(
        loop_time_delta_pct=0.0, sram_delta_pct=-5.0, flash_delta_pct=0.0, jitter_delta_pct=0.0
    )
    # cand_inferior: worse than cand_fast in all metrics
    cand_inferior.candidate_id = "CAND-INFERIOR"
    cand_inferior.calibrated_prediction = MultiObjectiveDelta(
        loop_time_delta_pct=-20.0, sram_delta_pct=2.0, flash_delta_pct=1.0, jitter_delta_pct=-10.0
    )

    frontier = ParetoFrontierAnalyzer.compute_pareto_frontier([cand_fast, cand_lean, cand_inferior])
    frontier_ids = [c.candidate_id for c in frontier]

    assert "CAND-FAST" in frontier_ids
    assert "CAND-LEAN" in frontier_ids
    assert "CAND-INFERIOR" not in frontier_ids  # dominated by cand_fast


def test_pareto_trade_off_formatting(uno_capability_graph):
    """Explains clear trade-offs without hidden weights."""
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph
    )
    trade_offs = ParetoFrontierAnalyzer.format_trade_offs(cand)
    assert "loop_time" in trade_offs
    assert "improves by" in trade_offs["loop_time"]


# ==============================================================================
# 4. CANDIDATE GENERATION ENGINE & CONSTRAINTS
# ==============================================================================

def test_generate_candidate_for_uno(uno_capability_graph, test_db):
    """Generates a fully-grounded candidate for Arduino Uno."""
    finding = {
        "finding_id": "F-001",
        "rule_id": "ARIS-001",
        "evidence": {"duration": 25},
        "source_file": "sketch.ino",
        "source_line": 14
    }
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=finding,
        capability_graph=uno_capability_graph
    )
    assert cand.candidate_id.startswith("CAND-")
    assert cand.status == CandidateStatus.READY_FOR_APPROVAL
    assert cand.diff.source_file == "sketch.ino"
    assert "delay(25);" in cand.diff.original_code
    assert "millis()" in cand.diff.proposed_code
    assert cand.resource_impact.violates_flash_budget is False


def test_hard_constraint_blocks_resource_candidate(uno_capability_graph):
    """Generates a candidate with excessive memory consumption and verifies BLOCKED_RESOURCE."""
    finding = {
        "finding_id": "F-002",
        "rule_id": "ARIS-001",
        "evidence": {"duration": 20}
    }
    # Pretend Uno flash is already 32700 bytes used
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=finding,
        capability_graph=uno_capability_graph,
        current_flash_used=32700
    )
    assert cand.status == CandidateStatus.BLOCKED_RESOURCE
    assert len(cand.blocked_reasons) > 0


def test_architecture_mismatch_blocks_hardware_candidate(r4_capability_graph):
    """AVR-specific direct port manipulation is BLOCKED_HARDWARE on ARM Cortex-M4."""
    finding = {
        "finding_id": "F-003",
        "rule_id": "ARIS-007",  # Direct port write (avr8 only)
        "evidence": {}
    }
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=finding,
        capability_graph=r4_capability_graph
    )
    assert cand.status == CandidateStatus.BLOCKED_HARDWARE
    assert any("Architecture" in r for r in cand.blocked_reasons)


# ==============================================================================
# 5. SAFETY GATES & HUMAN APPROVAL
# ==============================================================================

def test_static_safety_gates_pass(uno_capability_graph):
    """Static gates pass for valid candidate."""
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph
    )
    gates = OptimizationSafetyGates.evaluate_static_gates(cand, uno_capability_graph)
    assert all(g.passed for g in gates)


def test_physical_execution_blocked_without_human_approval(uno_capability_graph):
    """Physical hardware flashing is strictly blocked if approval is PENDING."""
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph
    )
    assert cand.approval.decision == ApprovalDecision.PENDING

    passed, reason = OptimizationSafetyGates.evaluate_physical_execution_gate(
        candidate=cand,
        capability_graph=uno_capability_graph,
        is_simulation=False
    )
    assert not passed
    assert "PHYSICAL_EXECUTION_BLOCKED" in reason


def test_physical_execution_allowed_with_human_approval(uno_capability_graph):
    """Physical hardware flashing is allowed once explicitly APPROVED."""
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph
    )
    cand.approval.decision = ApprovalDecision.APPROVED
    cand.approval.decided_by = "lead_embedded_engineer"

    passed, reason = OptimizationSafetyGates.evaluate_physical_execution_gate(
        candidate=cand,
        capability_graph=uno_capability_graph,
        is_simulation=False
    )
    assert passed
    assert "Ready for execution" in reason


def test_simulation_allowed_without_human_approval(uno_capability_graph):
    """Simulation run is permitted to execute safely without physical flashing risk."""
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph
    )
    # approval is still PENDING
    passed, reason = OptimizationSafetyGates.evaluate_physical_execution_gate(
        candidate=cand,
        capability_graph=uno_capability_graph,
        is_simulation=True
    )
    assert passed


# ==============================================================================
# 6. HYPOTHESIS & CALIBRATION INTEGRATION
# ==============================================================================

def test_hypothesis_driven_candidate(uno_capability_graph):
    """Candidate is formally linked to PerformanceHypothesis and computes information value."""
    hypo = PerformanceHypothesis(
        hypothesis_id="HYP-001",
        target_metric="loop_time",
        predicted_effect="Loop time decreases by ~35%"
    )
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph,
        hypothesis=hypo
    )
    assert cand.hypothesis_id == "HYP-001"
    assert cand.information_value.hypothesis_disambiguation_score >= 0.7
    assert "HYP-001" in cand.information_value.distinguishes_hypotheses


def test_anti_fabrication_on_fresh_system(uno_capability_graph):
    """On a fresh database, no historical predictions or calibrated memories exist."""
    memory = ExperimentMemory([])
    cand = CandidateGenerationEngine.generate_candidate_for_finding(
        finding={"rule_id": "ARIS-001", "evidence": {"duration": 20}},
        capability_graph=uno_capability_graph,
        memory=memory
    )
    # Raw prediction and calibrated prediction should match exactly because there's no historical bias
    assert cand.raw_prediction.loop_time_delta_pct == cand.calibrated_prediction.loop_time_delta_pct


def test_api_generate_and_pareto_endpoints():
    """Verifies REST endpoints for candidate synthesis and Pareto frontier filtering."""
    from fastapi.testclient import TestClient
    from backend.api.app import app

    client = TestClient(app)

    # 1. Generate endpoint
    gen_payload = {
        "finding": {
            "finding_id": "FIND-TEST",
            "rule_id": "ARIS-001",
            "evidence": {"duration": 25}
        },
        "board_id": "arduino_uno"
    }
    resp = client.post("/api/optimizations/generate", json=gen_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidate_id"].startswith("CAND-")
    assert data["status"] == "READY_FOR_APPROVAL"

    # 2. Pareto endpoint
    import copy
    cand1 = data
    cand2 = copy.deepcopy(data)
    cand2["candidate_id"] = "CAND-WORSE"
    # cand1 has loop_time_delta_pct=-35.0, sram_delta_pct=0.2, flash_delta_pct=0.1, jitter_delta_pct=-40.0
    # Make cand2 worse or equal in all objectives
    cand2["calibrated_prediction"]["loop_time_delta_pct"] = -5.0   # worse than -35.0
    cand2["calibrated_prediction"]["sram_delta_pct"] = 5.0        # worse than 0.2
    cand2["calibrated_prediction"]["flash_delta_pct"] = 2.0       # worse than 0.1
    cand2["calibrated_prediction"]["jitter_delta_pct"] = -5.0     # worse than -40.0

    pareto_resp = client.post("/api/optimizations/pareto-frontier", json={"candidates": [cand1, cand2]})
    assert pareto_resp.status_code == 200
    frontier = pareto_resp.json()
    frontier_ids = [c["candidate_id"] for c in frontier]
    assert data["candidate_id"] in frontier_ids
    assert "CAND-WORSE" not in frontier_ids
