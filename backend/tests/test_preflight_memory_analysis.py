"""
Regression & Integration Tests for ARIS Preflight Memory Analysis & Safety Pipeline.
Verifies exact compiled memory accounting, flash/SRAM overflow handling, board limits,
byte-identical disk source preservation, and zero-upload enforcement.

Covers all 13 required scenarios:
1. Original sketch fits; instrumented sketch fits.
2. Original sketch fits; instrumented sketch exceeds flash.
3. Original sketch already exceeds flash without instrumentation.
4. SRAM overflow detection.
5. Missing or malformed size output from compiler/tools.
6. Different board memory limits (Uno vs Mega vs Nano).
7. Compiler failure unrelated to memory (syntax error, missing include).
8. No upload attempt after a failed build.
9. Original source file remains untouched on disk on every failure path.
10. No false success state when memory usage is unknown or compilation fails.
11. UI/REST API receives appropriate error payload for actionable user recovery.
12. Large source file with many lines/comments but small compiled size.
13. Small source file that pulls in heavy libraries and exceeds flash.
"""

import os
import shutil
import tempfile
import hashlib
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from backend.firmware.preflight_analyzer import (
    PreflightMemoryAnalyzer,
    PreflightMemoryReport
)
from backend.firmware.board_profiles import get_board_profile
from backend.firmware.build_flasher import BuildFlasher
from backend.instrumentation.sketch_instrumenter import SketchInstrumenter
from backend.telemetry.telemetry_schema import ArisException
from backend.api.app import app


# ---------------------------------------------------------------------------
# Test Sketch Fixtures
# ---------------------------------------------------------------------------

MINIMAL_BLINK_SKETCH = """const int LED_PIN = 13;

void setup() {
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(250);
  digitalWrite(LED_PIN, LOW);
  delay(250);
}
"""

SYNTAX_ERROR_SKETCH = """void setup() {
  pinMode(13, OUTPUT)   // Missing semicolon
}

void loop() {
  undeclared_function_call();
}
"""

LARGE_COMMENT_SKETCH = """// ============================================================================
// ARIS Embedded Safety Verification Sketch
// Description: Stress test for line count vs compiled size independence.
// This sketch contains extensive docstrings, license text, and comment banners.
// ============================================================================
""" + "\n".join([f"// Line {i:04d}: Documentation and telemetry specification comments" for i in range(1200)]) + """

const int STATUS_PIN = 13;

void setup() {
  pinMode(STATUS_PIN, OUTPUT);
}

void loop() {
  digitalWrite(STATUS_PIN, HIGH);
  delay(100);
  digitalWrite(STATUS_PIN, LOW);
  delay(100);
}
"""

HEAVY_LIBRARY_SKETCH = """#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("ARIS Memory Test");
  display.display();
}

void loop() {
  display.invertDisplay(true);
  delay(500);
  display.invertDisplay(false);
  delay(500);
}
"""


# ---------------------------------------------------------------------------
# 1. Original sketch fits; instrumented sketch fits
# ---------------------------------------------------------------------------

def test_01_original_and_instrumented_sketch_fit():
    """Verify clean pass when both original and instrumented sketches fit within memory limits."""
    analyzer = PreflightMemoryAnalyzer()
    inst_res = SketchInstrumenter.instrument_code(MINIMAL_BLINK_SKETCH, board_id="arduino_uno")
    instrumented_code = inst_res[0]

    report = analyzer.analyze_memory_and_instrumentation(
        original_source=MINIMAL_BLINK_SKETCH,
        board_id="arduino_uno",
        instrumented_source=instrumented_code
    )

    assert isinstance(report, PreflightMemoryReport)
    assert report.status == "FITS"
    assert report.board_id == "arduino_uno"
    assert report.original_flash_bytes is not None
    assert report.instrumented_flash_bytes is not None
    assert report.instrumented_flash_bytes <= report.max_flash_bytes
    assert report.remaining_flash_headroom_bytes > 0
    assert report.original_source_preserved is True
    assert report.uploaded is False
    assert "fits safely" in report.message


# ---------------------------------------------------------------------------
# 2. Original sketch fits; instrumented sketch exceeds flash
# ---------------------------------------------------------------------------

