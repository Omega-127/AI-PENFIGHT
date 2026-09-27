"""AI Penfight core AI package.

Provides modular input processing, lightweight pattern detection,
rule-based decision logic, model-agnostic LLM feedback generation,
and evaluation suites.
"""

from ai.input_processing import process_input, InputValidationError
from ai.pattern_detection import detect_patterns, extract_features
from ai.decision_engine import decide_strategy, DecisionEngine
from ai.feedback_generation import generate_feedback, load_feedback_prompt
from ai.evaluation import evaluate_feedback, evaluate_batch, run_local_evaluation
from ai.clients.base_client import BaseLLMClient, LLMResponse
from ai.clients.llm_client import get_llm_client
from ai.schemas.feedback_schema import (
    CorrectionItem,
    FallacyItem,
    PerformanceScore,
    FeedbackResponse,
    ProcessedInput,
    PatternFeatures,
    DecisionResult,
)

__all__ = [
    "process_input",
    "InputValidationError",
    "detect_patterns",
    "extract_features",
    "decide_strategy",
    "DecisionEngine",
    "generate_feedback",
    "load_feedback_prompt",
    "evaluate_feedback",
    "evaluate_batch",
    "run_local_evaluation",
    "BaseLLMClient",
    "LLMResponse",
    "get_llm_client",
    "CorrectionItem",
    "FallacyItem",
    "PerformanceScore",
    "FeedbackResponse",
    "ProcessedInput",
    "PatternFeatures",
    "DecisionResult",
]
