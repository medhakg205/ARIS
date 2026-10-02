"""
ARIS Hardware Acceptance Test API Routes.
Provides REST endpoints to trigger and inspect Hardware Acceptance Test Sessions (HAT-01 to HAT-27).
Endpoints:
- POST /api/acceptance/run
- GET /api/acceptance/sessions/latest
- GET /api/acceptance/sessions/{session_id}
- GET /api/acceptance/suite
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.acceptance.acceptance_runner import (
    HardwareAcceptanceRunner,
    get_latest_acceptance_session
)
from backend.acceptance.hat_suite import get_canonical_hat_suite
from backend.acceptance.acceptance_models import HardwareValidationSession, HardwareAcceptanceTestItem

router = APIRouter(tags=["Hardware Acceptance"])


class RunAcceptanceRequest(BaseModel):
    board_id: Optional[str] = Field(default="arduino_uno", description="Target Arduino board profile")
    port: Optional[str] = Field(default=None, description="Optional target serial port (e.g. COM3 or /dev/ttyUSB0)")
    force_simulation: Optional[bool] = Field(default=False, description="Run in dry-run simulation mode")


@router.post("/api/acceptance/run", response_model=HardwareValidationSession)
def run_hardware_acceptance_session(req: RunAcceptanceRequest) -> HardwareValidationSession:
    """
    Executes the 27-item Hardware Acceptance Test Suite.
    If physical hardware is connected, runs physical checks.
    If physical hardware is missing, reports PHYSICAL_HARDWARE_REQUIRED honestly without fake passes.
    """
    runner = HardwareAcceptanceRunner(board_id=req.board_id or "arduino_uno")
    session = runner.run_session(
        port=req.port,
        board_id=req.board_id,
        force_simulation=bool(req.force_simulation)
    )
    return session


@router.get("/api/acceptance/sessions/latest", response_model=HardwareValidationSession)
def get_latest_session() -> HardwareValidationSession:
    """
    Retrieves the most recently executed HardwareValidationSession.
    If none has been run yet, triggers an evaluation session.
    """
    sess = get_latest_acceptance_session()
    if not sess:
        runner = HardwareAcceptanceRunner()
        sess = runner.run_session()
    return sess


@router.get("/api/acceptance/sessions/{session_id}", response_model=HardwareValidationSession)
def get_session_by_id(session_id: str) -> HardwareValidationSession:
    """
    Retrieves a specific HardwareValidationSession by ID.
    """
    sess = get_latest_acceptance_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"Acceptance session '{session_id}' not found.")
    return sess


@router.get("/api/acceptance/suite", response_model=List[HardwareAcceptanceTestItem])
def get_acceptance_suite_definitions() -> List[HardwareAcceptanceTestItem]:
    """
    Returns the canonical definition of all 27 Hardware Acceptance Tests (HAT-01 to HAT-27).
    """
    return get_canonical_hat_suite()
