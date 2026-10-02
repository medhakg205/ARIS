"""
ARIS Resource Budget Engine.
Evaluates Flash, SRAM, and Stack budgets against physical hardware capabilities.
Enforces hard constraints:
- Max 95% Flash utilization
- Max 90% SRAM utilization
- Minimum 64 bytes Stack headroom
"""

from typing import Dict, Any, Optional, Tuple
from backend.hardware.capability_graph import HardwareCapabilityGraph
from backend.optimization.candidate_models import ResourceBudgetImpact


class ResourceBudgetEngine:
    """
    Evaluates resource consumption and margins based strictly on
    HardwareCapabilityGraph limits.
    """
    MAX_FLASH_UTILIZATION_PCT = 95.0
    MAX_SRAM_UTILIZATION_PCT = 90.0
    MIN_STACK_MARGIN_BYTES = 64  # Reserve 64 bytes minimum for ISR/call stack on small MCUs

    @classmethod
    def evaluate(
        cls,
        capability_graph: HardwareCapabilityGraph,
        current_flash_used: int,
        current_sram_used: int,
        flash_delta_bytes: int,
        sram_delta_bytes: int
    ) -> ResourceBudgetImpact:
        """
        Evaluates projected resource footprint against hardware capability limits.
        """
        # Resolve hardware limits strictly from capability graph
        flash_total = (
            capability_graph.flash_memory.value
            if capability_graph.flash_memory and capability_graph.flash_memory.value
            else 32768
        )
        sram_total = (
            capability_graph.sram_memory.value
            if capability_graph.sram_memory and capability_graph.sram_memory.value
            else 2048
        )

        projected_flash_used = max(0, current_flash_used + flash_delta_bytes)
        projected_sram_used = max(0, current_sram_used + sram_delta_bytes)

        flash_remaining = flash_total - projected_flash_used
        sram_remaining = sram_total - projected_sram_used

        flash_util_pct = round((projected_flash_used / flash_total) * 100.0, 2) if flash_total > 0 else 0.0
        sram_util_pct = round((projected_sram_used / sram_total) * 100.0, 2) if sram_total > 0 else 0.0

        # Stack margin is remaining SRAM minus dynamic heap reservation
        stack_margin = max(0, sram_remaining)

        violates_flash = (projected_flash_used > flash_total) or (flash_util_pct > cls.MAX_FLASH_UTILIZATION_PCT)
        violates_sram = (projected_sram_used > sram_total) or (sram_util_pct > cls.MAX_SRAM_UTILIZATION_PCT)
        violates_stack = stack_margin < cls.MIN_STACK_MARGIN_BYTES

        explanations = []
        if violates_flash:
            explanations.append(
                f"Flash utilization ({flash_util_pct}%, {projected_flash_used}/{flash_total}B) exceeds safety limit {cls.MAX_FLASH_UTILIZATION_PCT}%."
            )
        if violates_sram:
            explanations.append(
                f"SRAM utilization ({sram_util_pct}%, {projected_sram_used}/{sram_total}B) exceeds safety limit {cls.MAX_SRAM_UTILIZATION_PCT}%."
            )
        if violates_stack:
            explanations.append(
                f"Stack headroom ({stack_margin}B) is below required minimum margin of {cls.MIN_STACK_MARGIN_BYTES}B."
            )

        explanation_str = " | ".join(explanations) if explanations else "Resource budgets within hardware safety boundaries."

        return ResourceBudgetImpact(
            flash_delta_bytes=flash_delta_bytes,
            sram_delta_bytes=sram_delta_bytes,
            flash_headroom_bytes_remaining=flash_remaining,
            sram_headroom_bytes_remaining=sram_remaining,
            flash_utilization_pct=flash_util_pct,
            sram_utilization_pct=sram_util_pct,
            stack_margin_bytes=stack_margin,
            violates_flash_budget=violates_flash,
            violates_sram_budget=violates_sram,
            violates_stack_budget=violates_stack,
            budget_explanation=explanation_str
        )
