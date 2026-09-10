"""
ARIS Telemetry Package.
Exports canonical schemas and the TelemetryIngestor.
"""

from .telemetry_schema import (
    PROTOCOL_VERSION,
    CANONICAL_CLASSIFICATIONS,
    CANONICAL_METRIC_NAMES,
    METRIC_SPECIFICATIONS,
    CANONICAL_ERROR_CODES,
    TelemetrySample,
    ArisErrorResponse,
    ArisException
)
from .telemetry_ingestor import TelemetryIngestor

__all__ = [
    "PROTOCOL_VERSION",
    "CANONICAL_CLASSIFICATIONS",
    "CANONICAL_METRIC_NAMES",
    "METRIC_SPECIFICATIONS",
    "CANONICAL_ERROR_CODES",
    "TelemetrySample",
    "ArisErrorResponse",
    "ArisException",
    "TelemetryIngestor"
]
