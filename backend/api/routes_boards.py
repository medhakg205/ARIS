"""
ARIS Board Profiles REST API Routes.
Endpoints:
- GET /api/boards
- GET /api/boards/{board_id}
- POST /api/boards/resolve
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter

from backend.firmware.board_profiles import (
    CANONICAL_BOARD_PROFILES,
    ALL_BOARD_PROFILES,
    get_board_profile,
    BoardProfileResolver
)
from backend.telemetry.telemetry_schema import ArisException
from backend.api.dependencies import get_db

router = APIRouter(tags=["Boards"])


class ResolveBoardRequest(BaseModel):
    fqbn: Optional[str] = None
    board_id: Optional[str] = None
    handshake_data: Optional[Dict[str, Any]] = None


@router.get("/api/boards")
def list_boards() -> List[Dict[str, Any]]:
    """
    Returns registered target boards from cache and database.
    """
    db = get_db()
    db_records = db.list_boards()
    if db_records:
        return [r.model_dump() for r in db_records]
    return [p.to_dict() for p in CANONICAL_BOARD_PROFILES.values()]


@router.get("/api/boards/{board_id}")
def get_board(board_id: str) -> Dict[str, Any]:
    """
    Returns full hardware constraints and register map for a specific board.
    Resolves dynamically if not in fixed cache.
    """
    try:
        profile = get_board_profile(board_id)
        return profile.to_dict()
    except KeyError:
        raise ArisException(
            error_code="ARIS_UNSUPPORTED_BOARD",
            message=f"Board ID '{board_id}' cannot be resolved.",
            details={"board_id": board_id},
            recoverable=False,
            status_code=404
        )


@router.post("/api/boards/resolve")
def resolve_board(req: ResolveBoardRequest) -> Dict[str, Any]:
    """
    Dynamically resolves a board profile from FQBN, board_id, or handshake data.
    Stores newly derived profile into persistent database.
    """
    profile = None
    if req.fqbn:
        profile = BoardProfileResolver.resolve_from_toolchain(req.fqbn)
    elif req.handshake_data:
        profile = BoardProfileResolver.resolve_from_handshake(req.handshake_data)
    elif req.board_id:
        profile = get_board_profile(req.board_id)

    if not profile:
        profile = BoardProfileResolver.create_partially_resolved(
            board_id=req.board_id or (req.fqbn.replace(":", "_").lower() if req.fqbn else "unknown"),
            display_name=f"Target ({req.fqbn or req.board_id or 'unknown'})",
            fqbn=req.fqbn
        )

    # Persist in DB
    try:
        db = get_db()
        db.save_board(profile.to_record())
    except Exception:
        pass

    return {
        "resolved": True,
        "profile": profile.to_dict()
    }


@router.get("/api/boards/{board_id}/capabilities")
def get_board_capabilities(board_id: str) -> Dict[str, Any]:
    """
    Returns the normalized HardwareCapabilityGraph for the specified board,
    tracking capability provenance and valid/unavailable instrumentation operations.
    """
    from backend.hardware.capability_negotiator import CapabilityGraphBuilder
    try:
        profile = get_board_profile(board_id)
    except KeyError:
        raise ArisException(
            error_code="ARIS_UNSUPPORTED_BOARD",
            message=f"Board ID '{board_id}' cannot be resolved for capabilities.",
            details={"board_id": board_id},
            recoverable=False,
            status_code=404
        )

    graph = CapabilityGraphBuilder.build(profile)
    return graph.model_dump()

