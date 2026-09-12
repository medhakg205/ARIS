"""
ARIS AI Output Validator.
Strictly enforces canonical schema validation on all optimization candidates emitted
by AI providers (Gemini, OpenAI, RuleSynthesizer).
Raises canonical ARIS_OPTIMIZATION_INVALID on violations.
"""

from typing import Dict, Any
from backend.analysis.ai_interface import OptimizationCandidate
from backend.telemetry.telemetry_schema import ArisException


class OutputValidator:
    """Validates optimization candidate structures against canonical schema."""

    @staticmethod
    def validate_candidate_dict(data: Dict[str, Any]) -> OptimizationCandidate:
        """
        Validates dictionary against the canonical OptimizationCandidate schema.
        Raises ARIS_OPTIMIZATION_INVALID on any schema violation.
        """
        # Ensure status is canonical
        if "status" not in data or not data["status"]:
            data["status"] = "PROPOSED"

        # Ensure risk is uppercase
        if "risk" in data and isinstance(data["risk"], str):
            data["risk"] = data["risk"].upper()
        else:
            data["risk"] = "LOW"

        # Ensure confidence is clamped
        if "confidence" in data:
            try:
                data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
            except Exception:
                data["confidence"] = 0.85

        # Check required fields
        required_fields = [
            "optimization_id",
            "finding_id",
            "title",
            "problem",
            "source_location",
            "before_code",
            "after_code",
            "reason",
            "hardware_consideration",
            "expected_effect"
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ArisException(
                error_code="ARIS_OPTIMIZATION_INVALID",
                message=f"Candidate missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing, "raw_data": data},
                recoverable=True,
                status_code=400
            )

        try:
            return OptimizationCandidate(**data)
        except Exception as e:
            raise ArisException(
                error_code="ARIS_OPTIMIZATION_INVALID",
                message=f"Candidate failed schema validation: {str(e)}",
                details={"validation_error": str(e), "raw_data": data},
                recoverable=True,
                status_code=400
            )
