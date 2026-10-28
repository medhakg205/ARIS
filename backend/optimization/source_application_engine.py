"""
ARIS Local Source Application Engine.
Implements safe, transparent, verifiable on-disk modification and rollback of user Arduino sketches:
1. Target file validation (existence, allowed extensions: .ino, .cpp, .c, .h).
2. Parent SHA-256 integrity check (detects external modifications and stale analysis).
3. Timestamped backup creation in .aris/backups/<filename>.<timestamp>.bak.
4. Clean code transformation with strict ARIS transparency enforcement (zero runtime code injected).
5. Atomic write via temporary file with fsync flush.
6. Read-back verification (compares reread file SHA-256 against expected candidate hash).
7. Automatic rollback to backup if any write or verification error occurs.
8. Database lineage update (Candidate APPLIED, Firmware ACTIVE) only after successful verification.
9. Bit-for-bit rollback capability restoring original pre-optimization source.
"""

import os
import glob
import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backend.database.db_engine import DatabaseEngine
from backend.telemetry.telemetry_schema import ArisException


ALLOWED_SKETCH_EXTENSIONS = (".ino", ".cpp", ".c", ".h")


def apply_candidate_to_source(
    candidate_id: str,
    sketch_path: Optional[str] = None,
    expected_hash: Optional[str] = None,
    db: Optional[DatabaseEngine] = None
) -> Dict[str, Any]:
    """
    Safely applies a validated optimization candidate to the user's local Arduino source file on disk.
    Strictly preserves the ARIS transparency guarantee: no ARIS runtime code is ever injected into
    the permanent user source file.
    """
    if db is None:
        from backend.api.dependencies import get_db
        db = get_db()

    # 1. Fetch optimization candidate
    opt = db.get_optimization(candidate_id)
    if not opt:
        # Check physical evidence fallback
        from backend.api.routes_optimization import _get_physical_evidence_candidate
        phys_cand = _get_physical_evidence_candidate()
        if phys_cand and phys_cand.get("optimization_id") == candidate_id:
            from backend.database.models import OptimizationRecord
            opt = OptimizationRecord(**phys_cand)
            db.save_optimization(opt)
        else:
            raise ArisException(
                error_code="ARIS_OPTIMIZATION_INVALID",
                message=f"Optimization candidate '{candidate_id}' was not found.",
                details={"candidate_id": candidate_id},
                recoverable=False,
                status_code=404
            )

    # 2. Resolve target sketch path
    target_path = sketch_path
    if not target_path:
        if opt.source_location and opt.source_location.get("file"):
            candidate_file = opt.source_location["file"]
            if os.path.exists(candidate_file):
                target_path = candidate_file
        if not target_path:
            from backend.api.routes_firmware import _discover_arduino_ide_sketches
            sketches = _discover_arduino_ide_sketches()
            if sketches and os.path.exists(sketches[0]["path"]):
                target_path = sketches[0]["path"]

    if not target_path:
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message="No target Arduino sketch path specified or detected on disk.",
            details={"candidate_id": candidate_id},
            recoverable=True,
            status_code=400
        )

    target_path = os.path.abspath(target_path)

    # 3. Verify target file exists
    if not os.path.exists(target_path):
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Target sketch file does not exist on disk: {target_path}",
            details={"sketch_path": target_path},
            recoverable=True,
            status_code=400
        )

    # 4. Verify allowed extension (.ino, .cpp, .c, .h)
    if not target_path.lower().endswith(ALLOWED_SKETCH_EXTENSIONS):
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Invalid sketch file extension. Must be one of: {ALLOWED_SKETCH_EXTENSIONS}",
            details={"sketch_path": target_path},
            recoverable=False,
            status_code=400
        )

    # 5. Read current disk file & calculate SHA-256
    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as sf:
            current_source = sf.read()
    except Exception as e:
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Failed to read sketch file '{target_path}': {str(e)}",
            details={"sketch_path": target_path, "error": str(e)},
            recoverable=True,
            status_code=500
        )

    current_hash = hashlib.sha256(current_source.encode("utf-8")).hexdigest()

    # 6. Verify parent SHA-256 against expected hash (stale source protection)
    check_expected = expected_hash or opt.parent_source_hash
    if check_expected and check_expected != current_hash:
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message="Source hash mismatch prior to applying. The file has been modified externally after analysis.",
            details={
                "sketch_path": target_path,
                "current_disk_hash": current_hash,
                "expected_hash": check_expected
            },
            recoverable=True,
            status_code=409
        )

    # 7. Create timestamped backup
    sketch_dir = os.path.dirname(target_path)
    backup_dir = os.path.join(sketch_dir, ".aris", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp_ms = int(time.time() * 1000)
    base_name = os.path.basename(target_path)
    backup_path = os.path.join(backup_dir, f"{base_name}.{timestamp_ms}.bak")

    try:
        with open(backup_path, "w", encoding="utf-8") as bf:
            bf.write(current_source)
    except Exception as e:
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Failed to create safety backup prior to application: {str(e)}",
            details={"backup_path": backup_path, "error": str(e)},
            recoverable=True,
            status_code=500
        )

    # 8. Synthesize clean optimized code (Zero ARIS runtime code)
    new_source = current_source
    if opt.after_code:
        if "void setup" in opt.after_code and "void loop" in opt.after_code:
            new_source = opt.after_code
        elif opt.before_code and opt.before_code in current_source:
            new_source = current_source.replace(opt.before_code, opt.after_code, 1)
        elif opt.before_code and opt.before_code.strip() in current_source:
            new_source = current_source.replace(opt.before_code.strip(), opt.after_code.strip(), 1)
        else:
            new_source = current_source

    # Enforce strict transparency guarantee: strip any accidental ARIS instrumentation symbols
    clean_lines = []
    for line in new_source.splitlines(keepends=True):
        if any(kw in line for kw in ["aris_runtime.h", "ARIS.init", "ARIS.loop_enter", "ARIS.loop_exit", "ARIS_RUN_ID", "aris_loop_hook"]):
            continue
        clean_lines.append(line)
    new_source = "".join(clean_lines)

    target_hash = hashlib.sha256(new_source.encode("utf-8")).hexdigest()

    # 9. Write atomically via temporary file
    temp_path = f"{target_path}.tmp.{timestamp_ms}"
    try:
        with open(temp_path, "w", encoding="utf-8") as tf:
            tf.write(new_source)
            tf.flush()
            os.fsync(tf.fileno())

        os.replace(temp_path, target_path)

        # 10. Read back and verify resulting file
        with open(target_path, "r", encoding="utf-8") as vf:
            verified_content = vf.read()
        verified_hash = hashlib.sha256(verified_content.encode("utf-8")).hexdigest()

        if verified_hash != target_hash or verified_content != new_source:
            # Integrity check failure: automatic rollback
            with open(backup_path, "r", encoding="utf-8") as bf:
                orig_code = bf.read()
            with open(target_path, "w", encoding="utf-8") as rf:
                rf.write(orig_code)
            raise ArisException(
                error_code="ARIS_SOURCE_APPLY_FAILED",
                message="Integrity verification failed after writing to disk. Automatically reverted to backup.",
                details={"verified_hash": verified_hash, "target_hash": target_hash},
                recoverable=True,
                status_code=500
            )

    except Exception as e:
        # Clean up temp file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

        # Ensure backup restoration if target was partially written
        if os.path.exists(backup_path):
            try:
                with open(backup_path, "r", encoding="utf-8") as bf:
                    orig_code = bf.read()
                with open(target_path, "w", encoding="utf-8") as rf:
                    rf.write(orig_code)
            except Exception:
                pass

        if isinstance(e, ArisException):
            raise e
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Failed to apply source modification to '{target_path}': {str(e)}",
            details={"error": str(e), "sketch_path": target_path},
            recoverable=True,
            status_code=500
        )

    # 11. Update database models only after successful on-disk verification
    now_iso = datetime.now(timezone.utc).isoformat()
    opt.applied = True
    opt.applied_at = now_iso
    opt.backup_path = backup_path
    opt.parent_source_hash = current_hash
    opt.candidate_source_hash = target_hash
    opt.status = "APPLIED"
    db.save_optimization(opt)

    # Update active firmware record
    accepted_fw_id = f"FW-ACCEPTED-{opt.optimization_id}"
    accepted_fw = db.get_firmware(accepted_fw_id)
    if accepted_fw:
        accepted_fw.applied = True
        accepted_fw.applied_at = now_iso
        accepted_fw.backup_path = backup_path
        accepted_fw.source_code = new_source
        accepted_fw.source_hash = target_hash
        accepted_fw.status = "ACTIVE"
        db.save_firmware(accepted_fw)
    else:
        from backend.database.models import FirmwareRecord
        new_fw = FirmwareRecord(
            firmware_id=accepted_fw_id,
            name=f"Optimized: {opt.title}",
            source_code=new_source,
            parent_firmware_id=opt.parent_firmware_id,
            candidate_id=opt.optimization_id,
            source_hash=target_hash,
            status="ACTIVE",
            applied=True,
            applied_at=now_iso,
            backup_path=backup_path
        )
        db.save_firmware(new_fw)

    return {
        "success": True,
        "applied": True,
        "status": "APPLIED",
        "candidate_id": opt.optimization_id,
        "sketch_path": target_path,
        "backup_path": backup_path,
        "parent_source_hash": current_hash,
        "candidate_source_hash": target_hash,
        "applied_at": now_iso,
        "message": "Optimization applied to local Arduino source."
    }


