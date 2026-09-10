# ARIS Closed-Loop Experiment & Validation Engine Specification

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Subsystem Owner:** Engineer 2 (Backend & Analytical Core)

---

## 1. Closed-Loop Experiment Philosophy

In embedded engineering, theoretical optimizations often introduce hidden regressions (e.g. eliminating a delay might increase CPU power draw, or caching in SRAM might exhaust heap space).

ARIS enforces an empirical **closed-loop validation cycle**:

```
[ BASELINE RUN ] ─── Multiple Samples ───> Compute Baseline (Mean, Jitter)
       │
       ▼
[ OPTIMIZATION CANDIDATE ] ─── Proposed by AI / Synthesizer
       │
       ▼
[ BUILD + FLASH ] ─── Compile & Flash Candidate onto Microcontroller
       │
       ▼
[ CANDIDATE RUN ] ─── Measure Live Runtime Telemetry
       │
       ▼
[ COMPARE ] ─── Evaluate 8 Canonical Validation Metrics
       │
       ▼
[ DECIDE ] ─── Empirical Decision (VALIDATED, REGRESSION, etc.)
```

---

## 2. Statistical Baseline Engine

To prevent random noise from skewing decisions, a single sample is never used. The `BaselineEngine` aggregates multiple samples across an execution window ($\ge 5$ frames):

- **Mean:** $\mu = \frac{1}{N} \sum_{i=1}^N x_i$
- **Median:** 50th percentile of sorted values.
- **Minimum & Maximum:** Boundary values observed in epoch.
- **Variance:** $s^2 = \frac{1}{N-1} \sum_{i=1}^N (x_i - \mu)^2$
- **Jitter:** Mean absolute delta between consecutive loop samples:
  $$\text{Jitter} = \frac{1}{N-1} \sum_{i=2}^N |x_i - x_{i-1}|$$

---

## 3. The 8 Canonical Validation Metrics

When comparing `BASELINE` against `CANDIDATE`, the engine evaluates:

1. `cpu_load` (%)
2. `loop_time` (ms)
3. `loop_jitter` (ms)
4. `sram_used` (bytes)
5. `stack_used` (bytes)
6. `interrupt_rate` (Hz)
7. `runtime_fault` (code / counter)
8. `instrumentation_overhead` (us)

---

## 4. Difference & Percentage Change Formulas

For each metric $m$:
$$\text{difference}_m = \text{candidate}_m - \text{baseline}_m$$

$$\text{percentage\_change}_m = \frac{\text{candidate}_m - \text{baseline}_m}{|\text{baseline}_m|} \times 100\%$$

---

## 5. Canonical Validation Statuses

| Validation Status | Trigger Condition | Candidate Status Transition |
| :--- | :--- | :--- |
| **`VALIDATED`** | $\ge 2$ metrics improved with zero regressions and zero new runtime faults. | `VALIDATED` |
| **`PARTIALLY_VALIDATED`** | 1 metric improved with zero regressions. | `VALIDATED` |
| **`NO_SIGNIFICANT_CHANGE`** | All observed deltas remain within statistical noise ($\Delta < \pm 3\%$). | `PROPOSED` |
| **`REGRESSION`** | Performance degradation observed in $\ge 2$ metrics OR new runtime faults detected. | `FAILED` |
| **`REJECTED`** | Rejected by user or failed hardware safety constraints. | `REJECTED` |
| **`INCONCLUSIVE`** | Telemetry samples inconsistent or insufficient variance. | `PROPOSED` |
