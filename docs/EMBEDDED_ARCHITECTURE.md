# ARIS Embedded Systems Subsystem Architecture

**Adaptive Runtime Intelligence System for Embedded Devices**  
**Subsystem:** Embedded Runtime & Hardware Observability  
**Lead Engineer:** Engineer 1 (Real Embedded Hardware Subsystem)

---

## 1. Architectural Mission & Principles

ARIS is not an Arduino IDE clone and is not primarily a software simulator. It is an **external runtime intelligence and observability layer** designed to instrument real physical microcontrollers, collect reliable low-overhead telemetry, and stream that data over USB/Serial to the ARIS host intelligence engine for static/dynamic correlation and AI-assisted optimization.

### Core Engineering Axioms:
1. **Technical Veracity**: We do not claim features the hardware cannot physically support. The AVR architecture has no hardware performance monitoring unit (PMU). We estimate CPU load from instrumented execution windows and explicitly label it as `ESTIMATED`.
2. **Minimal Observer Effect**: Profiler probes must not distort target behavior. Probes are compensated using calibrated cycle subtraction.
3. **Board-Agnostic Modularity**: Core telemetry and runtime logic are decoupled from microcontroller specifics via the `BoardAdapter` abstraction.

---

## 2. Supported Hardware Platforms

| Specification | Arduino Uno (`arduino_uno`) | Arduino Nano (`arduino_nano`) | Arduino Mega 2560 (`arduino_mega`) |
| :--- | :--- | :--- | :--- |
| **Microcontroller (MCU)** | ATmega328P | ATmega328P | ATmega2560 |
| **Architecture** | AVR 8-bit RISC (Harvard) | AVR 8-bit RISC (Harvard) | AVR 8-bit RISC (Harvard) |
| **Core Clock** | 16,000,000 Hz | 16,000,000 Hz | 16,000,000 Hz |
| **Flash Memory** | 32,768 bytes (32 KB) | 32,768 bytes (32 KB) | 262,144 bytes (256 KB) |
| **Static RAM (SRAM)** | 2,048 bytes (2 KB) | 2,048 bytes (2 KB) | 8,192 bytes (8 KB) |
| **EEPROM** | 1,024 bytes (1 KB) | 1,024 bytes (1 KB) | 4,096 bytes (4 KB) |
| **Digital GPIO Pins** | 14 (D0 - D13) | 14 (D0 - D13) | 54 (D0 - D53) |
| **Analog ADC Channels** | 6 (A0 - A5, 10-bit) | 8 (A0 - A7, 10-bit; A6/A7 analog only) | 16 (A0 - A15, 10-bit) |
| **Hardware UARTs** | 1 (`Serial`) | 1 (`Serial`) | 4 (`Serial`, `Serial1`, `Serial2`, `Serial3`) |
| **SPI Buses** | 1 (Hardware SPI on D10-D13) | 1 (Hardware SPI) | 1 (Hardware SPI on D50-D53) |
| **I2C / TWI** | 1 (A4/SDA, A5/SCL) | 1 (A4/SDA, A5/SCL) | 1 (D20/SDA, D21/SCL) |
| **Hardware Timers** | 3 (Timer0 8-bit, Timer1 16-bit, Timer2 8-bit) | 3 (Timer0, Timer1, Timer2) | 6 (Timer0-Timer5) |

---

## 3. Subsystem Architecture

```
embedded/
├── runtime/
│   ├── aris_runtime.h          # Singleton ArisRuntime API for user sketches
│   ├── aris_runtime.cpp        # Loop lifecycle, epoch timer, serial dispatch
│   ├── aris_types.h / .c       # Canonical enums, metric names, units, classifications
│   └── aris_config.h           # Instrumentation profiles (LOW, BALANCED, FULL)
├── boards/
│   ├── board_profile.h / .c    # Canonical BoardProfile C struct and static instances
│   ├── board_profile.py        # Python canonical BoardProfile data model and registry
│   ├── board_adapter.h         # Abstract BoardAdapter polymorphic base class
│   ├── board_uno.h / .cpp      # Uno adapter (ATmega328P specifics)
│   ├── board_nano.h / .cpp     # Nano adapter (ATmega328P + A6/A7 handling)
│   ├── board_mega.h / .cpp     # Mega adapter (ATmega2560 8KB SRAM, 54 GPIOs, 16 ADCs)
│   └── board_factory.h         # BoardAdapter factory instantiation
├── instrumentation/
│   ├── timing_probe.h / .cpp   # Hardware timer microsecond tracking, jitter EMA, overhead
│   ├── memory_probe.h / .cpp   # Free SRAM, stack pointer calculation, sentinel watermarking
│   ├── interrupt_probe.h / .cpp# Atomic ISR execution counters and rate estimation
│   ├── peripheral_probe.h / .cpp # Activity monitoring for GPIO, ADC, UART, SPI, I2C, Timers
│   ├── cpu_estimator.h / .cpp  # Defensible AVR CPU load estimation methodology
│   └── instrumentation_manager.h / .cpp # Orchestrator coordinating all probes
├── telemetry/
│   ├── telemetry_collector.h / .cpp # Sequence numbering, run ID management, sample creation
│   ├── telemetry_encoder.h / .cpp   # Canonical JSON encoding and $ARIS1 fast framing
│   ├── telemetry_collector.py       # Python test and host collection harness
│   └── telemetry_encoder.py         # Python serialization helper
├── protocol/
│   ├── protocol_schema.py      # Pydantic v1.0 canonical schema and strict validators
│   └── protocol_parser.py      # Parses JSON, $ARIS1 framing, and legacy frames into samples
├── examples/
│   ├── blink/blink.ino         # Clean, non-blocking baseline
│   ├── sensor/sensor.ino       # Analog sensing with ADC and GPIO telemetry
│   ├── inefficient/inefficient.ino # Antipattern sketch (delays, float math, polling, serial spam)
│   ├── interrupts/interrupts.ino # Interrupt-driven firmware
│   └── memory/memory.ino       # Dynamic memory allocation and stack recursion test
└── tests/
    ├── test_protocol.py        # Validates canonical schema, 11 fields, 20 metrics
    ├── test_boards.py          # Validates board profile specs and constraints
    ├── test_encoder_decoder.py # Roundtrip serialization and parsing tests
    ├── test_cpu_estimation.py  # Validates estimation formulas and bounds
    └── test_c_native.cpp       # Native C++ verification compiled with MSYS2 GCC
```

