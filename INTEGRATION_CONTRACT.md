# ARIS Engineering Integration Contract (v1.0)

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Document Version:** 1.0.0  
**Status:** ACTIVE & BINDING

---

## 1. Engineering Division of Responsibilities

| Role | Domain Owner | Primary Codebase | Core Deliverables |
| :--- | :--- | :--- | :--- |
| **Engineer 1** | Embedded Systems | `embedded/` | Embedded probes, ISR watermarking, AVR serial framer (`$ARIS1...#`), C native runtime. |
| **Engineer 2** | Backend & Analytics | `backend/` | Serial discovery, telemetry ingestion, static firmware analysis, correlation engine, baseline engine, experiment management, validation, SQLite database, REST API, WebSockets, hardware simulator. |
| **Engineer 3** | AI & Frontend | `aris_desktop/`, AI | AI optimization advisor, prompt templates, candidate generation, Electron desktop GUI, interactive board visualizer. |

---

## 2. Invariant Subsystem Contracts

### 2.1 Canonical Supported Boards & MCUs
- `arduino_uno`: ATmega328P, AVR 8-bit, 16 MHz, 32KB Flash, 2KB SRAM, 1KB EEPROM.
- `arduino_nano`: ATmega328P, AVR 8-bit, 16 MHz, 32KB Flash, 2KB SRAM, 1KB EEPROM.
- `arduino_mega`: ATmega2560, AVR 8-bit, 16 MHz, 256KB Flash, 8KB SRAM, 4KB EEPROM.

### 2.2 The 20 Canonical Metric Identifiers (Never Rename or Alias)
`cpu_load`, `loop_time`, `loop_frequency`, `loop_jitter`, `sram_used`, `sram_free`, `stack_used`, `stack_high_water_mark`, `interrupt_count`, `interrupt_rate`, `gpio_activity`, `adc_activity`, `uart_activity`, `spi_activity`, `i2c_activity`, `timer_activity`, `reset_event`, `watchdog_event`, `runtime_fault`, `instrumentation_overhead`.

### 2.3 The 4 Metric Veracity Classifications
- `MEASURED`: Physical hardware registers, timer differences, memory scans.
- `ESTIMATED`: Sampled duty-cycle approximations. **CRITICAL INVARIANT:** `cpu_load` on AVR microcontrollers must **ALWAYS** be classified as `ESTIMATED`.
- `DERIVED`: Arithmetic calculations combining measurements.
- `PREDICTED`: Static model forecasts.

### 2.4 Canonical Telemetry JSON Schema
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

### 2.5 Canonical Error Schema
```json
{
    "error_code": "ARIS_SERIAL_DISCONNECTED",
    "message": "Arduino serial connection was lost.",
    "details": {},
    "recoverable": true
}
```

### 2.6 Canonical Optimization Candidate Schema (Engineer 3 Contract)
```json
{
    "optimization_id": "OPT-000001",
    "finding_id": "ARIS-001",
    "title": "Eliminate blocking delay in main loop",
    "problem": "delay(100) blocks loop scheduling and elevates jitter",
    "source_location": {"file": "main.ino", "line": 42},
    "before_code": "delay(100);",
    "after_code": "millis() timer state machine",
    "reason": "Yields CPU cycles for periodic tasks and lowers jitter",
    "hardware_consideration": "Saves 100ms active wait cycles per loop",
    "expected_effect": {"loop_time_reduction_ms": 99.0},
    "risk": "LOW",
    "confidence": 0.89,
    "validation_required": true,
    "status": "PROPOSED"
}
```

---

## 3. Communication Protocols

1. **Physical Microcontroller to Backend:**
   Transmitted over serial UART at 115200 baud via Fast Micro-Framing:
   `$ARIS1,<run_id>,<board_id>,<mcu>,<timestamp_ms>,<seq>,<cpu>,<loop_t>,...#`
2. **Backend to Frontend WebSocket:**
   Streamed over WebSocket at `/ws/telemetry/{run_id}` as real-time canonical JSON objects.
3. **Frontend to Backend REST API:**
   Standard HTTP requests hitting `/api/...` endpoints.