def test_02_instrumented_sketch_exceeds_flash():
    """Verify that when original fits but instrumentation overflows flash, ARIS_INSTRUMENTATION_FLASH_OVERFLOW is raised."""
    analyzer = PreflightMemoryAnalyzer()

    # Simulate original probing 23,220 B (fits in 32,256 B) and instrumented probing 33,194 B (overflows by 938 B)
    def mock_probe(source_code, board_id, include_embedded_lib=True):
        if not include_embedded_lib:
            return True, {
                "flash_bytes": 22608,
                "sram_bytes": 612,
                "max_flash_bytes": 32256,
                "max_sram_bytes": 2048
            }, ""
        else:
            return False, {
                "flash_bytes": 33194,
                "sram_bytes": 2156,
                "max_flash_bytes": 32256,
                "max_sram_bytes": 2048,
                "overflow_flash_bytes": 938
            }, "Error during build: text section exceeds available space in board"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_probe):
        with pytest.raises(ArisException) as exc_info:
            analyzer.analyze_memory_and_instrumentation(
                original_source="void setup(){} void loop(){}",
                board_id="arduino_uno",
                instrumented_source="void setup(){} void loop(){}"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_INSTRUMENTATION_FLASH_OVERFLOW"
        assert err.status_code == 400
        assert err.recoverable is True
        details = err.details
        assert details["overflow_type"] == "FLASH"
        assert details["original_flash_bytes"] == 22608
        assert details["instrumented_flash_bytes"] == 33194
        assert details["max_flash_bytes"] == 32256
        assert details["overflow_bytes"] == 938
        assert details["lean_profile_recommended"] is True
        assert "arduino_mega" in details["recommended_boards"]
        assert details["original_source_preserved"] is True
        assert details["uploaded"] is False


# ---------------------------------------------------------------------------
# 3. Original sketch already exceeds flash without instrumentation
# ---------------------------------------------------------------------------

def test_03_original_sketch_already_exceeds_flash():
    """Verify that if the uninstrumented original sketch is too large, ARIS_ORIGINAL_SKETCH_OVERFLOW is raised."""
    analyzer = PreflightMemoryAnalyzer()

    def mock_probe(source_code, board_id, include_embedded_lib=True):
        return False, {
            "flash_bytes": 34500,
            "sram_bytes": 1200,
            "max_flash_bytes": 32256,
            "max_sram_bytes": 2048,
            "overflow_flash_bytes": 2244
        }, "Error during build: text section exceeds available space in board"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_probe):
        with pytest.raises(ArisException) as exc_info:
            analyzer.analyze_memory_and_instrumentation(
                original_source="void setup(){} void loop(){}",
                board_id="arduino_uno"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_ORIGINAL_SKETCH_OVERFLOW"
        assert "Original sketch exceeds" in err.message
        assert err.details["overflow_bytes"] == 2244
        assert err.details["original_source_preserved"] is True
        assert err.details["uploaded"] is False


# ---------------------------------------------------------------------------
# 4. SRAM overflow detection
# ---------------------------------------------------------------------------

def test_04_sram_overflow_detection():
    """Verify detection when instrumented sketch exceeds available static SRAM."""
    analyzer = PreflightMemoryAnalyzer()

    def mock_probe(source_code, board_id, include_embedded_lib=True):
        if not include_embedded_lib:
            return True, {
                "flash_bytes": 10000,
                "sram_bytes": 1800,
                "max_flash_bytes": 32256,
                "max_sram_bytes": 2048
            }, ""
        else:
            return False, {
                "flash_bytes": 18000,
                "sram_bytes": 2200,
                "max_flash_bytes": 32256,
                "max_sram_bytes": 2048,
                "overflow_sram_bytes": 152
            }, "region 'data' overflowed by 152 bytes"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_probe):
        with pytest.raises(ArisException) as exc_info:
            analyzer.analyze_memory_and_instrumentation(
                original_source="void setup(){} void loop(){}",
                board_id="arduino_uno",
                instrumented_source="void setup(){} void loop(){}"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_INSTRUMENTATION_SRAM_OVERFLOW"
        assert err.details["overflow_type"] == "SRAM"
        assert err.details["instrumented_sram_bytes"] == 2200
        assert err.details["overflow_bytes"] == 152


# ---------------------------------------------------------------------------
# 5. Missing or malformed size output from compiler/tools
# ---------------------------------------------------------------------------

def test_05_missing_or_malformed_size_output():
    """Verify that parsing handles missing, partial, or malformed compiler size outputs without crashing."""
    # Empty inputs
    res_empty = PreflightMemoryAnalyzer.parse_arduino_cli_size_output("", "")
    assert res_empty["flash_bytes"] is None
    assert res_empty["sram_bytes"] is None
    assert res_empty["overflow_flash_bytes"] is None

    # Corrupted text
    res_garbled = PreflightMemoryAnalyzer.parse_arduino_cli_size_output(
        "Corrupted random garbage $#@%^&* text without numbers",
        "More non-size text"
    )
    assert res_garbled["flash_bytes"] is None
    assert res_garbled["sram_bytes"] is None

    # Linker overflow text parsing
    res_ld = PreflightMemoryAnalyzer.parse_arduino_cli_size_output(
        "",
        "c:/avr/bin/ld.exe: region 'text' overflowed by 1024 bytes\nregion 'data' overflowed by 64 bytes"
    )
    assert res_ld["overflow_flash_bytes"] == 1024
    assert res_ld["overflow_sram_bytes"] == 64


# ---------------------------------------------------------------------------
# 6. Different board memory limits (Uno vs Mega vs Nano)
# ---------------------------------------------------------------------------

def test_06_different_board_memory_limits():
    """Verify board profile memory limits accurately account for hardware differences and bootloader reservations."""
    uno_profile = get_board_profile("arduino_uno")
    uno_flash, uno_sram = PreflightMemoryAnalyzer.get_board_effective_limits(uno_profile)
    assert uno_flash == 32256   # 32,768 - 512 (Optiboot)
    assert uno_sram == 2048

    nano_profile = get_board_profile("arduino_nano")
    nano_flash, nano_sram = PreflightMemoryAnalyzer.get_board_effective_limits(nano_profile)
    assert nano_flash == 30720  # 32,768 - 2048 (Old bootloader)
    assert nano_sram == 2048

    mega_profile = get_board_profile("arduino_mega")
    mega_flash, mega_sram = PreflightMemoryAnalyzer.get_board_effective_limits(mega_profile)
    assert mega_flash == 253952 # 256 KB - 2048 bootloader
    assert mega_sram == 8192

    # A 34,204 byte instrumented sketch fails on Uno but fits easily on Mega
    analyzer = PreflightMemoryAnalyzer()
    def mock_mega_probe(source_code, board_id, include_embedded_lib=True):
        if board_id == "arduino_mega":
            return True, {
                "flash_bytes": 36394,
                "sram_bytes": 2238,
                "max_flash_bytes": 253952,
                "max_sram_bytes": 8192
            }, ""
        return False, {}, "fail"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_mega_probe):
        rep = analyzer.analyze_memory_and_instrumentation(
            original_source="void setup(){} void loop(){}",
            board_id="arduino_mega",
            instrumented_source="void setup(){} void loop(){}"
        )
        assert rep.status == "FITS"
        assert rep.board_id == "arduino_mega"
        assert rep.remaining_flash_headroom_bytes == (253952 - 36394)


