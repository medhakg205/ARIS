"""
ARIS Static + Runtime Correlation Engine.
Fuses static structural firmware findings with live empirical runtime telemetry.
Calculates explicit correlation confidence and elevates diagnostic certainty.
Transforms generic code warnings into empirically validated embedded bottlenecks.
"""

from typing import List, Dict, Any, Optional
from backend.analysis.rules import Finding, RULE_ARIS_001, RULE_ARIS_002, RULE_ARIS_003, RULE_ARIS_004, RULE_ARIS_005, RULE_ARIS_006, RULE_ARIS_007, RULE_ARIS_008, RULE_ARIS_009, RULE_ARIS_010
from backend.database.models import BaselineRecord, BaselineMetricStats, FindingRecord


class CorrelationEngine:
    """
    Correlates static AST/binary findings against runtime baseline performance metrics.
    """

    @staticmethod
    def correlate(
        static_findings: List[Finding],
        baseline: BaselineRecord
    ) -> List[Finding]:
        """
        Takes static analysis findings and correlates each against the measured baseline statistics.
        Returns updated findings with runtime_correlation ("HIGH", "MEDIUM", "LOW", "NONE"),
        adjusted confidence scores (0.0 to 1.0), and combined empirical evidence.
        """
        correlated_findings: List[Finding] = []
        metrics = baseline.metrics

        # Extract primary runtime metrics with fallbacks
        loop_time_mean = metrics["loop_time"].mean if "loop_time" in metrics else 0.0
        loop_freq_mean = metrics["loop_frequency"].mean if "loop_frequency" in metrics else 0.0
        loop_jitter_mean = metrics["loop_jitter"].mean if "loop_jitter" in metrics else 0.0
        cpu_load_mean = metrics["cpu_load"].mean if "cpu_load" in metrics else 0.0
        sram_free_mean = metrics["sram_free"].mean if "sram_free" in metrics else 2048.0
        sram_used_mean = metrics["sram_used"].mean if "sram_used" in metrics else 0.0
        stack_used_mean = metrics["stack_used"].mean if "stack_used" in metrics else 0.0
        isr_rate_mean = metrics["interrupt_rate"].mean if "interrupt_rate" in metrics else 0.0
        uart_act_mean = metrics["uart_activity"].mean if "uart_activity" in metrics else 0.0
        gpio_act_mean = metrics["gpio_activity"].mean if "gpio_activity" in metrics else 0.0

        for f in static_findings:
            corr_level = "NONE"
            conf = f.confidence
            evidence = dict(f.evidence)
            desc = f.description
            rec = f.recommended_action

            # -----------------------------------------------------------------
            # Correlation 1: ARIS-001 (Blocking Delay)
            # -----------------------------------------------------------------
            if f.rule_id == RULE_ARIS_001:
                static_delay_ms = evidence.get("duration", 0)
                if evidence.get("unit") == "us":
                    static_delay_ms /= 1000.0

                # Check if observed loop_time matches or exceeds static delay
                if loop_time_mean >= (static_delay_ms * 0.9):
                    corr_level = "HIGH"
                    conf = min(0.99, conf + 0.10)
                    pct_contribution = min(100.0, round((static_delay_ms / max(0.001, loop_time_mean)) * 100, 1))
                    evidence.update({
                        "runtime_loop_time_mean_ms": loop_time_mean,
                        "runtime_loop_frequency_hz": loop_freq_mean,
                        "delay_time_contribution_pct": pct_contribution
                    })
                    desc = (
                        f"Static blocking delay of {static_delay_ms}ms empirically correlated with measured "
                        f"loop duration of {loop_time_mean}ms. Delay directly accounts for {pct_contribution}% of loop time."
                    )
                    rec = "Replace delay() with non-blocking millis() timer state machine to recover loop frequency."
                elif loop_time_mean > 0:
                    corr_level = "LOW"
                    evidence["runtime_loop_time_mean_ms"] = loop_time_mean

            # -----------------------------------------------------------------
            # Correlation 2: ARIS-002 (Excessive Serial Logging)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_002:
                if uart_act_mean > 10.0 and loop_time_mean > 2.0:
                    corr_level = "HIGH"
                    conf = min(0.97, conf + 0.12)
                    evidence.update({
                        "runtime_uart_bytes_sec": uart_act_mean,
                        "runtime_loop_time_ms": loop_time_mean
                    })
                    desc = (
                        f"Serial logging in loop is saturating hardware UART (observed {uart_act_mean} bytes/epoch), "
                        f"introducing UART TX buffer blocking overhead."
                    )

            # -----------------------------------------------------------------
            # Correlation 3: ARIS-003 (Excessive Polling)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_003:
                if cpu_load_mean > 70.0 and gpio_act_mean > 50:
                    corr_level = "HIGH"
                    conf = min(0.95, conf + 0.10)
                    evidence.update({
                        "runtime_cpu_load_pct": cpu_load_mean,
                        "runtime_gpio_activity": gpio_act_mean
                    })
                    desc = f"Busy polling loop correlates with elevated CPU execution load ({cpu_load_mean}%)."

            # -----------------------------------------------------------------
            # Correlation 4: ARIS-004 (Large Local Allocation)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_004:
                alloc_bytes = evidence.get("allocated_bytes", 0)
                if stack_used_mean > alloc_bytes or (sram_free_mean < 300):
                    corr_level = "HIGH"
                    conf = min(0.98, conf + 0.12)
                    evidence.update({
                        "runtime_stack_used_bytes": stack_used_mean,
                        "runtime_sram_free_bytes": sram_free_mean
                    })
                    desc = (
                        f"Local stack allocation of {alloc_bytes}B correlates with observed stack depth of "
                        f"{stack_used_mean}B (free SRAM margin: {sram_free_mean}B)."
                    )

            # -----------------------------------------------------------------
            # Correlation 5: ARIS-005 (High Loop Jitter)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_005:
                if loop_jitter_mean > (0.15 * max(0.1, loop_time_mean)):
                    corr_level = "HIGH"
                    conf = min(0.96, conf + 0.14)
                    evidence.update({
                        "runtime_jitter_ms": loop_jitter_mean,
                        "runtime_loop_time_ms": loop_time_mean
                    })
                    desc = f"Branch timing variances empirically confirmed: measured timing jitter of {loop_jitter_mean}ms."

            # -----------------------------------------------------------------
            # Correlation 6: ARIS-006 (High Interrupt Frequency)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_006:
                if isr_rate_mean > 1500.0:
                    corr_level = "HIGH"
                    conf = min(0.96, conf + 0.15)
                    evidence.update({"runtime_interrupt_rate_hz": isr_rate_mean})
                    desc = f"Active ISR correlates with measured interrupt firing rate of {isr_rate_mean} Hz."

            # -----------------------------------------------------------------
            # Correlation 7: ARIS-007 (Redundant GPIO Activity)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_007:
                if gpio_act_mean > 100.0:
                    corr_level = "HIGH"
                    conf = min(0.93, conf + 0.10)
                    evidence.update({"runtime_gpio_toggles_sec": gpio_act_mean})
                    desc = f"Repeated GPIO writes confirmed: {gpio_act_mean} pin operations recorded per window."

            # -----------------------------------------------------------------
            # Correlation 8: ARIS-008 (Repeated Computation)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_008:
                if cpu_load_mean > 60.0 and loop_time_mean > 1.0:
                    corr_level = "HIGH"
                    conf = min(0.92, conf + 0.10)
                    evidence.update({"runtime_cpu_load_pct": cpu_load_mean, "runtime_loop_time_ms": loop_time_mean})
                    desc = f"Floating point math execution load confirmed: CPU load is {cpu_load_mean}%."

            # -----------------------------------------------------------------
            # Correlation 9: ARIS-009 (Memory Pressure)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_009:
                if sram_free_mean < 256.0 or (sram_used_mean > 1600.0):
                    corr_level = "CRITICAL" if sram_free_mean < 128.0 else "HIGH"
                    conf = min(0.99, conf + 0.15)
                    evidence.update({
                        "runtime_sram_free_bytes": sram_free_mean,
                        "runtime_sram_used_bytes": sram_used_mean
                    })
                    desc = f"Severe memory pressure confirmed: remaining free SRAM is only {sram_free_mean} bytes."

            # -----------------------------------------------------------------
            # Correlation 10: ARIS-010 (Long Critical Section)
            # -----------------------------------------------------------------
            elif f.rule_id == RULE_ARIS_010:
                if loop_jitter_mean > 5.0:
                    corr_level = "HIGH"
                    conf = min(0.94, conf + 0.10)
                    evidence.update({"runtime_jitter_ms": loop_jitter_mean})
                    desc = f"Interrupt locking correlates with observed timing disruption and jitter ({loop_jitter_mean}ms)."

            # Construct updated finding with correlation
            updated_finding = Finding(
                finding_id=f.finding_id,
                rule_id=f.rule_id,
                severity=f.severity,
                title=f.title,
                description=desc,
                source_file=f.source_file,
                source_line=f.source_line,
                runtime_correlation=corr_level,
                confidence=round(conf, 2),
                evidence=evidence,
                recommended_action=rec
            )
            correlated_findings.append(updated_finding)

        return correlated_findings
