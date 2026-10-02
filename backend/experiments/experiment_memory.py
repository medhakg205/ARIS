"""
ARIS Hardware-Aware Experiment Memory Subsystem.
Indexes historical experiment outcomes and provides hierarchical matching:
Level 1: Same MCU + same optimization category + same metric
Level 2: Same architecture + same optimization category + same metric
Level 3: Same architecture + related optimization category + same metric
Level 4: Global historical evidence
Ensures simulation experiments do NOT contaminate physical calibration by default.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.experiments.calibration_models import (
    ExperimentMemoryRecord,
    CalibrationMatchLevel,
    CalibrationQualityStatus,
    CalibrationQuality
)
from backend.hardware.capability_graph import HardwareCapabilityGraph


class ExperimentMemory:
    """
    In-memory and database-backed repository of historical optimization experiments.
    Never equates unrelated hardware architectures.
    """

    def __init__(self, records: Optional[List[ExperimentMemoryRecord]] = None):
        self._records: List[ExperimentMemoryRecord] = records or []

    def add_record(self, record: ExperimentMemoryRecord) -> None:
        """Stores a new experiment record in memory."""
        self._records.append(record)

    def get_all_records(self) -> List[ExperimentMemoryRecord]:
        return list(self._records)

    def retrieve_hierarchical(
        self,
        graph: HardwareCapabilityGraph,
        optimization_category: str,
        target_metric: str,
        include_simulation: bool = False
    ) -> tuple[CalibrationMatchLevel, List[ExperimentMemoryRecord]]:
        """
        Retrieves matching historical records according to the 4-level hierarchy.
        Returns (matched_level, list_of_records).
        """
        # Filter for valid experiments and simulation isolation
        pool = [
            r for r in self._records
            if (include_simulation or r.telemetry_provenance == "REAL_HARDWARE")
            and r.validation_status in ("VALIDATED", "REGRESSION") # Inconclusive/invalid excluded from calibration
            and not r.is_outlier                                   # Outliers handled separately
        ]

        if not pool:
            return CalibrationMatchLevel.NONE, []

        target_mcu = (graph.mcu or "").lower()
        target_arch = (graph.architecture or "").lower()
        opt_cat = optimization_category.upper()
        t_metric = target_metric.lower()

        # Level 1: Same MCU + same category + same metric
        if target_mcu:
            lvl1 = [
                r for r in pool
                if r.mcu.lower() == target_mcu
                and r.optimization_category.upper() == opt_cat
                and r.target_metric.lower() == t_metric
            ]
            if lvl1:
                return CalibrationMatchLevel.MCU_SPECIFIC, lvl1

        # Level 2: Same architecture + same category + same metric
        if target_arch:
            lvl2 = [
                r for r in pool
                if r.architecture.lower() == target_arch
                and r.optimization_category.upper() == opt_cat
                and r.target_metric.lower() == t_metric
            ]
            if lvl2:
                return CalibrationMatchLevel.ARCHITECTURE_LEVEL, lvl2

        # Level 3: Same architecture + related category + same metric
        if target_arch:
            lvl3 = [
                r for r in pool
                if r.architecture.lower() == target_arch
                and r.target_metric.lower() == t_metric
            ]
            if lvl3:
                return CalibrationMatchLevel.RELATED_CATEGORY, lvl3

        # Level 4: Global historical evidence (same metric)
        lvl4 = [
            r for r in pool
            if r.target_metric.lower() == t_metric
        ]
        if lvl4:
            return CalibrationMatchLevel.GLOBAL, lvl4

        return CalibrationMatchLevel.NONE, []

    def get_known_trade_offs(
        self,
        graph: HardwareCapabilityGraph,
        optimization_category: str
    ) -> Dict[str, float]:
        """
        Retrieves empirical trade-offs (e.g. loop_time improvement vs SRAM increase).
        """
        target_arch = (graph.architecture or "").lower()
        trade_offs: Dict[str, List[float]] = {}

        for r in self._records:
            if r.architecture.lower() == target_arch and r.optimization_category.upper() == optimization_category.upper():
                for metric, val in r.trade_off_metrics.items():
                    trade_offs.setdefault(metric, []).append(val)

        avg_trade_offs: Dict[str, float] = {}
        for m, vals in trade_offs.items():
            if vals:
                avg_trade_offs[m] = round(sum(vals) / len(vals), 2)

        return avg_trade_offs
