"""
ARIS Modular AI Provider Abstraction.
Provides pluggable AI model providers for embedded microcontroller firmware optimization.
Supports Google Gemini, OpenAI, and deterministic architecture-aware RuleSynthesizer.
Gracefully handles missing API keys and errors with canonical ARIS_AI_UNAVAILABLE.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from backend.analysis.ai_interface import AIContextInput, OptimizationCandidate
from backend.telemetry.telemetry_schema import ArisException

logger = logging.getLogger("aris.ai.provider")


class AIProvider(ABC):
    """Abstract base class for ARIS AI model providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Canonical provider identifier (e.g. 'rule_synthesizer', 'gemini', 'openai')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider label."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the provider is configured and available for inference."""
        pass

    @abstractmethod
    def generate_candidate(
        self,
        context: AIContextInput,
        finding: Dict[str, Any],
        **kwargs: Any
    ) -> OptimizationCandidate:
        """
        Executes optimization reasoning over the embedded context and finding,
        emitting a validated canonical OptimizationCandidate.
        """
        pass

    def get_info(self) -> Dict[str, Any]:
        """Returns metadata about the provider state."""
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "available": self.is_available()
        }


class GeminiProvider(AIProvider):
    """
    Google Gemini AI Provider for ARIS.
    Uses Google Gemini models to perform embedded architecture reasoning and code optimization.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model_name = model_name

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return f"Google Gemini ({self._model_name})"

    def is_available(self) -> bool:
        return bool(self._api_key and len(self._api_key.strip()) > 0)

    def generate_candidate(
        self,
        context: AIContextInput,
        finding: Dict[str, Any],
        **kwargs: Any
    ) -> OptimizationCandidate:
        if not self.is_available():
            raise ArisException(
                error_code="ARIS_AI_UNAVAILABLE",
                message="Google Gemini AI is unavailable: GEMINI_API_KEY is not configured.",
                details={"provider": self.provider_id},
                recoverable=True,
                status_code=503
            )

        # In an actual online environment with httpx/google-genai, call the Gemini API.
        # Fall back to strict error if network request fails.
        try:
            import httpx
            prompt = self._build_gemini_prompt(context, finding)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:generateContent?key={self._api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }
            resp = httpx.post(url, json=payload, timeout=30.0)
            if resp.status_code != 200:
                raise ArisException(
                    error_code="ARIS_AI_UNAVAILABLE",
                    message=f"Gemini API returned status {resp.status_code}: {resp.text[:200]}",
                    details={"status_code": resp.status_code},
                    recoverable=True,
                    status_code=503
                )
            result_json = resp.json()
            text_content = result_json["candidates"][0]["content"]["parts"][0]["text"]
            candidate_dict = json.loads(text_content)
            from backend.ai.output_validator import OutputValidator
            return OutputValidator.validate_candidate_dict(candidate_dict)
        except ArisException:
            raise
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise ArisException(
                error_code="ARIS_AI_UNAVAILABLE",
                message=f"Gemini generation failed: {str(e)}",
                details={"provider": self.provider_id, "error": str(e)},
                recoverable=True,
                status_code=503
            )

    def _build_gemini_prompt(self, context: AIContextInput, finding: Dict[str, Any]) -> str:
        return (
            "You are an expert embedded AVR systems optimizer. Output valid JSON adhering to ARIS schema.\n"
            f"Board: {json.dumps(context.board_profile)}\n"
            f"Finding: {json.dumps(finding)}\n"
            "Return an object with: optimization_id, finding_id, title, problem, source_location, "
            "before_code, after_code, reason, hardware_consideration, expected_effect, risk, confidence, "
            "validation_required, status (PROPOSED)."
        )


class OpenAIProvider(AIProvider):
    """
    OpenAI Provider for ARIS.
    Uses OpenAI GPT models for firmware optimization.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model_name = model_name

    @property
    def provider_id(self) -> str:
        return "openai"

    @property
    def display_name(self) -> str:
        return f"OpenAI ({self._model_name})"

    def is_available(self) -> bool:
        return bool(self._api_key and len(self._api_key.strip()) > 0)

    def generate_candidate(
        self,
        context: AIContextInput,
        finding: Dict[str, Any],
        **kwargs: Any
    ) -> OptimizationCandidate:
        if not self.is_available():
            raise ArisException(
                error_code="ARIS_AI_UNAVAILABLE",
                message="OpenAI is unavailable: OPENAI_API_KEY is not configured.",
                details={"provider": self.provider_id},
                recoverable=True,
                status_code=503
            )

        try:
            import httpx
            # Call OpenAI API
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self._model_name,
                "messages": [
                    {"role": "system", "content": "You are ARIS Embedded Optimizer. Output JSON only."},
                    {"role": "user", "content": f"Optimize finding: {json.dumps(finding)} for board {json.dumps(context.board_profile)}"}
                ],
                "response_format": {"type": "json_object"}
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code != 200:
                raise ArisException(
                    error_code="ARIS_AI_UNAVAILABLE",
                    message=f"OpenAI API returned status {resp.status_code}",
                    details={"status_code": resp.status_code},
                    recoverable=True,
                    status_code=503
                )
            result_json = resp.json()
            content = result_json["choices"][0]["message"]["content"]
            from backend.ai.output_validator import OutputValidator
            return OutputValidator.validate_candidate_dict(json.loads(content))
        except ArisException:
            raise
        except Exception as e:
            raise ArisException(
                error_code="ARIS_AI_UNAVAILABLE",
                message=f"OpenAI inference failed: {str(e)}",
                details={"error": str(e)},
                recoverable=True,
                status_code=503
            )


