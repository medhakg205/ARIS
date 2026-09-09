# ARIS Telemetry Protocol Specification (v1.0)

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Document Version:** 1.0.0  
**Owner:** Embedded Systems Engineering (Engineer 1)

---

## 1. Overview & Architectural Role

The ARIS Telemetry Protocol defines the canonical communication contract between instrumented microcontroller targets (such as the Arduino Uno, Nano, and Mega) and the host-side ARIS analysis suite.

The protocol ensures:
1. Strict schema uniformity across all supported microcontrollers.
2. Defensible distinction between measured, estimated, and derived physical quantities.
3. Minimal CPU and SRAM overhead on 8-bit AVR hardware.

---

## 2. Canonical Telemetry Schema

Every individual telemetry metric sample transmitted to or stored by the host ARIS engine adheres to the following canonical JSON schema:

```json
{
    "protocol_version": "1.0",
    "run_id": "ARIS-2026-000001",
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

### 2.1 Required Fields

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `protocol_version` | String | Protocol specification version | `"1.0"` |
| `run_id` | String | Unique identifier for the active execution/benchmark session | `"ARIS-2026-000001"` |
| `board_id` | String | Canonical board identifier (`arduino_uno`, `arduino_nano`, `arduino_mega`) | `"arduino_uno"` |
| `mcu` | String | Target microcontroller part name (`atmega328p`, `atmega2560`) | `"atmega328p"` |
| `timestamp_ms` | Integer | Microcontroller uptime / sample timestamp in milliseconds | `123456` |
| `sequence` | Integer | Monotonically incrementing sample sequence number | `42` |
| `metric` | String | Canonical metric identifier (see Section 3) | `"loop_time"` |
| `value` | Float | Numeric measurement or calculated value | `4.21` |
| `unit` | String | Physical unit of measurement (`ms`, `Hz`, `%`, `bytes`, etc.) | `"ms"` |
| `classification` | String | Metric veracity classification (`MEASURED`, `ESTIMATED`, `DERIVED`, `PREDICTED`) | `"MEASURED"` |
| `confidence` | Float | Confidence factor between `0.0` and `1.0` | `1.0` |

---

## 3. Canonical Metric Identifiers & Classifications

ARIS mandates the use of **exact** metric names. Aliases (such as `cpuUsage`, `loopTime`, `freeRam`) are prohibited across all subsystems.

| Metric Identifier | Default Unit | Canonical Classification | Default Confidence | Measurement / Estimation Methodology |
| :--- | :--- | :--- | :--- | :--- |
| `cpu_load` | `%` | **`ESTIMATED`** | 0.85 | Bounded ratio of active loop execution time vs. epoch window. **Never claimed as MEASURED.** |
| `loop_time` | `ms` | `MEASURED` | 1.00 | Microsecond hardware timer difference between loop entry and exit. |
| `loop_frequency` | `Hz` | `DERIVED` | 1.00 | Loop iterations counted divided by observation epoch duration. |
| `loop_jitter` | `ms` | `DERIVED` | 0.95 | Exponential moving average of delta between successive loop durations. |
| `sram_used` | `bytes` | `DERIVED` | 1.00 | Total board SRAM capacity minus observed free SRAM. |
| `sram_free` | `bytes` | `MEASURED` | 1.00 | Distance between current stack pointer `SP` and heap break `__brkval`. |
| `stack_used` | `bytes` | `DERIVED` | 1.00 | Distance from `RAMEND` to current stack pointer `SP`. |
| `stack_high_water_mark` | `bytes` | `ESTIMATED` | 0.95 | Byte scan of unwritten `0x5A` sentinel pattern between BSS and RAMEND. |
| `interrupt_count` | `count` | `MEASURED` | 1.00 | Atomic counter incremented inside instrumented ISR routines. |
| `interrupt_rate` | `Hz` | `DERIVED` | 0.95 | ISR counts per second across the observation epoch window. |
| `gpio_activity` | `events` | `MEASURED` | 1.00 | Cumulative count of digital pin state toggles. |
| `adc_activity` | `conversions`| `MEASURED` | 1.00 | Cumulative count of analog-to-digital converter conversions. |
| `uart_activity` | `bytes` | `MEASURED` | 1.00 | Bytes transmitted and received over serial UART. |
| `spi_activity` | `transfers` | `MEASURED` | 1.00 | SPI bus transaction count. |
| `i2c_activity` | `transactions`| `MEASURED`| 1.00 | Two-wire interface (I2C) transaction count. |
| `timer_activity` | `events` | `MEASURED` | 1.00 | Hardware timer compare/overflow tick counter. |
| `reset_event` | `flags` | `MEASURED` | 1.00 | Hardware reset source flags captured from `MCUSR` on boot. |
| `watchdog_event` | `events` | `MEASURED` | 1.00 | Watchdog timeout reset flag detection (`WDRF`). |
| `runtime_fault` | `code` | `MEASURED` | 1.00 | Detected runtime anomalies (buffer overflows, watermarking errors). |
| `instrumentation_overhead`| `us` | `MEASURED` | 1.00 | Calibrated execution duration of ARIS probe instrumentation. |

---

## 4. Veracity Classifications

ARIS enforces scientific honesty regarding microcontroller observability:
- **`MEASURED`**: Directly read from physical timers, hardware registers, memory addresses, or atomic counters.
- **`ESTIMATED`**: Derived from behavioral sampling or heuristics where hardware counters do not exist. **CRITICAL REQUIREMENT:** On ATmega328P and ATmega2560, `cpu_load` must ALWAYS be classified as `ESTIMATED`.
- **`DERIVED`**: Mathematically computed from two or more direct measurements (e.g. $\text{used} = \text{total} - \text{free}$).
- **`PREDICTED`**: Generated by offline static analysis models or simulation estimates.

---

## 5. Serial Transport & Framing

To prevent 8-bit AVR microcontrollers from exhausting SRAM and saturating UART buffers with verbose JSON strings, ARIS supports two serial modes:

### 5.1 Fast Micro-Framing Mode (Default for Hardware)
Single-line framed ASCII packet transmitted every epoch ($\approx 100\text{ms}$):
```
$ARIS1,<run_id>,<board_id>,<mcu>,<timestamp_ms>,<seq>,<cpu_load>,<loop_time>,<loop_freq>,<jitter>,<sram_used>,<sram_free>,<stack_used>,<stack_watermark>,<isr_count>,<isr_rate>,<gpio>,<adc>,<uart>,<spi>,<i2c>,<timer>,<reset>,<wdt>,<fault>,<overhead>#
```
Example frame:
```
$ARIS1,ARIS-2026-000001,arduino_uno,atmega328p,10500,42,28.50,3.20,312.50,0.15,512,1536,64,142,12,120.00,10,5,35,0,0,100,1,0,0,1.50#
```

The ARIS Host Protocol Parser (`embedded/protocol/protocol_parser.py`) decodes this frame directly into 20 canonical JSON samples matching Section 2.

### 5.2 Direct Canonical JSON Stream Mode
Used for high-memory controllers or low-frequency benchmarking. Emits line-delimited JSON objects directly over serial.

---

## 6. Instrumentation Modes

Firmware can configure ARIS into three observability profiles:
1. **`LOW`**: Minimal overhead (< 0.5% CPU impact). Samples only `cpu_load`, `loop_time`, `sram_free`, and `instrumentation_overhead`.
2. **`BALANCED`**: Standard operational profile (< 1.5% CPU impact). Adds `loop_frequency`, `loop_jitter`, `sram_used`, `stack_high_water_mark`, `interrupt_count`, and `interrupt_rate`.
3. **`FULL`**: Maximum observability. Tracks all 20 canonical metrics including individual peripheral activities.
