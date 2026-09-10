"""
Unit & Integration tests for all ARIS REST API Endpoints.
Verifies exact endpoint paths, HTTP verbs, payload handling, and canonical error codes.
"""

import pytest
import time


def test_health_check_endpoint(test_client):
    """GET /api/health"""
    res = test_client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert "arduino_uno" in data["supported_boards"]


def test_boards_endpoints(test_client):
    """GET /api/boards and GET /api/boards/{board_id}"""
    res = test_client.get("/api/boards")
    assert res.status_code == 200
    boards = res.json()
    assert len(boards) == 3

    # Detail
    res_uno = test_client.get("/api/boards/arduino_uno")
    assert res_uno.status_code == 200
    assert res_uno.json()["mcu"] == "atmega328p"

    # Unsupported board returns ARIS_UNSUPPORTED_BOARD
    res_bad = test_client.get("/api/boards/unknown_board")
    assert res_bad.status_code == 404
    assert res_bad.json()["error_code"] == "ARIS_UNSUPPORTED_BOARD"


def test_connection_endpoints(test_client):
    """GET /api/connection/status, POST /api/connection/connect, POST /api/connection/disconnect"""
    res = test_client.get("/api/connection/status")
    assert res.status_code == 200
    assert "connected" in res.json()

    # Disconnect
    res_dc = test_client.post("/api/connection/disconnect")
    assert res_dc.status_code == 200
    assert res_dc.json()["connected"] is False

    # Connect to invalid port returns ARIS_SERIAL_DISCONNECTED
    res_conn = test_client.post("/api/connection/connect", json={"port": "INVALID_PORT_XYZ", "baud_rate": 115200})
    assert res_conn.status_code == 400
    assert res_conn.json()["error_code"] == "ARIS_SERIAL_DISCONNECTED"


def test_firmware_lifecycle_endpoints(test_client):
    """POST /api/firmware/upload, GET /api/firmware, GET /api/firmware/{firmware_id}"""
    payload = {
        "name": "BlinkTest",
        "source_code": "void setup() { pinMode(13, OUTPUT); } void loop() { digitalWrite(13, HIGH); delay(100); }"
    }
    res = test_client.post("/api/firmware/upload", json=payload)
    assert res.status_code == 200
    fw = res.json()
    fw_id = fw["firmware_id"]

    # List
    res_list = test_client.get("/api/firmware")
    assert res_list.status_code == 200
    assert any(f["firmware_id"] == fw_id for f in res_list.json())

    # Get Detail
    res_detail = test_client.get(f"/api/firmware/{fw_id}")
    assert res_detail.status_code == 200
    assert res_detail.json()["name"] == "BlinkTest"


def test_runs_lifecycle_endpoints(test_client):
    """POST /api/runs, GET /api/runs, GET /api/runs/{run_id}, POST /api/runs/{run_id}/start, stop"""
    # 1. Create run
    res = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True})
    assert res.status_code == 200
    run = res.json()
    run_id = run["run_id"]
    assert run["status"] == "CREATED"

    # 2. Get Detail
    res_get = test_client.get(f"/api/runs/{run_id}")
    assert res_get.status_code == 200
    assert res_get.json()["run_id"] == run_id

    # 3. Start Run (Activates simulator)
    res_start = test_client.post(f"/api/runs/{run_id}/start")
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "RUNNING"

    # 4. Stop Run
    res_stop = test_client.post(f"/api/runs/{run_id}/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "COMPLETED"


def test_telemetry_endpoint(test_client):
    """GET /api/runs/{run_id}/telemetry"""
    # Create and start run briefly
    res = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True})
    run_id = res.json()["run_id"]
    test_client.post(f"/api/runs/{run_id}/start")

    # Fetch telemetry
    res_t = test_client.get(f"/api/runs/{run_id}/telemetry")
    assert res_t.status_code == 200
    assert isinstance(res_t.json(), list)

    test_client.post(f"/api/runs/{run_id}/stop")