class RuleSynthesizerProvider(AIProvider):
    """
    Deterministic Architecture-Aware Embedded Synthesizer.
    Analyzes physical AVR constraints (ATmega328P / ATmega2560) and synthesizes
    safe, verifiable optimization candidates for canonical antipatterns.
    Always available for offline, mission-critical, or simulated environments.
    """

    @property
    def provider_id(self) -> str:
        return "rule_synthesizer"

    @property
    def display_name(self) -> str:
        return "ARIS Architecture-Aware Rule Synthesizer (Embedded AVR8)"

    def is_available(self) -> bool:
        return True

    def generate_candidate(
        self,
        context: AIContextInput,
        finding: Dict[str, Any],
        **kwargs: Any
    ) -> OptimizationCandidate:
        from backend.ai.optimization_reasoner import OptimizationReasoner
        from backend.ai.output_validator import OutputValidator

        candidate_data = OptimizationReasoner.reason_and_synthesize(context, finding)
        return OutputValidator.validate_candidate_dict(candidate_data)


# Provider Registry
_PROVIDERS: Dict[str, AIProvider] = {
    "rule_synthesizer": RuleSynthesizerProvider(),
    "gemini": GeminiProvider(),
    "openai": OpenAIProvider()
}


def get_ai_provider(provider_type: Optional[str] = None) -> AIProvider:
    """
    Returns an AIProvider instance.
    - 'auto': returns Gemini if configured, then OpenAI if configured, else RuleSynthesizer.
    - specific string ('gemini', 'openai', 'rule_synthesizer'): returns that provider.
    """
    target = (provider_type or "auto").lower()

    if target == "auto":
        gemini = _PROVIDERS["gemini"]
        if gemini.is_available():
            return gemini
        openai = _PROVIDERS["openai"]
        if openai.is_available():
            return openai
        return _PROVIDERS["rule_synthesizer"]

    if target in _PROVIDERS:
        return _PROVIDERS[target]

    raise ArisException(
        error_code="ARIS_AI_UNAVAILABLE",
        message=f"Unknown or unsupported AI provider '{provider_type}'. Supported: {list(_PROVIDERS.keys())}",
        details={"requested_provider": provider_type},
        recoverable=True,
        status_code=400
    )


def list_available_providers() -> List[Dict[str, Any]]:
    """Lists registered providers and their current availability."""
    return [p.get_info() for p in _PROVIDERS.values()]
