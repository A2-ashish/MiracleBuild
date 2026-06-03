"""Safe JSON extraction and Pydantic parsing utilities."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def extract_json_string(raw: str) -> str:
    """Extract JSON from a string that may contain markdown fences.

    Handles:
    - ``````json … `````` fenced blocks
    - Bare JSON objects / arrays
    - Trailing commas before ``}`` or ``]``
    - Truncated JSON (attempts to close open brackets)

    Returns:
        A cleaned JSON string ready for ``json.loads``.
    """
    text = raw.strip()

    # 1. Strip markdown code fences
    fence_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL
    )
    if fence_match:
        text = fence_match.group(1).strip()

    # 2. Try to find the outermost JSON object or array
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start_idx = text.find(start_char)
        if start_idx == -1:
            continue
        end_idx = text.rfind(end_char)
        if end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]
            break
        else:
            # Truncated — take from start_char onwards and try to close
            text = text[start_idx:]
            break

    # 3. Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 4. Attempt to close unclosed brackets (truncation recovery)
    text = _attempt_close_brackets(text)

    return text


def _attempt_close_brackets(text: str) -> str:
    """Heuristically close unclosed brackets/braces in *text*."""
    stack: list[str] = []
    in_string = False
    escape = False

    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            stack.append(ch)
        elif ch == "}" and stack and stack[-1] == "{":
            stack.pop()
        elif ch == "]" and stack and stack[-1] == "[":
            stack.pop()

    # Close in reverse order
    closers = {"[": "]", "{": "}"}
    while stack:
        opener = stack.pop()
        text += closers.get(opener, "")

    return text


def parse_json(raw: str) -> tuple[Any, list[str]]:
    """Parse a raw string into a Python object.

    Returns:
        A tuple of ``(parsed_data, errors)`` where *errors* is a list of
        human-readable strings (empty on success).
    """
    errors: list[str] = []
    cleaned = extract_json_string(raw)
    try:
        data = json.loads(cleaned)
        return data, errors
    except json.JSONDecodeError as exc:
        errors.append(f"JSON decode error: {exc}")
        return None, errors


def parse_into_model(
    raw: str, model_class: Type[T]
) -> tuple[T | None, list[str]]:
    """Parse a raw JSON string into a Pydantic model instance.

    Args:
        raw: Raw text (possibly markdown-fenced JSON).
        model_class: Target Pydantic model type.

    Returns:
        ``(model_instance, [])`` on success, or ``(None, [error_messages])``
        on failure.
    """
    data, json_errors = parse_json(raw)
    if json_errors:
        return None, json_errors

    try:
        instance = model_class.model_validate(data)
        return instance, []
    except ValidationError as exc:
        errors = [
            f"Field '{'.'.join(str(l) for l in e['loc'])}': {e['msg']}"
            for e in exc.errors()
        ]
        return None, errors
