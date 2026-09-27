"""Tests for ai/input_processing.py."""

import pytest
from ai.input_processing import (
    InputValidationError,
    normalize_text,
    process_input,
)
from ai.schemas.feedback_schema import ProcessedInput


def test_normal_valid_debate_input():
    raw_text = "Universal basic income is necessary to mitigate automation-induced technological unemployment."
    processed = process_input(raw_text)

    assert isinstance(processed, ProcessedInput)
    assert processed.raw_text == raw_text
    assert processed.normalized_text == raw_text
    assert processed.word_count == 11
    assert processed.char_count == len(raw_text)
    assert processed.session_id.startswith("sess_")
    assert processed.timestamp is not None


def test_input_normalization_and_typography():
    # Includes curly quotes, non-breaking space, em-dash, and extra spaces
    dirty_text = "  \u201cRenewable  energy\u201d\u00a0is\u2014vital   for \nour\r\nplanet.  "
    processed = process_input(dirty_text)

    # Should convert curly quotes to straight, em-dash to " -- ", collapse spaces
    assert '"Renewable energy"' in processed.normalized_text
    assert " -- " in processed.normalized_text
    assert "  " not in processed.normalized_text
    assert not processed.normalized_text.startswith(" ")


def test_control_character_stripping():
    # Null bytes and control characters
    text_with_null = "Carbon taxes\x00 are effective\x07 in reducing emissions."
    processed = process_input(text_with_null)
    assert "\x00" not in processed.normalized_text
    assert "\x07" not in processed.normalized_text
    assert "Carbon taxes are effective in reducing emissions." == processed.normalized_text


def test_empty_and_whitespace_input_rejected():
    with pytest.raises(InputValidationError, match="cannot be empty or solely whitespace"):
        process_input("")

    with pytest.raises(InputValidationError, match="cannot be empty or solely whitespace"):
        process_input("   \n\t   ")


def test_too_short_input_rejected():
    with pytest.raises(InputValidationError, match="too short"):
        process_input("A")


def test_extremely_long_input_rejected(monkeypatch):
    monkeypatch.setenv("MAX_INPUT_LENGTH", "100")
    long_text = "This debate assertion is deliberately made excessively long to exceed the hundred character limit configured in the test."
    with pytest.raises(InputValidationError, match="exceeds maximum allowed length"):
        process_input(long_text)


def test_dictionary_input_handling():
    payload = {
        "input": "Nuclear energy provides reliable baseline power.",
        "session_id": "sess_custom_123",
        "user_id": "user_456",
        "session_context": {
            "topic": "Clean Energy",
            "round": 1,
            "side": "affirmative",
            "password": "secret_should_be_stripped",
        }
    }
    processed = process_input(payload)

    assert processed.session_id == "sess_custom_123"
    assert processed.user_id == "user_456"
    assert processed.normalized_text == "Nuclear energy provides reliable baseline power."
    assert processed.session_context.get("topic") == "Clean Energy"
    assert processed.session_context.get("round") == 1
    # Check sensitive key removal
    assert "password" not in processed.session_context


def test_invalid_input_type_rejected():
    with pytest.raises(InputValidationError, match="Invalid input type"):
        process_input(12345)
