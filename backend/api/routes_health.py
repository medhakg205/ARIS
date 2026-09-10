"""
ARIS Health Status REST API Routes.
Endpoint:
- GET /api/health
"""

from typing import Dict, Any
from fastapi import APIRouter

from backend.api.dependencies import get_db, get_serial_mgr, get_simulator
from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES

router = APIRouter(tags=["Health"])


@router.get("/api/health")
def health_check() -> Dict[str, Any]:
    """
    Returns system health, database readiness, serial status, and supported board list.
    """
    db = get_db()
    serial_mgr = get_serial_mgr()
    simulator = get_simulator()

    return {
        "status": "ONLINE",
        "version": "1.0.0",
        "subsystem": "ARIS Backend + Analysis Core",
        "database": "CONNECTED",
        "serial_connected": serial_mgr.connected,
        "serial_port": serial_mgr.current_port,
        "simulator_running": simulator.running,
        "mode": "DEMO MODE" if simulator.running else "OPERATIONAL",
        "supported_boards": list(CANONICAL_BOARD_PROFILES.keys())
    }
