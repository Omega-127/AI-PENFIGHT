"""Analysis API router integrating the AI Penfight pipeline."""

import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ai.decision_engine import decide_strategy
from ai.feedback_generation import generate_feedback
from ai.input_processing import InputValidationError, process_input
from ai.pattern_detection import detect_patterns
from backend.app.schemas import AnalyzeAPIRequest, AnalyzeAPIResponse, ErrorResponse

logger = logging.getLogger("ai_penfight.routers.analysis")

router = APIRouter(tags=["AI Analysis"])


def run_pipeline(payload: AnalyzeAPIRequest) -> AnalyzeAPIResponse:
    """Execute the sequential AI Penfight pipeline:

    Raw Input -> Input Processing -> Pattern Detection -> Decision Engine -> Feedback Generation
    """
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

    # 5. Format to unified API contract
    return AnalyzeAPIResponse(
        success=True,
        analysisId=feedback.analysis_id,
        analysis=feedback.overall_feedback,
        feedback="\n".join(feedback.suggestions) if feedback.suggestions else feedback.overall_feedback,
        recommendations=feedback.actionable_recommendations,
        score=feedback.performance_score.model_dump(),
        details={
            "strengths": feedback.strengths,
            "weaknesses": feedback.weaknesses,
            "logical_fallacies": [f.model_dump() for f in feedback.logical_fallacies],
            "grammar_and_vocabulary": [c.model_dump() for c in feedback.grammar_and_vocabulary],
            "priority_patterns": decision.priority_patterns,
            "decision": decision.model_dump(),
            "prompt_version": feedback.prompt_version,
            "strategy_applied": feedback.strategy_applied,
        },
        createdAt=feedback.created_at,
    )


@router.post(
    "/api/ai/analyze",
    response_model=AnalyzeAPIResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Submit debate input for AI analysis (AI module endpoint)",
)
async def analyze_ai_endpoint(payload: AnalyzeAPIRequest):
    """Primary endpoint for AI Penfight analysis."""
    try:
        return run_pipeline(payload)
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
        logger.exception("Unexpected error during debate analysis: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "AI_PROCESSING_ERROR",
                    "message": "An error occurred while analyzing the debate submission. Please try again.",
                },
            },
        )


@router.post(
    "/api/v1/analyze",
    response_model=AnalyzeAPIResponse,
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Submit debate input for AI analysis (v1 contract alias)",
)
async def analyze_v1_endpoint(payload: AnalyzeAPIRequest):
    """V1 API contract endpoint matching ARCHITECTURE.md §5."""
    return await analyze_ai_endpoint(payload)
