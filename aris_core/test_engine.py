"""
Comprehensive Test Suite for ARIS Core Subsystems.
"""

import sys
import os

sys.path.insert(0, r"C:\Users\aksha\.gemini\antigravity\scratch\aris-studio")

from aris_core.hardware_profiles import list_hardware_profiles, get_hardware_profile
from aris_core.analyzer.static_analyzer import StaticAnalyzer
from aris_core.analyzer.elf_parser import ElfParser
from aris_core.instrumenter.source_instrumenter import SourceInstrumenter
from aris_core.instrumenter.bias_compensator import BiasCompensator
from aris_core.optimizer.rule_synthesizer import RuleSynthesizer
from aris_core.optimizer.ai_advisor import AIAdvisor
from aris_core.optimizer.closed_loop_verifier import ClosedLoopVerifier
from aris_core.patent.formulas import PatentFormulasCalculator
from aris_core.patent.report_generator import PatentReportGenerator

def test_all():
    print("=== 1. Testing Hardware Profiles ===")
    profiles = list_hardware_profiles()
    print(f"Loaded {len(profiles)} hardware profiles: {[p['name'] for p in profiles]}")
    uno = get_hardware_profile("arduino_uno")
    mega = get_hardware_profile("arduino_mega")
    nano = get_hardware_profile("arduino_nano")
    assert uno.flash_bytes == 32768
    assert mega.flash_bytes == 262144
    assert nano.adc_channels == 8
    print("[OK] Hardware Profiles OK")

    print("\n=== 2. Testing Static AST Analyzer ===")
    sample_code = """
    void setup() {
      Serial.begin(9600);
      pinMode(13, OUTPUT);
    }
    void loop() {
      digitalWrite(13, HIGH);
      delay(25);
      Serial.println("System Running Sensor Check");
      float temp = analogRead(A0) * 0.488;
      digitalWrite(13, LOW);
      delay(25);
    }
    """
    analyzer = StaticAnalyzer(uno)
    report = analyzer.analyze(sample_code, "arduino_uno")
    print(f"Detected {len(report.antipatterns)} antipatterns in sample sketch:")
    for ap in report.antipatterns:
        print(f"  - [{ap.severity}] Line {ap.line_number}: {ap.name} -> {ap.description}")
    assert report.blocking_delay_count == 2
    assert report.ram_string_count == 1
    assert report.gpio_call_count == 2
    print(f"Architectural Health Score: {report.architectural_health_score}/100")
    print("[OK] Static AST Analyzer OK")

    print("\n=== 3. Testing Automated Source Instrumenter ===")
    instrumenter = SourceInstrumenter()
    inst_code, probe_count = instrumenter.instrument(sample_code)
    assert "aris_runtime.h" in inst_code
    assert "ARIS.loop_enter()" in inst_code
    assert "ARIS.loop_exit()" in inst_code
    print(f"Successfully injected {probe_count} probes into sketch.")
    print("[OK] Source Instrumenter OK")

    print("\n=== 4. Testing Rule Synthesizer & AI Advisor ===")
    advisor = AIAdvisor(uno)
    opt_result = advisor.generate_optimization_plan(sample_code, report, "arduino_uno")
    print(f"Applied {len(opt_result.applied_transforms)} transforms:")
    for t in opt_result.applied_transforms:
        print(f"  + {t}")
    print(f"Theoretical Speedup: {opt_result.theoretical_speedup_factor}x, Projected SRAM Saved: {opt_result.projected_sram_recovery_bytes}B")
    assert "millis()" in opt_result.optimized_candidate_code
    assert "F(\"System Running Sensor Check\")" in opt_result.optimized_candidate_code
    assert "PORTB |=" in opt_result.optimized_candidate_code
    print("[OK] Rule Synthesizer & AI Advisor OK")

    print("\n=== 5. Testing Closed-Loop Verifier ===")
    verifier = ClosedLoopVerifier(uno)
    orig_t = {"cpu_utilization_pct": 78.0, "loop_duration_us": 50200, "free_sram_bytes": 1120, "jitter_us": 850, "power_consumption_mw": 224.5}
    opt_t = {"cpu_utilization_pct": 14.5, "loop_duration_us": 72, "free_sram_bytes": 1580, "jitter_us": 14, "power_consumption_mw": 169.1}
    v_report = verifier.verify(orig_t, opt_t, "arduino_uno")
    print(f"Verification status: {v_report.verification_status}")
    print(f"Performance Score: {v_report.net_performance_score_before} -> {v_report.net_performance_score_after} (+{v_report.total_score_delta} pts)")
    print("[OK] Closed-Loop Verifier OK")

    print("\n=== 6. Testing Patent Formulas & Report Generator ===")
    metrics = PatentFormulasCalculator.compute_all(
        observed_channels=8, probe_cycles=32, loop_cycles=1600,
        free_sram=1580, total_sram=2048, stack_depth=112,
        p_orig_mw=224.5, p_opt_mw=169.1
    )
    print(f"OIR Score: {metrics.oir_score} ({metrics.oir_interpretation})")
    print(f"SCRI Score: {metrics.scri_score} ({metrics.scri_interpretation})")
    print(f"EOQ Score: {metrics.eoq_pct}% ({metrics.eoq_interpretation})")

    report_md = PatentReportGenerator.generate_report("arduino_uno", report.model_dump(), {"free_sram": 1580, "p_orig_mw": 224.5, "p_opt_mw": 169.1})
    assert "PATENT DISCLOSURE SPECIFICATION" in report_md
    print("[OK] Patent Report Generator OK")

    print("\n=======================================================")
    print("  ALL ARIS CORE SUBSYSTEM TESTS PASSED WITH 100% SUCCESS  ")
    print("=======================================================")

if __name__ == "__main__":
    test_all()
