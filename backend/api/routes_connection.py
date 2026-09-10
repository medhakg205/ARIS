"""
ARIS Hardware Serial Connection REST API Routes.
Endpoints:
- GET /api/connection/status
- POST /api/connection/connect
- POST /api/connection/disconnect
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import get_serial_mgr, get_simulator
from backend.serial.serial_discovery import scan_serial_ports

router = APIRouter(tags=["Connection"])


class ConnectRequest(BaseModel):
    """Payload for establishing serial connection."""
    port: str
    baud_rate: int = Field(default=115200)
    run_id: Optional[str] = None


@router.get("/api/connection/status")
def connection_status() -> Dict[str, Any]:
    """
    Returns current hardware serial connection status, active port,
    and list of available discovered ports.
    """
    serial_mgr = get_serial_mgr()
    simulator = get_simulator()
    ports = [p.to_dict() for p in scan_serial_ports()]

    status = serial_mgr.get_status()
    status["discovered_ports"] = ports
    status["simulator_active"] = simulator.running
    status["mode"] = "DEMO MODE" if simulator.running else "PHYSICAL HARDWARE"
    return status


@router.post("/api/connection/connect")
def connect_hardware(req: ConnectRequest) -> Dict[str, Any]:
    """
    Connects to physical Arduino target over serial.
    Raises ARIS_SERIAL_DISCONNECTED if connection fails.
    """
    simulator = get_simulator()
    if simulator.running:
        simulator.stop()

    serial_mgr = get_serial_mgr()
    return serial_mgr.connect(port=req.port, baud_rate=req.baud_rate, run_id=req.run_id)


@router.post("/api/connection/disconnect")
def disconnect_hardware() -> Dict[str, Any]:
    """
    Disconnects the active physical serial interface.
    """
    serial_mgr = get_serial_mgr()
    return serial_mgr.disconnect()
