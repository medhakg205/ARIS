"""
ARIS Adaptive Measurement Planner & Models.
Defines:
- MeasurementPlan: Execution plan specifying enabled/disabled metrics, sampling parameters,
  expected overhead, hardware requirements, and explicit rationale for each selection.
- HypothesisDiscriminationPlan: Plan determining differentiating measurements across competing hypotheses.
- AdaptiveMeasurementPlanner: Backend planner consuming HardwareCapabilityGraph, hypotheses,
  baseline statistics, uncertainty, and overhead to produce an optimal MeasurementPlan.
"""

from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from backend.hardware.capability_graph import HardwareCapabilityGraph
from backend.experiments.manifest_models import PerformanceHypothesis
from backend.experiments.overhead_models import (
    InstrumentationOverheadEstimate,
    InstrumentationOverheadEstimator,
    OverheadProvenance
)


class MeasurementPlan(BaseModel):
    """
    Detailed, hardware-aware measurement plan.
    Specifies which metrics are enabled/disabled and grounds every selection in hypothesis evidence.
    """
    plan_id: str
    target_board_id: str
    instrumentation_mode: str = "BALANCED"       # "MINIMAL", "BALANCED", "FULL"
    enabled_metrics: List[str]                  # Metrics actively recorded
    disabled_metrics: List[str]                 # Metrics intentionally omitted to save overhead
    metric_reasons: Dict[str, str] = Field(default_factory=dict) # "Why these measurements?"
    sampling_interval_ms: int = 100
    sample_count: int = 50
    duration_seconds: float = 10.0
    required_capabilities: List[str] = Field(default_factory=list)
    overhead_estimate: InstrumentationOverheadEstimate
    required_confidence: float = 0.80
    overhead_acceptable: bool = True
    overhead_warning: Optional[str] = None


class HypothesisDiscriminationPlan(BaseModel):
    """
    Plan to distinguish between competing hypotheses via targeted measurements.
    """
    hypotheses: List[PerformanceHypothesis]
    distinguishing_metrics: List[str]
    required_instrumentation: List[str]
    expected_evidence: Dict[str, str] = Field(default_factory=dict)
    unresolved_ambiguity: List[str] = Field(default_factory=list)


