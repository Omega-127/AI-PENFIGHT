"""Tests for ai/feedback_generation.py per ARCHITECTURE.md §6.4 & §11."""

import json
from unittest.mock import MagicMock
import pytest

from ai.clients.base_client import BaseLLMClient, LLMResponse
from ai.clients.llm_client import DevelopmentFallbackClient, LLMTimeoutError
from ai.decision_engine import decide_strategy
from ai.feedback_generation import (
    generate_feedback,
    generate_rule_based_feedback,
    load_feedback_prompt,
)
from ai.input_processing import process_input
from ai.pattern_detection import detect_patterns
from ai.schemas.feedback_schema import FeedbackResponse


class MockSuccessfulClient(BaseLLMClient):
    """Mock client returning valid structured JSON."""

    def __init__(self, response_dict: dict):
        self.response_dict = response_dict

    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock"

    def generate(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        return LLMResponse(
            content=json.dumps(self.response_dict),
            raw_json=self.response_dict,
            model="mock-gpt",
            provider="mock",
            latency_ms=15.0,
        )

    async def generate_async(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        return self.generate(prompt, system_prompt, json_mode, temperature)


class MockMalformedThenSuccessClient(BaseLLMClient):
    """First attempt returns malformed text; retry returns valid JSON."""

    def __init__(self, valid_dict: dict):
        self.valid_dict = valid_dict
        self.call_count = 0

    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock"

    def generate(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        self.call_count += 1
        if self.call_count == 1:
            return LLMResponse(
                content="Here is your feedback: { not valid json ...",
                raw_json=None,
                model="mock-gpt",
                provider="mock",
            )
        return LLMResponse(
            content=json.dumps(self.valid_dict),
            raw_json=self.valid_dict,
            model="mock-gpt",
            provider="mock",
        )

    async def generate_async(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        return self.generate(prompt, system_prompt, json_mode, temperature)


class MockFailingClient(BaseLLMClient):
    """Client simulating persistent network timeouts."""

    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock"

    def generate(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        raise LLMTimeoutError("Connection to LLM provider timed out.")

    async def generate_async(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
        return self.generate(prompt, system_prompt, json_mode, temperature)


@pytest.fixture
def sample_valid_response_dict():
    return {
        "analysis_id": "an_test_123",
        "overall_feedback": "The debate argument provides an articulate overview with balanced evidence.",
        "strengths": ["Clear thesis", "Good evidentiary support"],
        "weaknesses": ["Counter-argument dismissed too quickly"],
        "logical_fallacies": [],
        "grammar_and_vocabulary": [],
        "suggestions": ["Include empirical citations."],
        "actionable_recommendations": ["1. State impact clearly."],
        "performance_score": {
            "argument_strength": 82.0,
            "logic_and_reasoning": 85.0,
            "evidence_and_support": 78.0,
            "clarity_and_style": 88.0,
            "rebuttal_effectiveness": 70.0,
            "overall_score": 81.2,
            "breakdown": {
                "argument_strength": "Sound thesis with cogent warrant.",
                "logic_and_reasoning": "Logically cohesive structure.",
                "evidence_and_support": "Includes plausible real-world mechanisms.",
                "clarity_and_style": "High clarity and vocabulary variety.",
                "rebuttal_effectiveness": "Moderate consideration of alternatives.",
            }
        },
        "prompt_version": "v1.2.0",
        "strategy_applied": "comprehensive_debate_analysis",
    }


def test_prompt_loading_and_version_tracking():
    content, version = load_feedback_prompt()
    assert version.startswith("v")
    assert "{{processed_input}}" in content
    assert "{{pattern_features}}" in content
    assert "{{analysis_strategy}}" in content


def test_llm_success_with_mock(sample_valid_response_dict):
    client = MockSuccessfulClient(sample_valid_response_dict)
    text = "Carbon fee and dividend policies create market incentives while protecting low-income consumers."
    processed = process_input(text)
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)

    feedback = generate_feedback(processed, patterns, decision, llm_client=client)

    assert isinstance(feedback, FeedbackResponse)
    assert feedback.analysis_id == "an_test_123"
    assert len(feedback.strengths) == 2
    assert feedback.performance_score.overall_score == 81.2
    assert feedback.prompt_version == "v1.2.0"


def test_invalid_json_recovered_on_retry(sample_valid_response_dict):
    client = MockMalformedThenSuccessClient(sample_valid_response_dict)
    text = "Governments must invest aggressively in high-speed rail to reduce domestic flight emissions."
    processed = process_input(text)
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)

    feedback = generate_feedback(processed, patterns, decision, llm_client=client)

    assert client.call_count == 2  # Proves retry was performed
    assert isinstance(feedback, FeedbackResponse)
    assert feedback.analysis_id == "an_test_123"


def test_llm_failure_falls_back_gracefully():
    failing_client = MockFailingClient()
    text = "Subsidies for fossil fuel exploration distort market price signals and prevent renewable adoption."
    processed = process_input(text)
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)

    # Should not raise exception; must return valid fallback FeedbackResponse
    feedback = generate_feedback(processed, patterns, decision, llm_client=failing_client)

    assert isinstance(feedback, FeedbackResponse)
    assert feedback.overall_feedback is not None
    assert len(feedback.suggestions) > 0
    assert feedback.performance_score.overall_score > 0
    assert "fallback" in feedback.prompt_version.lower()


def test_development_fallback_client_when_no_api_key():
    fallback_client = DevelopmentFallbackClient()
    assert fallback_client.is_available() is True
    assert fallback_client.get_provider_name() == "fallback"

    text = "Affirmative action policies promote socioeconomic mobility for historically underrepresented demographics."
    processed = process_input(text)
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)

    feedback = generate_feedback(processed, patterns, decision, llm_client=fallback_client)

    assert isinstance(feedback, FeedbackResponse)
    assert feedback.performance_score.overall_score > 0
    assert len(feedback.actionable_recommendations) >= 3


def test_rule_based_generation_for_short_input():
    # Very short input will have decision.use_llm == False
    processed = process_input("Taxation is theft.")
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)

    assert decision.use_llm is False
    feedback = generate_feedback(processed, patterns, decision)

    assert isinstance(feedback, FeedbackResponse)
    assert feedback.strategy_applied == "quick_rule_critique"
    assert any("brief" in w.lower() for w in feedback.weaknesses)
