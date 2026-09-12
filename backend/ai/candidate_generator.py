"""
ARIS Candidate Generator.
Coordinates AI reasoning, provider dispatch, validation, and candidate preparation.
Owner: Engineer 3 (AI + Frontend)
"""

from typing import Dict, Any, Optional
from backend.analysis.ai_interface import AIContextInput, OptimizationCandidate
from backend.ai.provider import get_ai_provider, AIProvider
from backend.ai.output_validator import OutputValidator


class CandidateGenerator:
    """Orchestrates generation and validation of optimization candidates."""

    @staticmethod
    def generate(
        context: AIContextInput,
        finding: Dict[str, Any],
        provider_name: Optional[str] = None
    ) -> OptimizationCandidate:
        """
        Dispatches context and finding to the configured AI provider,
        validating output against canonical schema.
        """
        provider: AIProvider = get_ai_provider(provider_name)
        candidate = provider.generate_candidate(context, finding)
        return OutputValidator.validate_candidate_dict(candidate.model_dump())
