# ARIS Analysis & Correlation Engine Architecture

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Subsystem Owner:** Engineer 2 (Backend & Analytical Core)

---

## 1. Overview
The ARIS Analysis Engine bridges the gap between static firmware inspection and physical embedded execution. Rather than merely alerting that a coding pattern exists, ARIS correlates **Static Code Evidence** with **Live Runtime Telemetry** to provide empirically proven optimization recommendations.

```
+--------------------------+          +---------------------------+
|  Static Firmware Input   |          |  Live Runtime Telemetry   |
|  (Source, ELF, HEX, MAP) |          |  ($ARIS1,...# or JSON)    |
+-------------+------------+          +-------------+-------------+
              |                                     |
              v                                     v
+-------------+------------+          +-------------+-------------+
|    Rule Evaluator        |          |      Baseline Engine      |
|    (ARIS-001 to 010)     |          |  (Mean, Variance, Jitter) |
+-------------+------------+          +-------------+-------------+
              |                                     |
              +------------------+------------------+
                                 |
                                 v
               +-----------------+-----------------+
               |       Correlation Engine          |
               |  (Fuses AST + Empirical Metrics)  |
               +-----------------+-----------------+
                                 |
                                 v
               +-----------------+-----------------+
               |  Correlated Finding (0.0 - 1.0)   |
               +-----------------------------------+
```

---

## 2. Canonical Analysis Rules (ARIS-001 to ARIS-010)

| Rule ID | Name | Static Signature | Runtime Metric Trigger | Architectural Impact |
| :--- | :--- | :--- | :--- | :--- |
| **ARIS-001** | Blocking Delay | `delay()`, `delayMicroseconds()` | `loop_time` matches/exceeds delay, low `loop_frequency` | Stalls CPU clock cycles, prevents real-time scheduling. |
| **ARIS-002** | Excessive Serial Logging | `Serial.print()` in unthrottled loop | High `uart_activity`, elevated `loop_time` | Fills 64-byte hardware UART buffer, blocking CPU. |
| **ARIS-003** | Excessive Polling | `while(digitalRead())`, busy loops | High `cpu_load`, high `gpio_activity` | 100% CPU utilization without power sleep. |
| **ARIS-004** | Large Local Allocation | Local array > 32 bytes on stack | High `stack_used`, `stack_high_water_mark` near limit | Risks stack-heap collision and memory corruption. |
| **ARIS-005** | High Loop Jitter | Disparate conditional delays | High `loop_jitter` (> 15% of `loop_time`) | Non-deterministic sampling and timing instability. |
| **ARIS-006** | High Interrupt Frequency| `attachInterrupt`, manual ISR registers | `interrupt_rate` > 1500 Hz | Starves background tasks and loop scheduling. |
| **ARIS-007** | Redundant GPIO Activity| Consecutive identical `digitalWrite` | High `gpio_activity` without state delta | Unnecessary pin switching cycles. |
| **ARIS-008** | Repeated Computation | Heavy floating-point / trig in loop | High `cpu_load`, extended `loop_time` | AVR lacks hardware FPU; consumes hundreds of clock cycles. |
| **ARIS-009** | Memory Pressure | Dynamic `malloc()`, `String` objects | Low `sram_free` (< 256 bytes), high `sram_used` | Heap fragmentation on 2KB SRAM microcontrollers. |
| **ARIS-010** | Long Critical Section | `cli()`, `noInterrupts()` across blocks | Dropped ticks, high `loop_jitter` | Missed timer overflows and lost serial bytes. |

---

## 3. Finding Schema

Every diagnostic issue emitted by the engine conforms to the canonical Finding schema:

```json
{
    "finding_id": "ARIS-001",
    "rule_id": "ARIS-001",
    "severity": "HIGH",
    "title": "Blocking delay detected",
    "description": "Static blocking delay of 100ms empirically correlated with measured loop duration of 102.4ms.",
    "source_file": "main.ino",
    "source_line": 42,
    "runtime_correlation": "HIGH",
    "confidence": 0.98,
    "evidence": {
        "call": "delay(100)",
        "duration": 100,
        "runtime_loop_time_mean_ms": 102.4,
        "runtime_loop_frequency_hz": 9.76,
        "delay_time_contribution_pct": 97.6
    },
    "recommended_action": "Replace delay() with non-blocking millis() timer state machine to recover loop frequency."
}
```

### Severities
- `LOW`: Stylistic or minor cycle optimizations.
- `MEDIUM`: Measurable performance inefficiencies without immediate crash risk.
- `HIGH`: Severe latency, UART buffer stalls, or high CPU utilization.
- `CRITICAL`: Stack collision risk, memory exhaustion, or complete loop stalling.

---

## 4. Correlation Methodology & Confidence Scoring

The Correlation Engine computes the `runtime_correlation` level and adjusts confidence scores:

1. **Static Evidence Baseline Confidence:**  
   Initial static AST match provides confidence $C_{\text{static}} \in [0.80, 0.92]$.
2. **Empirical Correlation Boost:**  
   When measured runtime metrics confirm the static hypothesis (e.g. measured loop latency matches static delay within 10%), correlation level is set to `HIGH`, and confidence is boosted:
   $$C_{\text{final}} = \min\left(0.99, C_{\text{static}} + \Delta_{\text{empirical}}\right)$$
   Where $\Delta_{\text{empirical}} \in [0.10, 0.15]$.
3. **Traceability:**  
   The resulting `evidence` dictionary captures exact observed physical units, ensuring that user-facing reports and Engineer 3's AI have access to empirical numbers.
