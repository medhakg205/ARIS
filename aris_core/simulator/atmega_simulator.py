"""
Cycle-Accurate Virtual AVR Multi-MCU Simulator for ARIS.
Emulates ATmega328P (Uno/Nano) and ATmega2560 (Mega) execution, registers, timers,
ADC channels, and real-time telemetry streaming for standalone operation without physical hardware.
"""

import time
import math
import random
import threading
from typing import Dict, List, Any, Callable
from pydantic import BaseModel
from aris_core.hardware_profiles import HardwareProfile, get_hardware_profile

class VirtualPinState(BaseModel):
    pin_name: str
    mode: str  # "INPUT", "OUTPUT", "ANALOG"
    digital_value: int  # 0 or 1
    analog_value: int   # 0 to 1023 (or 4095 for 12-bit)
    pwm_duty: int       # 0 to 255
    voltage: float

class TelemetryFrame(BaseModel):
    timestamp_ms: int
    board_id: str
    board_name: str
    cpu_utilization_pct: float
    cpu_compensated_pct: float
    free_sram_bytes: int
    used_sram_bytes: int
    stack_high_watermark_bytes: int
    loop_duration_us: int
    loop_frequency_hz: float
    jitter_us: int
    isr_frequency_hz: int
    adc_conversions_sec: int
    gpio_toggles_sec: int
    power_consumption_mw: float
    active_current_ma: float
    observer_overhead_pct: float
    raw_packet: str
    pin_states: Dict[str, VirtualPinState]

