"""
Unit & Integration Tests for ARIS Transparent Sketch Instrumentation.
Verifies AST/brace-matching, source code preservation, static rule evaluation,
and shadow-build compilation.
"""

import os
import shutil
import tempfile
import hashlib
import pytest
from fastapi.testclient import TestClient

from backend.instrumentation.sketch_instrumenter import SketchInstrumenter, InstrumentationResult
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.analysis.rules import RULE_ARIS_001
from backend.telemetry.telemetry_schema import ArisException
from backend.api.app import app


DEMO_USER_SKETCH = """const int LED_PIN = 13;

void setup() {
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(500);

  digitalWrite(LED_PIN, LOW);
  delay(500);
}
"""

NESTED_BRACE_SKETCH = """int counter = 0;

void setup() {
  pinMode(13, OUTPUT);
  for (int i = 0; i < 3; i++) {
    digitalWrite(13, HIGH);
    delay(10);
    digitalWrite(13, LOW);
  }
}

void loop() {
  if (counter < 10) {
    if (counter % 2 == 0) {
      digitalWrite(13, HIGH);
    } else {
      digitalWrite(13, LOW);
    }
    counter++;
  }
}
"""

COMMENTS_AND_STRINGS_SKETCH = """// Comment with void setup() { fake }
/* Block comment
   void loop() { fake }
*/
void setup() {
  Serial.begin(9600);
  Serial.println("Braces in strings: { } }");
}

void loop() {
  Serial.println("Loop brace { }");
  delay(100);
}
"""


def test_transparent_instrumentation_demo_sketch():
    """Verify clean header, setup, and loop instrumentation on standard sketch."""
    code, blocks, diff = SketchInstrumenter.instrument_code(
        DEMO_USER_SKETCH,
        board_id="arduino_uno",
        baud_rate=115200,
        run_id="DEMO-TEST"
    )

    assert "#include <aris_runtime.h>" in code
    assert 'ARIS.init("arduino_uno", 115200UL, "DEMO-TEST", ARIS_MODE_BALANCED);' in code
    assert "ARIS.loop_enter();" in code
    assert "ARIS.loop_exit();" in code
    assert "pinMode(LED_PIN, OUTPUT);" in code
    assert "digitalWrite(LED_PIN, HIGH);" in code
    assert len(blocks) == 4
    assert "--- original.ino" in diff
    assert "+++ instrumented.ino" in diff


def test_original_file_preservation():
    """Verify that source files on disk remain bit-for-bit unchanged."""
    with tempfile.TemporaryDirectory() as td:
        sketch_path = os.path.join(td, "user_sketch.ino")
        with open(sketch_path, "w", encoding="utf-8") as f:
            f.write(DEMO_USER_SKETCH)

        initial_hash = hashlib.sha256(DEMO_USER_SKETCH.encode("utf-8")).hexdigest()

        res = SketchInstrumenter.create_shadow_workspace(
            source_path=sketch_path,
            board_id="arduino_uno",
            run_id="SHADOW-PRESERVE-TEST"
        )

        # Confirm hash match reported
        assert res.verification_hash_match is True

        # Confirm disk file content and hash
        with open(sketch_path, "r", encoding="utf-8") as f:
            disk_content = f.read()

        after_hash = hashlib.sha256(disk_content.encode("utf-8")).hexdigest()
        assert initial_hash == after_hash
        assert disk_content == DEMO_USER_SKETCH

        # Confirm shadow file was written separately
        assert os.path.exists(res.shadow_sketch_path)
        assert res.shadow_sketch_path != sketch_path
        with open(res.shadow_sketch_path, "r", encoding="utf-8") as sf:
            shadow_content = sf.read()
        assert "#include <aris_runtime.h>" in shadow_content

        # Clean up shadow build artifacts created in backend/.aris_build
        if res.shadow_sketch_dir and os.path.exists(res.shadow_sketch_dir):
            build_root = os.path.abspath(os.path.join(res.shadow_sketch_dir, "..", ".."))
            if os.path.basename(build_root) == ".aris_build":
                shutil.rmtree(build_root, ignore_errors=True)


def test_nested_braces_handling():
    """Verify that nested loops and if/else blocks do not break function boundaries."""
    code, blocks, _ = SketchInstrumenter.instrument_code(
        NESTED_BRACE_SKETCH,
        board_id="arduino_uno"
    )

    assert "ARIS.init(" in code
    assert "ARIS.loop_enter();" in code
    assert "ARIS.loop_exit();" in code
    assert "for (int i = 0; i < 3; i++)" in code
    assert "if (counter < 10)" in code


def test_comments_and_strings_masking():
    """Verify that false function signatures and braces inside strings/comments are ignored."""
    code, blocks, _ = SketchInstrumenter.instrument_code(
        COMMENTS_AND_STRINGS_SKETCH,
        board_id="arduino_uno"
    )

    assert "Braces in strings: { } }" in code
    assert "ARIS.init(" in code
    assert "ARIS.loop_enter();" in code
    assert "ARIS.loop_exit();" in code


def test_missing_lifecycle_rejection():
    """Verify that sketches missing loop() or setup() raise ArisException."""
    bad_sketch = "int x = 10; void loop() { x++; }"
    with pytest.raises(ArisException) as exc:
        SketchInstrumenter.instrument_code(bad_sketch)
    assert exc.value.error_code == "ARIS_INSTRUMENTATION_FAILED"


def test_static_analysis_on_original_demo():
    """Verify that static analyzer detects ARIS-001 (Blocking Delay) on original source."""
    analyzer = StaticAnalyzer(default_board_id="arduino_uno")
    res = analyzer.analyze_source(
        source_code=DEMO_USER_SKETCH,
        board_id="arduino_uno",
        source_file="blink.ino"
    )

    delay_findings = [f for f in res.findings if f.rule_id == RULE_ARIS_001]
    assert len(delay_findings) == 2
    assert delay_findings[0].source_line == 9
    assert delay_findings[1].source_line == 12
    assert delay_findings[0].severity == "CRITICAL"


def test_api_instrument_and_build_endpoint(test_client):
    """Verify REST API endpoint performs transparent instrumentation and compilation."""
    client = test_client

    payload = {
        "source_code": DEMO_USER_SKETCH,
        "board_id": "arduino_uno",
        "execute_upload": False
    }

    resp = client.post("/api/firmware/instrument-and-build", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "BUILD_SUCCESS"
    assert data["original_source_preserved"] is True
    assert "diff" in data
    assert len(data["inserted_blocks"]) == 4
    assert data["static_analysis"]["findings_count"] == 2
    assert data["build_result"]["status"] == "BUILD_SUCCESS"
    assert data["ready_for_physical_deployment"] is True

    # Clean up test .aris_build directory
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".aris_build"))
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
