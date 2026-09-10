"""
ARIS Dependency Injection and Service Singletons.
Provides shared global singletons for backend subsystems:
- DatabaseEngine
- TelemetryIngestor
- SerialManager
- SimulatedHardware
- FirmwareManager
- StaticAnalyzer
- BaselineEngine
- ExperimentEngine
- BuildFlasher
"""

import os
from backend.database.db_engine import DatabaseEngine
from backend.telemetry.telemetry_ingestor import TelemetryIngestor
from backend.serial.serial_manager import SerialManager
from backend.simulator.simulated_hardware import SimulatedHardware
from backend.firmware.firmware_manager import FirmwareManager
from backend.firmware.build_flasher import BuildFlasher
from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.analysis.baseline_engine import BaselineEngine
from backend.experiments.experiment_engine import ExperimentEngine

# Global singleton storage
_db: DatabaseEngine = None
_ingestor: TelemetryIngestor = None
_serial_mgr: SerialManager = None
_simulator: SimulatedHardware = None
_firmware_mgr: FirmwareManager = None
_build_flasher: BuildFlasher = None
_static_analyzer: StaticAnalyzer = None
_baseline_engine: BaselineEngine = None
_experiment_engine: ExperimentEngine = None


def get_db() -> DatabaseEngine:
    global _db
    if _db is None:
        db_path = os.environ.get("ARIS_DB_PATH", "aris.db")
        _db = DatabaseEngine(db_path)
        # Pre-seed canonical boards if not already present
        for profile in CANONICAL_BOARD_PROFILES.values():
            _db.save_board(profile.to_record())
    return _db


def get_ingestor() -> TelemetryIngestor:
    global _ingestor
    if _ingestor is None:
        _ingestor = TelemetryIngestor(get_db())
        from backend.api.websocket_server import ws_manager
        _ingestor.subscribe(ws_manager.dispatch_sample)
    return _ingestor


def get_serial_mgr() -> SerialManager:
    global _serial_mgr
    if _serial_mgr is None:
        _serial_mgr = SerialManager(get_ingestor())
    return _serial_mgr


def get_simulator() -> SimulatedHardware:
    global _simulator
    if _simulator is None:
        _simulator = SimulatedHardware(get_ingestor(), "arduino_uno")
    return _simulator


def get_firmware_mgr() -> FirmwareManager:
    return FirmwareManager(get_db())


def get_build_flasher() -> BuildFlasher:
    global _build_flasher
    if _build_flasher is None:
        _build_flasher = BuildFlasher()
    return _build_flasher


def get_static_analyzer() -> StaticAnalyzer:
    return StaticAnalyzer()


def get_baseline_engine() -> BaselineEngine:
    return BaselineEngine(get_db())


def get_experiment_engine() -> ExperimentEngine:
    return ExperimentEngine(get_db(), get_baseline_engine())
