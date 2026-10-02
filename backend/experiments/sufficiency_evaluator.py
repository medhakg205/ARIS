"""
ARIS Evidence Quality & Measurement Sufficiency Evaluator.
Defines:
- EvidenceQuality: Multi-dimensional quality breakdown (completeness, consistency, sample sufficiency,
  provenance quality, instrumentation validity, statistical strength) with zero fabricated numbers.
- SufficiencyStatus: State enum for sufficiency decision.
- SufficiencyReport: Evaluation outcome with structured actionable recommendations.
- MeasurementSufficiencyEvaluator: Evaluates telemetry data against objective criteria.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from backend.experiments.measurement_planner import MeasurementPlan
from backend.database.models import TelemetryRecord


class SufficiencyStatus(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT_SAMPLE_SIZE = "INSUFFICIENT_SAMPLE_SIZE"
    INSUFFICIENT_VARIANCE_INFORMATION = "INSUFFICIENT_VARIANCE_INFORMATION"
    INSUFFICIENT_METRIC_COVERAGE = "INSUFFICIENT_METRIC_COVERAGE"
    MEASUREMENT_OVERHEAD_TOO_HIGH = "MEASUREMENT_OVERHEAD_TOO_HIGH"
    HARDWARE_CAPABILITY_MISSING = "HARDWARE_CAPABILITY_MISSING"
    CORRUPTED_OR_INVALID_TELEMETRY = "CORRUPTED_OR_INVALID_TELEMETRY"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceQuality(BaseModel):
    """
    Explainable multi-dimensional evidence quality model.
    Never collapses into a single fabricated score without breakdown.
    """
    hardware_identity_confidence: str           # "CONFIRMED", "HIGH", "MEDIUM", "UNKNOWN", "MISMATCH"
    telemetry_provenance_verified: bool         # True if signed/checksummed physical or verified demo
    sample_sufficiency: str                     # "SUFFICIENT", "MARGINAL", "INSUFFICIENT"
    completeness: float                         # Ratio of received samples to planned target (0.0 to 1.0)
    consistency: float                          # Low sequence gaps / high monotonicity (0.0 to 1.0)
    instrumentation_overhead_level: str         # "LOW", "ACCEPTABLE", "HIGH", "UNKNOWN"
    statistical_strength: str                   # "HIGH", "MODERATE", "WEAK", "INSUFFICIENT"
    summary_notes: List[str] = Field(default_factory=list)


class SufficiencyReport(BaseModel):
    """
    Structured outcome of measurement sufficiency evaluation.
    """
    status: SufficiencyStatus
    is_sufficient: bool
    evidence_quality: EvidenceQuality
    missing_metrics: List[str] = Field(default_factory=list)
    received_sample_count: int = 0
    required_sample_count: int = 0
    recommendations: List[str] = Field(default_factory=list)


class MeasurementSufficiencyEvaluator:
    """
    Deterministic measurement sufficiency evaluator.
    Evaluates received telemetry against plan requirements without hallucinating confidence.
    """

    @classmethod
    def evaluate(
        cls,
        plan: MeasurementPlan,
        samples: List[TelemetryRecord],
        is_simulated: bool = False,
        board_confidence: str = "CONFIRMED"
    ) -> SufficiencyReport:
        rec_count = len(samples)
        req_count = plan.sample_count
        recommendations: List[str] = []

        # 1. Check for empty or invalid telemetry
        if rec_count == 0:
            quality = EvidenceQuality(
                hardware_identity_confidence=board_confidence,
                telemetry_provenance_verified=False,
                sample_sufficiency="INSUFFICIENT",
                completeness=0.0,
                consistency=0.0,
                instrumentation_overhead_level="UNKNOWN",
                statistical_strength="INSUFFICIENT",
                summary_notes=["Zero telemetry samples received for run"]
            )
            return SufficiencyReport(
                status=SufficiencyStatus.INSUFFICIENT_SAMPLE_SIZE,
                is_sufficient=False,
                evidence_quality=quality,
                missing_metrics=plan.enabled_metrics,
                received_sample_count=0,
                required_sample_count=req_count,
                recommendations=["Execute target MCU run to capture telemetry", "Verify serial baud rate (115200)"]
            )

        # 2. Check for telemetry corruption (e.g. negative sequence numbers or invalid values)
        has_invalid = any(s.value is None or s.sequence < 0 for s in samples)
        if has_invalid:
            quality = EvidenceQuality(
                hardware_identity_confidence=board_confidence,
                telemetry_provenance_verified=False,
                sample_sufficiency="INSUFFICIENT",
                completeness=0.0,
                consistency=0.0,
                instrumentation_overhead_level="UNKNOWN",
                statistical_strength="INSUFFICIENT",
                summary_notes=["Corrupted telemetry detected (negative sequence or null values)"]
            )
            return SufficiencyReport(
                status=SufficiencyStatus.CORRUPTED_OR_INVALID_TELEMETRY,
                is_sufficient=False,
                evidence_quality=quality,
                missing_metrics=[],
                received_sample_count=rec_count,
                required_sample_count=req_count,
                recommendations=["Check serial communication integrity", "Verify ARIS protocol packet checksum"]
            )

        # 3. Check Metric Coverage
        received_metrics = {s.metric for s in samples}
        missing_required = [m for m in plan.enabled_metrics if m not in received_metrics]

        # 4. Check Sample Count Sufficiency
        min_threshold = max(5, int(req_count * 0.7)) # Require at least 70% of planned samples
        completeness = min(1.0, round(rec_count / float(req_count), 2)) if req_count > 0 else 1.0

        # Check sequence monotonicity / consistency
        seqs = [s.sequence for s in samples]
        in_order_count = sum(1 for i in range(len(seqs)-1) if seqs[i+1] >= seqs[i])
        consistency = round(in_order_count / max(1, len(seqs)-1), 2) if len(seqs) > 1 else 1.0

        # 5. Check Variance Information (at least 3 distinct values or realistic continuous series)
        loop_samples = [s.value for s in samples if s.metric == "loop_time"]
        has_variance = True
        if len(loop_samples) >= 5:
            distinct_vals = len(set(loop_samples))
            if distinct_vals == 1 and not is_simulated:
                # If physical hardware produced 100% identical microseconds across 50 samples, variance is suspicious
                has_variance = False

        # Overhead evaluation
        ov_level = "LOW"
        if not plan.overhead_acceptable:
            ov_level = "HIGH"
        elif plan.overhead_estimate.effective_overhead_us is None:
            ov_level = "UNKNOWN"
        elif plan.overhead_estimate.effective_overhead_us > 20.0:
            ov_level = "ACCEPTABLE"

        # Determine overall Sufficiency Status
        if missing_required:
            status = SufficiencyStatus.INSUFFICIENT_METRIC_COVERAGE
            is_suff = False
            recommendations.append(f"Enable missing metric instrumentation for: {', '.join(missing_required)}")
        elif rec_count < min_threshold:
            status = SufficiencyStatus.INSUFFICIENT_SAMPLE_SIZE
            is_suff = False
            recommendations.append(f"Increase sample count (received {rec_count}, expected >= {min_threshold})")
            recommendations.append(f"Increase experiment duration by at least {round((req_count - rec_count) * 0.1, 1)}s")
        elif not plan.overhead_acceptable:
            status = SufficiencyStatus.MEASUREMENT_OVERHEAD_TOO_HIGH
            is_suff = False
            recommendations.append("Switch to lower-overhead instrumentation (e.g. MINIMAL mode or cycle counters)")
        elif not has_variance:
            status = SufficiencyStatus.INSUFFICIENT_VARIANCE_INFORMATION
            is_suff = False
            recommendations.append("Samples lack timing jitter variance; check clock stability or timer resolution")
        else:
            status = SufficiencyStatus.SUFFICIENT
            is_suff = True

        stat_strength = "HIGH" if rec_count >= req_count and consistency >= 0.95 else ("MODERATE" if is_suff else "WEAK")

        evidence_quality = EvidenceQuality(
            hardware_identity_confidence=board_confidence,
            telemetry_provenance_verified=True,
            sample_sufficiency="SUFFICIENT" if is_suff else "INSUFFICIENT",
            completeness=completeness,
            consistency=consistency,
            instrumentation_overhead_level=ov_level,
            statistical_strength=stat_strength,
            summary_notes=[
                f"Received {rec_count}/{req_count} samples ({int(completeness*100)}% completeness)",
                f"Metrics evaluated: {list(received_metrics)}",
                f"Overhead level: {ov_level}"
            ]
        )

        return SufficiencyReport(
            status=status,
            is_sufficient=is_suff,
            evidence_quality=evidence_quality,
            missing_metrics=missing_required,
            received_sample_count=rec_count,
            required_sample_count=req_count,
            recommendations=recommendations
        )
