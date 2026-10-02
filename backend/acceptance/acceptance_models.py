"""
ARIS Hardware Acceptance Test Suite & Session Models (HAT-01 to HAT-27).
Defines formal models, states, and verification levels for real-hardware acceptance:
- PhysicalVerificationState:
    IMPLEMENTED
    PHYSICALLY_VERIFIED
    SIMULATION_ONLY
    NOT_VERIFIED
    FAILED_PHYSICAL_VALIDATION
- HardwareAcceptanceTestItem: Individual test spec (HAT-01 through HAT-27)
- HardwareValidationSession: Complete auditable session record.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class PhysicalVerificationState(str, Enum):
    IMPLEMENTED = "IMPLEMENTED"
    PHYSICALLY_VERIFIED = "PHYSICALLY_VERIFIED"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    NOT_VERIFIED = "NOT_VERIFIED"
    FAILED_PHYSICAL_VALIDATION = "FAILED_PHYSICAL_VALIDATION"


class TestExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED_NO_HARDWARE = "SKIPPED_NO_HARDWARE"


TestExecutionStatus.__test__ = False


class HardwareAcceptanceTestItem(BaseModel):
    """
    Formal representation of an ARIS Hardware Acceptance Test (HAT-01 to HAT-27).
    """
    test_id: str                      # e.g. "HAT-01"
    name: str                         # e.g. "Board Discovery"
    purpose: str                      # Purpose of the test
    prerequisites: List[str]          # Required conditions
    input_data: Dict[str, Any] = Field(default_factory=dict)
    expected_result: str              # What must happen for pass
    actual_result: Optional[str] = None
    provenance: str = "HOST_TOOLCHAIN" # "PHYSICAL_SERIAL", "HOST_TOOLCHAIN", "SIMULATION"
    physical_vs_simulation: str = "PHYSICAL" # "PHYSICAL", "SIMULATION"
    verification_state: PhysicalVerificationState = PhysicalVerificationState.NOT_VERIFIED
    status: TestExecutionStatus = TestExecutionStatus.NOT_STARTED
    failure_reason: Optional[str] = None
    executed_at: Optional[str] = None


class HardwareValidationSession(BaseModel):
    """
    Formal hardware validation session capturing entire HAT suite execution
    and real hardware physical proof.
    """
    session_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    # Target Hardware Context
    serial_port: Optional[str] = None
    board_identity: Optional[str] = None
    board_profile: Optional[str] = None
    mcu: Optional[str] = None
    architecture: Optional[str] = None
    fqbn: Optional[str] = None
    clock_hz: Optional[int] = None
    usb_vid_pid: Optional[str] = None

    # Protocol & Runtimes
    runtime_version: Optional[str] = None
    protocol_version: Optional[str] = None

    # Firmware Hashes
    baseline_firmware_hash: Optional[str] = None
    candidate_firmware_hash: Optional[str] = None

    # Hardware Capability Graph Summary
    hardware_capabilities: Dict[str, Any] = Field(default_factory=dict)

    # Acceptance Tests
    tests: List[HardwareAcceptanceTestItem] = Field(default_factory=list)
    passed_tests_count: int = 0
    failed_tests_count: int = 0
    skipped_tests_count: int = 0

    # Evidence & Artifacts
    physical_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)

    overall_status: str = "NOT_STARTED" # "NOT_STARTED", "RUNNING", "PASSED", "FAILED", "PARTIALLY_VERIFIED"
    summary_notes: Optional[str] = None
