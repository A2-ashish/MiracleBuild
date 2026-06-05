"""Async wrapper around the Google Generative AI SDK with retry, token tracking, and cost estimation."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Type

from pydantic import BaseModel
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Pricing per token (USD) — approximations as of mid-2025
_MODEL_COSTS: dict[str, dict[str, float]] = {
    "gemini-2.5-pro": {"input": 1.25 / 1_000_000, "output": 10.0 / 1_000_000},
    "gemini-2.5-flash": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gemini-2.0-flash": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
}

# Retry configuration
_MAX_RETRIES = 3
_BASE_DELAY_S = 1.0


class LLMClient:
    """Thin async client over Google Generative AI with structured-output support.

    Args:
        api_key: Gemini API key.
        model: Model identifier (e.g. ``gemini-2.5-pro``).
        temperature: Sampling temperature (0-2). Lower is more deterministic.
    """

    def __init__(
        self,
        api_keys: str | list[str],
        model: str = "gemini-2.5-pro",
        temperature: float = 0.1,
    ) -> None:
        self.api_keys = [api_keys] if isinstance(api_keys, str) else list(api_keys)
        if not self.api_keys:
            raise ValueError("No API keys provided")
        self.current_key_idx = 0
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
        self.model = model
        self.temperature = temperature
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def _rotate_key(self):
        old_idx = self.current_key_idx
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        self.client = genai.Client(api_key=self.api_keys[self.current_key_idx])
        logger.warning(f"Rotated API key from index {old_idx} to {self.current_key_idx}")

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        response_schema: Type[BaseModel] | None = None,
    ) -> str:
        """Generate text from a prompt, optionally enforcing a Pydantic schema.

        The call is retried up to ``_MAX_RETRIES`` times with exponential
        back-off on transient errors.

        Args:
            prompt: The user-facing prompt text.
            system_instruction: Optional system-level instruction prepended to the request.
            response_schema: If provided, Gemini is asked to return JSON that
                conforms to this Pydantic model.

        Returns:
            The raw text emitted by the model (JSON string when
            ``response_schema`` is supplied).
        """
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction if system_instruction else None,
        )

        if response_schema is not None:
            config.response_mime_type = "application/json"
            # Instead of passing response_schema to the SDK, which crashes on complex nested Enums,
            # we dump the Pydantic schema and inject it into the system instruction.
            import json
            schema_json = response_schema.model_json_schema()
            schema_str = json.dumps(schema_json, indent=2)
            
            base_instruction = system_instruction or ""
            new_instruction = (
                f"{base_instruction}\n\n"
                "IMPORTANT: You MUST return a valid JSON object that adheres exactly to the following JSON Schema:\n"
                f"{schema_str}"
            ).strip()
            config.system_instruction = new_instruction

        last_exc: Exception | None = None
        max_attempts = max(_MAX_RETRIES, len(self.api_keys) + 1)
        
        for attempt in range(max_attempts):
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=prompt,
                    config=config,
                )

                # Track token usage
                if response.usage_metadata:
                    self.total_input_tokens += (
                        response.usage_metadata.prompt_token_count or 0
                    )
                    self.total_output_tokens += (
                        response.usage_metadata.candidates_token_count or 0
                    )

                text = response.text
                if text is None:
                    raise ValueError("Model returned empty response")
                return text

            except Exception as exc:
                last_exc = exc
                exc_str = str(exc)
                if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                    logger.warning("Quota exhausted for current key.")
                    if len(self.api_keys) > 1:
                        self._rotate_key()
                        await asyncio.sleep(0.5)  # Brief pause to avoid hammering
                        continue
                        
                delay = _BASE_DELAY_S * (2 ** attempt)
                logger.warning(
                    "LLM call attempt %d/%d failed: %s — retrying in %.1fs",
                    attempt + 1,
                    max_attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

        raise RuntimeError(
            f"LLM call failed after {max_attempts} retries: {last_exc}"
        ) from last_exc

    # ------------------------------------------------------------------
    # Observability helpers
    # ------------------------------------------------------------------

    def get_token_usage(self) -> dict[str, int]:
        """Return cumulative token counts."""
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
        }

    def estimate_cost(self) -> float:
        """Return estimated USD cost based on cumulative token usage."""
        rates = _MODEL_COSTS.get(self.model, _MODEL_COSTS["gemini-2.5-pro"])
        return (
            self.total_input_tokens * rates["input"]
            + self.total_output_tokens * rates["output"]
        )

    def reset_usage(self) -> None:
        """Reset cumulative token counters to zero."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
