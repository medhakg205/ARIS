"""
Unit tests for ARIS Static + Runtime Correlation Engine.
Verifies:
- Fusing static delay(100) with live high loop_time -> runtime_correlation="HIGH"
- Elevation of confidence factors based on empirical convergence
- Generation of detailed empirical evidence dictionaries
"""

import pytest
from backend.analysis.rules import Finding, RULE_ARIS_001, RULE_ARIS_002, RULE_ARIS_009
from backend.database.models import BaselineRecord, BaselineMetricStats
from backend.correlation.correlation_engine import CorrelationEngine


def test_correlate_blocking_delay_with_high_loop_time():
    """Verify static delay(100) + runtime loop_time of 102.4ms produces HIGH correlation."""
    static_finding = Finding(
        finding_id="FIND-001-1",
        rule_id=RULE_ARIS_001,
        severity="CRITICAL",
        title="Blocking delay detected",
        description="delay(100) blocks execution",
        source_file="main.ino",
        source_line=42,
        runtime_correlation="NONE",
        confidence=0.88,
        evidence={"call": "delay(100)", "duration": 100, "unit": "ms"},
        recommended_action="Use millis()"
    )

    baseline = BaselineRecord(
        baseline_id="BASE-001",
        run_id="ARIS-001",
        board_id="arduino_uno",
        sample_window_ms=5000,
        metrics={
            "loop_time": BaselineMetricStats(
                metric="loop_time", sample_count=50, mean=102.4, median=102.1,
                minimum=100.8, maximum=105.2, variance=1.2, jitter=0.4
            ),
            "loop_frequency": BaselineMetricStats(
                metric="loop_frequency", sample_count=50, mean=9.76, median=9.79,
                minimum=9.5, maximum=9.9, variance=0.01, jitter=0.02
            )
        }
    )

    correlated = CorrelationEngine.correlate([static_finding], baseline)
    assert len(correlated) == 1
    c = correlated[0]
    assert c.runtime_correlation == "HIGH"
    assert c.confidence >= 0.95
    assert "runtime_loop_time_mean_ms" in c.evidence
    assert c.evidence["runtime_loop_time_mean_ms"] == 102.4


def test_correlate_memory_pressure():
    """Verify static memory allocation + high sram_used yields HIGH correlation."""
    static_finding = Finding(
        finding_id="FIND-009-1",
        rule_id=RULE_ARIS_009,
        severity="HIGH",
        title="Memory pressure",
        description="String usage",
        source_file="main.ino",
        source_line=10,
        runtime_correlation="NONE",
        confidence=0.85,
        evidence={"call": "String msg"},
        recommended_action="Use char array"
    )

    baseline = BaselineRecord(
        baseline_id="BASE-002",
        run_id="ARIS-002",
        board_id="arduino_uno",
        sample_window_ms=3000,
        metrics={
            "sram_used": BaselineMetricStats(
                metric="sram_used", sample_count=30, mean=1930.0, median=1930.0,
                minimum=1920.0, maximum=1940.0, variance=5.0, jitter=2.0
            ),
            "sram_free": BaselineMetricStats(
                metric="sram_free", sample_count=30, mean=118.0, median=118.0,
                minimum=108.0, maximum=128.0, variance=5.0, jitter=2.0
            )
        }
    )

    correlated = CorrelationEngine.correlate([static_finding], baseline)
    c = correlated[0]
    assert c.runtime_correlation in ["HIGH", "CRITICAL"]
    assert c.confidence > 0.90
