"""
ARIS Baseline Generation Engine.
Collects and aggregates multiple runtime telemetry samples to establish a defensible,
statistically sound performance baseline.
Calculates:
- Mean
- Median
- Minimum
- Maximum
- Variance
- Jitter
Constructs persistent BaselineRecord entities for use by the Experiment Engine.
"""

import math
import uuid
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.database.db_engine import DatabaseEngine
from backend.database.models import (
    BaselineRecord,
    BaselineMetricStats,
    TelemetryRecord,
    RunRecord
)
from backend.telemetry.telemetry_schema import CANONICAL_METRIC_NAMES, ArisException


class BaselineEngine:
    """
    Computes statistical performance baselines across canonical metrics from a run's telemetry.
    """

    def __init__(self, db: DatabaseEngine):
        self.db = db

    def generate_baseline(
        self,
        run_id: str,
        min_samples_required: int = 5
    ) -> BaselineRecord:
        """
        Gathers all telemetry recorded for a given run and calculates statistical metrics.
        Raises ARIS_VALIDATION_FAILED if insufficient samples exist.
        """
        run = self.db.get_run(run_id)
        if not run:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Run '{run_id}' not found for baseline computation.",
                details={"run_id": run_id},
                recoverable=False,
                status_code=404
            )

        samples = self.db.get_telemetry_by_run(run_id, limit=10000)
        if len(samples) < min_samples_required:
            raise ArisException(
                error_code="ARIS_VALIDATION_FAILED",
                message=f"Insufficient telemetry samples to establish baseline: {len(samples)} found, {min_samples_required} required.",
                details={"run_id": run_id, "sample_count": len(samples), "min_required": min_samples_required},
                recoverable=True,
                status_code=400
            )

        # Group samples by metric
        grouped: Dict[str, List[float]] = {m: [] for m in CANONICAL_METRIC_NAMES}
        start_ts = None
        end_ts = None

        for s in samples:
            if s.metric in grouped:
                grouped[s.metric].append(s.value)
            if start_ts is None or s.timestamp_ms < start_ts:
                start_ts = s.timestamp_ms
            if end_ts is None or s.timestamp_ms > end_ts:
                end_ts = s.timestamp_ms

        window_duration = (end_ts - start_ts) if (start_ts is not None and end_ts is not None) else 0

        # Calculate statistics for each metric that has samples
        computed_stats: Dict[str, BaselineMetricStats] = {}

        for metric_name, values in grouped.items():
            if not values:
                continue

            count = len(values)
            avg = float(statistics.mean(values))
            med = float(statistics.median(values))
            mn = float(min(values))
            mx = float(max(values))

            # Variance requires at least 2 points
            var = float(statistics.variance(values)) if count > 1 else 0.0

            # Calculate jitter (mean absolute delta between consecutive samples, or standard deviation)
            if count > 1:
                consecutive_deltas = [abs(values[i] - values[i - 1]) for i in range(1, count)]
                jitter_val = float(statistics.mean(consecutive_deltas))
            else:
                jitter_val = 0.0

            computed_stats[metric_name] = BaselineMetricStats(
                metric=metric_name,
                sample_count=count,
                mean=round(avg, 3),
                median=round(med, 3),
                minimum=round(mn, 3),
                maximum=round(mx, 3),
                variance=round(var, 4),
                jitter=round(jitter_val, 4)
            )

        baseline_id = f"BASE-{uuid.uuid4().hex[:8].upper()}"
        baseline_record = BaselineRecord(
            baseline_id=baseline_id,
            run_id=run_id,
            board_id=run.board_id,
            sample_window_ms=window_duration,
            metrics=computed_stats,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        # Save to database
        self.db.save_baseline(baseline_record)

        # Update run reference
        run.baseline_id = baseline_id
        self.db.save_run(run)

        return baseline_record
