"""Tests for FastAPI backend routes and AI module integration."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "ai_provider" in data
    assert "ai_available" in data


def test_analyze_ai_endpoint_success():
    payload = {
        "input": "Implementing universal school breakfast programs improves cognitive retention and attendance in secondary schools.",
        "session_id": "test_session_api_1",
        "mode": "analysis",
        "session_context": {"topic": "Education", "round": 1}
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "analysisId" in data
    assert "analysis" in data
    assert "feedback" in data
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0
    assert "score" in data
    assert data["score"]["overall_score"] > 0
    assert "details" in data
    assert "createdAt" in data


def test_analyze_v1_endpoint_alias():
    payload = {
        "input": "Decentralized renewable microgrids increase grid resilience during severe climatic events.",
        "mode": "analysis"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["analysisId"].startswith("an_")


def test_analyze_empty_input_validation_error():
    payload = {"input": ""}
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "cannot be empty" in data["error"]["message"].lower()


def test_analyze_missing_input_field():
    payload = {"mode": "analysis"}
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_analyze_with_history():
    payload = {
        "input": "Their is no alternative to carbon capture technology.",
        "history": [
            {"errors": ["their/there confusion"], "overall_score": 60.0}
        ]
    }
    response = client.post("/api/ai/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Priority patterns should capture recurring error
    priority_patterns = data["details"]["priority_patterns"]
    assert any("their/there" in p.lower() for p in priority_patterns)
