"""
ARIS Capability Graph Builder & Negotiation Engine.
Constructs normalized HardwareCapabilityGraph instances from BoardProfile objects
and negotiates valid runtime telemetry and instrumentation operations for targets.
Enforces:
- Zero fabrication of capabilities or architecture traits.
- AVR8 vs ARM vs ESP32 vs unknown peripheral/timer discrimination.
- Dynamic identification of valid vs invalid ARIS instrumentation metrics.
"""

from typing import List, Dict, Any, Optional
from backend.firmware.board_profiles import BoardProfile
from backend.hardware.capability_graph import (
    HardwareCapabilityGraph,
    CapabilityItem,
    CapabilityProvenance
)


class CapabilityGraphBuilder:
    """Builds a verified HardwareCapabilityGraph from a dynamic BoardProfile."""

    @classmethod
    def build(cls, profile: BoardProfile) -> HardwareCapabilityGraph:
        # Determine source provenance
        prov_map = {
            "EXACT_PROFILE": CapabilityProvenance.EXACT_PROFILE,
            "TOOLCHAIN_DERIVED": CapabilityProvenance.TOOLCHAIN,
            "RUNTIME_VERIFIED": CapabilityProvenance.RUNTIME,
            "PARTIALLY_RESOLVED": CapabilityProvenance.UNKNOWN,
            "UNKNOWN": CapabilityProvenance.UNKNOWN
        }
        default_prov = prov_map.get(profile.profile_source, CapabilityProvenance.UNKNOWN)

        unknown_props = list(profile.unavailable_properties)

        # 1. Clock
        if profile.clock_hz is not None:
            clock_item = CapabilityItem(
                name="clock",
                available=True,
                value=profile.clock_hz,
                unit="Hz",
                provenance=default_prov
            )
        else:
            clock_item = CapabilityItem(name="clock", available=None, value=None, unit="Hz", provenance=CapabilityProvenance.UNKNOWN)

        # 2. Flash Memory
        if profile.flash_bytes is not None:
            flash_item = CapabilityItem(
                name="flash_memory",
                available=True,
                value=profile.flash_bytes,
                unit="bytes",
                provenance=default_prov
            )
        else:
            flash_item = CapabilityItem(name="flash_memory", available=None, value=None, unit="bytes", provenance=CapabilityProvenance.UNKNOWN)

        # 3. SRAM Memory
        if profile.sram_bytes is not None:
            sram_item = CapabilityItem(
                name="sram_memory",
                available=True,
                value=profile.sram_bytes,
                unit="bytes",
                provenance=default_prov
            )
        else:
            sram_item = CapabilityItem(name="sram_memory", available=None, value=None, unit="bytes", provenance=CapabilityProvenance.UNKNOWN)

        # 4. EEPROM Memory
        if profile.eeprom_bytes is not None:
            eeprom_item = CapabilityItem(
                name="eeprom_memory",
                available=profile.eeprom_bytes > 0,
                value=profile.eeprom_bytes,
                unit="bytes",
                provenance=default_prov
            )
        else:
            eeprom_item = CapabilityItem(name="eeprom_memory", available=None, value=None, unit="bytes", provenance=CapabilityProvenance.UNKNOWN)

        # 5. GPIO
        if profile.gpio_count is not None:
            gpio_item = CapabilityItem(
                name="gpio",
                available=True,
                value=profile.gpio_count,
                unit="pins",
                provenance=default_prov
            )
        else:
            gpio_item = CapabilityItem(name="gpio", available=None, value=None, unit="pins", provenance=CapabilityProvenance.UNKNOWN)

        # 6. ADC
        if profile.adc_channels is not None:
            adc_item = CapabilityItem(
                name="adc",
                available=profile.adc_channels > 0,
                value=profile.adc_channels,
                unit="channels",
                provenance=default_prov
            )
        else:
            adc_item = CapabilityItem(name="adc", available=None, value=None, unit="channels", provenance=CapabilityProvenance.UNKNOWN)

        # 7. UART
        if profile.uart_count is not None:
            uart_item = CapabilityItem(
                name="uart",
                available=profile.uart_count > 0,
                value=profile.uart_count,
                unit="peripherals",
                provenance=default_prov
            )
        else:
            uart_item = CapabilityItem(name="uart", available=None, value=None, unit="peripherals", provenance=CapabilityProvenance.UNKNOWN)

        # 8. SPI & I2C
        spi_item = CapabilityItem(
            name="spi",
            available=profile.spi_available,
            value=bool(profile.spi_available) if profile.spi_available is not None else None,
            provenance=default_prov if profile.spi_available is not None else CapabilityProvenance.UNKNOWN
        )
        i2c_item = CapabilityItem(
            name="i2c",
            available=profile.i2c_available,
            value=bool(profile.i2c_available) if profile.i2c_available is not None else None,
            provenance=default_prov if profile.i2c_available is not None else CapabilityProvenance.UNKNOWN
        )

        # 9. Timers
        if profile.timer_count is not None:
            timers_item = CapabilityItem(
                name="timers",
                available=profile.timer_count > 0,
                value=profile.timer_count,
                unit="timers",
                provenance=default_prov
            )
        else:
            timers_item = CapabilityItem(name="timers", available=None, value=None, unit="timers", provenance=CapabilityProvenance.UNKNOWN)

        # 10. Interrupts
        if profile.interrupt_capabilities:
            interrupts_item = CapabilityItem(
                name="interrupts",
                available=True,
                value=list(profile.interrupt_capabilities),
                provenance=default_prov
            )
        elif "interrupt_capabilities" in unknown_props or profile.profile_source in ("PARTIALLY_RESOLVED", "UNKNOWN"):
            interrupts_item = CapabilityItem(name="interrupts", available=None, value=[], provenance=CapabilityProvenance.UNKNOWN)
        else:
            interrupts_item = CapabilityItem(name="interrupts", available=False, value=[], provenance=default_prov)

        # 11. Watchdog
        arch = (profile.architecture or "").lower()
        if "avr" in arch:
            watchdog_item = CapabilityItem(name="watchdog", available=True, value="WDT", provenance=CapabilityProvenance.INFERRED)
        elif "arm" in arch or "cortex" in arch:
            watchdog_item = CapabilityItem(name="watchdog", available=True, value="WDT/IWDT", provenance=CapabilityProvenance.INFERRED)
        elif "esp" in arch:
            watchdog_item = CapabilityItem(name="watchdog", available=True, value="ESP_WDT", provenance=CapabilityProvenance.INFERRED)
        else:
            watchdog_item = CapabilityItem(name="watchdog", available=None, value=None, provenance=CapabilityProvenance.UNKNOWN)

        # 12. Compiler Toolchain
        toolchain_val = profile.build_toolchain if profile.build_toolchain != "unknown" else None
        compiler_item = CapabilityItem(
            name="compiler_toolchain",
            available=bool(toolchain_val),
            value=toolchain_val,
            provenance=default_prov if toolchain_val else CapabilityProvenance.UNKNOWN
        )

        # 13. Runtime Protocol
        runtime_item = CapabilityItem(
            name="runtime_protocol",
            available=True,
            value="ARIS Telemetry Protocol v1.0",
            provenance=CapabilityProvenance.INFERRED
        )

        # 14. Negotiate Instrumentation Operations
        avail_inst, unavail_inst = CapabilityNegotiator.negotiate_instrumentation(profile)

        return HardwareCapabilityGraph(
            board_id=profile.board_id,
            display_name=profile.display_name,
            fqbn=profile.fqbn,
            platform=profile.platform,
            mcu=profile.mcu,
            architecture=profile.architecture,
            clock=clock_item,
            flash_memory=flash_item,
            sram_memory=sram_item,
            eeprom_memory=eeprom_item,
            gpio=gpio_item,
            adc=adc_item,
            uart=uart_item,
            spi=spi_item,
            i2c=i2c_item,
            timers=timers_item,
            interrupts=interrupts_item,
            watchdog=watchdog_item,
            compiler_toolchain=compiler_item,
            runtime_protocol=runtime_item,
            available_instrumentation=avail_inst,
            unavailable_instrumentation=unavail_inst,
            unknown_properties=unknown_props,
            raw_properties_count=len(profile.capabilities)
        )


