"""
ARIS Benchmark Validation REST API Routes.
Endpoints:
- POST /api/experiments/{experiment_id}/validate
- GET /api/experiments/{experiment_id}/result
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter

from backend.api.dependencies import get_experiment_engine, get_db
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Validation"])


class ValidateRequest(BaseModel):
    """Optional payload specifying candidate run to bind and validate."""
    candidate_run_id: Optional[str] = None


@router.post("/api/experiments/{experiment_id}/validate")
def validate_experiment(experiment_id: str, req: Optional[ValidateRequest] = None) -> Dict[str, Any]:
    """
    Triggers empirical benchmark validation between baseline and candidate runs.
    Decides validation status (VALIDATED, REGRESSION, etc.).
    """
    eng = get_experiment_engine()
    if req and req.candidate_run_id:
        eng.bind_candidate_run(experiment_id, req.candidate_run_id)

    report = eng.validate_experiment(experiment_id)
    return report.model_dump()


@router.get("/api/experiments/{experiment_id}/result")
def get_validation_result(experiment_id: str) -> Dict[str, Any]:
    """
    Returns the stored validation comparison result for the experiment.
    """
    eng = get_experiment_engine()
    db = get_db()
    exp = eng.get_experiment(experiment_id)

    if not exp.validation_id:
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Validation has not been run for experiment '{experiment_id}'.",
            details={"experiment_id": experiment_id},
            recoverable=True,
            status_code=400
        )

    val = db.get_validation_result(exp.validation_id)
    if not val:
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Validation result '{exp.validation_id}' not found.",
            details={"validation_id": exp.validation_id},
            recoverable=False,
            status_code=404
        )

    return val.model_dump()
