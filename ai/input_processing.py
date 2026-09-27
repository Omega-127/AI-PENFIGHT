"""Input Processing Module for AI Penfight.

Validates, cleans, and normalizes incoming debate inputs and session data.
Enforces size constraints, strips control characters, and constructs a
structured ProcessedInput object for downstream pattern detection.
"""

import os
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from ai.schemas.feedback_schema import ProcessedInput

# Configurable limits
DEFAULT_MAX_INPUT_LENGTH = 5000
DEFAULT_MIN_INPUT_LENGTH = 2


class InputValidationError(ValueError):
    """Raised when user input fails validation constraints."""
    pass


def get_max_input_length() -> int:
    """Retrieve maximum allowed input character length from environment or default."""
    try:
        return int(os.getenv("MAX_INPUT_LENGTH", str(DEFAULT_MAX_INPUT_LENGTH)))
    except (ValueError, TypeError):
        return DEFAULT_MAX_INPUT_LENGTH


def get_min_input_length() -> int:
    """Retrieve minimum allowed input character length from environment or default."""
    try:
        return int(os.getenv("MIN_INPUT_LENGTH", str(DEFAULT_MIN_INPUT_LENGTH)))
    except (ValueError, TypeError):
        return DEFAULT_MIN_INPUT_LENGTH


def normalize_text(text: str) -> str:
    """Normalize text by handling Unicode, smart quotes, control characters, and whitespace.

    - Normalizes Unicode to NFC form.
    - Replaces typographic quotes, dashes, and non-breaking spaces.
    - Strips non-printable ASCII control characters (preserving newlines/tabs).
    - Collapses multiple horizontal spaces and redundant blank lines.
    """
    if not isinstance(text, str):
        raise InputValidationError("Input text must be a valid string.")

    # 1. Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", text)

    # 2. Standardize typographic characters
    replacements = {
        "\u2018": "'",  # Left single quotation mark
        "\u2019": "'",  # Right single quotation mark
        "\u201c": '"',  # Left double quotation mark
        "\u201d": '"',  # Right double quotation mark
        "\u2014": " -- ",  # Em dash
        "\u2013": " - ",   # En dash
        "\u00a0": " ",     # Non-breaking space
        "\u2026": "...",   # Ellipsis
    }
    for char, repl in replacements.items():
        normalized = normalized.replace(char, repl)

    # 3. Strip dangerous / invisible control characters (preserve \n, \r, \t)
    normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)

    # 4. Standardize newlines
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # 5. Collapse consecutive horizontal whitespace (spaces/tabs), but keep paragraphs
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n\s*\n\s*\n+", "\n\n", normalized)

    # 6. Final strip
    return normalized.strip()


def validate_input_bounds(text: str, min_len: int, max_len: int) -> None:
    """Enforce minimum and maximum length bounds on normalized text."""
    if not text:
        raise InputValidationError("Input text cannot be empty or solely whitespace.")

    char_len = len(text)
    if char_len < min_len:
        raise InputValidationError(
            f"Input is too short ({char_len} characters). Minimum required is {min_len} characters."
        )

    if char_len > max_len:
        raise InputValidationError(
            f"Input exceeds maximum allowed length of {max_len} characters (received {char_len})."
        )


def process_input(
    raw_input: Union[str, Dict[str, Any], Any],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    session_context: Optional[Dict[str, Any]] = None,
) -> ProcessedInput:
    """Main input processing function.

    Accepts raw text or dictionary input, validates types and lengths,
    normalizes the content, and outputs a validated ProcessedInput object.

    Args:
        raw_input: A raw string or a dictionary containing 'input', 'text', or 'content'
        session_id: Optional session identifier (UUID generated if omitted)
        user_id: Optional user identifier (PII is excluded)
        session_context: Optional contextual parameters (topic, round, side, etc.)

    Returns:
        ProcessedInput: Validated, structured representation ready for pattern detection.

    Raises:
        InputValidationError: If input is null, non-string, empty, or exceeds bounds.
    """
    extracted_text = ""
    extracted_session_id = session_id
    extracted_user_id = user_id
    extracted_context = dict(session_context or {})

    # Extract text and session metadata depending on input shape
    if isinstance(raw_input, str):
        extracted_text = raw_input
    elif isinstance(raw_input, dict):
        # Look for standard keys
        for key in ("input", "raw_text", "text", "content", "argument"):
            if key in raw_input and isinstance(raw_input[key], str):
                extracted_text = raw_input[key]
                break

        if not extracted_text and "input" in raw_input and raw_input["input"] is not None:
            extracted_text = str(raw_input["input"])

        # Extract session info from dict if not explicitly provided as args
        if not extracted_session_id and "session_id" in raw_input:
            extracted_session_id = str(raw_input["session_id"])
        if not extracted_user_id and "user_id" in raw_input:
            extracted_user_id = str(raw_input["user_id"])
        if "session_context" in raw_input and isinstance(raw_input["session_context"], dict):
            extracted_context.update(raw_input["session_context"])
        elif "topic" in raw_input or "round" in raw_input or "mode" in raw_input:
            for ctx_key in ("topic", "round", "mode", "side", "motion"):
                if ctx_key in raw_input:
                    extracted_context[ctx_key] = raw_input[ctx_key]
    elif hasattr(raw_input, "input") and isinstance(raw_input.input, str):
        extracted_text = raw_input.input
        if hasattr(raw_input, "session_id") and raw_input.session_id:
            extracted_session_id = str(raw_input.session_id)
        if hasattr(raw_input, "user_id") and raw_input.user_id:
            extracted_user_id = str(raw_input.user_id)
    else:
        raise InputValidationError(
            f"Invalid input type: expected string or dictionary, got {type(raw_input).__name__}."
        )

    # Normalization
    normalized = normalize_text(extracted_text)

    # Bounds validation
    min_len = get_min_input_length()
    max_len = get_max_input_length()
    validate_input_bounds(normalized, min_len, max_len)

    # Word and character count
    words = re.findall(r"\b\w+\b", normalized)
    word_count = len(words)
    char_count = len(normalized)

    # Ensure robust session id
    if not extracted_session_id:
        extracted_session_id = f"sess_{uuid.uuid4().hex[:12]}"

    # Filter context to avoid sensitive PII (passwords, emails, tokens)
    sanitized_context = {
        k: v for k, v in extracted_context.items()
        if not any(sensitive in k.lower() for sensitive in ("pass", "secret", "token", "auth", "key", "email", "phone"))
    }

    return ProcessedInput(
        session_id=extracted_session_id,
        user_id=extracted_user_id,
        raw_text=extracted_text,
        normalized_text=normalized,
        timestamp=datetime.now(timezone.utc).isoformat(),
        session_context=sanitized_context,
        char_count=char_count,
        word_count=word_count,
    )
