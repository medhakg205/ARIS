"""
Observer-Effect Bias Compensator for ARIS.
Calculates probe execution cycle cost and statically/dynamically subtracts
instrumentation overhead from measured metrics to ensure true runtime fidelity.
"""

from pydantic import BaseModel
from aris_core.hardware_profiles import HardwareProfile, get_hardware_profile

class ObserverBiasMetrics(BaseModel):
    probe_count: int
    probe_cycles_per_iteration: int
    probe_time_us: float
    total_iterations_sec: int
    gross_cpu_pct: float
    net_compensated_cpu_pct: float
    observer_overhead_pct: float
    measurement_fidelity_score: float  # 0.0 to 100.0

class BiasCompensator:
    # Calibrated AVR instruction cycle costs for ARIS runtime probes @ 16MHz
    CYCLES_LOOP_ENTER = 8    # micros() call + variable assignment
    CYCLES_LOOP_EXIT = 24    # micros() + subtraction + comparison + conditional epoch branch
    CYCLES_TELEMETRY_DISPATCH = 160 # periodic packet formatting & UART write (amortized per 100ms)

    def __init__(self, hardware_profile: HardwareProfile = None):
        self.hw = hardware_profile or get_hardware_profile("arduino_uno")

    def compensate(self, gross_cpu_pct: float, loop_duration_us: float, loop_hz: float, probe_count: int = 3) -> ObserverBiasMetrics:
        """
        Subtracts the observer effect from gross measured telemetry.
        """
        cycles_per_loop = self.CYCLES_LOOP_ENTER + self.CYCLES_LOOP_EXIT + int(self.CYCLES_TELEMETRY_DISPATCH / max(1, loop_hz * 0.1))
        probe_time_us = (cycles_per_loop / (self.hw.core_frequency_hz / 1_000_000))
        
        # Total probe overhead per second
        total_probe_us_sec = probe_time_us * loop_hz
        observer_overhead_pct = round((total_probe_us_sec / 1_000_000) * 100, 2)
        
        net_cpu_pct = max(0.0, round(gross_cpu_pct - observer_overhead_pct, 1))
        fidelity = max(90.0, round(100.0 - observer_overhead_pct, 1))

        return ObserverBiasMetrics(
            probe_count=probe_count,
            probe_cycles_per_iteration=cycles_per_loop,
            probe_time_us=round(probe_time_us, 2),
            total_iterations_sec=int(loop_hz),
            gross_cpu_pct=round(gross_cpu_pct, 1),
            net_compensated_cpu_pct=net_cpu_pct,
            observer_overhead_pct=observer_overhead_pct,
            measurement_fidelity_score=fidelity
        )
