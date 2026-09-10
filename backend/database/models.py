"""
ARIS Database Models and Entities.
Defines persistent entities and schema definitions for storing:
- Boards
- Firmwares
- Runs
- Telemetry samples
- Static and correlated Findings
- Optimization Candidates
- Experiments
- Validation Results
All data structures strictly preserve canonical naming and veracity invariants.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class BoardRecord(BaseModel):
    """
    Persistent model representing a microcontroller target board.
    Stores immutable hardware constraints, register layouts, and capabilities.
    """
    board_id: str                      # Canonical ID: e.g. "arduino_uno", "arduino_nano", "arduino_mega"
    display_name: str                  # Human readable name: e.g. "Arduino Uno"
    mcu: str                           # Microcontroller chip: e.g. "atmega328p", "atmega2560"
    architecture: str                  # Core architecture: e.g. "avr8"
    clock_hz: int                      # System clock frequency in Hertz (16 MHz = 16_000_000)
    flash_bytes: int                   # Non-volatile Program Flash memory capacity in bytes
    sram_bytes: int                    # Internal static RAM memory capacity in bytes
    eeprom_bytes: int                  # Electrically erasable programmable memory in bytes
    gpio_count: int                    # Total accessible general-purpose digital I/O pins
    adc_channels: int                  # Total analog-to-digital converter channels
    uart_count: int                    # Number of dedicated hardware serial UART peripherals
    spi_available: bool                # Indicates SPI peripheral availability
    i2c_available: bool                # Indicates Two-Wire Interface (I2C) peripheral availability
    timer_count: int                   # Number of internal hardware timers/counters
    interrupt_capabilities: List[str]  # List of hardware interrupt vectors supported


class FirmwareRecord(BaseModel):
    """
    Stores uploaded firmware artifacts, including source code, ELF binaries,
    HEX machine code images, and MAP symbol files.
    """
    firmware_id: str                   # Unique identifier (e.g. "FW-000001")
    name: str                          # Name or title of the firmware project
    source_code: Optional[str] = None  # Arduino C/C++ sketch source code (.ino/.cpp)
    hex_content: Optional[str] = None  # Intel HEX format hex records if provided
    elf_path: Optional[str] = None     # Absolute filesystem path to compiled ELF binary
    map_content: Optional[str] = None  # GCC map file text showing memory symbol layout
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TelemetryRecord(BaseModel):
    """
    Persistent database representation of an individual canonical telemetry sample.
    Adheres strictly to ARIS Telemetry Protocol v1.0.
    """
    id: Optional[int] = None           # Primary key auto-increment integer ID
    protocol_version: str = "1.0"      # Protocol version string (always "1.0")
    run_id: str                        # Execution run ID this sample belongs to (e.g. "ARIS-000001")
    board_id: str                      # Target microcontroller board canonical ID
    mcu: str                           # Target microcontroller model
    timestamp_ms: int                  # Milliseconds since target MCU boot/epoch
    sequence: int                      # Monotonically increasing sequence number
    metric: str                        # Canonical metric name (e.g. "loop_time")
    value: float                       # Numerical measurement value
    unit: str                          # Unit of measurement (e.g. "ms", "%", "bytes")
    classification: str                # Veracity: "MEASURED", "ESTIMATED", "DERIVED", "PREDICTED"
    confidence: float                  # Confidence factor between 0.0 and 1.0
    is_demo: bool = False              # Clearly flags whether data originated from DEMO MODE simulation


class FindingRecord(BaseModel):
    """
    Represents an actionable issue or antipattern discovered by static analysis,
    runtime telemetry, or correlation between both.
    """
    finding_id: str                    # Unique finding ID (e.g. "ARIS-001" or "FIND-001")
    run_id: Optional[str] = None       # Associated run ID if tied to an execution session
    rule_id: str                       # Canonical rule identifier (e.g. "ARIS-001" to "ARIS-010")
    severity: str                      # Severity: "LOW", "MEDIUM", "HIGH", "CRITICAL"
    title: str                         # Summary title of the problem detected
    description: str                   # Detailed diagnostic explanation
    source_file: str                   # Filename where issue is located (e.g. "main.ino")
    source_line: int                   # 1-indexed line number in source file
    runtime_correlation: str           # Correlation level: "NONE", "LOW", "MEDIUM", "HIGH"
    confidence: float                  # Confidence factor between 0.0 and 1.0
    evidence: Dict[str, Any]           # Structured evidence payload (code snippet, metrics, etc.)
    recommended_action: str            # Actionable remediation guidance


class BaselineMetricStats(BaseModel):
    """
    Calculated statistical aggregations for a single canonical metric over multiple samples.
    """
    metric: str                        # Metric name
    sample_count: int                  # Number of data points aggregated
    mean: float                        # Arithmetic average
    median: float                      # 50th percentile / median value
    minimum: float                     # Lowest observed value
    maximum: float                     # Highest observed value
    variance: float                    # Sample variance
    jitter: float                      # Standard deviation or delta-to-delta jitter estimate


class BaselineRecord(BaseModel):
    """
    Baseline performance profile created across multiple telemetry samples
    to serve as the benchmark foundation for closed-loop optimizations.
    """
    baseline_id: str                   # Unique baseline ID (e.g. "BASE-000001")
    run_id: str                        # Execution run ID from which baseline was computed
    board_id: str                      # Board ID benchmarked
    sample_window_ms: int              # Duration of sample window in milliseconds
    metrics: Dict[str, BaselineMetricStats] # Map of metric name to computed statistics
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OptimizationRecord(BaseModel):
    """
    Represents an optimization candidate proposed to remediate a finding.
    Used by Engineer 3 (AI + Frontend) and the closed-loop Experiment Engine.
    """
    optimization_id: str               # Unique candidate ID (e.g. "OPT-000001")
    finding_id: str                    # ID of finding being resolved
    run_id: Optional[str] = None       # Associated run ID
    title: str                         # Short descriptive title of the change
    problem: str                       # Summary of the performance bottleneck being tackled
    source_location: Dict[str, Any]    # Dictionary with 'file' and 'line'
    before_code: str                   # Original source code snippet before transform
    after_code: str                    # Proposed optimized replacement code snippet
    reason: str                        # Architectural rationale for the modification
    hardware_consideration: str        # Explanation of hardware effects (timers, registers, SRAM)
    expected_effect: Dict[str, Any]    # Projected metrics improvements (e.g. {"loop_time_delta_ms": -45})
    risk: str = "LOW"                  # Risk evaluation: "LOW", "MEDIUM", "HIGH"
    confidence: float = 0.89           # Confidence factor 0.0 to 1.0
    validation_required: bool = True   # Indicates whether closed-loop verification is mandated
    status: str = "PROPOSED"           # "PROPOSED", "APPROVED", "BUILDING", "TESTING", "VALIDATED", "REJECTED", "ROLLED_BACK", "FAILED"


class RunRecord(BaseModel):
    """
    Represents an execution run of a firmware on physical or simulated hardware.
    Tracks state transitions from CREATED through COMPLETED or FAILED.
    """
    run_id: str                        # Canonical run ID (e.g. "ARIS-000001")
    board_id: str                      # Target board identifier
    firmware_id: Optional[str] = None  # Firmware artifact associated with run
    instrumentation_mode: str = "BALANCED" # "LOW", "BALANCED", "FULL"
    start_time: Optional[str] = None   # ISO-8601 start timestamp
    end_time: Optional[str] = None     # ISO-8601 completion timestamp
    status: str = "CREATED"            # "CREATED", "BUILDING", "FLASHING", "RUNNING", "COLLECTING", "COMPLETED", "FAILED", "ROLLED_BACK"
    is_simulated: bool = False         # True if run operates on virtual hardware
    is_demo: bool = False              # Explicit DEMO MODE indicator (never disguised as real)
    baseline_id: Optional[str] = None  # Reference to generated baseline once calculated


class ValidationMetricDelta(BaseModel):
    """
    Detailed delta comparison between baseline and candidate for a specific metric.
    """
    metric: str                        # Canonical metric name
    baseline_value: float              # Measured/estimated baseline value
    candidate_value: float             # Measured/estimated candidate value
    difference: float                  # Arithmetic delta (candidate - baseline)
    percentage_change: float           # Relative percentage change ((candidate - baseline) / baseline) * 100
    is_improvement: bool               # True if difference represents positive hardware behavior


class ValidationResultRecord(BaseModel):
    """
    Formal result of comparing baseline runtime performance against candidate runtime performance.
    """
    validation_id: str                 # Unique validation ID (e.g. "VAL-000001")
    experiment_id: str                 # Experiment ID this validation evaluates
    baseline_run_id: str               # Run ID for baseline
    candidate_run_id: str              # Run ID for candidate
    metrics: Dict[str, ValidationMetricDelta] # Map of metric name to comparison delta
    validation_status: str             # "VALIDATED", "PARTIALLY_VALIDATED", "NO_SIGNIFICANT_CHANGE", "REGRESSION", "REJECTED", "INCONCLUSIVE"
    reason: str                        # Human-readable engineering justification
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExperimentRecord(BaseModel):
    """
    Encapsulates the closed-loop optimization experiment:
    BASELINE -> OPTIMIZATION CANDIDATE -> BUILD -> FLASH -> RUN -> MEASURE -> COMPARE -> DECIDE.
    """
    experiment_id: str                 # Unique experiment ID (e.g. "EXP-000001")
    title: str                         # Title of experiment
    board_id: str                      # Board under test
    baseline_run_id: str               # Benchmark baseline run reference
    candidate_run_id: Optional[str] = None # Optimization candidate run reference
    optimization_id: str               # Optimization candidate evaluated
    status: str = "CREATED"            # "CREATED", "RUNNING", "COMPLETED", "FAILED"
    validation_id: Optional[str] = None # Reference to ValidationResultRecord once completed
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
