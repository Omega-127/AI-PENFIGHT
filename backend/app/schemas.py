"""API Request and Response schemas for the FastAPI backend."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class AnalyzeAPIRequest(BaseModel):
    """Payload for submitting a debate argument for AI analysis."""
    model_config = ConfigDict(extra="ignore")

    input: str = Field(..., description="Debate text or argument submission")
    mode: Optional[str] = Field(default="analysis", description="Mode: 'analysis' or 'feedback'")
    session_id: Optional[str] = Field(default=None, description="Optional persistent session identifier")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Bounded list of prior turns or session records"
    )
    session_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Contextual metadata (e.g. topic, round, side)"
    )


class AnalyzeAPIResponse(BaseModel):
    """Structured response conforming to ARCHITECTURE.md §5 and frontend lib/api.ts."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    analysisId: str
    analysis: str
    feedback: str
    recommendations: List[str]
    score: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None
    createdAt: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    version: str
    ai_provider: str
    ai_available: bool


class FeedbackAPIRequest(BaseModel):
    """Payload for generating or refreshing feedback on a debate argument."""
    model_config = ConfigDict(extra="ignore")

    input: str = Field(..., description="Debate text or argument submission to generate feedback for")
    analysis_id: Optional[str] = Field(default=None, description="Linked analysis identifier if refreshing feedback")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific feedback focus areas (e.g. logic, evidence, grammar)")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Prior turns or session records")
    session_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contextual metadata")


class FeedbackAPIResponse(BaseModel):
    """Structured feedback response conforming to ARCHITECTURE.md §5."""
    model_config = ConfigDict(extra="ignore")

    success: bool = True
    analysisId: str
    feedback: str
    recommendations: List[str]
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    focus_areas: Optional[List[str]] = None
    score: Optional[Dict[str, Any]] = None
    createdAt: str

