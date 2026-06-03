"""Stage 1 — Intent Extraction.

Converts a free-form user prompt into a structured ``IntentResult``.
"""
from __future__ import annotations

import logging
from typing import List

from app.llm.client import LLMClient
from app.llm.prompts import INTENT_EXTRACTION_SYSTEM, INTENT_EXTRACTION_USER
from app.llm.response_parser import parse_into_model
from app.schemas.intent import IntentResult, Assumption

logger = logging.getLogger(__name__)

# Minimum word count before we inject default assumptions
_MIN_WORDS = 10

_DEFAULT_ASSUMPTIONS: List[Assumption] = [
    Assumption(
        description="Application requires user authentication with email/password",
        reason="No auth mechanism was specified",
        impact="medium",
    ),
    Assumption(
        description="Two default roles assumed: admin and regular user",
        reason="No roles were specified",
        impact="medium",
    ),
    Assumption(
        description="Application uses a relational database",
        reason="No data-store preference given",
        impact="low",
    ),
    Assumption(
        description="A responsive web dashboard interface is assumed",
        reason="No UI preference specified",
        impact="low",
    ),
]


class IntentExtractor:
    """Extracts structured intent from a natural-language prompt."""

    async def extract(self, prompt: str, llm: LLMClient) -> IntentResult:
        """Run intent extraction.

        If the prompt is shorter than ``_MIN_WORDS`` words the model is
        nudged with default assumptions so it can still produce a useful
        result.

        Args:
            prompt: Raw user description of the desired application.
            llm: Configured LLM client.

        Returns:
            Validated ``IntentResult``.

        Raises:
            ValueError: If the model output cannot be parsed.
        """
        enhanced_prompt = prompt
        forced_assumptions: list[Assumption] = []

        if len(prompt.split()) < _MIN_WORDS:
            logger.info(
                "Prompt has fewer than %d words — injecting default assumptions",
                _MIN_WORDS,
            )
            enhanced_prompt = (
                f"{prompt}\n\nAdditional context: This application needs user "
                "authentication with email/password login, an admin and a "
                "regular-user role, a relational database, and a modern web "
                "dashboard UI. Make reasonable assumptions for anything not "
                "explicitly mentioned."
            )
            forced_assumptions = list(_DEFAULT_ASSUMPTIONS)

        user_msg = INTENT_EXTRACTION_USER.format(user_prompt=enhanced_prompt)
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=INTENT_EXTRACTION_SYSTEM,
            response_schema=IntentResult,
        )

        result, errors = parse_into_model(raw, IntentResult)
        if result is None:
            raise ValueError(
                f"Intent extraction failed to parse: {'; '.join(errors)}"
            )

        # Merge in forced assumptions (avoid duplicates)
        existing = {a.description for a in result.assumptions}
        for a in forced_assumptions:
            if a.description not in existing:
                result.assumptions.append(a)

        logger.info(
            "Intent extracted: app=%s, entities=%d, features=%d",
            result.app_name,
            len(result.entities),
            len(result.features),
        )
        return result
