"""
ARIS Pytest Fixtures and Shared Configuration.
Provides:
- Isolated temporary SQLite databases
- Pre-configured TelemetryIngestor
- TestClient for FastAPI endpoints
- Fixture generators for telemetry and sketches
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient

from backend.database.db_engine import DatabaseEngine
from backend.telemetry.telemetry_ingestor import TelemetryIngestor
from backend.firmware.board_profiles import CANONICAL_BOARD_PROFILES
from backend.analysis.static_analyzer import StaticAnalyzer
from backend.analysis.baseline_engine import BaselineEngine
from backend.experiments.experiment_engine import ExperimentEngine
from backend.simulator.simulated_hardware import SimulatedHardware
from backend.serial.serial_manager import SerialManager
from backend.api.app import app
import backend.api.dependencies as deps


@pytest.fixture
def temp_db():
    """Provides a fresh isolated database for each test."""
    temp_dir = tempfile.mkdtemp()
    db_file = os.path.join(temp_dir, "test_aris.db")
    engine = DatabaseEngine(db_file)
    for p in CANONICAL_BOARD_PROFILES.values():
        engine.save_board(p.to_record())
    yield engine
    # Stop background tasks before cleanup
    if deps._simulator:
        deps._simulator.stop()
    if deps._serial_mgr:
        deps._serial_mgr.disconnect()
    # Cleanup temp file
    try:
        if os.path.exists(db_file):
            os.remove(db_file)
    except Exception:
        pass


@pytest.fixture
def ingestor(temp_db):
    """Provides a TelemetryIngestor attached to the isolated database."""
    return TelemetryIngestor(temp_db)


@pytest.fixture
def test_client(temp_db):
    """Provides a FastAPI TestClient with mocked dependencies."""
    orig_db = deps._db
    orig_ingestor = deps._ingestor
    orig_sim = deps._simulator
    orig_serial = deps._serial_mgr

    deps._db = temp_db
    deps._ingestor = TelemetryIngestor(temp_db)
    from backend.api.websocket_server import ws_manager
    deps._ingestor.subscribe(ws_manager.dispatch_sample)
    deps._simulator = SimulatedHardware(deps._ingestor, "arduino_uno")
    deps._serial_mgr = SerialManager(deps._ingestor)

    with TestClient(app) as client:
        yield client

    deps._db = orig_db
    deps._ingestor = orig_ingestor
    deps._simulator = orig_sim
    deps._serial_mgr = orig_serial