---

## 4. Measurement & Estimation Methodologies

### 4.1 CPU Load Estimation
- **Physical Reality**: ATmega microcontrollers do not feature a cycle counter register, hardware performance counters, or an operating system task scheduler. Direct CPU utilization registers do not exist.
- **ARIS Methodology**: Active execution time $\sum t_{\text{active}}$ is measured by instrumenting loop entry and exit points with microsecond timestamps (`micros()`). Over a fixed epoch window ($\Delta T_{\text{epoch}} \approx 100\text{ms}$), ARIS computes:
  $$\text{load}_{\text{estimated}} = \min\left(100.0, \max\left(0.0, \frac{\sum t_{\text{active}}}{\Delta T_{\text{epoch}}} \times 100.0\right)\right)$$
  If cooperative idle hooks (`record_idle()`) are registered, idle time is incorporated directly.
- **Veracity Classification**: **Strictly `ESTIMATED`**. Confidence factor is bounded at `0.85`. ARIS never outputs an estimated metric as `MEASURED`.

### 4.2 Timing Telemetry & Observer Compensation
- `loop_time` is measured via microsecond difference between `loop_enter()` and `loop_exit()`.
- **Cycle-Subtraction Compensation**: Probe execution requires approximately 24 to 32 clock cycles ($\approx 1.5 - 2.0 \mu\text{s}$ at 16 MHz). ARIS subtracts this calibrated duration from elapsed loop time so the profiler does not artificially inflate measured loop durations.
- `loop_jitter` is tracked as an Exponential Moving Average (EMA) of cycle-to-cycle duration delta:
  $$\text{Jitter}_{n} = 0.2 \times |t_n - t_{n-1}| + 0.8 \times \text{Jitter}_{n-1}$$
- `loop_frequency` is derived from loop iterations completed divided by epoch elapsed time.

### 4.3 Memory Telemetry & Stack Watermarking
- **Free SRAM**: Measured as the difference between the current Stack Pointer (`SP`) and the heap break pointer (`__brkval`). If no heap allocations have occurred, the end of BSS (`__bss_end`) is used.
- **Stack High-Water Mark**: During initialization, unused memory between `__bss_end` and `SP - 32` is painted with a sentinel byte (`0x5A`). During runtime telemetry dispatch, ARIS scans upwards from `__bss_end` for the first modified byte. The maximum distance between `RAMEND` and the first overwritten byte represents the peak stack depth reached.

### 4.4 Interrupt Telemetry
- Instrumented ISR routines execute a single inline atomic increment (`record_isr()`).
- No expensive operations, formatted serial printing, or blocking delays are executed inside ISRs.
- Counts are aggregated and converted to `interrupt_rate` (Hz) during host dispatch.

---

## 5. Technical Limitations & Boundaries

1. **CPU Utilization Estimation**: ARIS estimates CPU load using runtime instrumentation. It does NOT read a CPU usage register.
2. **Internal Observability**: ARIS observes accessible runtime behavior (instruction timings, memory boundaries, peripheral counters) and correlates them with static analysis. It does NOT observe internal silicon gates or undocumented CPU state.
3. **Timer0 Contention**: The Arduino core uses Timer0 for `millis()` and `micros()`. Reconfiguring Timer0 prescalers in user code will shift timing baselines.
4. **Serial Transmission Overhead**: Emitting verbose text over UART consumes CPU cycles. ARIS uses compact fast framing (`$ARIS1,...#`) by default to limit serial overhead to under 1.5% of total CPU time at 115200 baud.