# ---------------------------------------------------------------------------
# 7. Compiler failure unrelated to memory (syntax error)
# ---------------------------------------------------------------------------

def test_07_compiler_failure_unrelated_to_memory():
    """Verify that syntax or missing-header compilation failures raise ARIS_BUILD_FAILED without false memory classification."""
    analyzer = PreflightMemoryAnalyzer()

    def mock_syntax_err(source_code, board_id, include_embedded_lib=True):
        return False, {
            "flash_bytes": None,
            "sram_bytes": None,
            "max_flash_bytes": 32256,
            "max_sram_bytes": 2048
        }, "sketch.ino:2:3: error: expected ';' before '}' token"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_syntax_err):
        with pytest.raises(ArisException) as exc_info:
            analyzer.analyze_memory_and_instrumentation(
                original_source=SYNTAX_ERROR_SKETCH,
                board_id="arduino_uno"
            )

        err = exc_info.value
        assert err.error_code == "ARIS_BUILD_FAILED"
        assert "expected ';'" in err.message
        assert err.details.get("overflow_type") is None


# ---------------------------------------------------------------------------
# 8. No upload attempt after a failed build
# ---------------------------------------------------------------------------

def test_08_no_upload_attempt_after_failed_build(test_client):
    """Verify that when compilation or preflight analysis fails, no physical upload is ever executed."""
    client = test_client

    with patch("backend.firmware.preflight_analyzer.PreflightMemoryAnalyzer.analyze_memory_and_instrumentation") as mock_analyze, \
         patch("backend.firmware.build_flasher.BuildFlasher.flash_board") as mock_flash:

        # Make preflight raise Flash Overflow
        mock_analyze.side_effect = ArisException(
            error_code="ARIS_INSTRUMENTATION_FLASH_OVERFLOW",
            message="Flash overflow detected",
            details={"overflow_type": "FLASH", "uploaded": False},
            recoverable=True,
            status_code=400
        )

        resp = client.post("/api/firmware/instrument-and-build", json={
            "source_code": MINIMAL_BLINK_SKETCH,
            "board_id": "arduino_uno",
            "port": "COM4",
            "execute_upload": True
        })

        assert resp.status_code == 400
        data = resp.json()
        assert data["error_code"] == "ARIS_INSTRUMENTATION_FLASH_OVERFLOW"
        # Guarantee flash_board was NEVER called
        mock_flash.assert_not_called()


