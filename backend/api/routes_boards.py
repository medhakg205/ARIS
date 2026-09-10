"""
ARIS Board Profiles REST API Routes.
Endpoints:
- GET /api/boards
- GET /api/boards/{board_id}
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends

from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES, get_board_profile
from backend.telemetry.telemetry_schema import ArisException

router = APIRouter(tags=["Boards"])


@router.get("/api/boards")
def list_boards() -> List[Dict[str, Any]]:
    """
    Returns all canonical supported target boards:
    arduino_uno, arduino_nano, arduino_mega.
    """
    return [p.to_dict() for p in CANONICAL_BOARD_PROFILES.values()]


@router.get("/api/boards/{board_id}")
def get_board(board_id: str) -> Dict[str, Any]:
    """
    Returns full hardware constraints and register map for a specific board.
    Raises ARIS_UNSUPPORTED_BOARD if board is unrecognized.
    """
    try:
        profile = get_board_profile(board_id)
        return profile.to_dict()
    except KeyError:
        raise ArisException(
            error_code="ARIS_UNSUPPORTED_BOARD",
            message=f"Board ID '{board_id}' is not supported. Supported: {list(CANONICAL_BOARD_PROFILES.keys())}",
            details={"board_id": board_id},
            recoverable=False,
            status_code=404
        )
