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
    ports_objects = scan_serial_ports()
    ports = [p.to_dict() for p in ports_objects]

    status = serial_mgr.get_status()
    status["discovered_ports"] = ports
    status["available_ports"] = [p["device"] for p in ports]
    status["simulator_active"] = simulator.running
    status["mode"] = "DEMO MODE" if simulator.running else "PHYSICAL HARDWARE"
    return status


@router.post("/api/connection/auto-detect")
def auto_detect_and_connect(run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Automatically scans USB/COM ports, identifies the connected Arduino board model
    (Uno, Nano, Mega), retrieves its hardware memory specifications, and establishes
    a serial telemetry connection without requiring manual selection.
    """
    ports = scan_serial_ports()
    if not ports:
        return {
            "found": False,
            "connected": False,
            "message": "No serial ports detected. Please connect an Arduino via USB.",
            "board": None
        }

    # Find first port identified as Arduino, or first available serial device
    target_port = next((p for p in ports if p.is_arduino), ports[0])
    board_id = target_port.suggested_board_id or "arduino_uno"

    from backend.firmware.board_profiles import get_board_profile
    profile = get_board_profile(board_id)

    serial_mgr = get_serial_mgr()
    simulator = get_simulator()
    if simulator.running:
        simulator.stop()

    connect_result = serial_mgr.connect(port=target_port.device, baud_rate=115200, run_id=run_id)

    return {
        "found": True,
        "connected": connect_result.get("connected", False),
        "port": target_port.device,
        "board_id": board_id,
        "board_profile": profile.to_dict(),
        "description": target_port.description
    }


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
