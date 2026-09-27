"""Tests for ai/pattern_detection.py."""

from ai.input_processing import process_input
from ai.pattern_detection import (
    MAX_HISTORY_WINDOW,
    detect_grammar_errors,
    detect_patterns,
    extract_features,
)
from ai.schemas.feedback_schema import PatternFeatures


def test_no_previous_history():
    processed = process_input("Education should be completely tuition-free for all citizens.")
    patterns = detect_patterns(processed, history=None)

    assert isinstance(patterns, PatternFeatures)
    assert patterns.improvement_trends["history_available"] is False
    assert patterns.improvement_trends["score_trend"] == "no_history"
    assert patterns.confidence > 0.6


def test_repeated_grammar_and_spelling_mistakes():
    # Input has their/there, loose/lose, and alot
    text = "Their is no doubt that teams loose alot of points when they fail to provide warrants."
    processed = process_input(text)
    features = extract_features(processed)

    detected_names = [e["name"] for e in features["grammar_errors"]]
    assert any("their/there" in n for n in detected_names)
    assert any("loose/lose" in n for n in detected_names)
    assert any("a lot" in n for n in detected_names)


def test_repeated_errors_across_interactions():
    # Interaction history where user repeatedly made their/there mistake
    history = [
        {"errors": ["their/there confusion"], "overall_score": 65.0},
        {"errors": ["their/there confusion"], "overall_score": 68.0},
    ]

    current_text = "Their is another reason why carbon taxation is essential."
    processed = process_input(current_text)
    patterns = detect_patterns(processed, history=history)

    assert any("Recurring mistake: their/there confusion" in err for err in patterns.repeated_errors)
    assert patterns.improvement_trends["history_available"] is True


def test_repeated_arguments_and_cliches():
    history = [
        {"text": "At the end of the day, artificial intelligence cannot replace human empathy."},
    ]
    current_text = "At the end of the day, we must consider the human factors."
    processed = process_input(current_text)
    patterns = detect_patterns(processed, history=history)

    assert any("Repeated cliché" in p for p in patterns.repeated_phrases)


def test_vocabulary_diversity_and_weak_words():
    # Very repetitive vocabulary with high word count
    repetitive_text = "The thing is a thing and the thing is a bad thing and a bad thing and a bad thing."
    processed = process_input(repetitive_text)
    features = extract_features(processed)

    assert features["vocab_stats"]["ttr"] < 0.6
    assert len(features["vocab_stats"]["weak_words_used"]) > 0


def test_sentence_structure_run_on_and_fragments():
    # Run on: 46 words in single sentence without punctuation
    long_sentence = (
        "The economic implications of space exploration are extraordinarily vast and encompass numerous technological "
        "innovations that benefit humanity across communications and agriculture and manufacturing while simultaneously "
        "expanding the horizons of scientific knowledge and inspiring the next generation of engineers and philosophers "
        "to solve our most pressing ecological crises on earth."
    )
    processed = process_input(long_sentence)
    features = extract_features(processed)

    issues = features["structure_stats"]["structure_issues"]
    assert any("run-on" in issue.lower() for issue in issues)


def test_improvement_trend_detection():
    # History with lower scores
    history = [
        {"overall_score": 50.0},
        {"overall_score": 52.0},
    ]
    # High-quality current text with evidence
    current_text = (
        "According to research published by university economists, early childhood education "
        "demonstrates a seven-to-one return on investment because early intervention dramatically "
        "reduces remedial education and criminal justice expenditures."
    )
    processed = process_input(current_text)
    patterns = detect_patterns(processed, history=history)

    assert patterns.improvement_trends["score_trend"] == "improving"


def test_bounded_history_window():
    # Pass 15 historical items, verify only MAX_HISTORY_WINDOW (5) are analyzed
    large_history = [{"overall_score": 60.0 + i} for i in range(15)]
    processed = process_input("Democratic institutions require active civic participation.")
    patterns = detect_patterns(processed, history=large_history)

    assert patterns.improvement_trends["interactions_analyzed"] == MAX_HISTORY_WINDOW
