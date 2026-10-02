# ARIS — Final Audit Architecture Map

**Document Date:** October 2, 2026  
**System:** ARIS (Adaptive Runtime Intelligence System)  
**Version:** 2.0.0-rc  
**Audit Status:** FINAL SOFTWARE AUDIT COMPLETE — FREEZE CERTIFICATION

---

## 1. System-Wide Structural Architecture

```
                                +-----------------------------+
                                |  Desktop UI (React/TS/Vite) |
                                +-----------------------------+
                                              │
                                              │ HTTP / JSON & WebSocket
                                              ▼
                                +-----------------------------+
                                |  FastAPI REST / WS Backend  |
                                +-----------------------------+
                                  │            │            │
            ┌─────────────────────┘            │            └─────────────────────┐
            ▼                                  ▼                                  ▼
+───────────────────────+          +───────────────────────+          +───────────────────────+
| Core Analysis Engine  |          | Experiment Pipeline   |          | Hardware & Serial     |
| - Static AST Parser   |          | - Measurement Planner |          | - Universal Discovery |
| - Baseline Engine     |          | - Experiment Engine   |          | - Serial Manager      |
| - Evidence Fusion     |          | - Candidate Generator |          | - Build & Flash CLI   |
| - Pareto Analyzer     |          | - Prediction Calibrator|         | - Handshake Protocol  |
+───────────────────────+          +───────────────────────+          +───────────────────────+
            │                                  │                                  │
            └─────────────────────┬────────────┴──────────────────────────────────┘
                                  ▼
                      +─────────────────────────+
                      | SQLite Database (WAL)   |
                      | (15 Relational Tables)  |
                      +─────────────────────────+
                                  ▲
                                  │ Serial Telemetry ($ARIS1 Frames)
                      +─────────────────────────+
                      | Physical Arduino / MCU  |
                      | (or SimulatedHardware)  |
                      +─────────────────────────+
```

---

## 2. Evidence-Driven Firmware Experimentation Pipeline

The end-to-end operational sequence implemented across backend services:

```
Static Analysis (AST & Regex Rules)
           +
Runtime Telemetry ($ARIS1 Frame Samples)
           +
Hardware Capability Graph (MCU Limits, Clock, Peripherals)
           ↓
Evidence Fusion (Grounded Bottleneck Characterization)
           ↓
Performance Hypothesis (Target Metric, Mechanism, Expected Delta)
           ↓
Adaptive Measurement Plan (Sample Size, Interval, Overhead Budget)
           ↓
Hardware-Constrained Candidate Generation (Transformation Registry)
           ↓
Multi-Objective Pareto Analysis (Latency, SRAM, Flash, Jitter)
           ↓
Human Safety Approval Gate (Explicit Operator Sign-off)
           ↓
Prediction Calibration (Prior Error Residuals & Uncertainty Bounds)
           ↓
Closed-Loop Experiment Execution (Build -> Flash -> Handshake -> Collect)
           ↓
Physical Measurement & Statistical Delta (Welch's t-test, Cohen's d)
           ↓
Validation Decision (VALIDATED, REGRESSION, INCONCLUSIVE)
           ↓
Prediction Error Computation (Residual Tracking: Error = Actual - Predicted)
           ↓
Hardware-Aware Experiment Memory (Simulation Isolated, Provenance Tracked)
           ↓
Automatic Rollback (Triggered on Regression / Fault; Verifies Re-flash)
```

---

## 3. Physical Truth vs. Simulation Separation

| Component | Physical Hardware Path | Simulation Path |
|:---|:---|:---|
| **Port Descriptor** | Enumerated COM port (e.g. `COM3`, `/dev/ttyACM0`) | `SIMULATED` / `COM_MOCK` |
| **Telemetry Provenance** | `REAL_HARDWARE` | `SIMULATED` (`is_demo=1`, `is_simulated=1`) |
| **Upload Pipeline** | `arduino-cli compile` & `upload` to physical port | In-memory virtual build and mock flash |
| **Verification Gate** | Serial `$ARIS_HELLO` -> `$ARIS_ACK` handshake | Virtual mock ACK handshake |
| **Experiment Memory** | Queried and updated for future physical calibration | Stored with `telemetry_provenance=SIMULATED` |
| **Calibration Impact** | Updates error bias and narrows confidence intervals | Excluded by default (`include_simulation=False`) |
| **Status Produced** | `IMPLEMENTED` / `PHYSICALLY_VERIFIED` (hardware only) | `SIMULATION_ONLY` / `SOFTWARE_VERIFIED` |
