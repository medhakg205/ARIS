"""
ARIS Optimization Safety Gates & Human Approval Verification.
Validates candidate safety, resource constraints, hardware prerequisites,
and mandates explicit human engineer approval before physical target flashing.
"""

from typing import List, Dict, Any, Tuple
from backend.hardware.capability_graph import HardwareCapabilityGraph
from backend.optimization.candidate_models import (
    HardwareAwareCandidate,
    CandidateStatus,
    ApprovalDecision
)


class SafetyGateResult:
    def __init__(self, passed: bool, gate_name: str, reason: str):
        self.passed = passed
        self.gate_name = gate_name
        self.reason = reason


class OptimizationSafetyGates:
    """
    Independent gatekeeper enforcing deterministic safety boundaries.
    No candidate can reach physical hardware execution without passing all gates.
    """

    @classmethod
    def evaluate_static_gates(
        cls,
        candidate: HardwareAwareCandidate,
        capability_graph: HardwareCapabilityGraph
    ) -> List[SafetyGateResult]:
        """
        Runs static verification gates prior to candidate promotion.
        """
        results: List[SafetyGateResult] = []

        # Gate 1: Hardware peripheral & capability check
        hw_ok = True
        missing_periphs = []
        for req in candidate.required_peripherals:
            cap_item = getattr(capability_graph, req, None)
            if cap_item is None or cap_item.available is False:
                hw_ok = False
                missing_periphs.append(req)

        if not hw_ok:
            results.append(SafetyGateResult(
                passed=False,
                gate_name="HARDWARE_CAPABILITY_GATE",
                reason=f"Target hardware lacks required capability/peripheral: {', '.join(missing_periphs)}"
            ))
        else:
            results.append(SafetyGateResult(
                passed=True,
                gate_name="HARDWARE_CAPABILITY_GATE",
                reason="All required hardware peripherals verified available."
            ))

        # Gate 2: Incompatible capability check (e.g. FPU, etc.)
        if candidate.incompatible_capabilities_detected:
            results.append(SafetyGateResult(
                passed=False,
                gate_name="HARDWARE_COMPATIBILITY_GATE",
                reason=f"Incompatible capabilities present: {', '.join(candidate.incompatible_capabilities_detected)}"
            ))
        else:
            results.append(SafetyGateResult(
                passed=True,
                gate_name="HARDWARE_COMPATIBILITY_GATE",
                reason="No incompatible hardware features detected."
            ))

        # Gate 3: Resource Budget gate
        res = candidate.resource_impact
        if res.violates_flash_budget or res.violates_sram_budget or res.violates_stack_budget:
            results.append(SafetyGateResult(
                passed=False,
                gate_name="RESOURCE_BUDGET_GATE",
                reason=f"Resource budget violation: {res.budget_explanation}"
            ))
        else:
            results.append(SafetyGateResult(
                passed=True,
                gate_name="RESOURCE_BUDGET_GATE",
                reason="Memory and stack projections comfortably within hardware headroom limits."
            ))

        # Gate 4: Diff & Syntax gate
        if not candidate.diff.syntax_valid or not candidate.diff.preserves_semantics:
            results.append(SafetyGateResult(
                passed=False,
                gate_name="DIFF_SEMANTICS_GATE",
                reason="Syntactic error or semantic regression in proposed candidate diff."
            ))
        else:
            results.append(SafetyGateResult(
                passed=True,
                gate_name="DIFF_SEMANTICS_GATE",
                reason="Candidate diff is syntactically well-formed and preserves program intent."
            ))

        return results

    @classmethod
    def evaluate_physical_execution_gate(
        cls,
        candidate: HardwareAwareCandidate,
        capability_graph: HardwareCapabilityGraph,
        is_simulation: bool = False
    ) -> Tuple[bool, str]:
        """
        Authoritative gate check before deploying firmware to physical MCU.
        Simulations may run safely in sandboxes, but physical hardware execution
        MANDATES human approval.
        """
        # 1. Run all static gates
        static_gates = cls.evaluate_static_gates(candidate, capability_graph)
        failed_gates = [g for g in static_gates if not g.passed]
        if failed_gates:
            reasons = "; ".join([f"{g.gate_name}: {g.reason}" for g in failed_gates])
            return False, f"Static safety gates failed: {reasons}"

        # 2. Human approval gate for physical hardware
        if not is_simulation:
            if candidate.approval.decision != ApprovalDecision.APPROVED:
                return False, "PHYSICAL_EXECUTION_BLOCKED: Explicit human engineer approval is required before flashing physical MCU target."

        return True, "All safety gates passed. Ready for execution."
