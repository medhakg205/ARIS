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
    static_analyzer = get_static_analyzer()
    firmware_mgr = get_firmware_mgr()
    source_code = "void setup() {}\nvoid loop() {}"
    if run.firmware_id:
        try:
            fw = firmware_mgr.get_firmware(run.firmware_id)
            if fw.source_code:
                source_code = fw.source_code
        except Exception:
            pass

    static_result = static_analyzer.analyze_source(source_code, board_id=run.board_id)

    # 3. Fuse correlations if baseline exists
    correlated_findings: List[Finding] = []
    if baseline:
        correlated_findings = CorrelationEngine.correlate(static_result.findings, baseline)
    else:
        correlated_findings = static_result.findings

    return {
        "run_id": run_id,
        "board_id": run.board_id,
        "static_metrics": {
            "total_lines": static_result.total_lines,
            "function_count": static_result.function_count,
            "estimated_flash_bytes": static_result.estimated_flash_bytes,
            "estimated_sram_static_bytes": static_result.estimated_sram_static_bytes,
            "flash_utilization_pct": static_result.flash_utilization_pct,
            "sram_utilization_pct": static_result.sram_utilization_pct
        },
        "baseline": baseline.model_dump() if baseline else None,
        "findings_count": len(correlated_findings),
        "findings": [f.model_dump() for f in correlated_findings]
    }


@router.get("/api/runs/{run_id}/findings")
def get_run_findings(run_id: str) -> List[Dict[str, Any]]:
    """
    Returns the list of correlated Finding records for this run conforming to Finding Schema.
    """
    analysis = get_run_analysis(run_id)
    return analysis["findings"]
