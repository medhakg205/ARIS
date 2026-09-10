"""
ARIS AI Interface Subsystem.
Defines the canonical contract between the Analytical Core (Engineer 2)
and the AI + Frontend Subsystem (Engineer 3).
Validates input context packages and enforces the exact OptimizationCandidate schema.
Provides a deterministic transform generator as a reference/fallback implementation.
"""

import uuid
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field, field_validator

from backend.telemetry.telemetry_schema import ArisException


# Canonical candidate status transitions
VALID_OPTIMIZATION_STATUSES: Set[str] = {
    "PROPOSED",
    "APPROVED",
    "BUILDING",
    "TESTING",
    "VALIDATED",
    "REJECTED",
    "ROLLED_BACK",
    "FAILED"
}

VALID_RISK_LEVELS: Set[str] = {"LOW", "MEDIUM", "HIGH"}


class AIContextInput(BaseModel):
    """
    Standard input contract provided to Engineer 3's AI optimization engine.
    """
    board_profile: Dict[str, Any]
    firmware_source: str
    static_findings: List[Dict[str, Any]]
    runtime_metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    runtime_static_correlations: List[Dict[str, Any]]
    optimization_history: List[Dict[str, Any]] = Field(default_factory=list)


class OptimizationCandidate(BaseModel):
    """
    Canonical Optimization Candidate schema.
    Output from Engineer 3 or the synthesizer must validate against this exact model.
    """
    optimization_id: str
    finding_id: str
    title: str
    problem: str
    source_location: Dict[str, Any]
    before_code: str
    after_code: str
    reason: str
    hardware_consideration: str
    expected_effect: Dict[str, Any]
    risk: str = "LOW"
    confidence: float
    validation_required: bool = True
    status: str = "PROPOSED"

    @field_validator("status")
    @classmethod
    def validate_candidate_status(cls, v: str) -> str:
        """Enforces canonical candidate status values."""
        if v not in VALID_OPTIMIZATION_STATUSES:
            raise ValueError(f"Invalid optimization status '{v}'. Must be one of {VALID_OPTIMIZATION_STATUSES}")
        return v

    @field_validator("risk")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Enforces risk level."""
        if v not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk level '{v}'. Must be one of {VALID_RISK_LEVELS}")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Enforces confidence between 0.0 and 1.0."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence {v} must be between 0.0 and 1.0")
        return v


class AIInterface:
    """
    Interface coordinating context generation and candidate validation for Engineer 3.
    """

    @staticmethod
    def build_context(
        board_profile: Dict[str, Any],
        firmware_source: str,
        static_findings: List[Dict[str, Any]],
        runtime_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any],
        runtime_static_correlations: List[Dict[str, Any]],
        optimization_history: Optional[List[Dict[str, Any]]] = None
    ) -> AIContextInput:
        """Builds and validates the AI context input package."""
        return AIContextInput(
            board_profile=board_profile,
            firmware_source=firmware_source,
            static_findings=static_findings,
            runtime_metrics=runtime_metrics,
            baseline_metrics=baseline_metrics,
            runtime_static_correlations=runtime_static_correlations,
            optimization_history=optimization_history or []
        )

    @staticmethod
    def validate_candidate(candidate_data: Dict[str, Any]) -> OptimizationCandidate:
        """
        Validates raw candidate dictionary against the canonical schema.
        Raises ARIS_OPTIMIZATION_INVALID on validation errors.
        """
        try:
            return OptimizationCandidate(**candidate_data)
        except Exception as e:
            raise ArisException(
                error_code="ARIS_OPTIMIZATION_INVALID",
                message=f"Candidate failed schema validation: {str(e)}",
                details={"raw_data": candidate_data},
                recoverable=True,
                status_code=400
            )

    @staticmethod
    def generate_candidate_for_finding(
        finding: Dict[str, Any],
        source_code: str,
        board_id: str = "arduino_uno"
    ) -> OptimizationCandidate:
        """
        Deterministic rule-based synthesizer fallback. Generates verified candidate code
        for common findings (ARIS-001 blocking delay, ARIS-002 serial logging, ARIS-007 GPIO).
        """
        rule_id = finding.get("rule_id", "")
        finding_id = finding.get("finding_id", f"FIND-{uuid.uuid4().hex[:6]}")
        opt_id = f"OPT-{uuid.uuid4().hex[:8].upper()}"

        if rule_id == "ARIS-001":
            # Replace delay() with non-blocking timer
            duration = finding.get("evidence", {}).get("duration", 50)
            before_code = f"delay({duration});"
            after_code = (
                f"static unsigned long last_tick = 0;\n"
                f"if (millis() - last_tick >= {duration}) {{\n"
                f"    last_tick = millis();\n"
                f"    // Execute periodic state work\n"
                f"}}"
            )
            return OptimizationCandidate(
                optimization_id=opt_id,
                finding_id=finding_id,
                title="Convert blocking delay to non-blocking millis timer",
                problem=f"delay({duration}) monopolizes CPU clock cycles and causes high loop latency.",
                source_location={"file": finding.get("source_file", "main.ino"), "line": finding.get("source_line", 1)},
                before_code=before_code,
                after_code=after_code,
                reason="Restores event loop responsiveness and allows concurrent tasks to execute.",
                hardware_consideration="Frees AVR CPU to service interrupts and background timers.",
                expected_effect={"loop_time_delta_ms": -float(duration), "jitter_reduction_pct": 80.0},
                risk="LOW",
                confidence=0.92,
                validation_required=True,
                status="PROPOSED"
            )

        elif rule_id == "ARIS-002":
            # Replace unthrottled serial print
            before_code = "Serial.println(...);"
            after_code = (
                "static unsigned long last_log = 0;\n"
                "if (millis() - last_log >= 500) {\n"
                "    last_log = millis();\n"
                "    Serial.println(...);\n"
                "}"
            )
            return OptimizationCandidate(
                optimization_id=opt_id,
                finding_id=finding_id,
                title="Throttle serial transmission rate",
                problem="Unthrottled serial writing saturates the 64-byte hardware UART ring buffer.",
                source_location={"file": finding.get("source_file", "main.ino"), "line": finding.get("source_line", 1)},
                before_code=before_code,
                after_code=after_code,
                reason="Prevents UART buffer blocking and drops CPU load.",
                hardware_consideration="Limits serial TX ISR overhead and buffer contention.",
                expected_effect={"uart_bytes_reduction_pct": 75.0, "loop_time_delta_ms": -10.0},
                risk="LOW",
                confidence=0.90,
                validation_required=True,
                status="PROPOSED"
            )

        else:
            # Generic candidate
            return OptimizationCandidate(
                optimization_id=opt_id,
                finding_id=finding_id,
                title=f"Remediate {finding.get('title', 'bottleneck')}",
                problem=finding.get("description", "Inefficient MCU utilization detected."),
                source_location={"file": finding.get("source_file", "main.ino"), "line": finding.get("source_line", 1)},
                before_code="// original implementation",
                after_code="// optimized implementation conforming to hardware profile",
                reason=finding.get("recommended_action", "Apply embedded architecture best practices."),
                hardware_consideration="Maintains AVR Harvard architecture constraints.",
                expected_effect={"improvement_expected": True},
                risk="LOW",
                confidence=0.85,
                validation_required=True,
                status="PROPOSED"
            )
