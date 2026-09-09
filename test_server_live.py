import sys
import os
import time
import requests
import subprocess

# Start server as subprocess
server_process = subprocess.Popen(
    ["python", r"C:\Users\aksha\.gemini\antigravity\scratch\aris-studio\aris_core\api_server.py"],
    cwd=r"C:\Users\aksha\.gemini\antigravity\scratch\aris-studio"
)

try:
    # Wait for server to start
    time.sleep(2.5)
    
    # 1. Health check
    res = requests.get("http://127.0.0.1:8765/api/health")
    print("Health Check:", res.status_code, res.json())
    assert res.status_code == 200
    
    # 2. Boards list
    res_b = requests.get("http://127.0.0.1:8765/api/boards")
    print("Boards:", len(res_b.json()))
    assert len(res_b.json()) >= 6
    
    # 3. Analyze request
    sample = "void setup(){ pinMode(13, OUTPUT); } void loop(){ digitalWrite(13, HIGH); delay(20); }"
    res_a = requests.post("http://127.0.0.1:8765/api/analyze", json={"source_code": sample, "board_id": "arduino_uno"})
    print("Analyze Antipatterns:", len(res_a.json()["antipatterns"]))
    assert len(res_a.json()["antipatterns"]) >= 2
    
    # 4. Optimize request
    res_o = requests.post("http://127.0.0.1:8765/api/optimize", json={"source_code": sample, "board_id": "arduino_uno"})
    print("Optimize Transforms:", res_o.json()["applied_transforms"])
    assert len(res_o.json()["applied_transforms"]) >= 2

    # 5. Patent report request
    res_p = requests.post("http://127.0.0.1:8765/api/patent-report", json={"source_code": sample, "board_id": "arduino_uno"})
    print("Patent Report length:", len(res_p.json()["markdown_report"]))
    assert "PATENT DISCLOSURE" in res_p.json()["markdown_report"]

    print("\n[OK] API SERVER VERIFICATION TEST PASSED WITH 100% SUCCESS!")

finally:
    server_process.terminate()
