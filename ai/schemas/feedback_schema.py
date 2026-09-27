"""Schema definitions for AI Penfight."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict


class CorrectionItem(BaseModel):
    """Represents a grammar, spelling, or vocabulary issue with correction."""
    model_config = ConfigDict(extra="ignore")

    error_type: str = Field(
        ...,
        description="Type of error: grammar, spelling, vocabulary, punctuation, or structure"
    )
    original: str = Field(..., description="The original problematic phrase or word")
    correction: str = Field(..., description="The recommended replacement or correction")
    explanation: str = Field(..., description="Reason for the correction")


class FallacyItem(BaseModel):
    """Represents an identified logical fallacy or reasoning flaw."""
    model_config = ConfigDict(extra="ignore")

    fallacy_name: str = Field(
        ...,
        description="Name of the fallacy, e.g. Ad Hominem, Straw Man, Slippery Slope, False Dilemma"
    )
    quote: str = Field(..., description="Quote from user input demonstrating the fallacy")
    explanation: str = Field(..., description="Detailed explanation of why this reasoning is flawed")
    severity: str = Field(
        default="medium",
        description="Severity level: low, medium, high"
    )


class PerformanceScore(BaseModel):
    """Detailed score criteria for debate argument evaluation (0 - 100 scale)."""
    model_config = ConfigDict(extra="ignore")

    argument_strength: float = Field(
        ..., ge=0.0, le=100.0,
        description="Clarity, persuasiveness, and relevance of the central thesis"
    )
    logic_and_reasoning: float = Field(
        ..., ge=0.0, le=100.0,
        description="Soundness of deductive/inductive inferences and absence of fallacies"
    )
    evidence_and_support: float = Field(
        ..., ge=0.0, le=100.0,
        description="Use of factual backing, examples, or structured reasoning"
    )
    clarity_and_style: float = Field(
        ..., ge=0.0, le=100.0,
        description="Grammar, vocabulary richness, sentence structure, and tone"
    )
    rebuttal_effectiveness: float = Field(
        ..., ge=0.0, le=100.0,
        description="Effectiveness in addressing counter-arguments or opposing views"
    )
    overall_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Weighted composite score of the above criteria"
    )
    breakdown: Dict[str, str] = Field(
        default_factory=dict,
        description="Brief qualitative justification for each individual score criterion"
    )


class FeedbackResponse(BaseModel):
    """Validated structured feedback returned by the AI module."""
    model_config = ConfigDict(extra="ignore")

    analysis_id: str = Field(..., description="Unique identifier for this analysis run")
    overall_feedback: str = Field(..., description="Executive summary and overall impression")
    strengths: List[str] = Field(
        default_factory=list,
        description="Specific strong points of the argument"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Specific weak points or logical gaps identified"
    )
    logical_fallacies: List[FallacyItem] = Field(
        default_factory=list,
        description="Identified logical fallacies with evidence quotes"
    )
    grammar_and_vocabulary: List[CorrectionItem] = Field(
        default_factory=list,
        description="Concrete linguistic and grammatical corrections"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Constructive guidance to strengthen the argument"
    )
    actionable_recommendations: List[str] = Field(
        default_factory=list,
        description="Clear, numbered steps for the next debate round"
    )
    performance_score: PerformanceScore = Field(
        ...,
        description="Explicit criteria-based scoring"
    )
    prompt_version: str = Field(default="v1.0.0", description="Version of the prompt template used")
    strategy_applied: str = Field(default="standard", description="Analysis strategy decided")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of creation"
    )


class ProcessedInput(BaseModel):
    """Structured, validated, and normalized user input."""
    model_config = ConfigDict(extra="ignore")

    session_id: str = Field(..., description="Unique identifier for user session")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")
    raw_text: str = Field(..., description="Raw text as provided")
    normalized_text: str = Field(..., description="Sanitized, normalized text")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of input reception"
    )
    session_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata (e.g. topic, round, side)"
    )
    char_count: int = Field(..., ge=0)
    word_count: int = Field(..., ge=0)


class PatternFeatures(BaseModel):
    """Extracted linguistic, rhetorical, and historical pattern features."""
    model_config = ConfigDict(extra="ignore")

    detected_patterns: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Specific patterns detected with category and confidence"
    )
    repeated_errors: List[str] = Field(
        default_factory=list,
        description="Grammar or argument errors appearing repeatedly"
    )
    improvement_trends: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metrics comparing current performance against history"
    )
    performance_signals: Dict[str, Any] = Field(
        default_factory=dict,
        description="Low-level signals (TTR, sentence lengths, readability, fallacy flags)"
    )
    confidence: float = Field(
        default=0.85, ge=0.0, le=1.0,
        description="Confidence score for pattern detection"
    )
    vocabulary_diversity: float = Field(default=0.0, ge=0.0, le=1.0)
    repeated_phrases: List[str] = Field(default_factory=list)
    sentence_structure_issues: List[str] = Field(default_factory=list)


class DecisionResult(BaseModel):
    """Output of the Decision Engine determining pipeline strategy."""
    model_config = ConfigDict(extra="ignore")

    decision: str = Field(
        ...,
        description="Decision status: PROCEED_WITH_LLM, RULE_BASED_EVALUATION, SAFETY_FLAG, REJECT_INVALID"
    )
    analysis_strategy: str = Field(
        ...,
        description="Strategy: comprehensive_debate_analysis, fallacy_and_logic_focus, style_and_delivery, quick_rule_critique, safety_warning"
    )
    reason: str = Field(..., description="Human-readable justification for the decision")
    priority_patterns: List[str] = Field(
        default_factory=list,
        description="Ranked patterns/weaknesses that must be prioritized in feedback"
    )
    use_llm: bool = Field(..., description="Whether an external LLM call is required")


class EvaluationMetric(BaseModel):
    """Individual metric result in the evaluation system."""
    name: str
    score: float
    description: str
    details: Optional[Dict[str, Any]] = None


class SingleEvaluationResult(BaseModel):
    """Evaluation result for a single interaction feedback."""
    analysis_id: str
    schema_validity: float
    feedback_relevance: float
    grammar_accuracy: float
    pattern_detection_accuracy: float
    logical_analysis_quality: float
    latency_ms: float
    overall_quality_score: float
    estimated_cost_usd: float = 0.0
    token_usage: Dict[str, int] = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)


class BatchEvaluationReport(BaseModel):
    """Aggregated evaluation report across multiple test cases."""
    total_cases: int
    successful_cases: int
    mean_schema_validity: float
    mean_feedback_relevance: float
    mean_grammar_accuracy: float
    mean_pattern_accuracy: float
    mean_logical_quality: float
    mean_overall_quality: float
    p95_latency_ms: float
    total_estimated_cost_usd: float
    results: List[SingleEvaluationResult] = Field(default_factory=list)
