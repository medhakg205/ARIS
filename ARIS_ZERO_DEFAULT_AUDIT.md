# ARIS 2.0 — Final Truthfulness & Zero-Default Audit Report
**Adaptive Runtime Intelligence System**  
**Document Ref:** `AUDIT-ZERO-DEFAULT-2026-10-04`  
**Git Checkpoint Tag:** `v2.0.0-pre-hardware` (`commit 466f58e`)  
**Status:** COMPLETE & VERIFIED — ZERO UNJUSTIFIED DEFAULTS

---

## 1. Executive Summary

This audit establishes absolute physical truthfulness across the ARIS user interface, state machine, and data presentation layers.

### Governing Law
> **"IF HARDWARE IS NOT CONNECTED, ARIS MUST NOT DISPLAY HARDWARE-SPECIFIC INFORMATION AS IF IT WERE KNOWN."**

Every occurrence of hardcoded placeholder numbers, deceptive simulation defaults masquerading as live measurements, and silent target fallbacks (`arduino_uno`, `16 MHz`, `2048 B SRAM`, `428 Bytes`, synthetic p-values, or fake telemetry deltas) has been systematically eliminated.

When a property is not empirically detected from physical hardware or explicit simulation models, ARIS truthfully renders:
`—` (dash), `Not connected`, `Not detected`, `Unknown`, `Unavailable`, or `N/A`.

---

## 2. Core Truth Model State Matrix

ARIS enforces explicit state separation across two independent dimensions: **API/Backend Connectivity** and **Hardware Connectivity**.

| Hardware State | API State | Target Display | Clock Display | SRAM / Flash Display | Metric Displays | Status Strip State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DISCONNECTED** | **ONLINE** | `—` | `—` | `—` | `—` (waiting for run) | `DISCONNECTED` (Green API indicator, grey target) |
| **DISCONNECTED** | **OFFLINE** | `—` | `—` | `—` | `—` | `DISCONNECTED` (Amber API indicator) |
| **DETECTED** | **ONLINE** | Dynamic Board Name | Dynamic Clock | Dynamic Specs | `—` (Telemetry Idle) | `DETECTED (Port X)` |
| **CONNECTING** | **ONLINE** | Dynamic Board Name | Dynamic Clock | Dynamic Specs | `—` | `HANDSHAKE PENDING` |
| **CONNECTED** | **ONLINE** | Dynamic Board Name | Dynamic Clock | Dynamic Specs | Real Measured Values | `CONNECTED · ARIS v1.2.0` |
| **SIMULATION** | **ONLINE** | `Board Name (Simulated)` | `Clock (Simulated)` | Dynamic Specs | Modelled Values | `CONNECTED (SIMULATION)` |

### Distinct Semantics
- **Zero (`0` or `0.00`)**: A genuine, empirically measured arithmetic zero (e.g. `0 deadline overruns`, `0 bytes dropped`).
- **Dash (`—`)**: Missing, unmeasured, or non-applicable data (e.g. board disconnected, telemetry not yet run, no candidate validated).
- **API Status vs Hardware Status**: API online proves the Python daemon is running; Hardware Status proves an MCU responded to the UART handshake protocol.

---

## 3. Comprehensive File Audit & Rectifications

### A. Global Shell & Navigation
- [`aris_desktop/src/App.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/App.tsx):
  - **Before:** Footer Engineering Strip unconditionally rendered `selectedBoard?.display_name || 'Arduino Uno'`, `16 MHz`, and `2048 B SRAM`.
  - **Rectification:** Strictly checks `deviceState === 'CONNECTED'`. When disconnected, displays `Target: —`, `Clock: —`, `SRAM: —`. Displays `(SIMULATION)` when simulated.

### B. Firmware & Workspace
- [`aris_desktop/src/components/Firmware/FirmwareWorkspace.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Firmware/FirmwareWorkspace.tsx):
  - **Before:** Defaulted target to `'Arduino Uno (arduino:avr:uno)'`.
  - **Rectification:** Replaced with `selectedBoard ? ... : 'Target: —'`. Safe default empty arrays for sketches.

### C. Optimization Pipeline & Stepper
- [`aris_desktop/src/components/Optimization/OptimizationPipeline.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Optimization/OptimizationPipeline.tsx):
  - **Before:** Step 01 Device hardcoded `'Uno R3'`, `'AVR 8-bit Harvard'`, `'ATmega328P'`, `'16 MHz'`. Step 07 Build hardcoded `'arduino:avr:uno'`.
  - **Rectification:** Dynamic resolution via `selectedBoard?.field || '—'`. Status displays `DISCONNECTED` when no board is connected. Build target displays `selectedBoard?.fqbn || '—'`.

### D. Experiment Replay & History
- [`aris_desktop/src/components/Optimization/ExperimentReplayAndHistory.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Optimization/ExperimentReplayAndHistory.tsx):
  - **Before:** Hardcoded `'ATmega328P'`, `'RUN-BL-01 · 320 samples collected'`, `'0.95 confidence'`, and fake comparison deltas (`-18.5 ms`, `-28.0%`).
  - **Rectification:** Resolves strictly from `activeExp` fields; all fallbacks set to `—`.