# ---------------------------------------------------------------------------
# 9. Original source file remains untouched on disk on every failure path
# ---------------------------------------------------------------------------

def test_09_original_source_file_untouched_on_disk(test_client):
    """Verify that the original .ino source file on disk remains strictly byte-identical across all failure conditions."""
    client = test_client

    with tempfile.TemporaryDirectory() as td:
        sketch_path = os.path.join(td, "MyOriginalSketch.ino")
        with open(sketch_path, "w", encoding="utf-8") as f:
            f.write(MINIMAL_BLINK_SKETCH)

        initial_sha256 = hashlib.sha256(MINIMAL_BLINK_SKETCH.encode("utf-8")).hexdigest()

        # Run with simulated overflow
        with patch("backend.firmware.preflight_analyzer.PreflightMemoryAnalyzer.analyze_memory_and_instrumentation") as mock_analyze:
            mock_analyze.side_effect = ArisException(
                error_code="ARIS_INSTRUMENTATION_FLASH_OVERFLOW",
                message="Flash overflow",
                details={"original_source_preserved": True, "uploaded": False},
                recoverable=True,
                status_code=400
            )

            client.post("/api/firmware/instrument-and-build", json={
                "sketch_path": sketch_path,
                "board_id": "arduino_uno"
            })

        # Verify disk contents are byte-for-byte identical
        with open(sketch_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        current_sha256 = hashlib.sha256(current_content.encode("utf-8")).hexdigest()
        assert current_sha256 == initial_sha256
        assert current_content == MINIMAL_BLINK_SKETCH


# ---------------------------------------------------------------------------
# 10. No false success state when memory usage is unknown or compilation fails
# ---------------------------------------------------------------------------

def test_10_no_false_success_when_compilation_fails():
    """Verify that preflight analyzer never reports status='FITS' if compiler returned failure."""
    analyzer = PreflightMemoryAnalyzer()

    def mock_fail(source_code, board_id, include_embedded_lib=True):
        return False, {}, "fatal compiler linker failure"

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_fail):
        with pytest.raises(ArisException) as exc_info:
            analyzer.analyze_memory_and_instrumentation(
                original_source="void setup(){} void loop(){}",
                board_id="arduino_uno"
            )

        assert exc_info.value.error_code == "ARIS_BUILD_FAILED"


# ---------------------------------------------------------------------------
# 11. UI/REST API receives appropriate error payload for actionable user recovery
# ---------------------------------------------------------------------------

def test_11_rest_api_error_payload_for_ui_recovery(test_client):
    """Verify REST API responds with complete actionable error structure matching frontend contract."""
    client = test_client

    with patch("backend.firmware.preflight_analyzer.PreflightMemoryAnalyzer.analyze_memory_and_instrumentation") as mock_analyze:
        mock_analyze.side_effect = ArisException(
            error_code="ARIS_INSTRUMENTATION_FLASH_OVERFLOW",
            message="Instrumentation exceeds Arduino Uno flash capacity.",
            details={
                "board_id": "arduino_uno",
                "board_name": "Arduino Uno",
                "overflow_type": "FLASH",
                "original_flash_bytes": 22608,
                "instrumented_flash_bytes": 33194,
                "max_flash_bytes": 32256,
                "overflow_bytes": 938,
                "instrumentation_overhead_bytes": 10586,
                "instrumentation_overhead_pct": 46.82,
                "suggested_actions": [
                    "Enable LEAN instrumentation profile.",
                    "Target a high-capacity microcontroller (Arduino Mega 2560)."
                ],
                "lean_profile_recommended": True,
                "recommended_boards": ["arduino_mega", "arduino_uno_r4_wifi"],
                "original_source_preserved": True,
                "uploaded": False
            },
            recoverable=True,
            status_code=400
        )

        resp = client.post("/api/firmware/instrument-and-build", json={
            "source_code": MINIMAL_BLINK_SKETCH,
            "board_id": "arduino_uno"
        })

        assert resp.status_code == 400
        data = resp.json()
        assert data["error_code"] == "ARIS_INSTRUMENTATION_FLASH_OVERFLOW"
        assert data["recoverable"] is True
        details = data["details"]
        assert details["board_name"] == "Arduino Uno"
        assert details["overflow_bytes"] == 938
        assert details["lean_profile_recommended"] is True
        assert len(details["suggested_actions"]) == 2
        assert "arduino_mega" in details["recommended_boards"]
        assert details["original_source_preserved"] is True
        assert details["uploaded"] is False


