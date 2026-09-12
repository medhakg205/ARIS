"""
Unit and Integration Tests for ARIS AI Engine.
Tests:
- AI Provider abstraction and fallback
- Graceful ARIS_AI_UNAVAILABLE handling
- AVR8 Zero Hardware Hallucination guarantees
- Optimization Reasoner 7-step pipeline
- Risk Evaluator
- Prediction Engine & Prediction vs. Reality calculation
- Output Validator canonical schema enforcement
- REST API AI endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.app import app
from backend.ai.provider import (
    AIProvider,
    GeminiProvider,
    OpenAIProvider,
    RuleSynthesizerProvider,
    get_ai_provider,
    list_available_providers,
)
from backend.ai.context_builder import ContextBuilder
from backend.ai.firmware_analyzer import FirmwareAnalyzer
from backend.ai.optimization_reasoner import OptimizationReasoner
from backend.ai.risk_evaluator import RiskEvaluator
from backend.ai.prediction_engine import PredictionEngine
from backend.ai.output_validator import OutputValidator
from backend.telemetry.telemetry_schema import ArisException


def test_ai_provider_registry():
    """Verify AI provider registry and discovery."""
    providers = list_available_providers()
    assert len(providers) >= 3
    ids = [p["provider_id"] for p in providers]
    assert "rule_synthesizer" in ids
    assert "gemini" in ids
    assert "openai" in ids

    # Default auto fallback
    auto_provider = get_ai_provider("auto")
    assert isinstance(auto_provider, AIProvider)

    # Specific valid provider
    rule_provider = get_ai_provider("rule_synthesizer")
    assert isinstance(rule_provider, RuleSynthesizerProvider)
    assert rule_provider.is_available() is True


def test_gemini_unavailable_without_key():
    """Verify GeminiProvider raises canonical ARIS_AI_UNAVAILABLE when key is missing."""
    provider = GeminiProvider(api_key="")
    assert provider.is_available() is False

    context = ContextBuilder.build(board_id="arduino_uno")
    finding = {"rule_id": "ARIS-001", "finding_id": "FIND-01", "source_file": "sketch.ino", "source_line": 10}

    with pytest.raises(ArisException) as exc_info:
        provider.generate_candidate(context, finding)
    assert exc_info.value.error_code == "ARIS_AI_UNAVAILABLE"


def test_invalid_provider_raises():
    """Requesting an unsupported provider raises ARIS_AI_UNAVAILABLE."""
    with pytest.raises(ArisException) as exc:
        get_ai_provider("non_existent_provider")
    assert exc.value.error_code == "ARIS_AI_UNAVAILABLE"


def test_context_builder():
    """Verify ContextBuilder produces valid AIContextInput with AVR architecture limits."""
    context = ContextBuilder.build(
        board_id="arduino_uno",
        firmware_source="void setup() { delay(100); }\nvoid loop() {}",
        static_findings=[{"finding_id": "FIND-001", "rule_id": "ARIS-001"}],
        runtime_metrics={"loop_time": 102.5},
        baseline_metrics={"loop_time": {"mean": 102.5}}
    )
    assert context.board_profile["board_id"] == "arduino_uno"
    assert context.board_profile["mcu"] == "atmega328p"
    assert context.board_profile["has_hardware_perf_counters"] is False
    assert len(context.static_findings) == 1
    assert "loop_time" in context.runtime_metrics


def test_firmware_analyzer():
    """Verify FirmwareAnalyzer inspects AVR Arduino code features."""
    code = (
        'void setup() { Serial.begin(115200); }\n'
        'void loop() {\n'
        '  int v = analogRead(A0);\n'
        '  Serial.println("Reading sensor val");\n'
        '  digitalWrite(13, HIGH);\n'
        '  delay(50);\n'
        '  digitalWrite(13, LOW);\n'
        '}\n'
    )
    analysis = FirmwareAnalyzer.analyze_sketch(code)
    assert analysis["has_delay"] is True
    assert analysis["total_delay_ms"] == 50
    assert analysis["has_serial_in_loop"] is True
    assert analysis["has_slow_gpio"] is True
    assert analysis["has_non_progmem_strings"] is True


def test_zero_hardware_hallucination_guard():
    """Verify that hallucinating non-existent AVR hardware raises ValueError."""
    with pytest.raises(ValueError, match="Hardware hallucination detected"):
        OptimizationReasoner._verify_zero_hardware_hallucinations(
            "Use the hardware CPU performance counter register to benchmark instruction cycles."
        )

    with pytest.raises(ValueError, match="Hardware hallucination detected"):
        OptimizationReasoner._verify_zero_hardware_hallucinations(
            "Leverage L1 cache locality to optimize lookup speed."
        )


def test_optimization_reasoner_canonical_rules():
    """Verify OptimizationReasoner generates valid candidates for canonical findings."""
    context = ContextBuilder.build(board_id="arduino_uno")

    # Test ARIS-001 (delay)
    finding_delay = {
        "rule_id": "ARIS-001",
        "finding_id": "FIND-101",
        "source_file": "main.ino",
        "source_line": 25,
        "evidence": {"duration": 40}
    }
    cand_dict = OptimizationReasoner.reason_and_synthesize(context, finding_delay)
    assert cand_dict["risk"] == "LOW"
    assert "millis()" in cand_dict["after_code"]
    assert cand_dict["status"] == "PROPOSED"
    assert cand_dict["expected_effect"]["classification"] == "PREDICTED"

    # Validate output schema
    candidate = OutputValidator.validate_candidate_dict(cand_dict)
    assert candidate.optimization_id.startswith("OPT-")
    assert candidate.confidence >= 0.0 and candidate.confidence <= 1.0


def test_risk_evaluator():
    """Verify RiskEvaluator accurately classifies risk on AVR architecture."""
    # ISR modification -> HIGH
    risk, _ = RiskEvaluator.evaluate("ARIS-099", "arduino_uno", "void foo()", "void ISR(TIMER1_OVF_vect) { cli(); }")
    assert risk == "HIGH"

    # Direct port register write -> MEDIUM
    risk, _ = RiskEvaluator.evaluate("ARIS-007", "arduino_uno", "digitalWrite(13, HIGH);", "PORTB |= (1 << PB5);")
    assert risk == "MEDIUM"

    # Non-blocking millis -> LOW
    risk, _ = RiskEvaluator.evaluate("ARIS-001", "arduino_uno", "delay(20);", "if (millis() - t >= 20) { t = millis(); }")
    assert risk == "LOW"


def test_prediction_engine_prediction_vs_reality():
    """Verify PredictionEngine forecasts and compares PREDICTED vs ACTUAL measurements."""
    forecast = PredictionEngine.forecast_effect(
        rule_id="ARIS-001",
        board_id="arduino_uno",
        evidence={"duration": 25.0}
    )
    assert forecast["loop_time_delta_ms"] == -25.0
    assert forecast["classification"] == "PREDICTED"

    # Actual outcome from hardware validation
    actual_deltas = {
        "loop_time": {"difference": -24.2, "baseline": 26.0, "candidate": 1.8},
        "cpu_load": {"difference": -35.0, "baseline": 70.0, "candidate": 35.0}
    }
    accuracy_report = PredictionEngine.calculate_prediction_accuracy(forecast, actual_deltas)
    assert "loop_time" in accuracy_report["metrics_compared"]
    assert accuracy_report["mean_prediction_error_pct"] > 0
    assert accuracy_report["prediction_accuracy_score"] > 0.5
    assert "scientific_note" in accuracy_report


def test_output_validator_rejection():
    """Verify OutputValidator raises canonical ARIS_OPTIMIZATION_INVALID on malformed input."""
    # Missing required field
    invalid_data = {
        "optimization_id": "OPT-1",
        "finding_id": "FIND-1"
        # missing title, problem, before_code, after_code, etc.
    }
    with pytest.raises(ArisException) as exc:
        OutputValidator.validate_candidate_dict(invalid_data)
    assert exc.value.error_code == "ARIS_OPTIMIZATION_INVALID"


def test_rest_api_ai_integration():
    """Verify FastAPI endpoints /api/ai/analyze and /api/ai/generate-candidate."""
    client = TestClient(app)

    # Test /api/ai/analyze
    resp = client.post("/api/ai/analyze", json={
        "board_id": "arduino_uno",
        "source_code": "void setup() { delay(10); }\nvoid loop() {}"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "board_profile" in data
    assert data["board_profile"]["board_id"] == "arduino_uno"
    assert "static_findings" in data

    # Test /api/ai/generate-candidate
    cand_resp = client.post("/api/ai/generate-candidate", json={
        "board_id": "arduino_uno",
        "source_code": "void setup() { delay(10); }\nvoid loop() {}",
        "finding": {
            "finding_id": "FIND-TEST-1",
            "rule_id": "ARIS-001",
            "title": "Blocking delay",
            "source_file": "sketch.ino",
            "source_line": 1,
            "evidence": {"duration": 10}
        }
    })
    assert cand_resp.status_code == 200
    candidate = cand_resp.json()
    assert candidate["optimization_id"].startswith("OPT-")
    assert candidate["status"] == "PROPOSED"
    assert candidate["risk"] == "LOW"
    assert "millis()" in candidate["after_code"]
