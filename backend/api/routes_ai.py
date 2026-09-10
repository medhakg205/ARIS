"""
ARIS AI Interface REST API Routes (Contract for Engineer 3).
Endpoints:
- POST /api/ai/analyze
- POST /api/ai/generate-candidate
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import (
    get_db,
    get_static_analyzer,
    get_baseline_engine,
    get_firmware_mgr
)
from backend.firmware.board_profiles import get_board_profile
from backend.correlation.correlation_engine import CorrelationEngine
from backend.analysis.ai_interface import AIInterface, OptimizationCandidate, AIContextInput
from backend.database.models import OptimizationRecord
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["AI"])


class AIAnalyzeRequest(BaseModel):
    """Payload to request aggregated diagnostic context for AI optimization."""
    run_id: Optional[str] = None
    source_code: Optional[str] = None
    board_id: str = Field(default="arduino_uno")


class GenerateCandidateRequest(BaseModel):
    """Payload to request an optimization candidate."""
    finding: Dict[str, Any]
    source_code: str
    board_id: str = Field(default="arduino_uno")
    run_id: Optional[str] = None


@router.post("/api/ai/analyze")
def ai_analyze(req: AIAnalyzeRequest) -> Dict[str, Any]:
    """
    Assembles the complete analytical input context for Engineer 3's AI advisor:
    - board_profile
    - firmware_source
    - static_findings
    - runtime_metrics
    - baseline_metrics
    - runtime_static_correlations
    - optimization_history
    """
    db = get_db()
    profile = get_board_profile(req.board_id)

    source = req.source_code or "void setup() {}\nvoid loop() {}"
    static_analyzer = get_static_analyzer()
    static_result = static_analyzer.analyze_source(source, board_id=req.board_id)

    runtime_metrics = {}
    baseline_metrics = {}
    correlations = []

    if req.run_id:
        run = db.get_run(req.run_id)
        if run:
            base = None
            if run.baseline_id:
                base = db.get_baseline(run.baseline_id)
            if not base:
                try:
                    base = get_baseline_engine().generate_baseline(req.run_id, min_samples_required=2)
                except Exception:
                    pass

            if base:
                baseline_metrics = {k: v.model_dump() for k, v in base.metrics.items()}
                runtime_metrics = {k: v.mean for k, v in base.metrics.items()}
                correlated = CorrelationEngine.correlate(static_result.findings, base)
                correlations = [f.model_dump() for f in correlated]

    context = AIInterface.build_context(
        board_profile=profile.to_dict(),
        firmware_source=source,
        static_findings=[f.model_dump() for f in static_result.findings],
        runtime_metrics=runtime_metrics,
        baseline_metrics=baseline_metrics,
        runtime_static_correlations=correlations,
        optimization_history=[]
    )
    return context.model_dump()


@router.post("/api/ai/generate-candidate")
def generate_candidate(req: GenerateCandidateRequest) -> Dict[str, Any]:
    """
    Generates and validates an OptimizationCandidate conforming strictly
    to the canonical schema. Stores candidate in database.
    """
    candidate: OptimizationCandidate = AIInterface.generate_candidate_for_finding(
        finding=req.finding,
        source_code=req.source_code,
        board_id=req.board_id
    )

    # Persist in database
    db = get_db()
    record = OptimizationRecord(
        optimization_id=candidate.optimization_id,
        finding_id=candidate.finding_id,
        run_id=req.run_id,
        title=candidate.title,
        problem=candidate.problem,
        source_location=candidate.source_location,
        before_code=candidate.before_code,
        after_code=candidate.after_code,
        reason=candidate.reason,
        hardware_consideration=candidate.hardware_consideration,
        expected_effect=candidate.expected_effect,
        risk=candidate.risk,
        confidence=candidate.confidence,
        validation_required=candidate.validation_required,
        status=candidate.status
    )
    db.save_optimization(record)

    return candidate.model_dump()
