"""
ARIS Simulated Hardware Adapter.
Emulates physical Arduino Uno, Nano, and Mega microcontrollers.
Generates valid ARIS telemetry conforming EXACTLY to the canonical TelemetrySample schema.
Clearly identifies synthetic telemetry as: DEMO MODE.
Never allows synthetic data to masquerade as real hardware measurements.
Feeds directly into TelemetryIngestor to share the exact same telemetry pipeline.
"""

import time
import math
import random
import threading
import logging
from typing import Dict, Any, Optional, Callable, List

from backend.firmware.board_profiles import get_board_profile, BoardProfile
from backend.telemetry.telemetry_schema import (
    TelemetrySample,
    CANONICAL_METRIC_NAMES,
    METRIC_SPECIFICATIONS,
    PROTOCOL_VERSION
)
from backend.telemetry.telemetry_ingestor import TelemetryIngestor

logger = logging.getLogger("aris.simulator.hardware")


class SimulatedHardware:
    """
    Virtual MCU simulator emitting canonical ARIS telemetry samples tagged with DEMO MODE.
    """

    def __init__(self, ingestor: TelemetryIngestor, board_id: str = "arduino_uno"):
        self.ingestor = ingestor
        self.board_id = board_id
        self.profile: BoardProfile = get_board_profile(board_id)

        self.running: bool = False
        self.run_id: str = "ARIS-DEMO-000001"
        self.simulation_mode: str = "default"  # "default", "blocking_delay", "optimized", "memory_pressure", "high_isr"
        self.delay_ms: int = 20

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Simulated internal MCU state
        self._sequence: int = 1
        self._uptime_ms: int = 0
        self._isr_counter: int = 0
        self._gpio_counter: int = 0
        self._adc_counter: int = 0
        self._uart_counter: int = 0

    def set_board(self, board_id: str) -> None:
        """Configures target simulated board."""
        with self._lock:
            self.board_id = board_id
            self.profile = get_board_profile(board_id)

    def set_mode(self, mode: str, delay_ms: int = 20) -> None:
        """Sets the behavioral simulation profile."""
        with self._lock:
            self.simulation_mode = mode
            self.delay_ms = delay_ms

    def start(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Starts the simulation thread generating periodic telemetry frames.
        """
        with self._lock:
            if self.running:
                return {"status": "ALREADY_RUNNING", "run_id": self.run_id, "mode": "DEMO MODE"}

            if run_id:
                self.run_id = run_id
            else:
                self.run_id = f"ARIS-DEMO-{int(time.time())}"

            self.running = True
            self._stop_event.clear()
            self._uptime_ms = 0
            self._sequence = 1

            self._thread = threading.Thread(
                target=self._simulation_loop,
                name=f"ARIS-Sim-{self.board_id}",
                daemon=True
            )
            self._thread.start()

            logger.info(f"Started ARIS Virtual MCU Simulator for {self.board_id} in DEMO MODE.")
            return {
                "status": "SIMULATION_STARTED",
                "run_id": self.run_id,
                "board_id": self.board_id,
                "mode": "DEMO MODE",
                "behavior": self.simulation_mode
            }

    def stop(self) -> Dict[str, Any]:
        """Stops the simulator background worker."""
        with self._lock:
            self.running = False
            self._stop_event.set()
        if self._thread and self._thread.is_alive():
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
        return {"status": "SIMULATION_STOPPED", "mode": "DEMO MODE"}

    def _simulation_loop(self) -> None:
        """
        Main simulation generation loop.
        Transmits 20 canonical metrics every 100ms epoch.
        """
        while not self._stop_event.is_set():
            time.sleep(0.10)  # 100ms epoch interval
            self._uptime_ms += 100

            samples = self.generate_telemetry_snapshot()
            # Push samples directly into the same ingestion pipeline
            for sample in samples:
                self.ingestor._validate_and_store_sample(sample)

    def generate_telemetry_snapshot(self) -> List[TelemetrySample]:
        """
        Generates a synchronized snapshot of all 20 canonical ARIS metrics
        based on active behavioral simulation mode.
        """
        with self._lock:
            uptime = self._uptime_ms
            seq = self._sequence
            self._sequence += len(CANONICAL_METRIC_NAMES)

            # Determine baseline values based on simulation mode
            if self.simulation_mode == "blocking_delay":
                loop_t = float(self.delay_ms) + random.uniform(1.5, 3.2)
                loop_f = round(1000.0 / max(0.1, loop_t), 2)
                jitter = random.uniform(4.5, 8.2)
                cpu_load = min(98.5, 75.0 + random.uniform(1.0, 5.0))
                sram_used = min(self.profile.sram_bytes - 200, 620 + random.randint(0, 16))
            elif self.simulation_mode == "optimized":
                loop_t = random.uniform(0.65, 1.85)
                loop_f = round(1000.0 / max(0.1, loop_t), 2)
                jitter = random.uniform(0.08, 0.35)
                cpu_load = random.uniform(12.0, 18.5)
                sram_used = min(self.profile.sram_bytes - 400, 480 + random.randint(0, 8))
            elif self.simulation_mode == "memory_pressure":
                loop_t = random.uniform(5.0, 12.0)
                loop_f = round(1000.0 / loop_t, 2)
                jitter = random.uniform(1.0, 3.0)
                cpu_load = random.uniform(45.0, 60.0)
                sram_used = self.profile.sram_bytes - 110  # Near SRAM exhaustion
            elif self.simulation_mode == "high_isr":
                loop_t = random.uniform(12.0, 24.0)
                loop_f = round(1000.0 / loop_t, 2)
                jitter = random.uniform(8.0, 15.0)
                cpu_load = random.uniform(88.0, 96.0)
                sram_used = 750
            else:  # Default nominal behavior
                loop_t = random.uniform(8.0, 12.0)
                loop_f = round(1000.0 / loop_t, 2)
                jitter = random.uniform(0.5, 1.8)
                cpu_load = random.uniform(35.0, 45.0)
                sram_used = 512

            sram_free = max(0, self.profile.sram_bytes - sram_used)
            stack_used = 64 + random.randint(0, 12)
            stack_watermark = 142

            # Advance counters
            isr_rate = 2400.0 if self.simulation_mode == "high_isr" else 120.0
            self._isr_counter += int(isr_rate * 0.1)
            self._gpio_counter += random.randint(2, 10)
            self._adc_counter += random.randint(1, 4)
            self._uart_counter += random.randint(10, 40)

            metric_values = {
                # Invariant: cpu_load on AVR is ALWAYS ESTIMATED, NEVER MEASURED
                "cpu_load": round(cpu_load, 2),
                "loop_time": round(loop_t, 3),
                "loop_frequency": round(loop_f, 2),
                "loop_jitter": round(jitter, 3),
                "sram_used": float(sram_used),
                "sram_free": float(sram_free),
                "stack_used": float(stack_used),
                "stack_high_water_mark": float(stack_watermark),
                "interrupt_count": float(self._isr_counter),
                "interrupt_rate": float(isr_rate),
                "gpio_activity": float(self._gpio_counter),
                "adc_activity": float(self._adc_counter),
                "uart_activity": float(self._uart_counter),
                "spi_activity": 0.0,
                "i2c_activity": 0.0,
                "timer_activity": float(uptime // 10),
                "reset_event": 1.0 if uptime <= 100 else 0.0,
                "watchdog_event": 0.0,
                "runtime_fault": 1.0 if (self.simulation_mode == "memory_pressure" and sram_free < 64) else 0.0,
                "instrumentation_overhead": 1.50
            }

            samples: List[TelemetrySample] = []
            curr_seq = seq

            for metric_name in CANONICAL_METRIC_NAMES:
                val = metric_values[metric_name]
                meta = METRIC_SPECIFICATIONS[metric_name]

                # Strict conformance to canonical TelemetrySample
                sample = TelemetrySample(
                    protocol_version=PROTOCOL_VERSION,
                    run_id=self.run_id,
                    board_id=self.board_id,
                    mcu=self.profile.mcu,
                    timestamp_ms=uptime,
                    sequence=curr_seq,
                    metric=metric_name,
                    value=val,
                    unit=meta["unit"],
                    classification=meta["classification"],
                    confidence=meta["confidence"]
                )
                samples.append(sample)
                curr_seq += 1

            return samples
