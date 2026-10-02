"""
ARIS Hardware Acceptance Test Suite Definition (HAT-01 through HAT-27).
Defines exact requirements, prerequisites, inputs, and expected outcomes
for all 27 canonical acceptance tests.
"""

from typing import List
from backend.acceptance.acceptance_models import (
    HardwareAcceptanceTestItem,
    PhysicalVerificationState,
    TestExecutionStatus
)


def get_canonical_hat_suite() -> List[HardwareAcceptanceTestItem]:
    """Returns the canonical 27 Hardware Acceptance Tests."""
    return [
        HardwareAcceptanceTestItem(
            test_id="HAT-01",
            name="Board Discovery",
            purpose="Detect connected serial microcontroller port and USB VID/PID descriptors.",
            prerequisites=["Physical Arduino board connected to USB host port"],
            expected_result="Serial COM/TTY port identified with valid hardware VID/PID.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-02",
            name="Board Identity Resolution",
            purpose="Resolve board model name, target FQBN, and confidence via toolchain/database.",
            prerequisites=["HAT-01 passed"],
            expected_result="Accurate board profile resolved without guessing (e.g. arduino:avr:uno).",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-03",
            name="Hardware Capability Resolution",
            purpose="Build HardwareCapabilityGraph with clocks, Flash/SRAM boundaries, and peripherals.",
            prerequisites=["HAT-02 passed"],
            expected_result="Capability graph populated with strict truth provenance for each item.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-04",
            name="Runtime Handshake",
            purpose="Send $ARIS_HELLO# and receive $ARIS_ACK runtime identification over UART.",
            prerequisites=["Target flashed with ARIS runtime or bootloader responder"],
            expected_result="$ARIS_ACK frame received matching expected MCU, clock, and architecture.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-05",
            name="Firmware Build",
            purpose="Compile Arduino sketch using resolved dynamic FQBN via arduino-cli.",
            prerequisites=["arduino-cli toolchain installed on host", "Valid sketch source"],
            expected_result="Zero compiler errors, valid ELF/HEX binary produced with flash/RAM sizes.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-06",
            name="Firmware Flash",
            purpose="Upload compiled binary to target microcontroller via serial programmer.",
            prerequisites=["HAT-05 passed", "Target serial port open and ready"],
            expected_result="arduino-cli upload succeeds without programmer timeout or verification error.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-07",
            name="Flash Verification",
            purpose="Confirm target boots newly flashed firmware via serial post-flash handshake.",
            prerequisites=["HAT-06 passed"],
            expected_result="MCU boots, serial reconnects, and $ARIS_ACK confirms identity.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-08",
            name="Runtime Telemetry",
            purpose="Receive and ingest fast micro-framing telemetry ($ARIS1,...#) over UART.",
            prerequisites=["HAT-07 passed"],
            expected_result="Continuous telemetry frames ingested into database with REAL_HARDWARE provenance.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-09",
            name="Telemetry Integrity",
            purpose="Validate sequence monotonicity, frame checksums, and timestamp ordering.",
            prerequisites=["HAT-08 passed"],
            expected_result="TelemetryQualityReport confirms sequence continuity and zero malformed frames.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-10",
            name="Baseline Experiment",
            purpose="Aggregate baseline telemetry across defined sampling window into statistics.",
            prerequisites=["HAT-09 passed"],
            expected_result="BaselineRecord computed with sample count, mean, median, variance, and jitter.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-11",
            name="Static/Runtime Evidence Fusion",
            purpose="Correlate static AST findings with runtime loop/SRAM telemetry on target MCU.",
            prerequisites=["Static analysis complete", "HAT-10 passed"],
            expected_result="Bottleneck finding generated linked to both static line and runtime measurement.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-12",
            name="Hypothesis Generation",
            purpose="Synthesize formal PerformanceHypothesis from grounded evidence without hallucinations.",
            prerequisites=["HAT-11 passed"],
            expected_result="Hypothesis specifies target metric, directional impact, and supporting evidence.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-13",
            name="Adaptive Measurement Planning",
            purpose="Generate MeasurementPlan selecting relevant metrics and overhead constraints.",
            prerequisites=["HAT-12 passed", "CapabilityGraph available"],
            expected_result="Plan specifies metrics, duration, sample count, and overhead budget.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-14",
            name="Candidate Generation",
            purpose="Synthesize hardware-constrained candidate using transformation registry and diffs.",
            prerequisites=["HAT-12 passed"],
            expected_result="HardwareAwareCandidate created with valid C++ diff and explainable rationale.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-15",
            name="Candidate Constraint Validation",
            purpose="Verify candidate against Flash headroom, SRAM budget, and peripheral requirements.",
            prerequisites=["HAT-14 passed"],
            expected_result="Hard resource constraints pass; unsafe candidates blocked before flash.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-16",
            name="Human Approval Gate",
            purpose="Enforce mandatory engineer authorization before physical candidate deployment.",
            prerequisites=["HAT-15 passed"],
            expected_result="Physical flash blocked when PENDING; authorized only when APPROVED.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-17",
            name="Candidate Build",
            purpose="Compile candidate sketch using dynamic FQBN and capture binary size deltas.",
            prerequisites=["HAT-16 passed (Approved)"],
            expected_result="Candidate compilation succeeds and verifies ROM/RAM usage within budgets.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-18",
            name="Candidate Flash",
            purpose="Flash candidate binary to physical board and verify target boot and handshake.",
            prerequisites=["HAT-17 passed"],
            expected_result="Target programmed and runtime handshake confirms candidate execution.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-19",
            name="Candidate Physical Experiment",
            purpose="Collect physical candidate telemetry matching the exact ExperimentPlan.",
            prerequisites=["HAT-18 passed"],
            expected_result="Candidate telemetry recorded with identical sampling rate and REAL_HARDWARE flag.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-20",
            name="Baseline/Candidate Statistical Comparison",
            purpose="Compare baseline vs candidate distributions via Welch's t-test and Cohen's d.",
            prerequisites=["HAT-10 passed", "HAT-19 passed"],
            expected_result="Empirical differences, 95% CIs, and practical significance evaluated.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-21",
            name="Prediction-vs-Measurement Error",
            purpose="Calculate quantitative signed prediction error (percentage points) vs reality.",
            prerequisites=["HAT-20 passed"],
            expected_result="PredictionError record stores raw vs calibrated prediction error.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-22",
            name="Prediction Calibration",
            purpose="Adjust future forecast bias based on historical physical prediction errors.",
            prerequisites=["HAT-21 passed"],
            expected_result="Systematic signed bias updated without manufacturing corrections.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-23",
            name="Experiment Memory Update",
            purpose="Index valid physical outcome into hierarchical hardware experiment memory.",
            prerequisites=["HAT-22 passed"],
            expected_result="Record indexed under MCU, architecture, and category for future learning.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-24",
            name="Reproducibility",
            purpose="Generate ConditionFingerprint and verify exact/compatible replay eligibility.",
            prerequisites=["HAT-20 passed"],
            expected_result="Fingerprint captures hardware/software parameters; replay creates distinct ID.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-25",
            name="Rollback",
            purpose="Revert candidate and re-flash baseline firmware on performance regression.",
            prerequisites=["Regression detected or manual rollback triggered"],
            expected_result="Baseline firmware binary uploaded back to microcontroller.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-26",
            name="Rollback Verification",
            purpose="Verify baseline runtime handshake and telemetry resumption after rollback.",
            prerequisites=["HAT-25 passed"],
            expected_result="Handshake confirms baseline identity and status marked ROLLBACK_SUCCESS.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        ),
        HardwareAcceptanceTestItem(
            test_id="HAT-27",
            name="Evidence Package Generation",
            purpose="Compile comprehensive machine-readable evidence package with hashes.",
            prerequisites=["Experiment complete or rolled back"],
            expected_result="PhysicalExperimentEvidencePackage generated containing full provenance.",
            verification_state=PhysicalVerificationState.IMPLEMENTED
        )
    ]
