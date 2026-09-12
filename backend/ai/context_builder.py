"""
ARIS AI Context Builder.
Assembles, validates, and normalizes full embedded context for the AI Engine:
- Target board hardware profile & architecture limits
- Firmware source code
- Static code analysis findings
- Empirical runtime telemetry metrics
- Statistical baseline metrics
- Correlated static + runtime findings
- Prior optimization history
"""

from typing import Dict, Any, List, Optional
from backend.analysis.ai_interface import AIContextInput
from backend.firmware.board_profiles import get_board_profile


class ContextBuilder:
    """Builder for assembling comprehensive AI diagnostic context."""

    @staticmethod
    def build(
        board_id: str = "arduino_uno",
        firmware_source: Optional[str] = None,
        static_findings: Optional[List[Dict[str, Any]]] = None,
        runtime_metrics: Optional[Dict[str, Any]] = None,
        baseline_metrics: Optional[Dict[str, Any]] = None,
        runtime_static_correlations: Optional[List[Dict[str, Any]]] = None,
        optimization_history: Optional[List[Dict[str, Any]]] = None,
        board_profile_override: Optional[Dict[str, Any]] = None
    ) -> AIContextInput:
        """
        Constructs and validates the canonical AIContextInput object.
        """
        # Resolve board profile
        if board_profile_override:
            board_dict = board_profile_override
        else:
            profile = get_board_profile(board_id)
            board_dict = profile.to_dict()

        # Add architecture metadata to board profile
        board_dict.setdefault("architecture_class", "avr8")
        board_dict.setdefault("has_hardware_perf_counters", False)
        board_dict.setdefault("instruction_cycle_ns", 62.5 if board_dict.get("clock_hz") == 16000000 else 125.0)

        source = firmware_source or "void setup() {}\nvoid loop() {}"

        return AIContextInput(
            board_profile=board_dict,
            firmware_source=source,
            static_findings=static_findings or [],
            runtime_metrics=runtime_metrics or {},
            baseline_metrics=baseline_metrics or {},
            runtime_static_correlations=runtime_static_correlations or [],
            optimization_history=optimization_history or []
        )
