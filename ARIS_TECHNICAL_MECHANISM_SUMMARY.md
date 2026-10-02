# ARIS — Technical Mechanism Summary

**Document Date:** October 2, 2026  
**System:** ARIS (Adaptive Runtime Intelligence System)  
**Version:** 2.0.0-rc  
**Purpose:** Technical Mechanism Documentation for Engineering and Patent Professional Review  
**Notice:** This document contains objective descriptions of concrete algorithms, state machines, data structures, and system interactions. It makes no legal claims, legal conclusions, or assertions of patentability.

---

## 1. Universal Board Discovery & Dynamic FQBN Resolution Engine

### Technical Description
The Universal Board Discovery engine enables automated identification of target microcontrollers without maintaining a static compile-time board whitelist. It interfaces dynamically with system hardware descriptors and toolchain discovery mechanisms.

### Structural Flow
1. **Device Enumeration:** Enumerates available system serial communication ports and interrogates hardware descriptors (`VID:PID`, serial numbers, device manufacturer strings).
2. **Dynamic Toolchain Resolution:** Invokes `arduino-cli board list --format json` via secure non-shell subprocess execution.
3. **FQBN Extraction:** Extracts the canonical Fully Qualified Board Name (FQBN), architecture identifier, and platform core from toolchain output.
4. **Fallback Resolution:** When toolchain discovery yields ambiguous metadata, matches `VID:PID` pairs against a local cached registry of known development boards to infer architectural defaults.
5. **Dynamic Board Profile Instantiation:** Instantiates a runtime `BoardProfile` object populated with physical constraints (clock frequency, flash memory capacity, SRAM size, EEPROM, and communication buses).

```
[System Serial Ports] ──> [Query VID:PID / Toolchain] ──> [Dynamic FQBN Resolver] ──> [BoardProfile Object]
```

---

## 2. Hardware Capability Graph with Tiered Provenance Tracking

### Technical Description
A normalized graph model representing physical microcontroller limits, memory layouts, peripheral availability, and toolchain features. Every attribute within the graph maintains explicit metadata identifying how the property was determined.

### Provenance Classification Levels
- `EXACT_PROFILE`: Statically defined in verified hardware datasheets.
- `TOOLCHAIN`: Extracted directly from compiler and toolchain discovery commands (`board details`).
- `RUNTIME`: Empirically confirmed over serial handshake (`$ARIS_ACK` / `$ARIS_BOOT`).
- `INFERRED`: Deduced from architecture and compiler conventions (e.g., AVR 8-bit pointer sizes).
- `UNKNOWN`: Left unspecified when evidence is absent (strictly prevents speculative assumptions).

### Data Representation
The graph encapsulates:
- Processing characteristics (CPU architecture, clock speed, registers).
- Memory boundaries (Flash, SRAM, EEPROM, minimum stack margin).
- Peripheral blocks (Timers, UART, SPI, I2C, ADC, GPIO).
- Toolchain configuration (compiler binary, standard library, optimization flags).

---

## 3. Strict Veracity Runtime Telemetry Protocol & Architecture Invariant Enforcement

### Technical Description
The ARIS Canonical Telemetry Protocol v1.0 standardizes performance measurement ingestion across heterogeneous embedded microcontrollers using ASCII and binary frame formats with CRC16 verification.

### Metric Veracity Categories
Every emitted telemetry sample must belong to one of four mutually exclusive veracity classes:
1. `MEASURED`: Directly sampled from a physical hardware counter, cycle register, or system timer.
2. `ESTIMATED`: Calculated via empirical proxy models when hardware counters are unavailable.
3. `DERIVED`: Arithmetically computed from two or more existing metrics (e.g., frequency from period).
4. `PREDICTED`: Projected prior to execution via analytical or calibrated models.

### Architecture Invariant Enforcement
Microcontrollers based on the AVR 8-bit architecture (such as ATmega328P) do not provide hardware execution cycle counters or CPU utilization registers. The schema enforces that any `cpu_load` metric received from an AVR architecture must be classified strictly as `ESTIMATED`. A Pydantic model validator actively rejects any attempt to classify AVR `cpu_load` as `MEASURED`.

---

## 4. Evidence Fusion & Grounded Performance Hypothesis Generation

### Technical Description
A deterministic reasoning engine that synthesizes static firmware analysis results (AST and control flow inspection) with dynamic runtime telemetry (latency, memory usage, jitter).

### Algorithmic Sequence
1. **Static Issue Identification:** Analyzes firmware source code for performance bottlenecks (e.g., blocking `delay()` invocations, repeated string allocations in dynamic RAM, unbuffered bus operations).
2. **Runtime Correlation:** Queries database for telemetry samples coinciding with the identified code patterns (e.g., verifying that a `delay(100)` matches observed loop latency spikes $\ge 100\text{ ms}$).
3. **Hypothesis Instantiation:** Emits a formal `PerformanceHypothesis` data structure containing:
   - Primary target bottleneck.
   - Mechanism of impairment (e.g., CPU blocking vs memory fragmentation).
   - Expected improvement vectors across latency and memory.
   - Falsification criteria.

---

## 5. Adaptive Measurement Planner with Statistical Sufficiency Modeling

### Technical Description
An automated planner that configures experiment sampling parameters based on target confidence intervals and microcontroller capabilities.

### Functional Operation
1. **Sample Size Calculation:** Computes required observation counts based on desired statistical power and historical metric variance:
   $$n = \left(\frac{Z_{\alpha/2} \cdot \sigma}{E}\right)^2$$
2. **Overhead Budget Allocation:** Balances instrumentation granularity against microcontroller memory and bandwidth limits. Selects among `MINIMAL`, `BALANCED`, and `DETAILED` instrumentation modes to ensure telemetry overhead does not distort MCU execution by $> 5\%$.
3. **Measurement Plan Output:** Generates an immutable `MeasurementPlan` defining active metrics, sampling duration, target sample count, and required hardware timers.

