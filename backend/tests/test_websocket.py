"""
Unit tests for ARIS WebSocket Real-Time Telemetry Streaming.
Verifies:
- Connection to canonical /ws/telemetry/{run_id}
- Connection to catch-all /ws/telemetry
- Live streaming of TelemetrySample packets to subscribers
"""

import pytest
import json
import time


def test_websocket_telemetry_run_stream(test_client):
    """Verify WebSocket client connects to /ws/telemetry/{run_id} and receives frames."""
    # 1. Create run first
    run_res = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True})
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]

    with test_client.websocket_connect(f"/ws/telemetry/{run_id}") as ws:
        # Start simulated run for this run_id
        start_res = test_client.post(f"/api/runs/{run_id}/start")
        assert start_res.status_code == 200

        # Wait briefly for frames
        time.sleep(0.3)

        # Receive frame over websocket
        data = ws.receive_text()
        frame = json.loads(data)
        assert frame["protocol_version"] == "1.0"
        assert frame["run_id"] == run_id
        assert "metric" in frame
        assert "value" in frame

        test_client.post(f"/api/runs/{run_id}/stop")


def test_websocket_telemetry_all_catchall(test_client):
    """Verify WebSocket client connects to catch-all /ws/telemetry."""
    run_res = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True})
    assert run_res.status_code == 200
    run_id = run_res.json()["run_id"]

    with test_client.websocket_connect("/ws/telemetry") as ws:
        test_client.post(f"/api/runs/{run_id}/start")
        time.sleep(0.3)

        data = ws.receive_text()
        frame = json.loads(data)
        assert frame["protocol_version"] == "1.0"
        assert "metric" in frame

        test_client.post(f"/api/runs/{run_id}/stop")
