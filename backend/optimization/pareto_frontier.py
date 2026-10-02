"""
ARIS Multi-Objective Optimization Representation & Pareto Frontier Analyzer.
Computes non-dominated candidate sets across vector objectives:
- loop_time_delta_pct (minimize)
- sram_delta_pct (minimize)
- flash_delta_pct (minimize)
- jitter_delta_pct (minimize)

Never scalarizes objectives into arbitrary overall scores without exposing true trade-offs.
"""

from typing import List, Dict, Any, Tuple
from backend.optimization.candidate_models import HardwareAwareCandidate, MultiObjectiveDelta


class ParetoFrontierAnalyzer:
    """
    Computes Pareto-optimal (non-dominated) candidates from a candidate set.
    """

    @classmethod
    def dominates(cls, candidate_a: HardwareAwareCandidate, candidate_b: HardwareAwareCandidate) -> bool:
        """
        Returns True if candidate_a Pareto-dominates candidate_b.
        Candidate A dominates B if:
        1. A is at least as good as B in all objectives (<= since we minimize delta).
        2. A is strictly better than B in at least one objective (<).
        """
        vec_a = candidate_a.calibrated_prediction.as_vector()
        vec_b = candidate_b.calibrated_prediction.as_vector()

        at_least_as_good = True
        strictly_better = False

        for metric in ["loop_time_delta_pct", "sram_delta_pct", "flash_delta_pct", "jitter_delta_pct"]:
            val_a = vec_a[metric]
            val_b = vec_b[metric]

            if val_a > val_b:  # A is worse in this objective
                at_least_as_good = False
                break
            if val_a < val_b:  # A is strictly better
                strictly_better = True

        return at_least_as_good and strictly_better

    @classmethod
    def compute_pareto_frontier(cls, candidates: List[HardwareAwareCandidate]) -> List[HardwareAwareCandidate]:
        """
        Filters candidates down to the non-dominated Pareto frontier set.
        """
        if not candidates:
            return []

        pareto_set: List[HardwareAwareCandidate] = []

        for candidate in candidates:
            is_dominated = False
            for other in candidates:
                if candidate.candidate_id == other.candidate_id:
                    continue
                if cls.dominates(other, candidate):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_set.append(candidate)

        return pareto_set

    @classmethod
    def format_trade_offs(cls, candidate: HardwareAwareCandidate) -> Dict[str, str]:
        """
        Explains clear trade-offs without hidden weights.
        """
        p = candidate.calibrated_prediction
        trade_offs = {}

        if p.loop_time_delta_pct < 0:
            trade_offs["loop_time"] = f"Loop execution time improves by {abs(p.loop_time_delta_pct):.1f}%"
        elif p.loop_time_delta_pct > 0:
            trade_offs["loop_time"] = f"Loop latency increases by {p.loop_time_delta_pct:.1f}%"

        if p.sram_delta_pct > 0:
            trade_offs["sram"] = f"Consumes {p.sram_delta_pct:.1f}% more SRAM"
        elif p.sram_delta_pct < 0:
            trade_offs["sram"] = f"Reclaims {abs(p.sram_delta_pct):.1f}% SRAM"

        if p.flash_delta_pct > 0:
            trade_offs["flash"] = f"Expands Flash ROM by {p.flash_delta_pct:.1f}%"
        elif p.flash_delta_pct < 0:
            trade_offs["flash"] = f"Reclaims {abs(p.flash_delta_pct):.1f}% Flash ROM"

        if p.jitter_delta_pct < 0:
            trade_offs["jitter"] = f"Execution jitter reduced by {abs(p.jitter_delta_pct):.1f}%"

        return trade_offs