---

## 6. Formal Experiment State Machine & Multi-Party Contract Verification

### Technical Description
A state machine that governs the lifecycle of firmware optimization experiments, preventing state corruption, ungrounded validation, and invalid transitions.

### State Progression DAG
```
[PLANNED] ──> [PRECHECKING] ──> [BASELINE_READY] ──> [RUNNING_BASELINE]
                                                           │
[CANDIDATE_COLLECTED] <── [RUNNING_CANDIDATE] <── [BASELINE_COLLECTED]
        │
        └──> [EVALUATING] ──> [SUFFICIENT] ──> [COMPLETED / REGRESSION / FAILED]
```

### Invariants & Guards
- Validation or completion states (`COMPLETED`, `IMPROVEMENT`, `REGRESSION`) cannot be reached unless both baseline and candidate telemetry datasets have been executed and persisted.
- State reversions from terminal states (`COMPLETED`, `ROLLED_BACK`, `FAILED`) are rejected with domain exceptions (`ARIS_VALIDATION_FAILED`).
- Formal `OptimizationExperimentContract` binds the candidate to explicit invariants: target metric improvement thresholds and non-regression constraints on memory and faults.

---

## 7. Hardware-Constrained Optimization Candidate Generation & Multi-Objective Pareto Analysis

### Technical Description
A code transformation synthesis engine that filters proposed optimizations through strict physical resource budgets and architectural boundaries before presenting candidates for evaluation.

### Operation Pipeline
1. **Canonical Transformation Registry:** Matches AST findings against pre-defined semantic transformations (e.g., replacing blocking delays with non-blocking timer loops, replacing runtime `pinMode`/`digitalWrite` with direct port manipulation).
2. **Hardware Constraints Filter:** Evaluates target microcontroller architecture. AVR-specific direct port manipulation is blocked on ARM Cortex-M microcontrollers.
3. **Resource Budget Engine:** Evaluates projected Flash and SRAM delta:
   - Rejects candidates where projected Flash $> 95\%$ of capacity.
   - Rejects candidates where projected SRAM $> 90\%$ of capacity.
   - Rejects candidates leaving $< 64\text{ bytes}$ of stack headroom.
4. **Pareto Frontier Analysis:** Ranks viable candidates across multi-objective vectors (Loop Latency, SRAM Consumption, Flash Consumption, Execution Jitter). Identifies non-dominated solutions without arbitrary scalar weightings.

---

## 8. Human Safety Approval Gate & Verifiable Rollback Subsystem

### Technical Description
A deterministic safety gate that controls the deployment of generated firmware modifications to physical microcontrollers.

### Verification Workflow
1. **Human Operator Gate:** Firmware compilation and flashing cannot proceed while `candidate.approval.decision` equals `PENDING`. An explicit human approval action (`APPROVED`) signed with operator timestamp is required.
2. **Flash Verification Handshake:** Following flash upload, the host awaits a sequence of runtime handshake frames (`$ARIS_HELLO` $\rightarrow$ `$ARIS_ACK`) within a configurable timeout. If the handshake fails or times out, the flash is classified as `ARIS_FLASH_UNVERIFIED`.
3. **Automatic Rollback:** If candidate benchmark testing reveals regressions breaching contract invariants, or if runtime faults occur, the system automatically flashes the archived baseline firmware binary and verifies MCU recovery via handshake.

---

## 9. Prediction Calibration Engine & Physical Experiment Memory Isolation

### Technical Description
A predictive calibration system that continuously refines firmware performance estimates by tracking historical model prediction errors against empirical physical outcomes.

### Mathematical Formulation
1. **Residual Error Vector:** For completed experiment $k$:
   $$e_k = y_{\text{measured}, k} - \hat{y}_{\text{raw}, k}$$
2. **Calibrated Prediction:** Future prediction $\hat{y}_{\text{calibrated}}$ is computed by applying an error compensation factor derived from historical experiments matching the same transformation category, MCU architecture, and clock domain:
   $$\hat{y}_{\text{calibrated}} = \hat{y}_{\text{raw}} + \mu_{\text{error}}$$
3. **Uncertainty Interval:** Calculates standard deviation of historical residuals to establish 95% confidence bounds $[\hat{y}_{\text{lower}}, \hat{y}_{\text{upper}}]$.

### Physical Isolation Guarantee
Experiments executed under simulation (`is_simulated=True`, `is_demo=True`) are physically isolated in storage. Query interfaces for the calibration model filter out simulation records by default (`include_simulated=False`), preventing virtual data from biasing physical hardware predictions.

---

## 10. Self-Contained Reproducible Evidence Package & Audit Lineage

### Technical Description
An exportable, cryptographically grounded archive format that encapsulates every artifact, measurement, and transformation comprising an experimental run.

### Package Contents
- **System Lineage:** Complete linkage chain: Source Firmware Hash $\rightarrow$ Static Analysis Finding $\rightarrow$ Grounded Hypothesis $\rightarrow$ Candidate Model $\rightarrow$ Experiment Manifest $\rightarrow$ Physical Validation Record.
- **Hardware Snapshot:** Full serialized `HardwareCapabilityGraph` capturing the exact physical target environment.
- **Toolchain Provenance:** Compiler version, toolchain binary checksums, compilation flags, and build duration.
- **Raw Telemetry Stream:** Timestamped, sequence-numbered baseline and candidate telemetry samples.
- **Statistical Deltas:** Empirical mean, standard deviation, and percentage change across all monitored metrics.
- **Cryptographic Integrity:** SHA-256 digests over sketch sources, compiled binaries, and telemetry streams.