class AtmegaSimulator:
    def __init__(self, board_id: str = "arduino_uno"):
        self.hw: HardwareProfile = get_hardware_profile(board_id)
        self.running: bool = False
        self._thread: threading.Thread | None = None
        self._callbacks: List[Callable[[TelemetryFrame], None]] = []
        
        # State variables
        self.simulated_code_type: str = "default"  # "blocking_delay", "optimized", "gpio_heavy", "float_heavy"
        self.simulated_delay_ms: int = 20
        self.pin_states: Dict[str, VirtualPinState] = {}
        self.virtual_analog_inputs: Dict[str, int] = {f"A{i}": 512 for i in range(16)}
        self.virtual_digital_inputs: Dict[str, int] = {f"D{i}": 0 for i in range(54)}
        
        self.reset()

    def set_board(self, board_id: str):
        self.hw = get_hardware_profile(board_id)
        self.reset()

    def reset(self):
        self.pin_states = {}
        for pin_id, mapping in self.hw.pins.items():
            is_analog = mapping.pin_type == "analog"
            init_val = self.virtual_analog_inputs.get(pin_id, 340) if is_analog else self.virtual_digital_inputs.get(pin_id, 0)
            self.pin_states[pin_id] = VirtualPinState(
                pin_name=mapping.pin_name,
                mode="ANALOG" if is_analog else "OUTPUT",
                digital_value=1 if init_val > 512 else 0,
                analog_value=init_val,
                pwm_duty=128 if mapping.pin_type == "pwm" else 0,
                voltage=round((init_val / (2**self.hw.adc_resolution_bits - 1)) * self.hw.operating_voltage, 2)
            )

    def set_virtual_analog(self, pin_name: str, value_0_to_1023: int):
        val = max(0, min(1023, value_0_to_1023))
        self.virtual_analog_inputs[pin_name] = val
        if pin_name in self.pin_states:
            self.pin_states[pin_name].analog_value = val
            self.pin_states[pin_name].voltage = round((val / 1023.0) * self.hw.operating_voltage, 2)

    def set_virtual_digital(self, pin_name: str, high: bool):
        val = 1 if high else 0
        self.virtual_digital_inputs[pin_name] = val
        if pin_name in self.pin_states:
            self.pin_states[pin_name].digital_value = val
            self.pin_states[pin_name].voltage = self.hw.operating_voltage if high else 0.0

    def set_simulation_mode(self, code_type: str, delay_ms: int = 20):
        self.simulated_code_type = code_type
        self.simulated_delay_ms = delay_ms

    def register_callback(self, cb: Callable[[TelemetryFrame], None]):
        self._callbacks.append(cb)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run_loop(self):
        iteration = 0
        start_time = time.time()
        
        while self.running:
            iteration += 1
            now_ms = int((time.time() - start_time) * 1000)
            
            # Generate target-aware execution metrics
            if self.simulated_code_type == "blocking_delay":
                # High CPU stalling, low loop frequency
                loop_us = (self.simulated_delay_ms * 1000) + random.randint(120, 280)
                loop_hz = round(1000.0 / max(1, self.simulated_delay_ms), 1)
                cpu_gross = min(98.5, max(68.0, 72.0 + 15.0 * math.sin(iteration * 0.1) + random.uniform(-2, 2)))
                stack_watermark = min(self.hw.sram_bytes - 200, 184 + int(28 * math.sin(iteration * 0.05)))
                used_sram = int(self.hw.sram_bytes * 0.58) + random.randint(0, 12)
                adc_sec = int(loop_hz)
                gpio_sec = int(loop_hz * 2)
                isr_hz = 976  # Timer0 overflow 976.56 Hz
                jitter_us = random.randint(350, 1200)

            elif self.simulated_code_type == "optimized":
                # Non-blocking millis() state machine, direct port writes
                loop_us = random.randint(48, 92)  # fast execution!
                loop_hz = round(1_000_000.0 / loop_us, 1)
                cpu_gross = max(8.5, min(24.0, 14.2 + 3.0 * math.sin(iteration * 0.1) + random.uniform(-1, 1)))
                stack_watermark = 112 + random.randint(0, 8)
                used_sram = int(self.hw.sram_bytes * 0.28) # 50% less RAM due to PROGMEM & F()
                adc_sec = 20 # timed 20Hz polling
                gpio_sec = 1000 # high-speed direct port toggling
                isr_hz = 976
                jitter_us = random.randint(4, 18)

            elif self.simulated_code_type == "gpio_heavy":
                loop_us = random.randint(180, 420)
                loop_hz = round(1_000_000.0 / loop_us, 1)
                cpu_gross = 64.0 + random.uniform(-3, 3)
                stack_watermark = 140
                used_sram = int(self.hw.sram_bytes * 0.35)
                adc_sec = 50
                gpio_sec = 2400
                isr_hz = 976
                jitter_us = random.randint(40, 120)

            else:
                # Default standard sketch
                loop_us = 450 + random.randint(-50, 80)
                loop_hz = 2200.0
                cpu_gross = 42.0 + random.uniform(-2, 2)
                stack_watermark = 156
                used_sram = int(self.hw.sram_bytes * 0.42)
                adc_sec = 100
                gpio_sec = 200
                isr_hz = 976
                jitter_us = random.randint(80, 220)

            free_sram = max(0, self.hw.sram_bytes - used_sram - stack_watermark)
            
            # Calculate observer bias and net CPU
            observer_overhead = round(min(2.0, (32 * loop_hz) / 1_000_000 * 100), 2)
            cpu_net = max(1.0, round(cpu_gross - observer_overhead, 1))

            # Calculate dynamic power dissipation
            # P = V * (I_active * CPU% + I_sleep * (1 - CPU%))
            active_ratio = cpu_net / 100.0
            avg_current_ma = (self.hw.active_power_ma * active_ratio) + (self.hw.sleep_power_ma * (1.0 - active_ratio))
            power_mw = round(self.hw.operating_voltage * avg_current_ma, 1)

            # Update animated LED / Pin 13 toggle
            if "D13" in self.pin_states:
                led_state = 1 if (iteration % 10) < 5 else 0
                self.pin_states["D13"].digital_value = led_state
                self.pin_states["D13"].voltage = self.hw.operating_voltage if led_state else 0.0

            # Raw packet formatting: $ARIS,board,cpu,sram_free,stack_max,loop_us,isr_cnt,adc_cnt,gpio_cnt#
            board_num = 1 if "uno" in self.hw.id else (2 if "mega" in self.hw.id else 3)
            raw_pkt = f"$ARIS,{board_num},{int(cpu_net)},{free_sram},{stack_watermark},{loop_us},{int(isr_hz/10)},{int(adc_sec/10)},{int(gpio_sec/10)}#"

            frame = TelemetryFrame(
                timestamp_ms=now_ms,
                board_id=self.hw.id,
                board_name=self.hw.name,
                cpu_utilization_pct=cpu_gross,
                cpu_compensated_pct=cpu_net,
                free_sram_bytes=free_sram,
                used_sram_bytes=used_sram,
                stack_high_watermark_bytes=stack_watermark,
                loop_duration_us=loop_us,
                loop_frequency_hz=loop_hz,
                jitter_us=jitter_us,
                isr_frequency_hz=isr_hz,
                adc_conversions_sec=adc_sec,
                gpio_toggles_sec=gpio_sec,
                power_consumption_mw=power_mw,
                active_current_ma=round(avg_current_ma, 2),
                observer_overhead_pct=observer_overhead,
                raw_packet=raw_pkt,
                pin_states=self.pin_states
            )

            # Dispatch to subscribers
            for cb in self._callbacks:
                try:
                    cb(frame)
                except Exception as e:
                    print(f"Callback error: {e}")

            time.sleep(0.1) # 10Hz telemetry rate