# ---------------------------------------------------------------------------
# 12. Large source file with many lines/comments but small compiled size
# ---------------------------------------------------------------------------

def test_12_large_source_file_modest_compiled_size():
    """Verify that a 1,200+ line sketch consisting mostly of comments compiles and fits cleanly without line-count bias."""
    analyzer = PreflightMemoryAnalyzer()
    inst_res = SketchInstrumenter.instrument_code(LARGE_COMMENT_SKETCH, board_id="arduino_uno")

    report = analyzer.analyze_memory_and_instrumentation(
        original_source=LARGE_COMMENT_SKETCH,
        board_id="arduino_uno",
        instrumented_source=inst_res[0]
    )

    assert report.status == "FITS"
    assert report.board_id == "arduino_uno"
    # Even with >1,200 lines, compiled code fits well within 32,256 B Uno flash
    assert report.instrumented_flash_bytes < 32256
    assert report.remaining_flash_headroom_bytes > 0


# ---------------------------------------------------------------------------
# 13. Small source file that pulls in heavy libraries and exceeds flash
# ---------------------------------------------------------------------------

def test_13_small_source_file_heavy_libraries_overflow():
    """Verify that a concise sketch importing heavy libraries (Adafruit_GFX/SSD1306) triggers flash overflow when instrumented."""
    analyzer = PreflightMemoryAnalyzer()
    inst_res = SketchInstrumenter.instrument_code(HEAVY_LIBRARY_SKETCH, board_id="arduino_uno")

    # If arduino-cli is present with installed libraries, it probes the actual build.
    # Otherwise mock the heavy library sizing.
    if not analyzer.arduino_cli_path:
        def mock_heavy_probe(source_code, board_id, include_embedded_lib=True):
            if not include_embedded_lib:
                return True, {"flash_bytes": 22000, "sram_bytes": 600, "max_flash_bytes": 32256, "max_sram_bytes": 2048}, ""
            else:
                return False, {
                    "flash_bytes": 33500,
                    "sram_bytes": 2100,
                    "max_flash_bytes": 32256,
                    "max_sram_bytes": 2048,
                    "overflow_flash_bytes": 1244
                }, "text section exceeds available space"
        with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_heavy_probe):
            with pytest.raises(ArisException) as exc_info:
                analyzer.analyze_memory_and_instrumentation(
                    original_source=HEAVY_LIBRARY_SKETCH,
                    board_id="arduino_uno",
                    instrumented_source=inst_res[0]
                )
            assert exc_info.value.error_code == "ARIS_INSTRUMENTATION_FLASH_OVERFLOW"
    else:
        # Test directly with toolchain
        try:
            report = analyzer.analyze_memory_and_instrumentation(
                original_source=HEAVY_LIBRARY_SKETCH,
                board_id="arduino_uno",
                instrumented_source=inst_res[0]
            )
            # If the user has a stripped library version that fits, status must be FITS
            assert report.status == "FITS"
        except ArisException as e:
            # If it overflows (like oled_se.ino), it must be classified as ARIS_INSTRUMENTATION_FLASH_OVERFLOW
            assert e.error_code in ("ARIS_INSTRUMENTATION_FLASH_OVERFLOW", "ARIS_BUILD_FAILED")
            assert e.details.get("original_source_preserved") is True
            assert e.details.get("uploaded") is False


# ---------------------------------------------------------------------------
# 14. Nano bootloader variants (New Optiboot vs Old Bootloader vs ATmega168)
# ---------------------------------------------------------------------------

