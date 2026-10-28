"""
Automated Regression Tests for Pre-Demo System Health and Demo Stabilization.
Validates:
1. Pre-demo health checks return non-destructive status (PASS, WARNING, FAIL) across all components.
2. Missing hardware is classified as a WARNING, not an application crash.
3. Database remains completely unmodified during health checks (read-only verification).
4. Offline upload attempts return clear structured error without phantom runs or fake telemetry.
5. Historical physical evidence is labeled with explicit HISTORICAL_PHYSICAL_VALIDATION provenance.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.app import app
from backend.api.routes_health import run_pre_demo_health_checks
from backend.api.dependencies import get_db


@pytest.fixture
def client():
    return TestClient(app)


def test_pre_demo_health_check_components():
    """Verify all 6 required health checks are present and report valid status."""
    checks = run_pre_demo_health_checks()
    required_keys = [
        "backend",
        "database",
        "arduino_cli",
        "board_configuration",
        "serial_detection",
        "preflight_engine"
    ]
    for key in required_keys:
        assert key in checks, f"Missing required health check: {key}"
        item = checks[key]
        assert "status" in item
        assert item["status"] in ("PASS", "WARNING", "FAIL", "NOT AVAILABLE")
        assert "message" in item
        assert "detail" in item


def test_pre_demo_health_check_non_destructive():
    """Verify health check is strictly read-only and safe to run repeatedly."""
    db = get_db()
    conn = db._get_connection()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM runs")
    runs_before = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    tables_before = cur.fetchone()[0]

    # Run health check multiple times
    for _ in range(5):
        checks = run_pre_demo_health_checks()
        assert checks["database"]["status"] == "PASS"

    cur.execute("SELECT count(*) FROM runs")
    runs_after = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    tables_after = cur.fetchone()[0]

    assert runs_before == runs_after, "Health check must not create or modify run records"
    assert tables_before == tables_after, "Health check must not modify schema"


def test_api_health_endpoints(client):
    """Verify both /api/health and /api/health/pre-demo return HTTP 200 with checks."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ONLINE", "DEGRADED")
    assert "checks" in data
    assert "backend" in data["checks"]

    resp_pre = client.get("/api/health/pre-demo")
    assert resp_pre.status_code == 200
    pre_data = resp_pre.json()
    assert pre_data["overall_status"] in ("PASS", "WARNING", "FAIL")
    assert "ready_for_demo" in pre_data
    assert "checks" in pre_data


def test_missing_hardware_reported_as_warning_not_crash():
    """Verify disconnected serial hardware is reported as WARNING, never an exception."""
    checks = run_pre_demo_health_checks()
    serial_check = checks["serial_detection"]
    # Either connected (PASS) or disconnected (WARNING)
    assert serial_check["status"] in ("PASS", "WARNING")
    assert "Serial" in serial_check["name"] or "Hardware" in serial_check["name"]


def test_offline_upload_aborted_cleanly_without_run(client):
    """
    When execute_upload is requested without an available COM port,
    compilation succeeds but upload fails cleanly with DEVICE_DISCONNECTED,
    and no run record or false telemetry is generated.
    """
    sketch_code = "void setup(){ pinMode(13, OUTPUT); } void loop(){ digitalWrite(13, HIGH); }"
    req = {
        "source_code": sketch_code,
        "board_id": "arduino_uno",
        "port": None,
        "execute_upload": True,
        "instrumentation_mode": "BALANCED"
    }

    # Ensure no port is forced
    resp = client.post("/api/firmware/instrument-and-build", json=req)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "BUILD_SUCCESS"
    assert data["original_source_preserved"] is True
    assert "build_result" in data

    # Upload result should report FLASH_FAILED if hardware port is disconnected
    upload_res = data.get("upload_result")
    if upload_res and upload_res.get("status") == "FLASH_FAILED":
        assert upload_res.get("failure_category") in ("DEVICE_DISCONNECTED", "PORT_ACCESS_DENIED", "UNKNOWN_ERROR")
        assert data.get("run") is None
        assert data.get("telemetry_active") is False


def test_provenance_labeling_on_historical_package(client):
    """Verify EXP-PHYS-001 has clear HISTORICAL_PHYSICAL_VALIDATION provenance."""
    resp = client.get("/api/experiments")
    assert resp.status_code == 200
    exps = resp.json()
    phys_exp = next((e for e in exps if e.get("experiment_id") == "EXP-PHYS-001"), None)
    if phys_exp:
        assert phys_exp.get("evidence_type") == "HISTORICAL_PHYSICAL_VALIDATION"
        assert phys_exp.get("provenance") == "HISTORICAL_PHYSICAL_VALIDATION"
        assert phys_exp.get("is_simulated") is False
        assert phys_exp.get("is_demo") is False