def revert_candidate_source(
    candidate_id: Optional[str] = None,
    sketch_path: Optional[str] = None,
    backup_path: Optional[str] = None,
    db: Optional[DatabaseEngine] = None
) -> Dict[str, Any]:
    """
    Safely reverts an applied optimization candidate, restoring the user's sketch
    to the exact pre-modification state from its .aris/backups/ file.
    """
    if db is None:
        from backend.api.dependencies import get_db
        db = get_db()

    target_sketch = sketch_path
    target_backup = backup_path
    opt = None

    if candidate_id:
        opt = db.get_optimization(candidate_id)
        if opt:
            if not target_backup and opt.backup_path:
                target_backup = opt.backup_path
            if not target_sketch and opt.source_location and opt.source_location.get("file"):
                target_sketch = opt.source_location["file"]

    if not target_sketch:
        from backend.api.routes_firmware import _discover_arduino_ide_sketches
        sketches = _discover_arduino_ide_sketches()
        if sketches and os.path.exists(sketches[0]["path"]):
            target_sketch = sketches[0]["path"]

    if not target_backup and target_sketch:
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(target_sketch)), ".aris", "backups")
        if os.path.exists(backup_dir):
            baks = glob.glob(os.path.join(backup_dir, "*.bak"))
            if baks:
                baks.sort(key=os.path.getmtime, reverse=True)
                target_backup = baks[0]

    if not target_backup or not os.path.exists(target_backup):
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Backup file not found for rollback: {target_backup}",
            details={"backup_path": target_backup},
            recoverable=False,
            status_code=404
        )

    if not target_sketch or not os.path.exists(target_sketch):
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Target sketch file not found for rollback: {target_sketch}",
            details={"sketch_path": target_sketch},
            recoverable=False,
            status_code=404
        )

    # Read original code from backup
    with open(target_backup, "r", encoding="utf-8", errors="replace") as bf:
        restored_code = bf.read()

    expected_restored_hash = hashlib.sha256(restored_code.encode("utf-8")).hexdigest()

    # Write back atomically
    temp_path = f"{target_sketch}.rollback.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as tf:
            tf.write(restored_code)
            tf.flush()
            os.fsync(tf.fileno())

        os.replace(temp_path, target_sketch)

        # Verify restored file
        with open(target_sketch, "r", encoding="utf-8") as rf:
            verified_code = rf.read()
        verified_hash = hashlib.sha256(verified_code.encode("utf-8")).hexdigest()

        if verified_hash != expected_restored_hash:
            raise ArisException(
                error_code="ARIS_SOURCE_APPLY_FAILED",
                message="Integrity check failed during rollback restoration.",
                details={"verified_hash": verified_hash, "expected_hash": expected_restored_hash},
                recoverable=True,
                status_code=500
            )
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        if isinstance(e, ArisException):
            raise e
        raise ArisException(
            error_code="ARIS_SOURCE_APPLY_FAILED",
            message=f"Failed to restore backup: {str(e)}",
            details={"error": str(e)},
            recoverable=True,
            status_code=500
        )

    # Update database models
    if opt:
        opt.applied = False
        opt.status = "ROLLED_BACK"
        db.save_optimization(opt)

        accepted_fw_id = f"FW-ACCEPTED-{opt.optimization_id}"
        accepted_fw = db.get_firmware(accepted_fw_id)
        if accepted_fw:
            accepted_fw.applied = False
            accepted_fw.status = "ROLLED_BACK"
            db.save_firmware(accepted_fw)

        if opt.parent_firmware_id:
            parent_fw = db.get_firmware(opt.parent_firmware_id)
            if parent_fw:
                parent_fw.status = "ACTIVE"
                db.save_firmware(parent_fw)

    return {
        "success": True,
        "reverted": True,
        "status": "ROLLED_BACK",
        "candidate_id": candidate_id,
        "sketch_path": target_sketch,
        "restored_hash": expected_restored_hash,
        "message": "Sketch safely reverted to backup."
    }
