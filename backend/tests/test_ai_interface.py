"""
Unit tests for ARIS AI Interface Contract (Engineer 3 Integration).
Verifies:
- AIContextInput packaging
- OptimizationCandidate canonical schema validation
- Rejection of non-canonical statuses
- Deterministic candidate generation
"""

import pytest
from backend.analysis.ai_interface import AIInterface, OptimizationCandidate
from backend.telemetry.telemetry_schema import ArisException


def test_ai_context_input_structure():
    """Verify AI context input packaging adheres to specification."""
    context = AIInterface.build_context(
        board_profile={"board_id": "arduino_uno", "mcu": "atmega328p"},
        firmware_source="void loop() { delay(100); }",
        static_findings=[{"finding_id": "FIND-1", "rule_id": "ARIS-001"}],
        runtime_metrics={"loop_time": 102.0},
        baseline_metrics={"loop_time": {"mean": 102.0}},
        runtime_static_correlations=[{"finding_id": "FIND-1", "correlation": "HIGH"}]
    )
    d = context.model_dump()
    assert "board_profile" in d
    assert "firmware_source" in d
    assert "runtime_static_correlations" in d


def test_optimization_candidate_valid():
    """Verify valid candidate passes schema validation."""
    valid_data = {
        "optimization_id": "OPT-100",
        "finding_id": "FIND-1",
        "title": "Fix delay",
        "problem": "Blocking call",
        "source_location": {"file": "main.ino", "line": 42},
        "before_code": "delay(100);",
        "after_code": "millis() timer",
        "reason": "Eliminates stalls",
        "hardware_consideration": "Saves clock cycles",
        "expected_effect": {"loop_time_delta_ms": -98.0},
        "risk": "LOW",
        "confidence": 0.89,
        "validation_required": True,
        "status": "PROPOSED"
    }
    candidate = AIInterface.validate_candidate(valid_data)
    assert candidate.optimization_id == "OPT-100"
    assert candidate.status == "PROPOSED"


def test_optimization_candidate_invalid_status_raises():
    """Verify invalid candidate status raises ARIS_OPTIMIZATION_INVALID."""
    bad_data = {
        "optimization_id": "OPT-100",
        "finding_id": "FIND-1",
        "title": "Fix delay",
        "problem": "Blocking call",
        "source_location": {},
        "before_code": "",
        "after_code": "",
        "reason": "",
        "hardware_consideration": "",
        "expected_effect": {},
        "risk": "LOW",
        "confidence": 0.89,
        "validation_required": True,
        "status": "UNAUTHORIZED_STATUS"  # Invalid!
    }
    with pytest.raises(ArisException) as exc:
        AIInterface.validate_candidate(bad_data)
    assert exc.value.error_code == "ARIS_OPTIMIZATION_INVALID"


def test_generate_deterministic_candidate_for_aris_001():
    """Verify synthesizer creates valid non-blocking candidate for ARIS-001."""
    finding = {
        "finding_id": "FIND-001",
        "rule_id": "ARIS-001",
        "source_file": "sketch.ino",
        "source_line": 15,
        "evidence": {"duration": 50}
    }
    cand = AIInterface.generate_candidate_for_finding(finding, "delay(50);")
    assert "millis()" in cand.after_code
    assert cand.status == "PROPOSED"
    assert cand.validation_required is True
