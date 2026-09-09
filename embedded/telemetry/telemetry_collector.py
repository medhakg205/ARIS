"""
Python Telemetry Collector for ARIS.
Aggregates telemetry frames, tracks sequence numbers and run IDs,
and yields validated TelemetrySample instances.
"""

import time
from typing import Dict, Any, List, Optional
from ..protocol.protocol_schema import (
    TelemetrySample,
    PROTOCOL_VERSION,
    CANONICAL_METRIC_NAMES,
    METRIC_METADATA
)
from ..boards.board_profile import BoardProfile, get_board_profile

class TelemetryCollector:
    def __init__(self, board_id: str = "arduino_uno", run_id: str = "ARIS-2026-000001"):
        self.board: BoardProfile = get_board_profile(board_id)
        self.run_id: str = run_id
        self.sequence: int = 1

    def set_run_id(self, run_id: str):
        self.run_id = run_id

    def set_board(self, board_id: str):
        self.board = get_board_profile(board_id)

    def create_sample(
        self,
        metric: str,
        value: float,
        timestamp_ms: Optional[int] = None,
        custom_classification: Optional[str] = None,
        custom_confidence: Optional[float] = None
    ) -> TelemetrySample:
        if metric not in CANONICAL_METRIC_NAMES:
            raise ValueError(f"Metric '{metric}' is not canonical")

        ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
        meta = METRIC_METADATA[metric]
        classification = custom_classification or meta["classification"]
        confidence = custom_confidence if custom_confidence is not None else meta["confidence"]

        sample = TelemetrySample(
            protocol_version=PROTOCOL_VERSION,
            run_id=self.run_id,
            board_id=self.board.board_id,
            mcu=self.board.mcu,
            timestamp_ms=ts,
            sequence=self.sequence,
            metric=metric,
            value=float(value),
            unit=meta["unit"],
            classification=classification,
            confidence=confidence
        )
        self.sequence += 1
        return sample

    def create_batch_from_dict(
        self,
        metrics: Dict[str, float],
        timestamp_ms: Optional[int] = None
    ) -> List[TelemetrySample]:
        ts = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
        samples = []
        for metric, val in metrics.items():
            if metric in CANONICAL_METRIC_NAMES:
                samples.append(self.create_sample(metric, val, timestamp_ms=ts))
        return samples
