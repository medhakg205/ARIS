"""
ARIS Canonical Telemetry Protocol v1.0 Schema and Error Schema.
Enforces:
1. Strict schema uniformity across all supported microcontrollers.
2. Canonical naming for all 20 metrics (no aliases allowed).
3. The 4 canonical classifications: MEASURED, ESTIMATED, DERIVED, PREDICTED.
4. The AVR invariant: cpu_load must NEVER be classified as MEASURED.
5. Canonical error schemas and standard error codes.
"""

from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# Protocol version identifier
PROTOCOL_VERSION = "1.0"

# Canonical veracity classifications
CANONICAL_CLASSIFICATIONS: Set[str] = {
    "MEASURED",
    "ESTIMATED",
    "DERIVED",
    "PREDICTED"
}

# All 20 Canonical Metric Identifiers
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

# Canonical Metric Metadata: default unit, classification, and confidence
METRIC_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
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

# Canonical Error Codes mandated by specification
CANONICAL_ERROR_CODES: Set[str] = {
    "ARIS_SERIAL_DISCONNECTED",
    "ARIS_BOARD_NOT_FOUND",
    "ARIS_UNSUPPORTED_BOARD",
    "ARIS_INVALID_FIRMWARE",
    "ARIS_BUILD_FAILED",
    "ARIS_FLASH_FAILED",
    "ARIS_TELEMETRY_INVALID",
    "ARIS_AI_UNAVAILABLE",
    "ARIS_OPTIMIZATION_INVALID",
    "ARIS_VALIDATION_FAILED",
    "ARIS_BACKEND_UNAVAILABLE"
}


class TelemetrySample(BaseModel):
    """
    Validates a single canonical telemetry data point.
    Matches the canonical JSON schema exactly.
    """
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
    def validate_canonical_metric(cls, v: str) -> str:
        """Enforces that only canonical ARIS metric names are accepted."""
        if v not in CANONICAL_METRIC_NAMES:
            raise ValueError(
                f"Metric '{v}' is not a canonical ARIS metric. Must be one of {CANONICAL_METRIC_NAMES}"
            )
        return v

    @field_validator("classification")
    @classmethod
    def validate_classification(cls, v: str) -> str:
        """Enforces that only valid classifications are accepted."""
        if v not in CANONICAL_CLASSIFICATIONS:
            raise ValueError(
                f"Classification '{v}' invalid. Must be one of {CANONICAL_CLASSIFICATIONS}"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Enforces confidence interval [0.0, 1.0]."""
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Confidence {v} must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_avr_cpu_load_rule(self) -> "TelemetrySample":
        """
        Critical Rule: ATmega microcontrollers lack hardware CPU utilization registers.
        cpu_load must ALWAYS be classified as ESTIMATED and NEVER as MEASURED.
        """
        if self.metric == "cpu_load" and self.classification == "MEASURED":
            raise ValueError(
                "Metric 'cpu_load' must NEVER be classified as MEASURED on AVR architecture. "
                "It must be classified as ESTIMATED."
            )
        return self


class ArisErrorResponse(BaseModel):
    """
    Standard canonical error model.
    Returned on any failure condition across REST endpoints.
    """
    error_code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = True

    @field_validator("error_code")
    @classmethod
    def validate_error_code(cls, v: str) -> str:
        """Ensures only canonical error codes are utilized."""
        if v not in CANONICAL_ERROR_CODES:
            raise ValueError(f"Error code '{v}' is not a canonical ARIS error code.")
        return v


class ArisException(Exception):
    """
    Base domain exception that packages an ArisErrorResponse.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        status_code: int = 400
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable
        self.status_code = status_code

    def to_error_response(self) -> ArisErrorResponse:
        return ArisErrorResponse(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            recoverable=self.recoverable
        )
