"""
Test Local Source Application Engine & Integrity Verification
Validates that:
1. An accepted optimization actually modifies the user's local Arduino source file (.ino) on disk.
2. The user's target file contains ZERO ARIS runtime code (no #include <aris_runtime.h>, no ARIS hooks).
3. A timestamped safety backup is created in .aris/backups/ before any write.
4. Atomic write and disk read-back verification ensures exact SHA-256 matching.
5. Revert restores the exact original source byte-for-byte.
6. Stale source detection rejects modifications if the user edited the file externally (HTTP 409 / conflict).
7. Invalid target file extensions (.exe, .py, etc.) are strictly rejected.
"""

import os
import hashlib
import tempfile
import pytest

from backend.database.db_engine import DatabaseEngine
from backend.database.models import FirmwareRecord, OptimizationRecord
from backend.optimization.source_application_engine import (
    apply_candidate_to_source,
    revert_candidate_source,
)
from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES


ORIGINAL_SKETCH = """// User Arduino Sketch: Blink
const int ledPin = 13;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(1000);
  digitalWrite(ledPin, LOW);
  delay(1000);
}
"""

OPTIMIZED_CANDIDATE_CODE = """// User Arduino Sketch: Non-blocking Blink (ARIS Optimized)
const int ledPin = 13;
unsigned long previousMillis = 0;
const long interval = 1000;
int ledState = LOW;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    ledState = (ledState == LOW) ? HIGH : LOW;
    digitalWrite(ledPin, ledState);
  }
}
"""

CANDIDATE_WITH_INSTRUMENTATION_LEAK = """#include <aris_runtime.h>
// User Arduino Sketch: Non-blocking Blink
const int ledPin = 13;

void setup() {
  ARIS.init(115200);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  ARIS.loop_enter();
  // non-blocking logic
  ARIS.loop_exit();
}
"""


@pytest.fixture
def test_env():
    """Provides an isolated directory and test database."""
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_aris.db")
    db = DatabaseEngine(db_file)
    for p in CANONICAL_BOARD_PROFILES.values():
        db.save_board(p.to_record())

    # Create local sketch file
    sketch_path = os.path.join(temp_dir, "BlinkTest.ino")
    with open(sketch_path, "w", encoding="utf-8") as f:
        f.write(ORIGINAL_SKETCH)

    parent_hash = hashlib.sha256(ORIGINAL_SKETCH.encode("utf-8")).hexdigest()

    # Create baseline firmware record
    fw = FirmwareRecord(
        firmware_id="FW-BASE-001",
        name="BlinkTest",
        source_code=ORIGINAL_SKETCH,
        source_hash=parent_hash,
        status="ACTIVE",
    )
    db.save_firmware(fw)

    yield {
        "temp_dir": temp_dir,
        "db": db,
        "sketch_path": sketch_path,
        "parent_hash": parent_hash,
        "fw": fw,
    }

    # Cleanup
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass


