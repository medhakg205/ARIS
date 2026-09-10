"""
ARIS Telemetry Data REST API Routes.
Endpoint:
- GET /api/runs/{run_id}/telemetry
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query

from backend.api.dependencies import get_db
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Telemetry"])


@router.get("/api/runs/{run_id}/telemetry")
def get_run_telemetry(
    run_id: str,
    limit: int = Query(default=1000, ge=1, le=50000),
    metric: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Returns stored canonical telemetry samples for the specified execution run.
    """
    db = get_db()
    run = db.get_run(run_id)
    if not run:
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Run '{run_id}' does not exist.",
            details={"run_id": run_id},
            recoverable=False,
            status_code=404
        )

    samples = db.get_telemetry_by_run(run_id, limit=limit)
    if metric:
        samples = [s for s in samples if s.metric == metric]

    return [s.model_dump() for s in samples]
