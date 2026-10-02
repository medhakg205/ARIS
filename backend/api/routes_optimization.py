"""
ARIS Optimization Candidate Approval, Generation, Pareto & Listing REST API Routes.
Endpoints:
- GET /api/runs/{run_id}/optimizations
- POST /api/optimizations/{optimization_id}/approve
- POST /api/optimizations/{optimization_id}/reject
- POST /api/optimizations/{optimization_id}/rollback
- POST /api/optimizations/generate
- POST /api/optimizations/pareto-frontier
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.dependencies import get_db
from backend.telemetry.telemetry_schema import ArisException
from backend.firmware.board_profiles import get_board_profile
from backend.hardware.capability_negotiator import CapabilityGraphBuilder
from backend.experiments.experiment_memory import ExperimentMemory
from backend.experiments.manifest_models import PerformanceHypothesis
from backend.optimization.candidate_generation_engine import CandidateGenerationEngine
from backend.optimization.candidate_models import HardwareAwareCandidate, ApprovalDecision
from backend.optimization.pareto_frontier import ParetoFrontierAnalyzer

router = APIRouter(tags=["Optimization"])


class GenerateCandidateRequest(BaseModel):
    finding: Dict[str, Any]
    board_id: str = "arduino_uno"
    hypothesis_id: Optional[str] = None
    current_flash_used: int = 12000
    current_sram_used: int = 1000


class ParetoFrontierRequest(BaseModel):
    candidates: List[Dict[str, Any]]


@router.get("/api/runs/{run_id}/optimizations")
def list_run_optimizations(run_id: str) -> List[Dict[str, Any]]:
    """Lists all optimization candidates linked to a specific run."""
    db = get_db()
    opts = db.get_optimizations_by_run(run_id)
    return [o.model_dump() for o in opts]


@router.get("/api/optimizations/{optimization_id}")
def get_optimization(optimization_id: str) -> Dict[str, Any]:
    """Retrieves a specific optimization candidate by ID."""
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
    return opt.model_dump()


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


@router.post("/api/optimizations/{optimization_id}/rollback")
def rollback_optimization(optimization_id: str) -> Dict[str, Any]:
    """
    Transitions optimization candidate status to ROLLED_BACK.
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

    opt.status = "ROLLED_BACK"
    db.save_optimization(opt)
    return opt.model_dump()


@router.post("/api/optimizations/generate")
def generate_hardware_aware_candidate(req: GenerateCandidateRequest) -> Dict[str, Any]:
    """
    Synthesizes a HardwareAwareCandidate based on findings, capability graph,
    and historical experiment memory.
    """
    db = get_db()
    board_prof = get_board_profile(req.board_id)
    cap_graph = CapabilityGraphBuilder.build(board_prof)
    memory = ExperimentMemory([])

    hypothesis = None
    if req.hypothesis_id:
        hypo_dict = db.get_hypothesis(req.hypothesis_id) if hasattr(db, "get_hypothesis") else None
        if hypo_dict:
            hypothesis = PerformanceHypothesis(**hypo_dict)

    candidate = CandidateGenerationEngine.generate_candidate_for_finding(
        finding=req.finding,
        capability_graph=cap_graph,
        hypothesis=hypothesis,
        memory=memory,
        current_flash_used=req.current_flash_used,
        current_sram_used=req.current_sram_used
    )

    return candidate.model_dump()


@router.post("/api/optimizations/pareto-frontier")
def compute_pareto_frontier_endpoint(req: ParetoFrontierRequest) -> List[Dict[str, Any]]:
    """
    Filters a set of candidates to the non-dominated Pareto frontier set.
    """
    candidates = [HardwareAwareCandidate(**c) for c in req.candidates]
    frontier = ParetoFrontierAnalyzer.compute_pareto_frontier(candidates)
    return [c.model_dump() for c in frontier]
