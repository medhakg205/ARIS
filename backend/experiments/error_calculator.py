"""
ARIS Prediction Error & Error Calculator.
Calculates:
- Signed Error (percentage points)
- Absolute Error (percentage points)
- Relative Percentage Error (%) with zero/near-zero denominator safety
- Directional Match
- Outlier Identification (variance/threshold rules)
"""

import uuid
from typing import Optional
from datetime import datetime, timezone
from backend.experiments.calibration_models import (
    PredictionRecord,
    MeasurementOutcome,
    PredictionError
)


class PredictionErrorCalculator:
    """
    Computes rigorous prediction error between predictions and physical measurements.
    """

    @classmethod
    def calculate(
        cls,
        prediction: PredictionRecord,
        outcome: MeasurementOutcome,
        outlier_threshold_pp: float = 25.0
    ) -> PredictionError:
        """
        Calculates PredictionError metrics without confusing percentage points with percent error.
        """
        pred_delta = prediction.predicted_delta_pct
        actual_delta = outcome.actual_delta_pct

        # Signed error in percentage points: (actual - predicted)
        # e.g., predicted -20%, actual -17% => error is +3 percentage points (under-predicted latency reduction)
        signed_err_pp = round(actual_delta - pred_delta, 3)
        abs_err_pp = round(abs(actual_delta - pred_delta), 3)

        # Relative percent error: |actual - predicted| / |predicted| * 100
        # Guard against zero or near-zero predicted delta (< 0.001)
        rel_err_pct: Optional[float] = None
        if abs(pred_delta) >= 0.01:
            rel_err_pct = round((abs(actual_delta - pred_delta) / abs(pred_delta)) * 100.0, 2)
        else:
            rel_err_pct = None

        # Directional match: both improved (delta < 0 for latency) or both regressed
        directional = (pred_delta < 0 and actual_delta < 0) or (pred_delta > 0 and actual_delta > 0) or (pred_delta == 0 and actual_delta == 0)

        # Outlier detection: explicit rule based on extreme error deviation
        is_outlier = False
        outlier_reason = None
        if abs_err_pp >= outlier_threshold_pp:
            is_outlier = True
            outlier_reason = f"Prediction error ({abs_err_pp:.1f} pp) exceeds outlier threshold ({outlier_threshold_pp:.1f} pp)"
        elif outcome.variance > 100.0:
            is_outlier = True
            outlier_reason = f"Measurement sample variance ({outcome.variance:.1f}) exceeds acceptable stability limits"

        err_id = f"PERR-{uuid.uuid4().hex[:8].upper()}"

        return PredictionError(
            error_id=err_id,
            prediction_id=prediction.prediction_id,
            outcome_id=outcome.outcome_id,
            target_metric=prediction.target_metric,
            predicted_delta_pct=pred_delta,
            actual_delta_pct=actual_delta,
            signed_error_pp=signed_err_pp,
            absolute_error_pp=abs_err_pp,
            relative_error_pct=rel_err_pct,
            directional_match=directional,
            is_outlier=is_outlier,
            outlier_reason=outlier_reason,
            created_at=datetime.now(timezone.utc).isoformat()
        )
