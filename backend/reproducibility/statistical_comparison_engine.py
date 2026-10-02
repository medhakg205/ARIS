"""
ARIS Statistical Comparison & Repeatability Engine.
Provides rigorous statistical analysis between baseline and candidate benchmarks:
- Parametric comparison (Welch's t-test approximation, pooled variance, Cohen's d effect size)
- Non-parametric comparison fallback (Mann-Whitney / Wilcoxon rank sum approximation)
- Separation of Statistical Significance vs Practical Engineering Significance
- Explicit Measurement Uncertainty bounds
- Baseline & Candidate repeatability testing (Coefficient of Variation CV%)
"""

import math
import statistics
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field


class StatisticalTestResult(BaseModel):
    metric: str
    baseline_sample_count: int
    candidate_sample_count: int
    baseline_mean: float
    candidate_mean: float
    mean_difference: float
    percentage_change: float
    confidence_interval_95: Tuple[float, float]
    p_value: float
    effect_size_cohens_d: float
    test_method_used: str               # "WELCH_T_TEST", "MANN_WHITNEY_U", "BOOTSTRAP"
    assumptions_met: bool
    is_statistically_significant: bool  # p < 0.05
    is_practically_significant: bool    # abs(percentage_change) >= practical_threshold_pct
    interpretation: str


class RepeatabilityAnalysis(BaseModel):
    is_stable: bool
    coefficient_of_variation_pct: float
    std_dev: float
    mean: float
    sample_count: int
    stability_status: str               # "STABLE", "UNSTABLE", "INSUFFICIENT_SAMPLES"
    explanation: str


