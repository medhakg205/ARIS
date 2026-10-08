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


@router.get("/health")
def ping_health() -> Dict[str, Any]:
    """
    Lightweight health endpoint.
    Zero database queries, zero COM4/serial checks, zero heavy operations.
    Proves that the FastAPI process is alive and responsive.
    """
    return {
        "status": "ok",
        "service": "aris-backend",
        "version": "2.0.0",
        "port": 8765
    }


@router.get("/api/health")
def health_check() -> Dict[str, Any]:
    """
    Returns system health, database readiness, serial status, and supported board list.
    Safely catches any subsystem faults to prevent 500 crashes.
    """
    db_status = "UNKNOWN"
    serial_connected = False
    serial_port = None
    simulator_running = False

    try:
        db = get_db()
        db_status = "CONNECTED"
    except Exception as e:
        db_status = f"ERROR: {e}"

    try:
        serial_mgr = get_serial_mgr()
        serial_connected = serial_mgr.connected
        serial_port = serial_mgr.current_port
    except Exception:
        pass

    try:
        simulator = get_simulator()
        simulator_running = simulator.running
    except Exception:
        pass

    is_degraded = db_status.startswith("ERROR")
    return {
        "status": "DEGRADED" if is_degraded else "ONLINE",
        "version": "2.0.0",
        "subsystem": "ARIS Backend + Analysis Core",
        "database": db_status,
        "serial_connected": serial_connected,
        "serial_port": serial_port,
        "simulator_running": simulator_running,
        "mode": "DEMO MODE" if simulator_running else "OPERATIONAL",
        "supported_boards": list(CANONICAL_BOARD_PROFILES.keys())
    }
