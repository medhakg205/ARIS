"""
ARIS Prediction Calibrator & Calibration Engine.
Calculates systematic prediction bias and updates confidence based on historical empirical evidence.
Never manufactures corrections when evidence is sparse.
"""

import uuid
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.experiments.calibration_models import (
    PredictionRecord,
    CalibrationMatchLevel,
    CalibrationQualityStatus,
    CalibrationQuality,
    CalibrationProvenance,
    ExperimentMemoryRecord
)
from backend.experiments.experiment_memory import ExperimentMemory
from backend.hardware.capability_graph import HardwareCapabilityGraph


class PredictionCalibrator:
    """
    Deterministic and explainable calibration engine.
    Estimates systematic prediction bias and updates confidence based on evidence quality.
    """

    @classmethod
    def evaluate_quality(
        cls,
        records: List[ExperimentMemoryRecord],
        match_level: CalibrationMatchLevel,
        target_metric: str,
        optimization_category: str
    ) -> CalibrationQuality:
        """
        Assesses the quality of historical calibration evidence.
        """
        count = len(records)
        q_id = f"QUAL-{uuid.uuid4().hex[:8].upper()}"

        if count == 0:
            return CalibrationQuality(
                quality_id=q_id,
                target_metric=target_metric,
                optimization_category=optimization_category,
                match_level=match_level,
                relevant_experiment_count=0,
                status=CalibrationQualityStatus.NO_EVIDENCE
            )

        errors_pp = [r.signed_error_pp for r in records]
        mean_abs_err = round(sum(abs(e) for e in errors_pp) / count, 2)
        signed_bias = round(sum(errors_pp) / count, 2)
        var_err = round(statistics.variance(errors_pp), 3) if count > 1 else 0.0

        # Assess consistency: lower variance => higher consistency
        consistency = max(0.0, min(1.0, round(1.0 - (var_err / 25.0), 2))) if var_err < 25.0 else 0.2

        # Status decision
        if count < 3:
            status = CalibrationQualityStatus.SPARSE
        elif var_err > 16.0:
            status = CalibrationQualityStatus.INCONSISTENT
        elif count >= 6 and match_level == CalibrationMatchLevel.MCU_SPECIFIC and var_err < 4.0:
            status = CalibrationQualityStatus.STRONG
        elif count >= 3 and consistency >= 0.7:
            status = CalibrationQualityStatus.SUPPORTED
        else:
            status = CalibrationQualityStatus.PRELIMINARY

        return CalibrationQuality(
            quality_id=q_id,
            target_metric=target_metric,
            optimization_category=optimization_category,
            match_level=match_level,
            relevant_experiment_count=count,
            mean_absolute_error_pp=mean_abs_err,
            signed_bias_pp=signed_bias,
            error_variance=var_err,
            consistency=consistency,
            status=status,
            last_updated=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def calibrate_prediction(
        cls,
        raw_prediction_delta_pct: float,
        target_metric: str,
        optimization_category: str,
        graph: HardwareCapabilityGraph,
        memory: ExperimentMemory,
        include_simulation: bool = False
    ) -> tuple[float, float, float, CalibrationQuality, Optional[CalibrationProvenance]]:
        """
        Calculates calibrated predicted delta and updated confidence interval.
        Returns (calibrated_delta_pct, lower_bound_pct, upper_bound_pct, CalibrationQuality, CalibrationProvenance).
        """
        match_level, records = memory.retrieve_hierarchical(
            graph=graph,
            optimization_category=optimization_category,
            target_metric=target_metric,
            include_simulation=include_simulation
        )

        quality = cls.evaluate_quality(records, match_level, target_metric, optimization_category)

        # If evidence is NO_EVIDENCE or SPARSE, do not manufacture corrections
        if quality.status in (CalibrationQualityStatus.NO_EVIDENCE, CalibrationQualityStatus.SPARSE):
            # Interval defaults to +/- 20% uncertainty around raw prediction
            margin = round(abs(raw_prediction_delta_pct) * 0.25, 2)
            lower = round(raw_prediction_delta_pct - margin, 2)
            upper = round(raw_prediction_delta_pct + margin, 2)
            return raw_prediction_delta_pct, lower, upper, quality, None

        # Apply systematic signed bias correction
        # e.g., if model predicted -20% and historical error was +2.5 pp (actual was -17.5%),
        # calibrated prediction becomes: raw_prediction + signed_bias
        bias_adjustment = quality.signed_bias_pp
        # Dampen adjustment if match_level is global or related category
        dampening = 1.0
        if match_level == CalibrationMatchLevel.ARCHITECTURE_LEVEL:
            dampening = 0.8
        elif match_level in (CalibrationMatchLevel.RELATED_CATEGORY, CalibrationMatchLevel.GLOBAL):
            dampening = 0.5

        applied_bias = round(bias_adjustment * dampening, 2)
        calibrated_delta = round(raw_prediction_delta_pct + applied_bias, 2)

        # Bounding interval based on historical mean absolute error
        uncertainty_half_width = max(1.5, round(quality.mean_absolute_error_pp * 1.2, 2))
        lower_bound = round(calibrated_delta - uncertainty_half_width, 2)
        upper_bound = round(calibrated_delta + uncertainty_half_width, 2)

        prov = CalibrationProvenance(
            calibrated_prediction_id=f"CPRED-{uuid.uuid4().hex[:8].upper()}",
            raw_predicted_delta_pct=raw_prediction_delta_pct,
            calibrated_predicted_delta_pct=calibrated_delta,
            applied_bias_correction_pp=applied_bias,
            match_level=match_level,
            contributing_memory_ids=[r.memory_id for r in records],
            quality_status=quality.status,
            explanation=(
                f"Calibrated by {applied_bias:+.2f} pp based on {quality.relevant_experiment_count} "
                f"{match_level.value} physical experiment(s) with mean absolute error {quality.mean_absolute_error_pp:.1f} pp."
            )
        )

        return calibrated_delta, lower_bound, upper_bound, quality, prov