def test_analysis_and_findings_endpoints(test_client):
    """GET /api/runs/{run_id}/analysis and GET /api/runs/{run_id}/findings"""
    # Upload sketch with delay
    fw_res = test_client.post("/api/firmware/upload", json={
        "name": "DelaySketch",
        "source_code": "void setup() {} void loop() { delay(100); }"
    })
    fw_id = fw_res.json()["firmware_id"]

    # Create run with this firmware
    run_res = test_client.post("/api/runs", json={
        "board_id": "arduino_uno",
        "firmware_id": fw_id
    })
    run_id = run_res.json()["run_id"]

    # Request Analysis
    res_a = test_client.get(f"/api/runs/{run_id}/analysis")
    assert res_a.status_code == 200
    analysis = res_a.json()
    assert "static_metrics" in analysis
    assert "findings" in analysis
    assert analysis["findings_count"] >= 1

    # Request Findings
    res_f = test_client.get(f"/api/runs/{run_id}/findings")
    assert res_f.status_code == 200
    findings = res_f.json()
    assert any(f["rule_id"] == "ARIS-001" for f in findings)


def test_optimization_approval_endpoints(test_client):
    """POST /api/ai/generate-candidate, GET /api/runs/{run_id}/optimizations, POST /approve, reject"""
    # Create Run
    run_res = test_client.post("/api/runs", json={"board_id": "arduino_uno"})
    run_id = run_res.json()["run_id"]

    # Generate candidate
    cand_res = test_client.post("/api/ai/generate-candidate", json={
        "finding": {"finding_id": "FIND-101", "rule_id": "ARIS-001", "evidence": {"duration": 50}},
        "source_code": "delay(50);",
        "board_id": "arduino_uno",
        "run_id": run_id
    })
    assert cand_res.status_code == 200
    opt = cand_res.json()
    opt_id = opt["optimization_id"]

    # List optimizations
    res_list = test_client.get(f"/api/runs/{run_id}/optimizations")
    assert res_list.status_code == 200
    assert any(o["optimization_id"] == opt_id for o in res_list.json())

    # Approve
    res_app = test_client.post(f"/api/optimizations/{opt_id}/approve")
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"

    # Reject
    res_rej = test_client.post(f"/api/optimizations/{opt_id}/reject")
    assert res_rej.status_code == 200
    assert res_rej.json()["status"] == "REJECTED"


def test_experiments_and_validation_endpoints(test_client):
    """POST /api/experiments, GET /api/experiments, POST /validate, GET /result"""
    # 1. Setup baseline run
    r1 = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True}).json()
    base_id = r1["run_id"]
    # Seed samples via simulator
    test_client.post(f"/api/runs/{base_id}/start")
    time.sleep(0.35)
    test_client.post(f"/api/runs/{base_id}/stop")

    # 2. Setup candidate run
    r2 = test_client.post("/api/runs", json={"board_id": "arduino_uno", "is_simulated": True}).json()
    cand_id = r2["run_id"]
    test_client.post(f"/api/runs/{cand_id}/start")
    time.sleep(0.35)
    test_client.post(f"/api/runs/{cand_id}/stop")

    # 3. Setup optimization
    opt = test_client.post("/api/ai/generate-candidate", json={
        "finding": {"finding_id": "FIND-200", "rule_id": "ARIS-001"},
        "source_code": "delay(20);",
        "board_id": "arduino_uno",
        "run_id": base_id
    }).json()
    opt_id = opt["optimization_id"]

    # 4. Create experiment
    exp = test_client.post("/api/experiments", json={
        "title": "API Experiment Test",
        "board_id": "arduino_uno",
        "baseline_run_id": base_id,
        "optimization_id": opt_id
    }).json()
    exp_id = exp["experiment_id"]

    # 5. Validate experiment
    val_res = test_client.post(f"/api/experiments/{exp_id}/validate", json={"candidate_run_id": cand_id})
    assert val_res.status_code == 200
    val_report = val_res.json()
    assert "validation_status" in val_report
    assert "percentage_change" in val_report

    # 6. Retrieve validation result
    res_val = test_client.get(f"/api/experiments/{exp_id}/result")
    assert res_val.status_code == 200
    assert res_val.json()["validation_status"] == val_report["validation_status"]
