# ARIS Engineering Integration Contract (v2.0)

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Document Version:** 2.0.0  
**Status:** ACTIVE & BINDING  

---

## 1. Engineering Division of Responsibilities

| Role | Domain Owner | Primary Codebase | Core Deliverables |
| :--- | :--- | :--- | :--- |
| **Engineer 1** | Embedded Systems | `embedded/` | Embedded probes, ISR watermarking, AVR serial framer (`$ARIS1...#`), handshake packets (`$ARIS_ACK...#`, `$ARIS_BOOT...#`), C native runtime. |
| **Engineer 2** | Backend & Analytics | `backend/` | Serial discovery with multi-source confidence levels, real `arduino-cli` compilation/flashing (`build_flasher.py`), telemetry ingestion provenance, static firmware analysis, correlation engine, baseline engine, experiment management, validation, rollback endpoints, SQLite database, REST API, WebSockets. |
| **Engineer 3** | AI & Frontend | `aris_desktop/`, AI | Multi-objective optimization advisor (`latency`, `sram`, `flash`, `interrupt_risk`), prompt templates, candidate generation, desktop GUI, interactive board visualizer, closed-loop experiment workbench. |

---

## 2. Invariant Subsystem Contracts

### 2.1 Canonical Supported Boards & Architectures
- **`arduino_uno`**: Microchip ATmega328P, AVR 8-bit RISC, 16 MHz, 32KB Flash, 2KB SRAM, 1KB EEPROM. FQBN: `arduino:avr:uno`. Supported: `True`.
- **`arduino_nano`**: Microchip ATmega328P, AVR 8-bit RISC, 16 MHz, 32KB Flash, 2KB SRAM, 1KB EEPROM. FQBN: `arduino:avr:nano`. Supported: `True`.
- **`arduino_mega`**: Microchip ATmega2560, AVR 8-bit RISC, 16 MHz, 256KB Flash, 8KB SRAM, 4KB EEPROM. FQBN: `arduino:avr:mega`. Supported: `True`.
- **Extended Profile (Cataloged Non-AVR):**
  - `arduino_uno_r4_wifi` / `arduino_uno_r4_minima`: Renesas RA4M1 (ARM Cortex-M4 @ 48MHz, 256KB Flash, 32KB SRAM). FQBN: `arduino:renesas_uno:unor4wifi` / `arduino:renesas_uno:minima`. Supported: `False` (prevents false application of AVR8 optimization rules to ARM Cortex-M4).

### 2.2 Board Discovery & Identification Confidence Levels
Port scanning utilizes multi-source evidence (Arduino CLI JSON detection, USB VID/PID table, USB-UART bridge chips, and active serial handshake):
- `CONFIRMED`: Verified via official Arduino CLI FQBN or verified runtime serial handshake.
- `HIGH_CONFIDENCE`: Exact official Arduino USB VID/PID match (e.g. `0x2341:0x0043` for Uno R3).
- `UNCERTAIN`: Generic USB-Serial bridge (CH340, CP2102, FTDI) with ambiguous board type.
- `UNKNOWN`: Unclassified serial device.

### 2.3 The 20 Canonical Metric Identifiers (Never Rename or Alias)
`cpu_load`, `loop_time`, `loop_frequency`, `loop_jitter`, `sram_used`, `sram_free`, `stack_used`, `stack_high_water_mark`, `interrupt_count`, `interrupt_rate`, `gpio_activity`, `adc_activity`, `uart_activity`, `spi_activity`, `i2c_activity`, `timer_activity`, `reset_event`, `watchdog_event`, `runtime_fault`, `instrumentation_overhead`.

### 2.4 The 4 Metric Veracity Classifications
- `MEASURED`: Physical hardware registers, timer differences, memory scans.
- `ESTIMATED`: Sampled duty-cycle approximations. **CRITICAL INVARIANT:** `cpu_load` on AVR microcontrollers must **ALWAYS** be classified as `ESTIMATED`.
- `DERIVED`: Arithmetic calculations combining measurements.
- `PREDICTED`: Quantitative model forecasts.

### 2.5 Strict Telemetry Provenance Invariants
- Physical serial telemetry is ingested with `is_demo=False`.
- Virtual and simulation demo telemetry is strictly ingested with `is_demo=True`.
- Ingestion rejects unknown `run_id` without implicit creation to guarantee deterministic session binding.
- `BaselineEngine` is strictly analysis-only: calculates statistical distributions and percentiles over genuine ingested samples without synthesizing data.

### 2.6 Canonical Multi-Objective Optimization Candidate Schema
```json
{
    "optimization_id": "OPT-000001",
    "finding_id": "ARIS-001",
    "run_id": "ARIS-000001",
    "title": "Convert blocking delay() to non-blocking millis() state machine",
    "problem": "delay(50) burns 800,000 instruction cycles in an empty busy-wait loop",
    "source_location": {"file": "main.ino", "line": 42},
    "before_code": "delay(50);",
    "after_code": "static unsigned long last=0; if(millis()-last>=50){last=millis(); ...}",
    "reason": "Yields execution cycles to allow concurrent loop iterations, lowering loop latency and jitter",
    "hardware_consideration": "Non-blocking millis() leverages hardware Timer0 overflow ticks without blocking CPU execution",
    "expected_effect": {
        "latency_delta_ms": -50.0,
        "loop_time_delta_ms": -50.0,
        "sram_delta_bytes": 4,
        "flash_delta_bytes": 18,
        "cpu_load_delta_pct": -75.0,
        "interrupt_risk": "LOW",
        "classification": "PREDICTED",
        "hardware_notes": "Reclaims 800,000 active wait clock cycles per loop execution."
    },
    "risk": "LOW",
    "confidence": 0.94,
    "validation_required": true,
    "status": "PROPOSED"
}
```

### 2.7 Rollback Support
- `POST /api/experiments/{experiment_id}/rollback`: Transitions experiment, candidate run, and optimization candidate status to `ROLLED_BACK`.
- `POST /api/optimizations/{optimization_id}/rollback`: Transitions optimization candidate status to `ROLLED_BACK`.

---

## 3. Communication & Firmware Toolchain Protocols

1. **Hardware Handshake:**
   - Host sends `$ARIS_HELLO#`.
   - Microcontroller responds with `$ARIS_ACK,<runtime_ver>,<protocol_ver>,<board_id>,<mcu>,<arch>,<clock_hz>,<mode>#`.
   - On boot, microcontroller emits `$ARIS_BOOT,<runtime_ver>,<board_id>,<mcu>,<reset_flags>#`.
2. **Physical Microcontroller to Backend Stream:**
   Transmitted over serial UART at 115200 baud via Fast Micro-Framing:
   `$ARIS1,<run_id>,<board_id>,<mcu>,<timestamp_ms>,<seq>,<cpu>,<loop_t>,...#`
3. **Firmware Build & Flash (`arduino-cli`):**
   - Automatically detects bundled or system `arduino-cli`.
   - Compiles targeting canonical FQBN (`arduino:avr:uno`, `arduino:avr:nano`, `arduino:avr:mega`) with `--format json --export-binaries`.
   - Extracts exact Flash and SRAM sections (`.text`, `.data`, `.bss`).
   - Uploads via `arduino-cli upload -p <port> --fqbn <fqbn>`.
4. **Backend to Frontend WebSocket:**
   Streamed over WebSocket at `/ws/telemetry/{run_id}` as real-time canonical JSON objects.
5. **Frontend to Backend REST API:**
   Standard HTTP requests hitting `/api/...` endpoints.
