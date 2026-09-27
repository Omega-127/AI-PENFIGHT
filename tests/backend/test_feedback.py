"""Tests for backend feedback endpoints (/api/v1/feedback and /api/ai/feedback) per ARCHITECTURE.md §5 & §11."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_feedback_v1_endpoint_success():
    """Verify POST /api/v1/feedback returns structured actionable feedback."""
    payload = {
        "input": "Implementing progressive carbon taxation discourages high-emission industrial practices.",
        "session_id": "sess_feedback_001",
        "user_id": "user_feedback_01",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["analysisId"].startswith("an_")
    assert isinstance(data["feedback"], str) and len(data["feedback"]) > 0
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    assert isinstance(data["strengths"], list)
    assert isinstance(data["weaknesses"], list)
    assert "score" in data
    assert "createdAt" in data


def test_feedback_ai_endpoint_alias():
    """Verify POST /api/ai/feedback operates as expected."""
    payload = {
        "input": "Urban public transit expansion significantly reduces municipal traffic congestion and carbon footprints.",
    }
    response = client.post("/api/ai/feedback", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) > 0


def test_feedback_with_existing_analysis_id_refresh():
    """Verify refreshing feedback preserves the associated analysis_id."""
    analysis_id = "an_custom_existing_99"
    payload = {
        "input": "Nuclear fission produces constant baseload electricity with zero direct operational emissions.",
        "analysis_id": analysis_id,
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["analysisId"] == analysis_id


def test_feedback_with_focus_areas():
    """Verify focus_areas are respected and reflected in the feedback response."""
    payload = {
        "input": "Universal basic income prevents poverty traps caused by rapid workforce automation.",
        "focus_areas": ["evidence", "logic"],
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["focus_areas"] == ["evidence", "logic"]
    assert len(data["recommendations"]) > 0


def test_feedback_empty_input_validation_error():
    """Verify empty input returns 422 with VALIDATION_ERROR code."""
    payload = {"input": ""}
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "cannot be empty" in data["error"]["message"].lower()


def test_feedback_whitespace_only_validation_error():
    """Verify whitespace input returns 422 with VALIDATION_ERROR code."""
    payload = {"input": "   \n\t  "}
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_feedback_missing_input_field():
    """Verify payload without input field returns 422."""
    payload = {"analysis_id": "an_some_id"}
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_feedback_with_history_adaptation():
    """Verify repeated mistakes in history adapt feedback recommendations."""
    payload = {
        "input": "Their is clear economic evidence supporting early childhood education investments.",
        "history": [
            {"errors": ["their/there confusion"], "overall_score": 62.0},
            {"errors": ["their/there confusion"], "overall_score": 64.0},
        ],
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    # Recommendations or feedback should address the grammar/clarity issue
    recs_text = " ".join(data["recommendations"]).lower()
    feedback_text = data["feedback"].lower()
    assert "grammar" in recs_text or "there" in recs_text or "clarity" in recs_text or "grammar" in feedback_text


def test_feedback_pipeline_exception_returns_500():
    """Verify internal pipeline error returns 500 FEEDBACK_GENERATION_ERROR without crashing."""
    payload = {
        "input": "Valid proposition regarding high-speed rail corridors.",
    }
    with patch("backend.app.routers.feedback.run_feedback_pipeline", side_effect=RuntimeError("Simulated feedback engine crash")):
        response = client.post("/api/v1/feedback", json=payload)
        assert response.status_code == 500

        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FEEDBACK_GENERATION_ERROR"
        assert "error occurred while generating feedback" in data["error"]["message"]
