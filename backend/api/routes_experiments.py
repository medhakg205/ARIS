"""
ARIS Optimization Experiments REST API Routes.
Endpoints:
- POST /api/experiments
- GET /api/experiments
- GET /api/experiments/{experiment_id}
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import get_experiment_engine
from backend.database.models import ExperimentRecord

router = APIRouter(tags=["Experiments"])


class CreateExperimentRequest(BaseModel):
    """Payload to initiate a closed-loop optimization experiment."""
    title: str = Field(..., description="Experiment title")
    board_id: str = Field(default="arduino_uno")
    baseline_run_id: str = Field(..., description="Baseline reference execution run")
    optimization_id: str = Field(..., description="Optimization candidate to test")


@router.post("/api/experiments")
def create_experiment(req: CreateExperimentRequest) -> Dict[str, Any]:
    """
    Creates an experiment tying a baseline run to an optimization candidate.
    """
    eng = get_experiment_engine()
    exp = eng.create_experiment(
        title=req.title,
        board_id=req.board_id,
        baseline_run_id=req.baseline_run_id,
        optimization_id=req.optimization_id
    )
    return exp.model_dump()


@router.get("/api/experiments")
def list_experiments() -> List[Dict[str, Any]]:
    """Returns all optimization experiments."""
    eng = get_experiment_engine()
    return [e.model_dump() for e in eng.list_experiments()]


@router.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> Dict[str, Any]:
    """Returns details of a specific experiment."""
    eng = get_experiment_engine()
    exp = eng.get_experiment(experiment_id)
    return exp.model_dump()
