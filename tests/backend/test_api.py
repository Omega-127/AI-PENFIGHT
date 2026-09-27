"""Tests for backend API core infrastructure, routing, middleware, and error handling per ARCHITECTURE.md §5 & §10."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify /api/v1/health returns liveness, version, and AI provider availability."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "ai_provider" in data
    assert "ai_available" in data
    assert isinstance(data["ai_available"], bool)


def test_root_endpoint():
    """Verify root GET / returns service information and docs link."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "AI Penfight API"
    assert data["status"] == "online"
    assert data["docs_url"] == "/docs"


def test_openapi_schema_endpoint():
    """Verify OpenAPI specification is accessible and registers core routes."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/analyze" in schema["paths"]
    assert "/api/v1/feedback" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]


def test_docs_ui_endpoint():
    """Verify Swagger UI documentation is served."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower() or "html" in response.headers.get("content-type", "")


def test_cors_preflight_headers():
    """Verify CORS preflight OPTIONS request returns appropriate headers."""
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # Status code 200 for allowed CORS options preflight
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_not_found_endpoint():
    """Verify unknown routes return 404 status."""
    response = client.get("/api/v1/non_existent_route")
    assert response.status_code == 404


def test_method_not_allowed():
    """Verify sending GET to a POST-only endpoint returns 405 Method Not Allowed."""
    response = client.get("/api/v1/analyze")
    assert response.status_code == 405


def test_validation_exception_handler_format():
    """Verify validation errors follow the standardized error JSON shape per ARCHITECTURE.md §5."""
    # Sending invalid data type for input (e.g. integer instead of str)
    response = client.post(
        "/api/v1/analyze",
        headers={"Content-Type": "application/json"},
        content='{"input": 12345}',
    )
    assert response.status_code == 422

    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert isinstance(data["error"]["message"], str)
