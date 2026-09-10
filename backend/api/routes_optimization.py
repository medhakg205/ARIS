"""
ARIS Optimization Candidate Approval & Listing REST API Routes.
Endpoints:
- GET /api/runs/{run_id}/optimizations
- POST /api/optimizations/{optimization_id}/approve
- POST /api/optimizations/{optimization_id}/reject
"""

from typing import List, Dict, Any
from fastapi import APIRouter

from backend.api.dependencies import get_db
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Optimization"])


@router.get("/api/runs/{run_id}/optimizations")
def list_run_optimizations(run_id: str) -> List[Dict[str, Any]]:
    """Lists all optimization candidates linked to a specific run."""
    db = get_db()
    opts = db.get_optimizations_by_run(run_id)
    return [o.model_dump() for o in opts]


@router.post("/api/optimizations/{optimization_id}/approve")
def approve_optimization(optimization_id: str) -> Dict[str, Any]:
    """
    Transitions optimization candidate status to APPROVED.
    Authorizes the closed-loop build and flash verification stage.
    """
    db = get_db()
    opt = db.get_optimization(optimization_id)
    if not opt:
        raise ArisException(
            error_code="ARIS_OPTIMIZATION_INVALID",
            message=f"Optimization candidate '{optimization_id}' was not found.",
            details={"optimization_id": optimization_id},
            recoverable=False,
            status_code=404
        )

    opt.status = "APPROVED"
    db.save_optimization(opt)
    return opt.model_dump()


@router.post("/api/optimizations/{optimization_id}/reject")
def reject_optimization(optimization_id: str) -> Dict[str, Any]:
    """
    Transitions optimization candidate status to REJECTED.
    """
    db = get_db()
    opt = db.get_optimization(optimization_id)
    if not opt:
        raise ArisException(
            error_code="ARIS_OPTIMIZATION_INVALID",
            message=f"Optimization candidate '{optimization_id}' was not found.",
            details={"optimization_id": optimization_id},
            recoverable=False,
            status_code=404
        )

    opt.status = "REJECTED"
    db.save_optimization(opt)
    return opt.model_dump()
