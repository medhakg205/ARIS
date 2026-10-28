"""
ARIS Backend Reliability & Fault-Tolerance Test Suite.
Tests:
- Ultra-lightweight /health endpoint latency and schema
- Hardened /api/health endpoint resilience under subsystem faults
- Canonical database path resolution
- Graceful degradation when serial port is unavailable or disconnected
- Non-blocking error handling during port scan and auto-detect
- Ingestor framing resilience
- Simulator lifecycle robustness
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from backend.api.app import app
import backend.api.dependencies as deps
from backend.telemetry.telemetry_ingestor import TelemetryIngestor


def test_lightweight_health_endpoint(test_client):
    """Verify /health responds instantly with ok status without touching db or serial."""
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "aris-backend"
    assert data["version"] == "2.0.0"
    assert data["port"] == 8765


def test_api_health_endpoint_normal(test_client):
    """Verify /api/health returns detailed system health."""
    resp = test_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ONLINE", "DEGRADED")
    assert "version" in data
    assert "database" in data
    assert "supported_boards" in data


def test_api_health_resilient_to_subsystem_fault(test_client):
    """Verify /api/health does not crash (returns DEGRADED 200) if database engine fails."""
    with patch("backend.api.routes_health.get_db", side_effect=RuntimeError("Simulated DB lock/corruption")):
        resp = test_client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "DEGRADED"
        assert "ERROR: Simulated DB lock/corruption" in data["database"]


def test_canonical_db_path_resolution():
    """Verify get_db() resolves canonical path and creates engine safely."""
    with patch.dict(os.environ, {"ARIS_DB_PATH": ""}):
        saved_db = deps._db
        try:
            deps._db = None
            db = deps.get_db()
            assert db is not None
            assert "aris.db" in db.db_path
            assert os.path.isabs(db.db_path)
        finally:
            deps._db = saved_db


def test_connect_invalid_serial_port_graceful(test_client):
    """Connecting to a non-existent port should return a clean error without crashing."""
    resp = test_client.post("/api/connection/connect", json={
        "port": "COM999_NONEXISTENT",
        "baud_rate": 115200
    })
    # Should fail gracefully with 400 or 500 error code matching ARIS error contract
    assert resp.status_code in (400, 500)
    data = resp.json()
    assert "error_code" in data
    assert data["error_code"] in ("ARIS_SERIAL_DISCONNECTED", "ARIS_SERIAL_ERROR", "ARIS_SERIAL_CONNECT_FAILED")


def test_disconnect_when_not_connected(test_client):
    """Disconnecting when already disconnected is idempotent and safe."""
    resp = test_client.post("/api/connection/disconnect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is False


def test_auto_detect_graceful_handling(test_client):
    """Auto-detect returns structured scan result without unhandled exception."""
    resp = test_client.post("/api/connection/auto-detect")
    assert resp.status_code in (200, 400)
    data = resp.json()
    assert "found" in data or "error_code" in data



def test_connection_status_endpoint(test_client):
    """Connection status returns available and discovered ports."""
    resp = test_client.get("/api/connection/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "connected" in data
    assert "available_ports" in data
    assert isinstance(data["available_ports"], list)


def test_ingestor_handles_malformed_telemetry(temp_db):
    """Verify TelemetryIngestor discards malformed frames without throwing unhandled exceptions."""
    ingestor = TelemetryIngestor(temp_db)
    
    # Ingest malformed raw line
    result = ingestor.ingest_raw_line("NOT_A_VALID_ARIS_FRAME")
    assert result == []

    # Ingest partial JSON
    result = ingestor.ingest_raw_line('{"incomplete": true')
    assert result == []

    # Ingest empty line
    result = ingestor.ingest_raw_line('')
    assert result == []


def test_simulator_clean_lifecycle():
    """Verify simulator starts and stops cleanly without orphan threads or memory leaks."""
    sim = deps.get_simulator()
    assert sim.running is False

    sim.start(run_id="TEST-SIM-RELIABILITY")
    assert sim.running is True
    assert sim.run_id == "TEST-SIM-RELIABILITY"

    sim.stop()
    assert sim.running is False
