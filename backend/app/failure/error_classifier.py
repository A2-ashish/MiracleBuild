"""Error classifier — maps raw exceptions to user-friendly error messages.

Inspects exception types and message content to produce a structured
``PipelineError`` with a human-readable reason, code, and suggestion.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Machine-readable error codes surfaced to the frontend."""

    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"
    API_KEY_INVALID = "API_KEY_INVALID"
    API_KEY_MISSING = "API_KEY_MISSING"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    MODEL_OVERLOADED = "MODEL_OVERLOADED"
    CONTENT_SAFETY_BLOCKED = "CONTENT_SAFETY_BLOCKED"
    RESPONSE_PARSE_ERROR = "RESPONSE_PARSE_ERROR"
    CONTEXT_LENGTH_EXCEEDED = "CONTEXT_LENGTH_EXCEEDED"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class PipelineError:
    """Structured error returned to the user."""

    code: ErrorCode
    message: str  # user-friendly summary
    suggestion: str  # actionable next step
    stage: str = ""  # which pipeline stage failed
    detail: str = ""  # raw technical detail (optional)
    retryable: bool = False


# --------------------------------------------------------------------------
# Pattern-based classification rules
# --------------------------------------------------------------------------

_RULES: list[tuple[list[str], ErrorCode, str, str, bool]] = [
    # (patterns_any_match, code, user_message, suggestion, retryable)
    (
        ["429", "RESOURCE_EXHAUSTED", "rate limit", "quota", "Too Many Requests",
         "ResourceExhausted", "rateLimitExceeded", "Quota exceeded"],
        ErrorCode.API_RATE_LIMIT,
        "API rate limit exceeded — too many requests sent in a short period.",
        "Wait a minute and try again. If this keeps happening, add more API keys in your .env file or switch to a faster model (Gemini Flash).",
        True,
    ),
    (
        ["quota exceeded", "billing", "BILLING_DISABLED", "exceeded your current quota",
         "insufficient_quota", "billing not enabled"],
        ErrorCode.API_QUOTA_EXCEEDED,
        "API quota exceeded — your Gemini API key has hit its usage limit.",
        "Check your Google AI Studio billing/quota dashboard. Add a new API key or wait for the quota to reset.",
        False,
    ),
    (
        ["API_KEY_INVALID", "invalid api key", "API key not valid",
         "INVALID_ARGUMENT", "API key expired", "invalid key"],
        ErrorCode.API_KEY_INVALID,
        "Invalid API key — the Gemini API key is not valid or has been revoked.",
        "Double-check your GEMINI_API_KEY / GEMINI_API_KEYS in the .env file. Generate a fresh key at https://aistudio.google.com/apikey",
        False,
    ),
    (
        ["No API keys provided", "api_key is required", "missing api key"],
        ErrorCode.API_KEY_MISSING,
        "No API key configured — the server doesn't have a Gemini API key.",
        "Set GEMINI_API_KEY in your backend .env file. You can get a key from https://aistudio.google.com/apikey",
        False,
    ),
    (
        ["model not found", "is not found", "models/", "not found for API version",
         "NOT_FOUND", "does not exist"],
        ErrorCode.MODEL_NOT_FOUND,
        "Model not found — the selected model is not available.",
        "Try switching to a different model (e.g. Gemini 2.5 Flash or Gemini 2.0 Flash) from the model selector.",
        False,
    ),
    (
        ["overloaded", "503", "SERVICE_UNAVAILABLE", "model is overloaded",
         "The model is overloaded", "capacity"],
        ErrorCode.MODEL_OVERLOADED,
        "Model overloaded — the Gemini API is experiencing high traffic.",
        "Wait a few minutes and retry. You can also try a different model (e.g. Gemini Flash) which may have more capacity.",
        True,
    ),
    (
        ["safety", "SAFETY", "blocked", "HARM_CATEGORY", "content_filter",
         "BLOCKED", "FinishReason.SAFETY", "PROHIBITED_CONTENT"],
        ErrorCode.CONTENT_SAFETY_BLOCKED,
        "Content blocked by safety filters — the prompt or response triggered content safety checks.",
        "Rephrase your application description to avoid ambiguous or sensitive terms, then try again.",
        False,
    ),
    (
        ["failed to parse", "JSON decode error", "JSONDecodeError",
         "Expecting value", "model returned empty", "Unterminated string"],
        ErrorCode.RESPONSE_PARSE_ERROR,
        "Failed to parse AI response — the model returned malformed output.",
        "Try again — this is usually a one-time issue. If it persists, try a different model or simplify your prompt.",
        True,
    ),
    (
        ["context length", "token limit", "max tokens", "too long",
         "CONTEXT_LENGTH_EXCEEDED", "maximum context length", "prompt is too long"],
        ErrorCode.CONTEXT_LENGTH_EXCEEDED,
        "Prompt too long — the application description exceeds the model's context limit.",
        "Shorten your prompt or break it into smaller pieces. Try a model with a larger context window.",
        False,
    ),
    (
        ["ConnectionError", "ConnectionRefusedError", "getaddrinfo failed",
         "Name or service not known", "Network is unreachable",
         "RemoteDisconnected", "ConnectionReset"],
        ErrorCode.NETWORK_ERROR,
        "Network error — unable to connect to the Gemini API.",
        "Check your internet connection and firewall settings, then try again.",
        True,
    ),
    (
        ["TimeoutError", "timed out", "deadline exceeded", "DEADLINE_EXCEEDED",
         "ReadTimeout", "ConnectTimeout"],
        ErrorCode.TIMEOUT_ERROR,
        "Request timed out — the API took too long to respond.",
        "Try again. If the problem persists, try a faster model (Gemini Flash) or simplify your prompt.",
        True,
    ),
    (
        ["PERMISSION_DENIED", "permission denied", "403", "Forbidden",
         "not authorized", "access denied"],
        ErrorCode.PERMISSION_DENIED,
        "Permission denied — your API key doesn't have access to the requested resource.",
        "Verify your API key has the correct permissions. Make sure the selected model is available in your region.",
        False,
    ),
    (
        ["500", "INTERNAL", "Internal Server Error", "internal error"],
        ErrorCode.SERVER_ERROR,
        "Gemini API server error — the service encountered an internal problem.",
        "This is a temporary issue on Google's side. Wait a minute and try again.",
        True,
    ),
]