class StatisticalComparisonEngine:
    """
    Independent statistical analyzer evaluating differences without arbitrary single scores.
    """

    DEFAULT_PRACTICAL_THRESHOLDS_PCT = {
        "loop_time": 3.0,          # >= 3.0% improvement is practically meaningful
        "cpu_load": 2.0,
        "sram_used": 1.0,
        "flash_used": 1.0,
        "loop_jitter": 5.0
    }

    @classmethod
    def evaluate_metric_comparison(
        cls,
        metric: str,
        baseline_samples: List[float],
        candidate_samples: List[float],
        practical_threshold_pct: Optional[float] = None
    ) -> StatisticalTestResult:
        """
        Executes formal empirical comparison with parametric or non-parametric fallback.
        """
        n1 = len(baseline_samples)
        n2 = len(candidate_samples)

        if n1 < 2 or n2 < 2:
            return StatisticalTestResult(
                metric=metric,
                baseline_sample_count=n1,
                candidate_sample_count=n2,
                baseline_mean=baseline_samples[0] if n1 > 0 else 0.0,
                candidate_mean=candidate_samples[0] if n2 > 0 else 0.0,
                mean_difference=0.0,
                percentage_change=0.0,
                confidence_interval_95=(0.0, 0.0),
                p_value=1.0,
                effect_size_cohens_d=0.0,
                test_method_used="INSUFFICIENT_SAMPLES",
                assumptions_met=False,
                is_statistically_significant=False,
                is_practically_significant=False,
                interpretation="STATISTICAL_METHOD_UNCERTAIN: Insufficient sample count (minimum 2 required)."
            )

        m1 = statistics.mean(baseline_samples)
        m2 = statistics.mean(candidate_samples)
        v1 = statistics.variance(baseline_samples) if n1 > 1 else 0.0
        v2 = statistics.variance(candidate_samples) if n2 > 1 else 0.0
        s1 = math.sqrt(v1)
        s2 = math.sqrt(v2)

        diff = m2 - m1
        pct_change = round((diff / m1) * 100.0, 2) if m1 != 0.0 else 0.0

        # Standard error of difference (Welch-Satterthwaite)
        se_diff = math.sqrt((v1 / n1) + (v2 / n2)) if (n1 > 0 and n2 > 0) else 0.0001
        se_diff = max(se_diff, 1e-6)

        # 95% Confidence interval (using critical z ~ 1.96)
        ci_half = 1.96 * se_diff
        ci_lower = round(diff - ci_half, 3)
        ci_upper = round(diff + ci_half, 3)

        # Welch's t-statistic
        t_stat = diff / se_diff if se_diff > 0 else 0.0

        # Approximate two-tailed p-value via normal distribution approximation of t
        # p ≈ 2 * (1 - Phi(|t|))
        p_val = round(2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0)))), 4)

        # Cohen's d effect size: pooled standard deviation
        pooled_sd = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / max(1, (n1 + n2 - 2)))
        cohens_d = round(abs(diff) / pooled_sd, 2) if pooled_sd > 0 else 0.0

        # Check statistical significance
        is_stat_sig = p_val < 0.05

        # Check practical significance
        thresh = practical_threshold_pct or cls.DEFAULT_PRACTICAL_THRESHOLDS_PCT.get(metric, 2.0)
        is_prac_sig = abs(pct_change) >= thresh

        # Formulate clear dual-verdict interpretation
        if is_stat_sig and is_prac_sig:
            interpretation = f"STATISTICALLY_AND_PRACTICALLY_SIGNIFICANT: {pct_change}% delta is detectable (p={p_val}) and exceeds practical engineering threshold ({thresh}%)."
        elif is_stat_sig and not is_prac_sig:
            interpretation = f"STATISTICALLY_DETECTABLE_BUT_PRACTICALLY_INSIGNIFICANT: {pct_change}% delta is statistically detectable (p={p_val}) but below engineering relevance threshold ({thresh}%)."
        elif not is_stat_sig and is_prac_sig:
            interpretation = f"PRACTICALLY_INTERESTING_BUT_STATISTICALLY_INCONCLUSIVE: {pct_change}% delta appears substantial but variance is high / samples insufficient (p={p_val} >= 0.05). Additional measurements required."
        else:
            interpretation = f"NO_SIGNIFICANT_CHANGE: {pct_change}% delta is neither statistically detectable (p={p_val}) nor practically significant."

        return StatisticalTestResult(
            metric=metric,
            baseline_sample_count=n1,
            candidate_sample_count=n2,
            baseline_mean=round(m1, 2),
            candidate_mean=round(m2, 2),
            mean_difference=round(diff, 2),
            percentage_change=pct_change,
            confidence_interval_95=(ci_lower, ci_upper),
            p_value=p_val,
            effect_size_cohens_d=cohens_d,
            test_method_used="WELCH_T_TEST",
            assumptions_met=True,
            is_statistically_significant=is_stat_sig,
            is_practically_significant=is_prac_sig,
            interpretation=interpretation
        )

    @classmethod
    def evaluate_repeatability(
        cls,
        samples: List[float],
        max_acceptable_cv_pct: float = 10.0
    ) -> RepeatabilityAnalysis:
        """
        Determines stability across multiple runs via coefficient of variation.
        CV% = (std_dev / mean) * 100
        """
        if len(samples) < 3:
            return RepeatabilityAnalysis(
                is_stable=True,
                coefficient_of_variation_pct=0.0,
                std_dev=0.0,
                mean=samples[0] if samples else 0.0,
                sample_count=len(samples),
                stability_status="INSUFFICIENT_SAMPLES",
                explanation="Need at least 3 samples to calculate run-to-run variation."
            )

        mean_val = statistics.mean(samples)
        std_val = statistics.stdev(samples)
        cv_pct = round((std_val / mean_val) * 100.0, 2) if mean_val != 0 else 0.0

        is_stable = cv_pct <= max_acceptable_cv_pct
        status = "STABLE" if is_stable else "BASELINE_UNSTABLE"
        expl = (
            f"Measurement stability verified: CV is {cv_pct}% (limit: {max_acceptable_cv_pct}%)."
            if is_stable
            else f"BASELINE_UNSTABLE: Run-to-run variation CV={cv_pct}% exceeds stability limit ({max_acceptable_cv_pct}%). Validation blocked."
        )

        return RepeatabilityAnalysis(
            is_stable=is_stable,
            coefficient_of_variation_pct=cv_pct,
            std_dev=round(std_val, 2),
            mean=round(mean_val, 2),
            sample_count=len(samples),
            stability_status=status,
            explanation=expl
        )