def test_full_source_application_and_rollback_lifecycle(test_env):
    """
    Test complete lifecycle:
    1. Apply candidate -> local .ino modified on disk.
    2. Zero ARIS runtime code in destination file.
    3. Backup created and readable.
    4. Resulting hash verified.
    5. Revert restores exact original bytes and SHA-256.
    """
    db = test_env["db"]
    sketch_path = test_env["sketch_path"]
    parent_hash = test_env["parent_hash"]

    opt = OptimizationRecord(
        optimization_id="OPT-CAND-001",
        finding_id="FIND-001",
        title="Replace blocking delay with millis timer",
        problem="Blocking delay stalls execution",
        source_location={"file": sketch_path, "line": 8},
        before_code="delay(1000);",
        after_code=OPTIMIZED_CANDIDATE_CODE,
        reason="Converts blocking delays into non-blocking state machine",
        hardware_consideration="Uses millis hardware timer",
        expected_effect={"loop_time_reduction": 0.99},
        transformation_id="TR-001-DELAY-TO-MILLIS",
        parent_firmware_id="FW-BASE-001",
        parent_source_hash=parent_hash,
        candidate_source_hash="",
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    # 1. Apply candidate
    result = apply_candidate_to_source(
        candidate_id="OPT-CAND-001",
        sketch_path=sketch_path,
        expected_hash=parent_hash,
        db=db,
    )

    assert result["success"] is True
    assert result["applied"] is True
    assert os.path.exists(result["backup_path"])

    # 2. Verify disk file actually modified
    with open(sketch_path, "r", encoding="utf-8") as f:
        disk_content = f.read()

    assert disk_content == OPTIMIZED_CANDIDATE_CODE
    assert "millis()" in disk_content
    assert "delay(1000)" not in disk_content

    # 3. Verify ZERO ARIS runtime code in user source file
    assert "#include <aris_runtime.h>" not in disk_content
    assert "ARIS." not in disk_content
    assert "aris_loop_hook" not in disk_content
    assert "ARIS_RUN_ID" not in disk_content

    # 4. Verify backup content matches original sketch exactly
    with open(result["backup_path"], "r", encoding="utf-8") as f:
        backup_content = f.read()
    assert backup_content == ORIGINAL_SKETCH
    assert hashlib.sha256(backup_content.encode("utf-8")).hexdigest() == parent_hash

    # 5. Verify DB status
    updated_opt = db.get_optimization("OPT-CAND-001")
    assert updated_opt.applied is True
    assert updated_opt.status == "APPLIED"

    # 6. Revert candidate
    revert_result = revert_candidate_source(
        candidate_id="OPT-CAND-001",
        sketch_path=sketch_path,
        backup_path=result["backup_path"],
        db=db,
    )

    assert revert_result["success"] is True
    assert revert_result["reverted"] is True

    # 7. Verify disk file restored to exact original code
    with open(sketch_path, "r", encoding="utf-8") as f:
        reverted_content = f.read()

    assert reverted_content == ORIGINAL_SKETCH
    assert hashlib.sha256(reverted_content.encode("utf-8")).hexdigest() == parent_hash

    # 8. Verify DB status after rollback
    rolled_back_opt = db.get_optimization("OPT-CAND-001")
    assert rolled_back_opt.applied is False
    assert rolled_back_opt.status == "ROLLED_BACK"


def test_runtime_code_stripping_guarantee(test_env):
    """
    Guarantees that even if candidate code mistakenly contains ARIS runtime hooks,
    the source application engine strips them cleanly before writing to the user sketch.
    """
    db = test_env["db"]
    sketch_path = test_env["sketch_path"]
    parent_hash = test_env["parent_hash"]

    opt = OptimizationRecord(
        optimization_id="OPT-CAND-LEAK",
        finding_id="FIND-001",
        title="Candidate with potential leak",
        problem="Overhead",
        source_location={"file": sketch_path, "line": 5},
        before_code="",
        after_code=CANDIDATE_WITH_INSTRUMENTATION_LEAK,
        reason="Testing runtime stripping",
        hardware_consideration="None",
        expected_effect={},
        transformation_id="TR-001",
        parent_firmware_id="FW-BASE-001",
        parent_source_hash=parent_hash,
        candidate_source_hash="",
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    result = apply_candidate_to_source(
        candidate_id="OPT-CAND-LEAK",
        sketch_path=sketch_path,
        expected_hash=parent_hash,
        db=db,
    )

    assert result["success"] is True
    with open(sketch_path, "r", encoding="utf-8") as f:
        disk_content = f.read()

    # Must be stripped completely
    assert "#include <aris_runtime.h>" not in disk_content
    assert "ARIS.init" not in disk_content
    assert "ARIS.loop_enter" not in disk_content
    assert "ARIS.loop_exit" not in disk_content


def test_reject_external_stale_source_modification(test_env):
    """
    If the user modifies the .ino file externally in Arduino IDE while ARIS was analyzing/validating,
    the source application engine must detect SHA-256 mismatch and abort safely without overwriting.
    """
    db = test_env["db"]
    sketch_path = test_env["sketch_path"]
    parent_hash = test_env["parent_hash"]

    opt = OptimizationRecord(
        optimization_id="OPT-CAND-STALE",
        finding_id="FIND-001",
        title="Stale source test",
        problem="Overhead",
        source_location={"file": sketch_path, "line": 5},
        before_code="",
        after_code=OPTIMIZED_CANDIDATE_CODE,
        reason="Testing conflict abort",
        hardware_consideration="None",
        expected_effect={},
        transformation_id="TR-001",
        parent_firmware_id="FW-BASE-001",
        parent_source_hash=parent_hash,
        candidate_source_hash="",
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    # User modifies file externally
    external_edit = ORIGINAL_SKETCH + "\n// User edited this line in Arduino IDE!\n"
    with open(sketch_path, "w", encoding="utf-8") as f:
        f.write(external_edit)

    # Attempt to apply candidate with old parent_hash expectation
    with pytest.raises(Exception) as exc_info:
        apply_candidate_to_source(
            candidate_id="OPT-CAND-STALE",
            sketch_path=sketch_path,
            expected_hash=parent_hash,
            db=db,
        )

    # Check that error describes parent source mismatch
    assert "Source hash mismatch" in str(exc_info.value) or "modified externally" in str(exc_info.value) or "409" in str(exc_info.value)

    # Verify user's external edit was NOT overwritten
    with open(sketch_path, "r", encoding="utf-8") as f:
        preserved_content = f.read()
    assert preserved_content == external_edit


def test_reject_unsupported_file_extension(test_env):
    """
    Only Arduino sketches and C/C++ source files (.ino, .cpp, .c, .h) are permitted.
    All other file types must be rejected.
    """
    db = test_env["db"]
    temp_dir = test_env["temp_dir"]

    opt = OptimizationRecord(
        optimization_id="OPT-CAND-EXT",
        finding_id="FIND-001",
        title="Extension test",
        problem="Overhead",
        source_location={"file": os.path.join(temp_dir, "test.ino"), "line": 1},
        before_code="",
        after_code="",
        reason="Testing bad extension",
        hardware_consideration="None",
        expected_effect={},
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    bad_path = os.path.join(temp_dir, "danger.exe")
    with open(bad_path, "w") as f:
        f.write("test")

    with pytest.raises(Exception) as exc_info:
        apply_candidate_to_source(
            candidate_id="OPT-CAND-EXT",
            sketch_path=bad_path,
            expected_hash="any",
            db=db,
        )

    assert "Invalid sketch file extension" in str(exc_info.value) or "extension" in str(exc_info.value).lower()


def test_source_application_with_spaces_and_unicode_path(test_env):
    """
    Verifies that paths containing spaces and Unicode characters (e.g. accents)
    are handled safely without encoding errors or path corruption.
    """
    db = test_env["db"]
    temp_dir = test_env["temp_dir"]

    unicode_dir = os.path.join(temp_dir, "My Arduino Projects", "Robotique Électronique")
    os.makedirs(unicode_dir, exist_ok=True)
    sketch_path = os.path.join(unicode_dir, "Contrôleur Moteur.ino")

    custom_sketch = """// Contrôleur de moteur pas à pas
void setup() {
  Serial.begin(115200);
}
void loop() {
  delay(500);
}
"""
    with open(sketch_path, "w", encoding="utf-8") as f:
        f.write(custom_sketch)

    parent_hash = hashlib.sha256(custom_sketch.encode("utf-8")).hexdigest()

    opt = OptimizationRecord(
        optimization_id="OPT-UNICODE-001",
        finding_id="FIND-U1",
        title="Non-blocking delay replacement",
        problem="Busy wait",
        source_location={"file": sketch_path, "line": 6},
        before_code="delay(500);",
        after_code="""static unsigned long prev = 0;
  if (millis() - prev >= 500) {
    prev = millis();
  }""",
        reason="Non-blocking execution",
        hardware_consideration="None",
        expected_effect={},
        parent_source_hash=parent_hash,
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    # Apply
    res = apply_candidate_to_source(
        candidate_id="OPT-UNICODE-001",
        sketch_path=sketch_path,
        expected_hash=parent_hash,
        db=db,
    )

    assert res["success"] is True
    assert os.path.exists(res["backup_path"])

    with open(sketch_path, "r", encoding="utf-8") as f:
        modified_content = f.read()

    assert "Contrôleur de moteur" in modified_content
    assert "millis() - prev >= 500" in modified_content
    assert "delay(500)" not in modified_content

    # Revert
    rev = revert_candidate_source(
        candidate_id="OPT-UNICODE-001",
        sketch_path=sketch_path,
        backup_path=res["backup_path"],
        db=db,
    )

    assert rev["success"] is True
    with open(sketch_path, "r", encoding="utf-8") as f:
        reverted_content = f.read()

    assert reverted_content == custom_sketch
    assert hashlib.sha256(reverted_content.encode("utf-8")).hexdigest() == parent_hash


def test_preserve_unrelated_code_and_comments_on_diff_application(test_env):
    """
    Verifies that when applying an optimization targeted at a specific block,
    all surrounding custom functions, comments, indentation, formatting,
    and library includes are 100% preserved.
    """
    db = test_env["db"]
    temp_dir = test_env["temp_dir"]

    rich_sketch = """/*
 * Complex User Project
 * Author: Jane Doe (c) 2026
 * Description: Multi-sensor environmental monitor
 */
#include <Wire.h>
#include <SPI.h>

#define SENSOR_PIN A0
const float CALIBRATION_OFFSET = 1.42857;

// Critical state machine
enum SystemState { IDLE, SAMPLING, TRANSMITTING };
SystemState currentState = IDLE;

void readSensorValues() {
  int raw = analogRead(SENSOR_PIN);
  Serial.print("Raw: ");
  Serial.println(raw);
}

void setup() {
  Wire.begin();
  Serial.begin(115200);
  pinMode(13, OUTPUT);
}

void loop() {
  readSensorValues();
  // Target of optimization
  delay(100);
  // Important post-sampling trigger
  digitalWrite(13, !digitalRead(13));
}
"""
    sketch_path = os.path.join(temp_dir, "RichProject.ino")
    with open(sketch_path, "w", encoding="utf-8") as f:
        f.write(rich_sketch)

    parent_hash = hashlib.sha256(rich_sketch.encode("utf-8")).hexdigest()

    opt = OptimizationRecord(
        optimization_id="OPT-PRESERVE-001",
        finding_id="FIND-P1",
        title="Delay replacement",
        problem="delay(100) blocks loop",
        source_location={"file": sketch_path, "line": 31},
        before_code="  delay(100);",
        after_code="  static unsigned long lastTick = 0;\n  if (millis() - lastTick >= 100) {\n    lastTick = millis();\n  }",
        reason="Preserve structure",
        hardware_consideration="None",
        expected_effect={},
        parent_source_hash=parent_hash,
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    res = apply_candidate_to_source(
        candidate_id="OPT-PRESERVE-001",
        sketch_path=sketch_path,
        expected_hash=parent_hash,
        db=db,
    )

    assert res["success"] is True

    with open(sketch_path, "r", encoding="utf-8") as f:
        applied_content = f.read()

    # Verify comments and surrounding functions preserved
    assert "Complex User Project" in applied_content
    assert "Author: Jane Doe (c) 2026" in applied_content
    assert "#include <Wire.h>" in applied_content
    assert "#include <SPI.h>" in applied_content
    assert "enum SystemState { IDLE, SAMPLING, TRANSMITTING };" in applied_content
    assert "void readSensorValues() {" in applied_content
    assert "CALIBRATION_OFFSET = 1.42857" in applied_content
    assert "digitalWrite(13, !digitalRead(13));" in applied_content
    assert "delay(100);" not in applied_content
    assert "millis() - lastTick >= 100" in applied_content


def test_missing_file_and_nonexistent_candidate_safety(test_env):
    """
    Verifies that calling apply or revert with missing files or nonexistent candidates
    raises safe ArisException without corrupting any state.
    """
    db = test_env["db"]
    temp_dir = test_env["temp_dir"]

    # Nonexistent candidate
    with pytest.raises(Exception) as exc_info:
        apply_candidate_to_source(
            candidate_id="OPT-NONEXISTENT",
            sketch_path=os.path.join(temp_dir, "any.ino"),
            db=db,
        )
    assert "not found" in str(exc_info.value).lower()

    # Nonexistent file
    opt = OptimizationRecord(
        optimization_id="OPT-GHOST",
        finding_id="F-1",
        title="Ghost",
        problem="None",
        source_location={"file": "nonexistent.ino", "line": 1},
        before_code="",
        after_code="",
        reason="",
        hardware_consideration="",
        expected_effect={},
        status="VALIDATED",
        applied=False,
    )
    db.save_optimization(opt)

    with pytest.raises(Exception) as exc_info2:
        apply_candidate_to_source(
            candidate_id="OPT-GHOST",
            sketch_path=os.path.join(temp_dir, "does_not_exist.ino"),
            db=db,
        )
    assert "does not exist" in str(exc_info2.value).lower()
