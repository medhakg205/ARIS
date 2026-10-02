"""
ARIS Experiment Reproduction Engine & Fingerprint Comparator.
Determines whether a past experiment can be reproduced on current hardware,
firmware, toolchain, and measurement configuration without mixing incompatible conditions.
"""

from typing import Dict, Any, Tuple, Optional
from backend.reproducibility.snapshot_models import (
    ExperimentSnapshot,
    ConditionFingerprint,
    ReproductionClassification
)


class ExperimentReproductionEngine:
    """
    Evaluates experimental comparability and validates replay conditions.
    """

    @classmethod
    def evaluate_reproducibility(
        cls,
        original_snapshot: ExperimentSnapshot,
        target_snapshot: ExperimentSnapshot
    ) -> Tuple[ReproductionClassification, str]:
        """
        Compares two ExperimentSnapshots to determine exact or compatible reproducibility,
        or identifies the exact incompatibility preventing execution.
        """
        orig_fp = ConditionFingerprint.generate(original_snapshot)
        target_fp = ConditionFingerprint.generate(target_snapshot)

        # 1. Exact match across all conditions
        if orig_fp.fingerprint_hash == target_fp.fingerprint_hash:
            return (
                ReproductionClassification.EXACT_REPRODUCTION,
                "All hardware, MCU, toolchain, firmware hashes, and instrumentation settings match exactly."
            )

        # 2. Check Hardware Compatibility
        if (
            original_snapshot.hardware.mcu.lower() != target_snapshot.hardware.mcu.lower()
            or original_snapshot.hardware.architecture.lower() != target_snapshot.hardware.architecture.lower()
        ):
            return (
                ReproductionClassification.INCOMPATIBLE_HARDWARE,
                f"MCU / architecture mismatch: original={original_snapshot.hardware.mcu} ({original_snapshot.hardware.architecture}), target={target_snapshot.hardware.mcu} ({target_snapshot.hardware.architecture})."
            )

        if original_snapshot.hardware.fqbn.lower() != target_snapshot.hardware.fqbn.lower():
            return (
                ReproductionClassification.INCOMPATIBLE_HARDWARE,
                f"Board FQBN mismatch: original={original_snapshot.hardware.fqbn}, target={target_snapshot.hardware.fqbn}."
            )

        if original_snapshot.hardware.clock_hz != target_snapshot.hardware.clock_hz:
            return (
                ReproductionClassification.CONDITIONALLY_REPRODUCIBLE,
                f"Clock frequency differs: original={original_snapshot.hardware.clock_hz}Hz, target={target_snapshot.hardware.clock_hz}Hz."
            )

        # 3. Check Firmware Compatibility
        if original_snapshot.software.firmware_hash != target_snapshot.software.firmware_hash:
            return (
                ReproductionClassification.INCOMPATIBLE_FIRMWARE,
                "Baseline firmware code hash mismatch. The sketches have diverged."
            )

        # 4. Check Toolchain Compatibility
        if original_snapshot.software.compiler != target_snapshot.software.compiler:
            return (
                ReproductionClassification.INCOMPATIBLE_TOOLCHAIN,
                f"Compiler toolchain mismatch: original={original_snapshot.software.compiler}, target={target_snapshot.software.compiler}."
            )

        # 5. Check Instrumentation Compatibility
        if (
            original_snapshot.measurement.instrumentation_mode != target_snapshot.measurement.instrumentation_mode
            or set(original_snapshot.measurement.metrics) != set(target_snapshot.measurement.metrics)
        ):
            return (
                ReproductionClassification.INCOMPATIBLE_INSTRUMENTATION,
                f"Instrumentation mismatch: original mode={original_snapshot.measurement.instrumentation_mode}, target mode={target_snapshot.measurement.instrumentation_mode}."
            )

        # 6. Compatible reproduction (slight variation in sample count or toolchain minor version)
        return (
            ReproductionClassification.COMPATIBLE_REPRODUCTION,
            "Hardware, MCU, core architecture, and firmware hashes match; minor runtime environment differences exist."
        )
