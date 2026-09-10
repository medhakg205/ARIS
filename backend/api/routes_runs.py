"""
ARIS Execution Run Lifecycle REST API Routes.
Endpoints:
- POST /api/runs
- GET /api/runs
- GET /api/runs/{run_id}
- POST /api/runs/{run_id}/start
- POST /api/runs/{run_id}/stop
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import (
    get_db,
    get_simulator,
    get_serial_mgr,
    get_baseline_engine
)
from backend.database.models import RunRecord
from backend.firmware.board_profiles import get_board_profile
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Runs"])


class CreateRunRequest(BaseModel):
    """Payload to configure a new execution run."""
    board_id: str = Field(default="arduino_uno")
    firmware_id: Optional[str] = None
    instrumentation_mode: str = Field(default="BALANCED")  # "LOW", "BALANCED", "FULL"
    is_simulated: bool = Field(default=False)
    is_demo: bool = Field(default=False)


@router.post("/api/runs")
def create_run(req: CreateRunRequest) -> Dict[str, Any]:
    """
    Creates a new execution Run in state CREATED.
    Validates board profile existence.
    """
    # Verify board profile
    try:
        get_board_profile(req.board_id)
    except KeyError:
        raise ArisException(
            error_code="ARIS_UNSUPPORTED_BOARD",
            message=f"Board ID '{req.board_id}' is not supported.",
            details={"board_id": req.board_id},
            recoverable=False,
            status_code=400
        )

    db = get_db()
    run_id = f"ARIS-{uuid.uuid4().hex[:6].upper()}"
    record = RunRecord(
        run_id=run_id,
        board_id=req.board_id,
        firmware_id=req.firmware_id,
        instrumentation_mode=req.instrumentation_mode,
        start_time=None,
        end_time=None,
        status="CREATED",
        is_simulated=req.is_simulated,
        is_demo=req.is_demo,
        baseline_id=None
    )
    db.save_run(record)
    return record.model_dump()


@router.get("/api/runs")
def list_runs() -> List[Dict[str, Any]]:
    """Returns all execution runs."""
    db = get_db()
    return [r.model_dump() for r in db.list_runs()]


@router.get("/api/runs/{run_id}")
def get_run_detail(run_id: str) -> Dict[str, Any]:
    """Retrieves metadata and status of a specific run."""
    db = get_db()
    run = db.get_run(run_id)
    if not run:
        raise ArisException(
            error_code="ARIS_VALIDATION_FAILED",
            message=f"Run with ID '{run_id}' does not exist.",
            details={"run_id": run_id},
            recoverable=False,
            status_code=404
        )
    return run.model_dump()


@router.post("/api/runs/{run_id}/start")
def start_run(run_id: str) -> Dict[str, Any]:
    """
    Transitions run into RUNNING / COLLECTING status.
    If run is simulated or in DEMO MODE, activates the Virtual MCU simulator.
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

    run.status = "RUNNING"
    run.start_time = datetime.now(timezone.utc).isoformat()
    db.save_run(run)

    # Bind active run to serial manager
    serial_mgr = get_serial_mgr()
    serial_mgr.set_active_run(run_id)

    # If simulated, start Virtual MCU
    simulator = get_simulator()
    if run.is_simulated or run.is_demo:
        simulator.set_board(run.board_id)
        simulator.start(run_id=run_id)

    return run.model_dump()


@router.post("/api/runs/{run_id}/stop")
def stop_run(run_id: str) -> Dict[str, Any]:
    """
    Transitions run into COMPLETED status and triggers automated baseline computation.
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

    simulator = get_simulator()
    if simulator.running and simulator.run_id == run_id:
        simulator.stop()

    run.status = "COMPLETED"
    run.end_time = datetime.now(timezone.utc).isoformat()
    db.save_run(run)

    # Automatically compute baseline if samples were collected
    baseline_eng = get_baseline_engine()
    try:
        base_record = baseline_eng.generate_baseline(run_id, min_samples_required=3)
        run.baseline_id = base_record.baseline_id
    except Exception:
        pass

    return run.model_dump()
