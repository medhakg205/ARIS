# ARIS REST & WebSocket API Specification (v1.0)

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Subsystem Owner:** Engineer 2 (Backend & Analytical Core)

---

## 1. Overview
The ARIS Backend serves as the analytical, telemetry ingestion, and closed-loop optimization core for real Arduino-class microcontrollers. It provides a RESTful API under `/api` and real-time WebSocket streams for host-side telemetry visualization and AI closed-loop experimentation.

- **Base URL:** `http://127.0.0.1:8765`
- **REST Base Path:** `/api`
- **Real-Time WebSocket:** `/ws/telemetry/{run_id}`
- **Protocol Version:** `1.0`

---

## 2. Canonical Error Schema
All error responses from any API endpoint adhere strictly to the following JSON structure:

```json
{
    "error_code": "ARIS_SERIAL_DISCONNECTED",
    "message": "Arduino serial connection was lost.",
    "details": {},
    "recoverable": true
}
```

### Canonical Error Codes
- `ARIS_SERIAL_DISCONNECTED`: Serial port lost or disconnected during I/O.
- `ARIS_BOARD_NOT_FOUND`: Target microcontroller board not located on serial bus.
- `ARIS_UNSUPPORTED_BOARD`: Unrecognized or unsupported board ID.
- `ARIS_INVALID_FIRMWARE`: Missing, corrupt, or unparseable firmware artifact.
- `ARIS_BUILD_FAILED`: Compiler error during sketch build.
- `ARIS_FLASH_FAILED`: Hardware programmer communication failure during upload.
- `ARIS_TELEMETRY_INVALID`: Malformed telemetry packet or invalid schema/metric name.
- `ARIS_AI_UNAVAILABLE`: Optimization AI agent or model endpoint unreachable.
- `ARIS_OPTIMIZATION_INVALID`: Candidate transform failed schema or hardware validation.
- `ARIS_VALIDATION_FAILED`: Closed-loop empirical validation failure or regression.
- `ARIS_BACKEND_UNAVAILABLE`: Internal server exception or missing host tools.

---

## 3. Endpoints

### 3.1 Health
- `GET /api/health`
  - **Description:** Returns server readiness, database status, and supported boards.
  - **Response `200 OK`:**
    ```json
    {
      "status": "ONLINE",
      "version": "1.0.0",
      "subsystem": "ARIS Backend + Analysis Core",
      "database": "CONNECTED",
      "serial_connected": false,
      "serial_port": null,
      "simulator_running": false,
      "mode": "OPERATIONAL",
      "supported_boards": ["arduino_uno", "arduino_nano", "arduino_mega"]
    }
    ```

### 3.2 Boards
- `GET /api/boards`
  - **Description:** Returns array of all canonical board profiles.
- `GET /api/boards/{board_id}`
  - **Description:** Returns full hardware specification, register mapping, and memory limits for `board_id` (`arduino_uno`, `arduino_nano`, `arduino_mega`).

### 3.3 Hardware Serial Connection
- `GET /api/connection/status`
  - **Description:** Returns physical connection status and list of dynamically discovered serial ports.
- `POST /api/connection/connect`
  - **Body:** `{"port": "COM3", "baud_rate": 115200, "run_id": "ARIS-000001"}`
  - **Description:** Connects to physical microcontroller serial port.
- `POST /api/connection/disconnect`
  - **Description:** Safely disconnects the active serial port.

### 3.4 Firmware Management
- `POST /api/firmware/upload`
  - **Body:**
    ```json
    {
      "name": "BlinkTest",
      "source_code": "void setup() {...} void loop() {...}",
      "hex_content": ":10000000...",
      "elf_path": "/path/to/firmware.elf",
      "map_content": "Memory Configuration..."
    }
    ```
- `GET /api/firmware`
  - **Description:** Lists all registered firmware records.
- `GET /api/firmware/{firmware_id}`
  - **Description:** Returns detailed firmware record and normalized memory section representation.

