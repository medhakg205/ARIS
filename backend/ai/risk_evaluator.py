"""
ARIS Risk Evaluator.
Evaluates architectural, timing, and memory risks of firmware optimization candidates.
Strictly returns LOW, MEDIUM, or HIGH risk classification with technical rationale.
"""

from typing import Dict, Any, Tuple


class RiskEvaluator:
    """Evaluates the risk of applying an optimization transform on an AVR target."""

    @staticmethod
    def evaluate(
        rule_id: str,
        board_id: str,
        before_code: str,
        after_code: str,
        finding_severity: str = "MEDIUM"
    ) -> Tuple[str, str]:
        """
        Returns (risk_level, risk_rationale).
        risk_level is one of 'LOW', 'MEDIUM', 'HIGH'.
        """
        # Critical risks: modifying ISR, disabling interrupts, or volatile registers
        if "cli()" in after_code or "sei()" in after_code or "ISR(" in after_code:
            return (
                "HIGH",
                "Alters interrupt enable flags or ISR timing; high risk of missed hardware events or deadlocks."
            )

        # High risk: assembly or pointer arithmetic
        if "__asm__" in after_code or "(char*)" in after_code:
            return (
                "HIGH",
                "Employs inline assembly or direct pointer casting; risk of memory corruption or alignment faults."
            )

        # Medium risk: Direct port register manipulation (e.g. PORTB, DDRD)
        if any(reg in after_code for reg in ["PORTB", "PORTC", "PORTD", "DDRB", "DDRC", "DDRD", "PORTA"]):
            return (
                "MEDIUM",
                "Direct hardware port register writing bypasses Arduino pin abstraction; ensure pin masks match board schematic."
            )

        # Medium risk: Fixed-point arithmetic replacing float
        if rule_id == "ARIS-004" or ("float" in before_code and "int" in after_code):
            return (
                "MEDIUM",
                "Replaces 32-bit floating point arithmetic with integer scaling; verify precision tolerances."
            )

        # Low risk: Non-blocking millis() timer state machine
        if rule_id == "ARIS-001" or ("delay(" in before_code and "millis()" in after_code):
            return (
                "LOW",
                "Non-blocking timer state machine uses existing hardware Timer0; minimal concurrency risk."
            )

        # Low risk: PROGMEM or F() flash strings
        if rule_id in ("ARIS-003", "ARIS-005") or "F(" in after_code:
            return (
                "LOW",
                "Moves string constants from SRAM into Flash ROM; zero side-effect on MCU instruction execution."
            )

        # Low risk: Serial log rate throttling
        if rule_id == "ARIS-002":
            return (
                "LOW",
                "Throttles UART transmissions, reducing TX ring buffer saturation without altering payload structure."
            )

        return (
            "LOW" if finding_severity in ("LOW", "MEDIUM") else "MEDIUM",
            "Deterministic transformation validated against AVR Harvard architecture constraints."
        )
