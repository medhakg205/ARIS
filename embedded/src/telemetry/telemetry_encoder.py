"""
Python Telemetry Encoder for ARIS.
Serializes TelemetrySample models into canonical JSON payloads and compact micro-frames.
"""

import json
from typing import Dict, Any, List
from ..protocol.protocol_schema import TelemetrySample, PROTOCOL_VERSION

class TelemetryEncoder:
    @staticmethod
    def encode_sample_to_json(sample: TelemetrySample) -> str:
        """Serializes a single TelemetrySample into a canonical JSON string."""
        return sample.model_dump_json()

    @staticmethod
    def encode_sample_to_dict(sample: TelemetrySample) -> Dict[str, Any]:
        """Serializes a single TelemetrySample into a dictionary."""
        return sample.model_dump()

    @staticmethod
    def encode_compact_frame(
        run_id: str,
        board_id: str,
        mcu: str,
        timestamp_ms: int,
        sequence: int,
        metrics: Dict[str, float]
    ) -> str:
        """Encodes metrics dictionary into compact $ARIS1 framing."""
        return (
            f"$ARIS1,{run_id},{board_id},{mcu},{timestamp_ms},{sequence},"
            f"{metrics.get('cpu_load', 0.0):.2f},{metrics.get('loop_time', 0.0):.2f},"
            f"{metrics.get('loop_frequency', 0.0):.2f},{metrics.get('loop_jitter', 0.0):.2f},"
            f"{int(metrics.get('sram_used', 0))},{int(metrics.get('sram_free', 0))},"
            f"{int(metrics.get('stack_used', 0))},{int(metrics.get('stack_high_water_mark', 0))},"
            f"{int(metrics.get('interrupt_count', 0))},{metrics.get('interrupt_rate', 0.0):.2f},"
            f"{int(metrics.get('gpio_activity', 0))},{int(metrics.get('adc_activity', 0))},"
            f"{int(metrics.get('uart_activity', 0))},{int(metrics.get('spi_activity', 0))},"
            f"{int(metrics.get('i2c_activity', 0))},{int(metrics.get('timer_activity', 0))},"
            f"{int(metrics.get('reset_event', 0))},{int(metrics.get('watchdog_event', 0))},"
            f"{int(metrics.get('runtime_fault', 0))},{metrics.get('instrumentation_overhead', 0.0):.2f}#"
        )
