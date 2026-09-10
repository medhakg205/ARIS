"""
ARIS Validation Engine.
Compares measured BASELINE performance against optimization CANDIDATE performance.
Evaluates the 8 canonical validation metrics:
- cpu_load
- loop_time
- loop_jitter
- sram_used
- stack_used
- interrupt_rate
- runtime_fault
- instrumentation_overhead
Returns baseline, candidate, difference, percentage_change, validation_status, and engineering reason.
Canonical validation statuses:
- VALIDATED
- PARTIALLY_VALIDATED
- NO_SIGNIFICANT_CHANGE
- REGRESSION
- REJECTED
- INCONCLUSIVE
"""

from typing import Dict, Any, Set, Optional
from pydantic import BaseModel
from backend.database.models import BaselineRecord, ValidationMetricDelta, ValidationResultRecord

# The 8 canonical validation comparison metrics mandated by specification
VALIDATION_METRIC_NAMES = [
    "cpu_load",
    "loop_time",
    "loop_jitter",
    "sram_used",
    "stack_used",
    "interrupt_rate",
    "runtime_fault",
    "instrumentation_overhead"
]

CANONICAL_VALIDATION_STATUSES: Set[str] = {
    "VALIDATED",
    "PARTIALLY_VALIDATED",
    "NO_SIGNIFICANT_CHANGE",
    "REGRESSION",
    "REJECTED",
    "INCONCLUSIVE"
}


class ValidationReport(BaseModel):
    """
    Standard output payload for closed-loop validation comparisons.
    """
    validation_id: str
    experiment_id: str
    baseline: Dict[str, float]
    candidate: Dict[str, float]
    difference: Dict[str, float]
    percentage_change: Dict[str, float]
    validation_status: str
    reason: str


class ValidationEngine:
    """
    Empirical comparator analyzing delta changes between baseline and candidate benchmarks.
    """

    @staticmethod
    def validate_benchmarks(
        baseline_record: BaselineRecord,
        candidate_record: BaselineRecord,
        validation_id: str,
        experiment_id: str
    ) -> ValidationReport:
        """
        Executes formal empirical comparison across all 8 canonical validation metrics.
        Computes differences and percentage changes, determines status, and provides rationale.
        """
        base_vals: Dict[str, float] = {}
        cand_vals: Dict[str, float] = {}
        diffs: Dict[str, float] = {}
        pct_changes: Dict[str, float] = {}

        improvements_count = 0
        regressions_count = 0
        neutral_count = 0

        # Check for any runtime faults
        base_faults = baseline_record.metrics.get("runtime_fault", None)
        cand_faults = candidate_record.metrics.get("runtime_fault", None)
        has_new_runtime_fault = False
        if cand_faults and cand_faults.maximum > 0:
            if not base_faults or cand_faults.maximum > base_faults.maximum:
                has_new_runtime_fault = True

        for metric in VALIDATION_METRIC_NAMES:
            b_stat = baseline_record.metrics.get(metric)
            c_stat = candidate_record.metrics.get(metric)

            # Extract mean or default 0.0
            b_val = b_stat.mean if b_stat else 0.0
            c_val = c_stat.mean if c_stat else 0.0

            base_vals[metric] = b_val
            cand_vals[metric] = c_val

            diff = round(c_val - b_val, 4)
            diffs[metric] = diff

            if abs(b_val) > 0.0001:
                pct = round(((c_val - b_val) / abs(b_val)) * 100, 2)
            else:
                pct = 0.0 if abs(c_val) < 0.0001 else 100.0
            pct_changes[metric] = pct

            # Determine whether lower or higher is better
            # For latency, jitter, load, sram, stack, faults, overhead: LOWER is better
            # For throughput/frequency (if compared): HIGHER is better
            is_improvement = False
            is_regression = False

            if metric in ["cpu_load", "loop_time", "loop_jitter", "runtime_fault", "instrumentation_overhead"]:
                if pct <= -3.0:
                    is_improvement = True
                elif pct >= 5.0:
                    is_regression = True
            elif metric in ["sram_used", "stack_used"]:
                # SRAM memory savings
                if diff <= -1:
                    is_improvement = True
                elif diff >= 16:  # Growth in memory usage
                    is_regression = True
            elif metric == "interrupt_rate":
                # Significant unrequested increase in interrupt rate is considered regression
                if pct >= 50.0:
                    is_regression = True
                elif pct <= -10.0:
                    is_improvement = True

            if is_improvement:
                improvements_count += 1
            elif is_regression:
                regressions_count += 1
            else:
                neutral_count += 1

        # Determine validation status based on empirical outcome
        if has_new_runtime_fault:
            status = "REGRESSION"
            reason = "Runtime faults detected in optimization candidate execution."
        elif regressions_count >= 2:
            status = "REGRESSION"
            reason = f"Performance regressed across {regressions_count} canonical metrics."
        elif improvements_count >= 2 and regressions_count == 0:
            status = "VALIDATED"
            reason = f"Empirical confirmation: significant improvements observed across {improvements_count} metrics with zero regressions."
        elif improvements_count >= 1 and regressions_count == 0:
            status = "PARTIALLY_VALIDATED"
            reason = f"Partial improvement observed in {improvements_count} metric(s) without hardware regressions."
        elif neutral_count >= 6 and improvements_count == 0:
            status = "NO_SIGNIFICANT_CHANGE"
            reason = "Observed deltas remain within the statistical noise margin (< 3%)."
        else:
            status = "INCONCLUSIVE"
            reason = "Metric variances do not allow a conclusive validation decision."

        return ValidationReport(
            validation_id=validation_id,
            experiment_id=experiment_id,
            baseline=base_vals,
            candidate=cand_vals,
            difference=diffs,
            percentage_change=pct_changes,
            validation_status=status,
            reason=reason
        )
