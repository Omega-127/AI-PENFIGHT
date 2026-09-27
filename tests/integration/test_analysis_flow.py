"""Integration tests for AI Penfight end-to-end analysis flows.

Validates the full pipeline against all scenarios defined in ARCHITECTURE.md §11:
- Scenario 1: Valid input -> AI analysis generated
- Scenario 2: Empty input -> Validation error returned (422)
- Scenario 3: Invalid/oversized input -> Clear structured error returned
- Scenario 4: AI service unavailable/timeout -> Graceful fallback, no crash
- Scenario 5: Malformed LLM output -> Caught, retried, graceful fallback
- Scenario 6: Repeated interactions -> Adaptive history and pattern detection
- Scenario 7: External/database dependency error -> Graceful degradation
- Scenario 8: Concurrent requests (load test) -> No corruption, reliable throughput
"""

import concurrent.futures
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from ai.clients.base_client import BaseLLMClient, LLMResponse
from ai.clients.llm_client import LLMTimeoutError
from backend.app.main import app

client = TestClient(app)


def test_scenario_1_valid_input_end_to_end_flow():
    """Scenario 1: Valid debate input processes through the entire pipeline and returns structured AI analysis."""
    payload = {
        "input": (
            "Carbon dividend policies create market incentives for clean innovation while "
            "directly shielding low-income households from rising energy costs through quarterly rebates."
        ),
        "session_id": "sess_integration_001",
        "user_id": "debater_42",
        "mode": "analysis",
        "session_context": {"topic": "Climate Policy", "round": 2, "side": "affirmative"},
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["analysisId"].startswith("an_")
    assert isinstance(data["analysis"], str) and len(data["analysis"]) > 0
    assert isinstance(data["feedback"], str) and len(data["feedback"]) > 0
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0

    # Verify score breakdown
    score = data["score"]
    assert "overall_score" in score
    assert 0 <= score["overall_score"] <= 100

    # Verify details metadata
    details = data["details"]
    assert "decision" in details
    assert "prompt_version" in details
    assert "strategy_applied" in details
    assert details["decision"]["decision"] in ("PROCEED_WITH_LLM", "RULE_BASED_EVALUATION")


def test_scenario_2_empty_input_validation_error():
    """Scenario 2: Empty input is rejected early by validation with a 422 error."""
    payload = {"input": ""}
    response = client.post("/api/v1/analyze", json=payload)

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "cannot be empty" in data["error"]["message"].lower()


def test_scenario_3_invalid_and_oversized_input():
    """Scenario 3: Excessively long input exceeding length limits returns structured validation error."""
    with patch.dict("os.environ", {"MAX_INPUT_LENGTH": "150"}):
        payload = {
            "input": (
                "This debate submission is purposefully constructed to surpass the artificial length limit "
                "configured for this scenario, ensuring that the input processing boundary accurately catches "
                "and rejects excessively long submissions."
            )
        }
        response = client.post("/api/v1/analyze", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "exceeds maximum allowed length" in data["error"]["message"].lower()


def test_scenario_4_ai_service_timeout_graceful_fallback():
    """Scenario 4: When the upstream LLM service times out, the backend degrades gracefully to rule-based analysis."""
    class TimingOutLLMClient(BaseLLMClient):
        def is_available(self) -> bool:
            return True

        def get_provider_name(self) -> str:
            return "timeout-mock"

        def generate(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
            raise LLMTimeoutError("Gateway timeout connecting to LLM provider (10000ms exceeded).")

        async def generate_async(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
            return self.generate(prompt, system_prompt, json_mode, temperature)

    payload = {
        "input": "Subsidizing public university tuition produces positive economic externalities in technological research.",
        "mode": "analysis",
    }

    # Patch the LLM client in the feedback generation step
    with patch("ai.feedback_generation.get_llm_client", return_value=TimingOutLLMClient()):
        response = client.post("/api/v1/analyze", json=payload)

        # Must succeed gracefully rather than 500 crashing
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["analysisId"].startswith("an_")
        assert len(data["recommendations"]) > 0
        assert "fallback" in data["details"]["prompt_version"].lower()


def test_scenario_5_malformed_llm_output_retries_and_falls_back():
    """Scenario 5: When LLM outputs malformed JSON, backend catches parse failure, retries, and falls back gracefully."""
    class MalformedLLMClient(BaseLLMClient):
        def is_available(self) -> bool:
            return True

        def get_provider_name(self) -> str:
            return "malformed-mock"

        def generate(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
            return LLMResponse(
                content="Sorry, I cannot format this into JSON: { bad syntax",
                raw_json=None,
                model="malformed-v1",
                provider="malformed-mock",
            )

        async def generate_async(self, prompt: str, system_prompt=None, json_mode=True, temperature=0.3) -> LLMResponse:
            return self.generate(prompt, system_prompt, json_mode, temperature)

    payload = {
        "input": "Investments in passenger rail corridors stimulate regional economic development.",
    }

    with patch("ai.feedback_generation.get_llm_client", return_value=MalformedLLMClient()):
        response = client.post("/api/v1/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "fallback" in data["details"]["prompt_version"].lower()
        assert len(data["recommendations"]) > 0


def test_scenario_6_repeated_interactions_adaptive_history():
    """Scenario 6: Multi-turn history is analyzed to detect recurring mistakes and generate personalized suggestions."""
    history = [
        {"errors": ["their/there confusion"], "overall_score": 60.0},
        {"errors": ["their/there confusion"], "overall_score": 64.0},
    ]

    payload = {
        "input": "Their is compelling empirical evidence supporting early intervention in literacy programs.",
        "history": history,
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    priority_patterns = data["details"]["priority_patterns"]
    assert any("their/there" in p.lower() for p in priority_patterns)


def test_scenario_7_unexpected_service_error_handling():
    """Scenario 7: Unexpected downstream failure produces friendly, structured error response without crashing."""
    payload = {
        "input": "Implementing carbon border adjustment mechanisms prevents carbon leakage.",
    }

    with patch("backend.app.routers.analysis.run_pipeline", side_effect=Exception("Database connection pool exhausted")):
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 500

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AI_PROCESSING_ERROR"
        assert "An error occurred while analyzing" in data["error"]["message"]


def test_scenario_8_concurrent_requests_load_test():
    """Scenario 8: Concurrent requests execute simultaneously with no data corruption or race conditions."""
    inputs = [
        f"Contention {i}: Expanding renewable energy microgrids provides resilient power infrastructure under storm stress."
        for i in range(10)
    ]

    def make_request(prompt_text: str):
        return client.post("/api/v1/analyze", json={"input": prompt_text, "session_id": f"sess_concurrent_{prompt_text[:12]}"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        responses = list(executor.map(make_request, inputs))

    assert len(responses) == 10
    analysis_ids = set()

    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["analysisId"].startswith("an_")
        assert data["analysisId"] not in analysis_ids  # Each analysisId must be unique
        analysis_ids.add(data["analysisId"])
        assert len(data["recommendations"]) > 0
        assert data["score"]["overall_score"] > 0
