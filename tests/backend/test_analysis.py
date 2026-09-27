"""Tests for backend analysis endpoints (/api/v1/analyze and /api/ai/analyze) per ARCHITECTURE.md §5 & §11."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_analyze_v1_endpoint_success():
    """Verify POST /api/v1/analyze returns complete structured analysis conforming to ARCHITECTURE.md §5."""
    payload = {
        "input": "Decentralized renewable microgrids increase grid resilience during severe climatic events.",
        "mode": "analysis",
        "session_id": "sess_analysis_001",
        "user_id": "user_analyst_01",
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
    assert "score" in data and data["score"]["overall_score"] > 0
    assert "details" in data
    assert "createdAt" in data


def test_analyze_ai_endpoint_alias():
    """Verify POST /api/ai/analyze behaves identically as the AI module endpoint alias."""
    payload = {
        "input": "Implementing universal school breakfast programs improves cognitive retention and attendance in secondary schools.",
        "session_id": "test_session_api_1",
        "mode": "analysis",
        "session_context": {"topic": "Education", "round": 1},
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["analysisId"].startswith("an_")
    assert len(data["recommendations"]) > 0
    assert data["score"]["overall_score"] > 0
    assert data["details"]["decision"]["decision"] in ("PROCEED_WITH_LLM", "RULE_BASED_EVALUATION")


def test_analyze_empty_input_validation_error():
    """Verify empty input returns 422 with VALIDATION_ERROR code."""
    payload = {"input": ""}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "cannot be empty" in data["error"]["message"].lower()


def test_analyze_whitespace_only_validation_error():
    """Verify whitespace-only input returns 422 with VALIDATION_ERROR code."""
    payload = {"input": "   \n\t   "}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_missing_input_field():
    """Verify missing input field triggers standard request validation 422."""
    payload = {"mode": "analysis"}
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_with_history_tracking():
    """Verify history context informs priority patterns in analysis output."""
    payload = {
        "input": "Their is no alternative to carbon capture technology.",
        "history": [
            {"errors": ["their/there confusion"], "overall_score": 60.0}
        ],
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    priority_patterns = data["details"]["priority_patterns"]
    assert any("their/there" in p.lower() for p in priority_patterns)


def test_analyze_extra_fields_ignored():
    """Verify extra payload fields are ignored without causing validation errors."""
    payload = {
        "input": "Carbon dividends return revenue directly to citizens as quarterly equal rebates.",
        "extra_field_123": "irrelevant_value",
        "nested_extra": {"test": True},
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_analyze_pipeline_exception_returns_500():
    """Verify unexpected internal pipeline failure returns 500 AI_PROCESSING_ERROR without crashing."""
    payload = {
        "input": "Valid debate proposition about civic service programs.",
    }
    with patch("backend.app.routers.analysis.run_pipeline", side_effect=RuntimeError("Simulated internal AI crash")):
        response = client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 500

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AI_PROCESSING_ERROR"
        assert "error occurred while analyzing" in data["error"]["message"]