class AdaptiveMeasurementPlanner:
    """
    Adaptive measurement planner.
    Selects metrics based on hypothesis evidence, capability constraints, and overhead bounds.
    Does NOT use hardcoded board whitelists.
    """

    @classmethod
    def plan_measurement(
        cls,
        graph: HardwareCapabilityGraph,
        hypotheses: List[PerformanceHypothesis],
        baseline_stats: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> MeasurementPlan:
        constraints = constraints or {}
        max_overhead_ratio = constraints.get("max_overhead_ratio", 0.15) # Max 15% perturbation allowed
        requested_sample_count = constraints.get("sample_count", 50)
        requested_duration = constraints.get("duration_seconds", 10.0)

        # 1. Determine which metrics are required vs optional from hypotheses
        required_metrics: Set[str] = set()
        optional_metrics: Set[str] = set()
        metric_reasons: Dict[str, str] = {}

        for hyp in hypotheses:
            target_m = hyp.target_metric
            if target_m:
                required_metrics.add(target_m)
                metric_reasons[target_m] = f"Primary target for hypothesis '{hyp.hypothesis_id}': {hyp.predicted_effect}"

            # If evidence references jitter, interrupts, or memory, add them
            for ev_ref in hyp.evidence_references:
                ev_lower = ev_ref.lower()
                if "jitter" in ev_lower:
                    required_metrics.add("loop_jitter")
                    metric_reasons["loop_jitter"] = "Required to evaluate jitter variance in hypothesis evidence"
                if "interrupt" in ev_lower or "isr" in ev_lower:
                    required_metrics.add("interrupt_count")
                    metric_reasons["interrupt_count"] = "Required to evaluate interrupt interference"
                if "sram" in ev_lower or "ram" in ev_lower or "memory" in ev_lower:
                    required_metrics.add("sram_used")
                    metric_reasons["sram_used"] = "Required to evaluate memory footprint impact"

        # Baseline always tracks loop_time if not already added
        if not required_metrics:
            required_metrics.add("loop_time")
            metric_reasons["loop_time"] = "Default baseline execution latency tracking"

        # 2. Reconcile with target HardwareCapabilityGraph
        enabled_metrics: List[str] = []
        disabled_metrics: List[str] = []
        missing_capabilities: List[str] = []

        # Available pool on target
        avail_pool = set(graph.available_instrumentation)

        for m in sorted(required_metrics):
            if m in avail_pool:
                enabled_metrics.append(m)
            else:
                missing_capabilities.append(m)
                metric_reasons[m] = f"Disabled: requested by hypothesis but unsupported by target MCU architecture ({graph.architecture})"

        # Non-essential peripheral activities disabled to minimize measurement perturbation
        all_possible_metrics = [
            "loop_time", "loop_jitter", "loop_frequency",
            "cpu_load_timer_tick", "sram_used", "sram_free",
            "stack_high_water_mark", "gpio_activity", "adc_activity",
            "uart_activity", "spi_activity", "i2c_activity", "timer_activity"
        ]
        for m in all_possible_metrics:
            if m not in enabled_metrics and m in avail_pool:
                disabled_metrics.append(m)
                if m not in metric_reasons:
                    metric_reasons[m] = "Disabled: not required to resolve current hypothesis uncertainty; omitted to reduce overhead"

        # 3. Select measurement method & evaluate overhead
        arch = (graph.architecture or "").lower()
        if "arm" in arch and "dwt_cycle_counter" in avail_pool:
            method = "DWT_CYCCNT"
        elif "avr" in arch:
            method = "SOFTWARE_MICROS"
        else:
            method = "SOFTWARE_MILLIS"

        overhead = InstrumentationOverheadEstimator.estimate(graph, method=method, config="BALANCED")

        # 4. Overhead verification against baseline loop time (perturbation check)
        overhead_acceptable = True
        overhead_warning = None

        if baseline_stats and "loop_time" in baseline_stats:
            base_loop_us = baseline_stats["loop_time"].get("mean", 1000.0)
            if overhead.effective_overhead_us and base_loop_us > 0:
                overhead_ratio = overhead.effective_overhead_us / base_loop_us
                if overhead_ratio > max_overhead_ratio:
                    overhead_acceptable = False
                    overhead_warning = (
                        f"Measurement overhead ({overhead.effective_overhead_us:.2f}µs) is "
                        f"{overhead_ratio*100:.1f}% of baseline loop time ({base_loop_us:.2f}µs), "
                        f"exceeding max threshold ({max_overhead_ratio*100:.1f}%). "
                        "Measurement would significantly perturb target execution."
                    )

        # 5. Check memory constraints (e.g. low SRAM)
        if graph.sram_memory.available and graph.sram_memory.value:
            total_sram = graph.sram_memory.value
            if total_sram <= 1024 and overhead.sram_overhead_bytes >= 64:
                # Tighten metrics to avoid SRAM exhaustion
                overhead_warning = (overhead_warning or "") + f" SRAM is severely constrained ({total_sram}B). Minimal instrumentation required."

        import uuid
        plan_id = f"MPLAN-{uuid.uuid4().hex[:8].upper()}"

        return MeasurementPlan(
            plan_id=plan_id,
            target_board_id=graph.board_id,
            instrumentation_mode="MINIMAL" if not overhead_acceptable or len(enabled_metrics) <= 2 else "BALANCED",
            enabled_metrics=enabled_metrics,
            disabled_metrics=disabled_metrics,
            metric_reasons=metric_reasons,
            sampling_interval_ms=100,
            sample_count=requested_sample_count,
            duration_seconds=requested_duration,
            required_capabilities=list(enabled_metrics),
            overhead_estimate=overhead,
            required_confidence=0.85,
            overhead_acceptable=overhead_acceptable,
            overhead_warning=overhead_warning
        )

    @classmethod
    def plan_discrimination(
        cls,
        graph: HardwareCapabilityGraph,
        competing_hypotheses: List[PerformanceHypothesis]
    ) -> HypothesisDiscriminationPlan:
        """
        Builds a discrimination plan between multiple competing performance hypotheses.
        """
        all_metrics: Set[str] = set()
        expected_evidence: Dict[str, str] = {}

        for h in competing_hypotheses:
            all_metrics.add(h.target_metric)
            for ev in h.evidence_references:
                ev_l = ev.lower()
                if "jitter" in ev_l:
                    all_metrics.add("loop_jitter")
                if "interrupt" in ev_l:
                    all_metrics.add("interrupt_count")
                if "sram" in ev_l or "ram" in ev_l:
                    all_metrics.add("sram_used")

            expected_evidence[h.hypothesis_id] = (
                f"Hypothesis '{h.hypothesis_id}' predicts impact on {h.target_metric}: {h.predicted_effect}"
            )

        # Determine distinguishing metrics supported by hardware
        avail_pool = set(graph.available_instrumentation)
        distinguishing = [m for m in sorted(all_metrics) if m in avail_pool]
        unresolved = [m for m in sorted(all_metrics) if m not in avail_pool]

        return HypothesisDiscriminationPlan(
            hypotheses=competing_hypotheses,
            distinguishing_metrics=distinguishing,
            required_instrumentation=distinguishing,
            expected_evidence=expected_evidence,
            unresolved_ambiguity=[f"Hardware lacks instrumentation for '{m}'" for m in unresolved]
        )
