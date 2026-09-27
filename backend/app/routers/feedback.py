"""Feedback API router conforming to ARCHITECTURE.md §5."""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ai.decision_engine import decide_strategy
from ai.feedback_generation import generate_feedback
from ai.input_processing import InputValidationError, process_input
from ai.pattern_detection import detect_patterns
from backend.app.schemas import ErrorResponse, FeedbackAPIRequest, FeedbackAPIResponse

logger = logging.getLogger("ai_penfight.routers.feedback")

router = APIRouter(tags=["AI Feedback"])


def run_feedback_pipeline(payload: FeedbackAPIRequest) -> FeedbackAPIResponse:
    """Execute the feedback pipeline for new or existing analysis."""
    # 1. Input Processing
    processed = process_input(
        raw_input=payload.input,
        session_id=payload.session_id,
        user_id=payload.user_id,
        session_context=payload.session_context,
    )

    # 2. Pattern Detection
    patterns = detect_patterns(
        processed_input=processed,
        history=payload.history,
    )

    # 3. Decision Engine
    decision = decide_strategy(
        processed_input=processed,
        pattern_features=patterns,
    )

    # 4. Feedback Generation
    feedback = generate_feedback(
        processed_input=processed,
        pattern_features=patterns,
        decision=decision,
        history=payload.history,
    )

    # Use existing analysis_id if refreshing feedback
    analysis_id = payload.analysis_id or feedback.analysis_id

    # Filter recommendations if focus_areas are specified
    recs = list(feedback.actionable_recommendations)
    for err in patterns.repeated_errors:
        recs.append(f"Address recurring issue: {err}")

    if payload.focus_areas:
        focus_lower = [f.lower() for f in payload.focus_areas]
        focused_recs = [
            r for r in recs
            if any(term in r.lower() for term in focus_lower)
        ]
        if focused_recs:
            recs = focused_recs

    return FeedbackAPIResponse(
        success=True,
        analysisId=analysis_id,
        feedback="\n".join(feedback.suggestions) if feedback.suggestions else feedback.overall_feedback,
        recommendations=recs,
        strengths=feedback.strengths,
        weaknesses=feedback.weaknesses,
        focus_areas=payload.focus_areas,
        score=feedback.performance_score.model_dump(),
        createdAt=feedback.created_at,
    )


@router.post(
    "/api/v1/feedback",
    response_model=FeedbackAPIResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Generate or refresh feedback for an existing or new debate analysis",
)
async def feedback_v1_endpoint(payload: FeedbackAPIRequest):
    """V1 API feedback endpoint matching ARCHITECTURE.md §5."""
    try:
        return run_feedback_pipeline(payload)
    except InputValidationError as exc:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                },
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during feedback generation: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "FEEDBACK_GENERATION_ERROR",
                    "message": "An error occurred while generating feedback. Please try again.",
                },
            },
        )


@router.post(
    "/api/ai/feedback",
    response_model=FeedbackAPIResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Submit input to generate or refresh feedback (AI module alias)",
)
async def feedback_ai_endpoint(payload: FeedbackAPIRequest):
    return await feedback_v1_endpoint(payload)