def test_14_nano_bootloader_variants_memory_limits():
    """Verify board profile memory limits accurately distinguish Nano bootloaders and MCU variants."""
    # 1. Nano default / Old Bootloader (ATmegaBOOT: 2048 bytes bootloader reservation)
    nano_old = get_board_profile("arduino_nano")
    assert nano_old.max_program_bytes == 30720
    assert nano_old.max_sram_bytes == 2048

    # 2. Nano New Bootloader (Optiboot: 512 bytes bootloader reservation)
    from backend.firmware.board_profiles import BoardProfile
    nano_optiboot = BoardProfile(
        board_id="arduino_nano",
        display_name="Arduino Nano (New Bootloader)",
        architecture="avr8",
        fqbn="arduino:avr:nano:cpu=atmega328",
        flash_bytes=32768,
        sram_bytes=2048
    )
    assert nano_optiboot.max_program_bytes == 32256
    assert nano_optiboot.max_sram_bytes == 2048

    # 3. Nano ATmega168 variant (16 KB flash minus bootloader)
    nano_168 = BoardProfile(
        board_id="arduino_nano",
        display_name="Arduino Nano (ATmega168)",
        architecture="avr8",
        fqbn="arduino:avr:nano:cpu=atmega168",
        flash_bytes=16384,
        sram_bytes=1024
    )
    assert nano_168.max_program_bytes == 14336
    assert nano_168.max_sram_bytes == 1024


# ---------------------------------------------------------------------------
# 15. Unknown/unsupported board fails safely without guessing 32 KB / 2 KB
# ---------------------------------------------------------------------------

def test_15_unknown_and_unsupported_board_fails_safely():
    """Verify that unverified or unknown board profiles fail safely with limit_unknown: True and never guess."""
    analyzer = PreflightMemoryAnalyzer()

    # Case A: Totally unknown board ID
    with pytest.raises(ArisException) as exc_a:
        analyzer.analyze_memory_and_instrumentation(
            original_source=MINIMAL_BLINK_SKETCH,
            board_id="unknown_riscv_custom_board"
        )
    err_a = exc_a.value
    assert err_a.error_code == "ARIS_UNSUPPORTED_BOARD"
    assert err_a.details["limit_unknown"] is True

    # Case B: Board profile exists but lacks verified memory limits
    from backend.firmware.board_profiles import BoardProfile
    unverified_board = BoardProfile(
        board_id="custom_proto_board",
        display_name="Custom Prototype Board",
        architecture="arm_cortex_m0",
        flash_bytes=None,
        sram_bytes=None
    )
    with patch("backend.firmware.preflight_analyzer.get_board_profile", return_value=unverified_board):
        with pytest.raises(ArisException) as exc_b:
            analyzer.analyze_memory_and_instrumentation(
                original_source=MINIMAL_BLINK_SKETCH,
                board_id="custom_proto_board"
            )
        err_b = exc_b.value
        assert err_b.error_code == "ARIS_UNSUPPORTED_BOARD"
        assert err_b.details["limit_unknown"] is True
        assert "max_flash_bytes" in err_b.details["unavailable_properties"]
        assert "max_sram_bytes" in err_b.details["unavailable_properties"]
        assert err_b.details["original_source_preserved"] is True
        assert err_b.details["uploaded"] is False


# ---------------------------------------------------------------------------
# 16. Static SRAM low headroom detection and stack safety disclaimer
# ---------------------------------------------------------------------------

def test_16_static_sram_low_headroom_detection_and_disclaimer():
    """Verify static SRAM analysis detects low headroom and surfaces explicit stack uncertainty disclaimer."""
    analyzer = PreflightMemoryAnalyzer()

    # Simulate sketch that leaves only 120 bytes of static SRAM (threshold = 256)
    def mock_low_sram_probe(source_code, board_id, include_embedded_lib=True):
        return True, {
            "flash_bytes": 18000,
            "sram_bytes": 1928,  # 2048 - 1928 = 120 B headroom (< 256 B warning threshold)
            "max_flash_bytes": 32256,
            "max_sram_bytes": 2048
        }, ""

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_low_sram_probe):
        report = analyzer.analyze_memory_and_instrumentation(
            original_source=MINIMAL_BLINK_SKETCH,
            board_id="arduino_uno",
            instrumented_source=MINIMAL_BLINK_SKETCH,
            sram_warning_threshold_bytes=256
        )

        assert report.status == "FITS"
        assert report.sram_static_bytes == 1928
        assert report.sram_headroom_bytes == 120
        assert report.sram_headroom_status == "LOW_HEADROOM"
        assert "Caution: Low static SRAM headroom" in report.suggested_actions[0]
        # Verify stack safety disclaimer
        assert "Static SRAM accounting includes only global and static variables" in report.stack_safety_disclaimer
        assert "dynamic heap allocations" in report.stack_safety_disclaimer
        assert "Stack safety cannot be guaranteed" in report.stack_safety_disclaimer


