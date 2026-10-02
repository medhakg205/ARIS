# ARIS (Adaptive Runtime Intelligence System) v2.0

### Production-Quality Runtime Observability, Physical Hardware Benchmarking & Closed-Loop AI Optimization Framework for Embedded Microcontrollers

---

## 🌟 Overview & System Highlights
**ARIS (Adaptive Runtime Intelligence System)** is a comprehensive, non-intrusive runtime observability, multi-channel hardware-in-the-loop telemetry, and architecture-aware closed-loop optimization platform engineered specifically for resource-constrained microcontrollers:
- **Arduino Uno R3 (ATmega328P @ 16MHz, AVR8)**
- **Arduino Nano Classic (ATmega328P @ 16MHz, AVR8)**
- **Arduino Mega 2560 R3 (ATmega2560 @ 16MHz, AVR8)**
- *Cataloged Non-AVR Detection*: **Arduino Uno R4 WiFi / Minima (Renesas RA4M1 ARM Cortex-M4 @ 48MHz)** — explicitly distinguished to prevent false AVR8 optimization application.

Unlike basic serial loggers or generic static linters, ARIS delivers a **closed-loop empirical optimization cycle**:
$$\text{BASELINE} \longrightarrow \text{OPTIMIZATION CANDIDATE} \longrightarrow \text{BUILD} \longrightarrow \text{FLASH} \longrightarrow \text{RUN} \longrightarrow \text{MEASURE} \longrightarrow \text{COMPARE} \longrightarrow \text{DECIDE}$$

---

## 🔬 Core Architectural Innovations

### 1. Multi-Source Board Discovery & Runtime Serial Handshake
- Automatic host port scanning interrogating `arduino-cli board list --format json`, USB Vendor/Product IDs (VID/PID), USB-UART bridge chips (CH340, CP2102, FTDI), and active serial handshakes.
- Detection confidence classification: `CONFIRMED`, `HIGH_CONFIDENCE`, `UNCERTAIN`, `UNKNOWN`.
- Active bidirectional handshake: host sends `$ARIS_HELLO#`; firmware responds with `$ARIS_ACK,<runtime_ver>,<protocol_ver>,<board_id>,<mcu>,<arch>,<clock_hz>,<mode>#`.

### 2. Native Toolchain Build & Flash Engine (`arduino-cli`)
- Discovers system or bundled Arduino IDE 2.x `arduino-cli` binary.
- Compiles sketches targeting canonical FQBNs (`arduino:avr:uno`, `arduino:avr:nano`, `arduino:avr:mega`) with `--format json --export-binaries`.
- Automatically extracts Flash (`.text`, `.data`) and SRAM (`.data`, `.bss`) allocations directly from compiler memory section maps.
- Uploads compiled binaries to target physical COM ports via `arduino-cli upload`.
- Deterministic simulation fallback available when physical compilers are not present.

### 3. Strict Telemetry Provenance Invariants
- Real hardware runs ingested with `is_demo=False` and verified serial origins.
- Demo and virtual simulation runs tagged with `is_demo=True`.
- Ingestion enforces session registration (rejects uninitialized `run_id` without implicit database creation).
- `BaselineEngine` computes statistical distributions (mean, median, variance, jitter) strictly over observed measurements.

### 4. Multi-Objective AI Optimization Engine & Rollback
- Generates architecture-aware optimizations tailored to 8-bit AVR Harvard constraints (no caches, no FPUs, 62.5ns clock cycles).
- Exposes explicit multi-objective trade-offs:
  - Latency delta (`latency_delta_ms` / `loop_time_delta_ms`)
  - SRAM delta (`sram_delta_bytes`)
  - Flash delta (`flash_delta_bytes`)
  - CPU load delta (`cpu_load_delta_pct`)
  - Interrupt risk evaluation (`LOW`, `MEDIUM`, `HIGH`)
- Automated rollback endpoints (`POST /api/experiments/{id}/rollback`, `POST /api/optimizations/{id}/rollback`) restoring known-good baseline configurations on regression.

---

## 🚀 Running the System

### 1. Backend REST & WebSocket Server
```bash
# In the root repository:
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8765
```

### 2. Frontend Desktop Application (React 18 + Vite + Tailwind)
```bash
# In aris_desktop/:
npm install
npm run dev      # For interactive development on http://localhost:5173
npm run build    # For production bundle (dist/)
```

### 3. Running All Tests (101 Passing Tests)
```bash
# Backend test suite (80 tests):
python -m pytest backend/tests

# Embedded runtime test suite (21 tests):
python -m pytest embedded/tests
```

---

## 📁 Repository Structure
```
aris-studio/
├── backend/                       # Python Backend Engine
│   ├── ai/                        # Reasoner, Prediction Engine, Risk Evaluator
│   ├── analysis/                  # Static AST rules, Baseline Engine, Correlation
│   ├── api/                       # FastAPI REST routes, error handlers, WebSockets
│   ├── database/                  # SQLite models and DB engine (aris.db)
│   ├── experiments/               # Closed-loop validation & experiment engine
│   ├── firmware/                  # Board profiles & BuildFlasher (arduino-cli)
│   ├── serial/                    # Port discovery, serial manager, handshake
│   ├── simulator/                 # Virtual hardware MCU emulator
│   ├── telemetry/                 # Fast micro-framer & ingestion validator
│   └── tests/                     # 80 backend unit & integration test suites
│
├── embedded/                      # Microcontroller C++ Runtime
│   ├── aris_runtime.h / .cpp      # Core embedded timing, probes, and watermark
│   ├── board_adapters/            # Hardware-specific register abstraction
│   ├── encoder/                   # Fast ASCII serial micro-framer
│   └── tests/                     # 21 embedded C++ / Python test suites
│
├── aris_desktop/                  # Frontend User Interface
│   ├── src/                       # React 18 dashboard, visualizer, candidate workbench
│   └── dist/                      # Minified production build
│
├── examples/                      # Real AVR Arduino sketches with bottlenecks
├── build_artifacts/               # Exported .hex binaries and compiler logs
├── INTEGRATION_CONTRACT.md        # Binding architectural invariants (v2.0)
└── README.md                      # Project documentation
```

---

## 🔌 Hardware Verification Procedure (Physical Setup)
If physical Arduino hardware is connected:
1. Connect target board (e.g. Arduino Uno R3) via USB.
2. Verify detection via `GET /api/connection/ports`:
   - Official boards will report `confidence: "HIGH_CONFIDENCE"` or `"CONFIRMED"`.
3. Ingest baseline telemetry from instrumented firmware (`examples/`).
4. Apply candidate optimization in the ARIS Studio UI.
5. Trigger closed-loop validation to compile, flash, and record empirical hardware deltas.
