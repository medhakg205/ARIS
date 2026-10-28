"""
ARIS Analysis & Findings REST API Routes.
Endpoints:
- GET /api/runs/{run_id}/analysis
- GET /api/runs/{run_id}/findings
"""

from typing import List, Dict, Any
from fastapi import APIRouter

from backend.api.dependencies import (
    get_db,
    get_static_analyzer,
    get_baseline_engine,
    get_firmware_mgr
)
from backend.correlation.correlation_engine import CorrelationEngine
from backend.analysis.rules import Finding
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Analysis"])


@router.get("/api/runs/{run_id}/analysis")
def get_run_analysis(run_id: str) -> Dict[str, Any]:
    """
    Computes and returns comprehensive run analysis combining:
    1. Static Firmware Metrics and Antipatterns
    2. Statistical Baseline Metrics (Mean, Median, Min, Max, Variance, Jitter)
    3. Fused Static + Runtime Correlations with explicit confidence scoring
    """
    db = get_db()
    run = db.get_run(run_id)
    if not run:
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Run '{run_id}' not found.",
            details={"run_id": run_id},
            recoverable=False,
            status_code=404
        )

    # 1. Retrieve or generate baseline
    baseline_eng = get_baseline_engine()
    baseline = None
    if run.baseline_id:
        baseline = db.get_baseline(run.baseline_id)
    if not baseline:
        try:
            baseline = baseline_eng.generate_baseline(run_id, min_samples_required=3)
        except Exception:
            pass

    # 2. Retrieve firmware source
    import os
    static_analyzer = get_static_analyzer()
    firmware_mgr = get_firmware_mgr()
    source_code = "void setup() {}\nvoid loop() {}"
    source_filename = "sketch.ino"
    target_fw_id = run.firmware_id or ("ARIS-DEMO-FIRMWARE-001" if (run.is_demo or run.is_simulated) else None)
    if target_fw_id:
        try:
            fw = firmware_mgr.get_firmware(target_fw_id)
            if fw.source_code and fw.source_code.strip():
                source_code = fw.source_code
                if fw.name:
                    source_filename = fw.name
        except Exception:
            pass

    if source_code == "void setup() {}\nvoid loop() {}":
        # Fallback 1: check most recent stored firmware
        try:
            firmwares = firmware_mgr.list_firmwares()
            for fw in reversed(firmwares):
                if fw.source_code and fw.source_code.strip():
                    source_code = fw.source_code
                    if fw.name:
                        source_filename = fw.name
                    break
        except Exception:
            pass

    if source_code == "void setup() {}\nvoid loop() {}":
        # Fallback 2: check auto-discovered Arduino IDE sketches on disk
        try:
            from backend.api.routes_firmware import _discover_arduino_ide_sketches
            sketches = _discover_arduino_ide_sketches()
            if sketches and os.path.exists(sketches[0]["path"]):
                with open(sketches[0]["path"], "r", encoding="utf-8", errors="replace") as sf:
                    disk_code = sf.read()
                    if disk_code.strip():
                        source_code = disk_code
                        source_filename = sketches[0].get("name", os.path.basename(sketches[0]["path"]))
        except Exception:
            pass

    static_result = static_analyzer.analyze_source(source_code, board_id=run.board_id, source_file=source_filename)

    # 3. Fuse correlations if baseline exists
    correlated_findings: List[Finding] = []
    if baseline:
        correlated_findings = CorrelationEngine.correlate(static_result.findings, baseline)
    else:
        correlated_findings = static_result.findings

    return {
        "run_id": run_id,
        "board_id": run.board_id,
        "source_file": source_filename,
        "static_metrics": {
            "total_lines": static_result.total_lines,
            "function_count": static_result.function_count,
            "estimated_flash_bytes": static_result.estimated_flash_bytes,
            "estimated_sram_static_bytes": static_result.estimated_sram_static_bytes,
            "flash_util_pct": static_result.flash_utilization_pct,
            "sram_util_pct": static_result.sram_utilization_pct,
            "flash_utilization_pct": static_result.flash_utilization_pct,
            "sram_utilization_pct": static_result.sram_utilization_pct
        },
        "baseline": baseline.model_dump() if baseline else None,
        "findings_count": len(correlated_findings),
        "findings": [f.model_dump() for f in correlated_findings]
    }


from pydantic import BaseModel, Field
from typing import Optional

class ScanSourceRequest(BaseModel):
    source_code: Optional[str] = None
    sketch_path: Optional[str] = None
    board_id: str = "arduino_uno"
    source_file: Optional[str] = None


@router.post("/api/analysis/scan")
def scan_source(req: ScanSourceRequest) -> Dict[str, Any]:
    """
    Executes fast static AST analysis directly on source code or file path.
    """
    import os
    static_analyzer = get_static_analyzer()
    source_code = req.source_code or ""
    source_filename = req.source_file or "sketch.ino"
    if req.sketch_path and os.path.exists(req.sketch_path):
        if not source_code:
            with open(req.sketch_path, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()
        source_filename = os.path.basename(req.sketch_path)

    if not source_code.strip():
        try:
            from backend.api.routes_firmware import _discover_arduino_ide_sketches
            sketches = _discover_arduino_ide_sketches()
            if sketches and os.path.exists(sketches[0]["path"]):
                with open(sketches[0]["path"], "r", encoding="utf-8", errors="replace") as sf:
                    source_code = sf.read()
                    source_filename = sketches[0].get("name", os.path.basename(sketches[0]["path"]))
        except Exception:
            pass

    res = static_analyzer.analyze_source(source_code, board_id=req.board_id, source_file=source_filename)
    return {
        "board_id": req.board_id,
        "source_file": source_filename,
        "static_metrics": {
            "total_lines": res.total_lines,
            "function_count": res.function_count,
            "estimated_flash_bytes": res.estimated_flash_bytes,
            "estimated_sram_static_bytes": res.estimated_sram_static_bytes,
            "flash_utilization_pct": res.flash_utilization_pct,
            "sram_utilization_pct": res.sram_utilization_pct
        },
        "findings_count": len(res.findings),
        "findings": [f.model_dump() for f in res.findings]
    }


@router.get("/api/runs/{run_id}/findings")
def get_run_findings(run_id: str) -> List[Dict[str, Any]]:
    """
    Returns the list of correlated Finding records for this run conforming to Finding Schema.
    """
    analysis = get_run_analysis(run_id)
    return analysis["findings"]
