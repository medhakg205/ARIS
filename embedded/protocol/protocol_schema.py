"""
ARIS Canonical Telemetry Protocol v1.0 Schema.
Enforces exact field names, canonical metric names, and strict metric classifications.
"""

from typing import Dict, Any, List, Set, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

PROTOCOL_VERSION = "1.0"

VALID_CLASSIFICATIONS: Set[str] = {
    "MEASURED",
    "ESTIMATED",
    "DERIVED",
    "PREDICTED"
}

CANONICAL_METRIC_NAMES: List[str] = [
    "cpu_load",
    "loop_time",
    "loop_frequency",
    "loop_jitter",
    "sram_used",
    "sram_free",
    "stack_used",
    "stack_high_water_mark",
    "interrupt_count",
    "interrupt_rate",
    "gpio_activity",
    "adc_activity",
    "uart_activity",
    "spi_activity",
    "i2c_activity",
    "timer_activity",
    "reset_event",
    "watchdog_event",
    "runtime_fault",
    "instrumentation_overhead"
]

METRIC_METADATA: Dict[str, Dict[str, Any]] = {
    "cpu_load": {"unit": "%", "classification": "ESTIMATED", "confidence": 0.85},
    "loop_time": {"unit": "ms", "classification": "MEASURED", "confidence": 1.0},
    "loop_frequency": {"unit": "Hz", "classification": "DERIVED", "confidence": 1.0},
    "loop_jitter": {"unit": "ms", "classification": "DERIVED", "confidence": 0.95},
    "sram_used": {"unit": "bytes", "classification": "DERIVED", "confidence": 1.0},
    "sram_free": {"unit": "bytes", "classification": "MEASURED", "confidence": 1.0},
    "stack_used": {"unit": "bytes", "classification": "DERIVED", "confidence": 1.0},
    "stack_high_water_mark": {"unit": "bytes", "classification": "ESTIMATED", "confidence": 0.95},
    "interrupt_count": {"unit": "count", "classification": "MEASURED", "confidence": 1.0},
    "interrupt_rate": {"unit": "Hz", "classification": "DERIVED", "confidence": 0.95},
    "gpio_activity": {"unit": "events", "classification": "MEASURED", "confidence": 1.0},
    "adc_activity": {"unit": "conversions", "classification": "MEASURED", "confidence": 1.0},
    "uart_activity": {"unit": "bytes", "classification": "MEASURED", "confidence": 1.0},
    "spi_activity": {"unit": "transfers", "classification": "MEASURED", "confidence": 1.0},
    "i2c_activity": {"unit": "transactions", "classification": "MEASURED", "confidence": 1.0},
    "timer_activity": {"unit": "events", "classification": "MEASURED", "confidence": 1.0},
    "reset_event": {"unit": "flags", "classification": "MEASURED", "confidence": 1.0},
    "watchdog_event": {"unit": "events", "classification": "MEASURED", "confidence": 1.0},
    "runtime_fault": {"unit": "code", "classification": "MEASURED", "confidence": 1.0},
    "instrumentation_overhead": {"unit": "us", "classification": "MEASURED", "confidence": 1.0}
}

class TelemetrySample(BaseModel):
    protocol_version: str = Field(default=PROTOCOL_VERSION)
    run_id: str
    board_id: str
    mcu: str
    timestamp_ms: int
    sequence: int
    metric: str
    value: float
    unit: str
    classification: str
    confidence: float

    @field_validator("metric")
    @classmethod
    def validate_metric_name(cls, v: str) -> str:
        if v not in CANONICAL_METRIC_NAMES:
            raise ValueError(
                f"Metric '{v}' is not a canonical ARIS metric. "
                f"Must be one of {CANONICAL_METRIC_NAMES}"
            )
        return v

    @field_validator("classification")
    @classmethod
    def validate_classification(cls, v: str) -> str:
        if v not in VALID_CLASSIFICATIONS:
            raise ValueError(
                f"Classification '{v}' invalid. Must be one of {VALID_CLASSIFICATIONS}"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence {v} must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_cpu_load_not_measured(self) -> "TelemetrySample":
        # Critical Prompt Requirement: ATmega has no CPU usage registers.
        # CPU load MUST be explicitly classified as ESTIMATED and NEVER as MEASURED.
        if self.metric == "cpu_load" and self.classification == "MEASURED":
            raise ValueError(
                "Metric 'cpu_load' must NEVER be classified as MEASURED on AVR architecture. "
                "It must be classified as ESTIMATED."
            )
        return self