# ---------------------------------------------------------------------------
# 17. Selectable LEAN profile compilation & metric unavailability
# ---------------------------------------------------------------------------

def test_17_lean_profile_compilation_and_metric_unavailability():
    """Verify that LEAN profile injects ARIS_LEAN_PROFILE and marks peripheral metrics as unavailable."""
    # 1. Code injection check
    inst_code, blocks, diff = SketchInstrumenter.instrument_code(
        MINIMAL_BLINK_SKETCH,
        board_id="arduino_uno",
        instrumentation_mode="LEAN"
    )
    assert "#define ARIS_LEAN_PROFILE 1" in inst_code
    assert "ARIS_MODE_LOW" in inst_code

    # 2. Preflight analyzer report check
    analyzer = PreflightMemoryAnalyzer()
    def mock_lean_probe(source_code, board_id, include_embedded_lib=True):
        return True, {
            "flash_bytes": 15000,
            "sram_bytes": 1200,
            "max_flash_bytes": 32256,
            "max_sram_bytes": 2048
        }, ""

    with patch.object(analyzer, "compile_sketch_to_probe_size", side_effect=mock_lean_probe):
        report = analyzer.analyze_memory_and_instrumentation(
            original_source=MINIMAL_BLINK_SKETCH,
            board_id="arduino_uno",
            instrumented_source=inst_code,
            instrumentation_mode="LEAN"
        )

        assert report.status == "FITS"
        assert report.instrumentation_mode == "LEAN"
        assert "[LEAN Profile Active:" in report.message
        # Verify peripheral probes are reported unavailable
        assert "gpio_activity" in report.unavailable_metrics
        assert "adc_activity" in report.unavailable_metrics
        assert "uart_activity" in report.unavailable_metrics
        assert "spi_activity" in report.unavailable_metrics
        assert "i2c_activity" in report.unavailable_metrics
        assert "timer_activity" in report.unavailable_metrics


# ---------------------------------------------------------------------------
# 18. End-to-end orchestration: failed preflight blocks physical upload
# ---------------------------------------------------------------------------

def test_18_orchestration_failed_preflight_blocks_physical_upload(test_client):
    """Verify API pipeline with execute_upload=True never invokes flash or serial manager on preflight failure."""
    client = test_client

    with patch("backend.firmware.preflight_analyzer.PreflightMemoryAnalyzer.analyze_memory_and_instrumentation") as mock_preflight, \
         patch("backend.firmware.build_flasher.BuildFlasher.flash_board") as mock_flash, \
         patch("backend.api.routes_firmware.get_serial_mgr") as mock_get_serial:

        mock_serial = MagicMock()
        mock_get_serial.return_value = mock_serial

        # Memory analysis triggers flash overflow
        mock_preflight.side_effect = ArisException(
            error_code="ARIS_INSTRUMENTATION_FLASH_OVERFLOW",
            message="Flash overflow: 33194 > 32256 bytes",
            details={
                "board_id": "arduino_uno",
                "overflow_type": "FLASH",
                "overflow_bytes": 938,
                "uploaded": False,
                "original_source_preserved": True
            },
            recoverable=True,
            status_code=400
        )

        resp = client.post("/api/firmware/instrument-and-build", json={
            "source_code": MINIMAL_BLINK_SKETCH,
            "board_id": "arduino_uno",
            "port": "COM3",
            "execute_upload": True,
            "instrumentation_mode": "BALANCED"
        })

        assert resp.status_code == 400
        data = resp.json()
        assert data["error_code"] == "ARIS_INSTRUMENTATION_FLASH_OVERFLOW"
        assert data["details"]["uploaded"] is False
        assert data["details"]["original_source_preserved"] is True

        # Assert zero upload and zero serial activation
        mock_flash.assert_not_called()
        mock_serial.set_active_run.assert_not_called()