### E. Prediction vs Reality Matrix
- [`aris_desktop/src/components/Optimization/PredictionVsRealityView.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Optimization/PredictionVsRealityView.tsx):
  - **Before:** Rendered hardcoded prediction/actual numbers (`14.20 ms`, `-1.8 ms`, `428 B`, `1.4% error`, `p < 0.001`, `High Evidence`) even with null validation data.
  - **Rectification:** Truthfully displays `Prediction Accuracy Unavailable` when validation metrics do not exist. When rendering comparison rows, extracts genuine baseline values (`experiment.baseline_metrics`) and actual differences (`validationResult.metrics`); otherwise displays `—`. Badge dynamically renders `EMPIRICALLY VERIFIED` vs `AWAITING PHYSICAL VALIDATION`. Summary statistics render `—` until empirical data exists.

### F. Telemetry Views & Monitors
- [`aris_desktop/src/components/Optimization/LiveValidationMonitor.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Optimization/LiveValidationMonitor.tsx):
  - **Before:** Defaulted metrics to `8.31 ms`, `27.6%`, `396 B`, `0.12 ms`, `120 Hz`.
  - **Rectification:** Replaced with `—`. Displays `Run Candidate Validation to collect samples`.
- [`aris_desktop/src/components/Optimization/BeforeAfterTelemetryView.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Optimization/BeforeAfterTelemetryView.tsx):
  - **Before:** Displayed synthetic sine curves as if they were live telemetry.
  - **Rectification:** Prominently tagged with `SIMULATION PREVIEW` badge and subtitle: `"Modelled cycle-by-cycle comparison: Baseline vs Candidate firmware profile"`.
- [`aris_desktop/src/components/Dashboard/OverviewDashboard.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Dashboard/OverviewDashboard.tsx):
  - **Before:** `maxSram` defaulted to 2048 or 32768 when `selectedBoard` was null. FQBN defaulted to `arduino:avr:uno`.
  - **Rectification:** `maxSram` and `maxFlash` resolve to null and render `—` when no board is connected. FQBN renders `—`.
- [`aris_desktop/src/components/Dashboard/TelemetryDashboard.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Dashboard/TelemetryDashboard.tsx):
  - **Before:** Hardcoded `16MHz Clock`.
  - **Rectification:** Dynamic resolution using `boardDetail.clock_hz` / `boardDetail.clock_mhz` with `—` fallback.

### G. Devices & Reports
- [`aris_desktop/src/components/Devices/DevicesView.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Devices/DevicesView.tsx):
  - **Before:** Suggested board defaulted to `'arduino_uno'`.
  - **Rectification:** Replaced with `selectedPortDetail.suggested_board_id || '—'`.
- [`aris_desktop/src/components/Reports/ReportCenter.tsx`](file:///C:/Users/aksha/.gemini/antigravity/scratch/aris-studio/aris_desktop/src/components/Reports/ReportCenter.tsx):
  - **Before:** Defaulted board to `'Arduino Uno'`.
  - **Rectification:** Resolves `selectedExp.board_id || selectedBoard?.display_name || '—'`.

---

## 4. Test Verification Suite Status

All three test suites have executed and passed with 100% success rate:

```
======================================================================
TEST SUITE SUMMARY
======================================================================
1. Backend Suite (Python/Pytest):
   - Status: 201 / 201 PASSED (80.10s)
   - Scope: Hardware graphs, telemetry parser, handshake, calibration,
            memory, candidate generators, constraints, statistical gates.

2. Embedded Suite (Python/Pytest):
   - Status: 21 / 21 PASSED (0.56s)
   - Scope: Protocol framing, CRC-16, handshake parser, memory packet decoder.

3. Frontend Suite (Node/Vitest):
   - Status: 25 / 25 PASSED (6.59s)
   - Scope: Metric badges, error banners, shell components, type contracts,
            zero-default behavior in FirmwareWorkspace & PredictionVsRealityView.

4. Production Build (Vite):
   - Status: SUCCESS (dist/ index.html, CSS, JS rendered with zero errors)
======================================================================
```

---

## 5. Certification of Truthfulness

We certify that:
1. No synthetic or simulated metric is presented as real physical hardware data.
2. When hardware is disconnected, all hardware-specific specifications display `—` or clear disconnected indicators.
3. The API health status is completely decoupled from the MCU connection status.
4. Numerical `0` is strictly reserved for measured zeros, never as a stand-in for missing data.
5. The codebase remains frozen at tag `v2.0.0-pre-hardware` pending physical hardware arrival.
