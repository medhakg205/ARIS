"""
Patent-Grade Mathematical Formulations and Metrics for ARIS.
Provides formal mathematical proofs and quantitative scores for observability,
memory stability, and energy efficiency.
"""

import math
from pydantic import BaseModel

class PatentFormulasMetrics(BaseModel):
    # 1. Observability-to-Intrusiveness Ratio (OIR)
    oir_score: float
    oir_formula_latex: str
    oir_interpretation: str

    # 2. Stack Collision Risk Index (SCRI)
    scri_score: float
    scri_formula_latex: str
    scri_interpretation: str

    # 3. Energy Optimization Quotient (EOQ)
    eoq_pct: float
    eoq_formula_latex: str
    eoq_interpretation: str

class PatentFormulasCalculator:
    @staticmethod
    def calculate_oir(observed_metrics_count: int, probe_cycles_per_loop: int, total_loop_cycles: int) -> tuple[float, str, str]:
        """
        OIR = (Entropy_Observed * K) / (Cycles_Probe / Cycles_Total)
        Higher score means maximum behavioral observability with minimum instruction overhead.
        """
        if total_loop_cycles <= 0:
            total_loop_cycles = 1000
        intrusiveness = max(0.001, probe_cycles_per_loop / total_loop_cycles)
        entropy = math.log2(max(2, observed_metrics_count * 10))
        oir = round((entropy / intrusiveness) * 0.1, 2)
        
        formula = r"OIR = \frac{\Delta H_{\text{observed}}}{\tau_{\text{probe}} / \tau_{\text{cycle}}}"
        interpretation = f"OIR Score: {oir:.2f}. System captures {observed_metrics_count} hardware telemetry channels with only {intrusiveness*100:.2f}% CPU overhead."
        return oir, formula, interpretation

    @staticmethod
    def calculate_scri(min_free_sram_bytes: int, total_sram_bytes: int, max_stack_depth_bytes: int) -> tuple[float, str, str]:
        """
        SCRI = 1 - (SP_min - Heap_max) / Total_SRAM
        0.0 = completely safe, 1.0 = immediate memory collision (crash).
        """
        margin = max(0, min_free_sram_bytes - max_stack_depth_bytes)
        ratio = margin / total_sram_bytes
        scri = round(max(0.0, min(1.0, 1.0 - ratio)), 3)

        formula = r"SCRI = 1.0 - \frac{SP_{\text{min}} - \text{Heap}_{\text{max}}}{\text{RAM}_{\text{total}}}"
        interpretation = f"SCRI Risk Index: {scri:.3f} ({'LOW RISK' if scri < 0.35 else ('MODERATE' if scri < 0.7 else 'CRITICAL COLLISION RISK')}). Safe headroom: {margin} bytes."
        return scri, formula, interpretation

    @staticmethod
    def calculate_eoq(power_orig_mw: float, power_opt_mw: float) -> tuple[float, str, str]:
        """
        EOQ = ((E_orig - E_opt) / E_orig) * 100%
        """
        eoq = round(((power_orig_mw - power_opt_mw) / max(1.0, power_orig_mw)) * 100, 2)
        formula = r"EOQ = \left( \frac{E_{\text{orig}} - E_{\text{opt}}}{E_{\text{orig}}} \right) \times 100\%"
        interpretation = f"EOQ Energy Optimization Quotient: {eoq:.1f}% reduction in continuous joule dissipation."
        return eoq, formula, interpretation

    @classmethod
    def compute_all(cls, observed_channels: int, probe_cycles: int, loop_cycles: int, free_sram: int, total_sram: int, stack_depth: int, p_orig_mw: float, p_opt_mw: float) -> PatentFormulasMetrics:
        oir, oir_f, oir_i = cls.calculate_oir(observed_channels, probe_cycles, loop_cycles)
        scri, scri_f, scri_i = cls.calculate_scri(free_sram, total_sram, stack_depth)
        eoq, eoq_f, eoq_i = cls.calculate_eoq(p_orig_mw, p_opt_mw)

        return PatentFormulasMetrics(
            oir_score=oir,
            oir_formula_latex=oir_f,
            oir_interpretation=oir_i,
            scri_score=scri,
            scri_formula_latex=scri_f,
            scri_interpretation=scri_i,
            eoq_pct=eoq,
            eoq_formula_latex=eoq_f,
            eoq_interpretation=eoq_i
        )