### 3.5 Execution Runs
- `POST /api/runs`
  - **Body:** `{"board_id": "arduino_uno", "firmware_id": "FW-001", "instrumentation_mode": "BALANCED", "is_simulated": false, "is_demo": false}`
  - **Status Transitions:** `CREATED` -> `BUILDING` -> `FLASHING` -> `RUNNING` -> `COLLECTING` -> `COMPLETED` / `FAILED` / `ROLLED_BACK`.
- `GET /api/runs`
  - **Description:** Lists all execution runs.
- `GET /api/runs/{run_id}`
  - **Description:** Returns run status, board association, timestamps, and baseline references.
- `POST /api/runs/{run_id}/start`
  - **Description:** Activates data collection for `run_id`.
- `POST /api/runs/{run_id}/stop`
  - **Description:** Stops run and triggers automated baseline generation.

### 3.6 Telemetry
- `GET /api/runs/{run_id}/telemetry`
  - **Query Params:** `limit` (default 1000), `metric` (optional canonical metric filter)
  - **Description:** Returns array of validated `TelemetrySample` objects.

### 3.7 Static & Correlated Analysis
- `GET /api/runs/{run_id}/analysis`
  - **Description:** Returns consolidated report fusing static metrics, measured baseline statistics, and runtime-static correlations.
- `GET /api/runs/{run_id}/findings`
  - **Description:** Returns array of correlated `Finding` objects adhering to the Finding Schema.

### 3.8 Optimization Candidates
- `GET /api/runs/{run_id}/optimizations`
  - **Description:** Returns optimization candidates proposed for `run_id`.
- `POST /api/optimizations/{optimization_id}/approve`
  - **Description:** Transitions candidate status to `APPROVED`.
- `POST /api/optimizations/{optimization_id}/reject`
  - **Description:** Transitions candidate status to `REJECTED`.

### 3.9 Experiments
- `POST /api/experiments`
  - **Body:**
    ```json
    {
      "title": "Eliminate Delay in Loop",
      "board_id": "arduino_uno",
      "baseline_run_id": "ARIS-BASE-001",
      "optimization_id": "OPT-001"
    }
    ```
- `GET /api/experiments`
  - **Description:** Lists all experiments.
- `GET /api/experiments/{experiment_id}`
  - **Description:** Returns experiment status and links.

### 3.10 Validation
- `POST /api/experiments/{experiment_id}/validate`
  - **Body:** `{"candidate_run_id": "ARIS-CAND-001"}`
  - **Description:** Executes empirical comparison of the 8 canonical validation metrics and returns the `ValidationReport`.
- `GET /api/experiments/{experiment_id}/result`
  - **Description:** Returns stored validation metrics, deltas, and validation status (`VALIDATED`, `REGRESSION`, etc.).

### 3.11 AI Subsystem (Contract for Engineer 3)
- `POST /api/ai/analyze`
  - **Body:** `{"run_id": "...", "source_code": "...", "board_id": "arduino_uno"}`
  - **Description:** Assembles and packages `AIContextInput` for Engineer 3's LLM optimizer.
- `POST /api/ai/generate-candidate`
  - **Body:** `{"finding": {...}, "source_code": "...", "board_id": "arduino_uno", "run_id": "..."}`
  - **Description:** Validates and stores `OptimizationCandidate`.

---

## 4. Real-Time Telemetry WebSocket

- **Path:** `/ws/telemetry/{run_id}`
- **Fallback Path:** `/ws/telemetry`

### Packet Frame Schema
Each frame pushed across the WebSocket is a JSON object conforming to the ARIS Telemetry Protocol v1.0:

```json
{
  "protocol_version": "1.0",
  "run_id": "ARIS-000001",
  "board_id": "arduino_uno",
  "mcu": "atmega328p",
  "timestamp_ms": 123456,
  "sequence": 42,
  "metric": "loop_time",
  "value": 4.21,
  "unit": "ms",
  "classification": "MEASURED",
  "confidence": 1.0
}
```