class CapabilityNegotiator:
    """
    Evaluates what telemetry and instrumentation operations are physically valid
    for a target device without ever claiming unsupported operations.
    """

    @classmethod
    def negotiate_instrumentation(cls, profile: BoardProfile) -> tuple[List[str], List[str]]:
        """
        Determines supported vs unsupported ARIS instrumentation features.
        Returns (available_instrumentation, unavailable_instrumentation).
        """
        available: List[str] = []
        unavailable: List[str] = []

        arch = (profile.architecture or "").lower()

        # If architecture or MCU is totally unknown (partially resolved),
        # only basic software tick timing is assumed, specific hardware features are rejected.
        if not profile.architecture or profile.profile_source in ("PARTIALLY_RESOLVED", "UNKNOWN"):
            available.append("loop_time")
            unavailable.extend([
                "hardware_cycle_counter",
                "dwt_cycle_count",
                "dwt_cycle_counter",
                "cpu_load_register",
                "sram_watermark_stack_pointer",
                "per_pin_interrupt_tracing",
                "cache_miss_rate",
                "fpu_utilization"
            ])
            return available, unavailable

        # 1. Loop Timing & Jitter (Universal across instrumented boards)
        available.extend(["loop_time", "loop_frequency", "loop_jitter"])

        # 2. Memory instrumentation
        if profile.sram_bytes is not None:
            available.extend(["sram_used", "sram_free", "stack_high_water_mark"])
        else:
            unavailable.extend(["sram_used", "sram_free", "stack_high_water_mark"])

        # 3. CPU Load & Cycle Counting
        if "avr" in arch:
            # AVR8 ATmega/ATtiny targets:
            # - Timer0/Timer1 based CPU load estimation is available.
            # - Hardware CPU cycle counter registers (like ARM DWT->CYCCNT) DO NOT EXIST.
            # - No caches or hardware FPUs exist.
            available.append("cpu_load_timer_tick")
            unavailable.extend([
                "hardware_cycle_counter",
                "dwt_cycle_count",
                "dwt_cycle_counter",
                "branch_predictor_tracing",
                "cache_miss_rate",
                "hardware_fpu_metrics"
            ])
        elif "arm" in arch or "cortex" in arch:
            # ARM Cortex-M:
            # - DWT (Data Watchpoint and Trace) cycle counting is available on M3/M4/M7 cores.
            # - Cortex-M0/M0+ lacks DWT CYCCNT.
            if "m4" in arch or "m3" in arch or "m7" in arch:
                available.append("dwt_cycle_counter")
            else:
                unavailable.append("dwt_cycle_counter")
            available.append("systick_cpu_load")
            unavailable.append("avr_specific_io_registers")
        elif "esp" in arch:
            # ESP32 / ESP8266:
            # - FreeRTOS tick tracing, dual-core CPU utilization
            available.extend(["freertos_task_cpu_load", "heap_caps_memory"])
            unavailable.append("avr_specific_io_registers")
        else:
            unavailable.append("hardware_cycle_counter")

        # 4. Peripheral Activity Tracing
        if profile.gpio_count:
            available.append("gpio_activity")
        if profile.adc_channels:
            available.append("adc_activity")
        if profile.uart_count:
            available.append("uart_activity")
        if profile.spi_available:
            available.append("spi_activity")
        if profile.i2c_available:
            available.append("i2c_activity")
        if profile.timer_count:
            available.append("timer_activity")

        return available, unavailable

    @classmethod
    def is_operation_valid(cls, graph: HardwareCapabilityGraph, operation: str) -> bool:
        """Checks whether a requested instrumentation operation is valid on target."""
        return operation in graph.available_instrumentation
