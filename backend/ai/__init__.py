"""
ARIS Modular AI Engine Package.
Adaptive Runtime Intelligence System for Embedded Devices.
Owner: Engineer 3 (AI + Frontend)
"""

from backend.ai.provider import (
    AIProvider,
    GeminiProvider,
    OpenAIProvider,
    RuleSynthesizerProvider,
    get_ai_provider,
    list_available_providers,
)
from backend.ai.context_builder import ContextBuilder
from backend.ai.firmware_analyzer import FirmwareAnalyzer
from backend.ai.optimization_reasoner import OptimizationReasoner
from backend.ai.candidate_generator import CandidateGenerator
from backend.ai.risk_evaluator import RiskEvaluator
from backend.ai.prediction_engine import PredictionEngine
from backend.ai.output_validator import OutputValidator

__all__ = [
    "AIProvider",
    "GeminiProvider",
    "OpenAIProvider",
    "RuleSynthesizerProvider",
    "get_ai_provider",
    "list_available_providers",
    "ContextBuilder",
    "FirmwareAnalyzer",
    "OptimizationReasoner",
    "CandidateGenerator",
    "RiskEvaluator",
    "PredictionEngine",
    "OutputValidator",
]