def classify_error(
    exc: Exception,
    stage: str = "",
) -> PipelineError:
    """Inspect an exception and return a user-friendly ``PipelineError``.

    The classifier checks the exception message against known patterns
    and returns a structured error. Falls back to ``UNKNOWN`` if no
    pattern matches.
    """
    exc_str = str(exc)
    exc_type = type(exc).__name__

    # Check each rule
    for patterns, code, message, suggestion, retryable in _RULES:
        for pattern in patterns:
            if pattern.lower() in exc_str.lower() or pattern.lower() in exc_type.lower():
                logger.info(
                    "Classified error as %s (matched pattern '%s')",
                    code.value,
                    pattern,
                )
                return PipelineError(
                    code=code,
                    message=message,
                    suggestion=suggestion,
                    stage=stage,
                    detail=_truncate(exc_str, 300),
                    retryable=retryable,
                )

    # Fallback — unknown error
    logger.warning("Could not classify error: %s: %s", exc_type, exc_str[:200])
    return PipelineError(
        code=ErrorCode.UNKNOWN,
        message=f"An unexpected error occurred during pipeline execution.",
        suggestion="Try again. If the problem persists, check the server logs or try a different model.",
        stage=stage,
        detail=_truncate(exc_str, 300),
        retryable=True,
    )


def _truncate(text: str, max_len: int) -> str:
    """Truncate text, adding ellipsis if too long."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
