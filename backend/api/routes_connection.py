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
    status["is_physical_hardware"] = serial_mgr.connected and not simulator.running
    return status


@router.post("/api/connection/handshake")
def trigger_handshake(timeout_sec: float = 2.0) -> Dict[str, Any]:
    """
    Sends an explicit $ARIS_HELLO# query to the connected physical target,
    confirming embedded runtime version, architecture, and board identity.
    """
    serial_mgr = get_serial_mgr()
    return serial_mgr.perform_handshake(timeout_sec=timeout_sec)


@router.post("/api/connection/auto-detect")
def auto_detect_and_connect(run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Automatically scans USB/COM ports using multi-source evidence (Arduino CLI,
    VID/PID matching, and USB descriptors). Establishes serial connection,
    performs runtime handshake, resolves dynamic BoardProfile, detects identity mismatches,
    and saves the resolved profile to the persistent database.
    """
    ports = scan_serial_ports()
    if not ports:
        return {
            "found": False,
            "connected": False,
            "message": "No serial ports detected. Please connect an Arduino via USB.",
            "board": None,
            "confidence": "UNKNOWN"
        }

    arduino_ports = [p for p in ports if p.is_arduino]
    target_port = arduino_ports[0] if arduino_ports else ports[0]
    board_id = target_port.suggested_board_id
    confidence = target_port.confidence

    from backend.firmware.board_profiles import BoardProfileResolver, get_board_profile, BoardProfile
    from backend.database.db_engine import DatabaseEngine

    db = DatabaseEngine()
    profile: Optional[BoardProfile] = None

    if target_port.fqbn:
        profile = BoardProfileResolver.resolve_from_toolchain(target_port.fqbn)
    if not profile and board_id:
        profile = get_board_profile(board_id)
    if not profile:
        profile = BoardProfileResolver.create_partially_resolved(
            board_id=board_id or f"device_{target_port.device.lower()}",
            display_name=target_port.display_name or target_port.description,
            description=target_port.description
        )

    serial_mgr = get_serial_mgr()
    simulator = get_simulator()
    if simulator.running:
        simulator.stop()

    connect_result = serial_mgr.connect(port=target_port.device, baud_rate=115200, run_id=run_id)

    # Perform active runtime handshake to confirm MCU/board identity
    handshake_result = serial_mgr.perform_handshake(timeout_sec=1.5)
    mismatch_detected = False
    mismatch_reason = None

    if handshake_result.get("handshake_success"):
        # Verify discovered profile against handshake frame
        is_match, reason = BoardProfileResolver.verify_identity_match(profile, handshake_result)
        if not is_match:
            mismatch_detected = True
            mismatch_reason = reason
            confidence = "MISMATCH"
            # Upgrade profile to match authoritative runtime target
            profile = BoardProfileResolver.resolve_from_handshake(handshake_result)
            profile.confidence = "MISMATCH"
            board_id = profile.board_id
        else:
            confidence = "CONFIRMED"
            profile = BoardProfileResolver.resolve_from_handshake(handshake_result)
            profile.confidence = "CONFIRMED"
            board_id = profile.board_id

    # Persist the resolved board profile into the database
    if profile:
        try:
            db.save_board(profile.to_record())
        except Exception as e:
            pass

    return {
        "found": True,
        "connected": connect_result.get("connected", False),
        "port": target_port.device,
        "board_id": board_id or "unknown",
        "display_name": profile.display_name if profile else target_port.display_name,
        "mcu": profile.mcu if profile else None,
        "architecture": profile.architecture if profile else None,
        "clock_hz": profile.clock_hz if profile else None,
        "flash_bytes": profile.flash_bytes if profile else None,
        "sram_bytes": profile.sram_bytes if profile else None,
        "fqbn": profile.fqbn if profile else target_port.fqbn,
        "confidence": confidence,
        "profile_source": profile.profile_source if profile else target_port.profile_source,
        "unavailable_properties": profile.unavailable_properties if profile else [],
        "board_profile": profile.to_dict() if profile else None,
        "description": target_port.description,
        "handshake": handshake_result,
        "identity_mismatch": mismatch_detected,
        "mismatch_reason": mismatch_reason,
        "mode": "PHYSICAL HARDWARE"
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
