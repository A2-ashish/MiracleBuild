"""Pipeline orchestrator — runs all five stages and collects metrics."""
from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, Optional

from app.llm.client import LLMClient
from app.schemas.app_config import (
    CompilationMetrics,
    CompilationResult,
    ValidationReport,
)
from app.schemas.intent import IntentResult
from app.pipeline.stage1_intent import IntentExtractor
from app.pipeline.stage2_design import SystemDesigner
from app.pipeline.stage3_schemas import SchemaGenerator
from app.pipeline.stage4_refinement import SchemaRefiner
from app.pipeline.stage5_validation import ValidationEngine
from app.failure.handler import FailureHandler
from app.failure.error_classifier import classify_error, PipelineError

logger = logging.getLogger(__name__)

# Type alias for an optional SSE callback:
#   callback(stage_name, status, data)
StageCallback = Callable[[str, str, dict[str, Any]], Awaitable[None]]


class CompilerOrchestrator:
    """End-to-end orchestrator that runs all pipeline stages.

    Args:
        api_keys: Gemini API key or list of keys.
        model: Model identifier.
        max_repair_cycles: Maximum validation/repair iterations.
    """

    def __init__(
        self,
        api_keys: str | list[str],
        model: str = "gemini-2.5-pro",
        max_repair_cycles: int = 3,
    ) -> None:
        self.api_keys = api_keys
        self.model = model
        self.max_repair_cycles = max_repair_cycles

    async def compile(
        self,
        prompt: str,
        callback: Optional[StageCallback] = None,
    ) -> CompilationResult:
        """Run the full compilation pipeline.

        Args:
            prompt: Natural-language application description.
            callback: Optional async callback invoked at the start and end
                of every stage for SSE streaming.

        Returns:
            ``CompilationResult`` with config, metrics, and validation report.
        """
        llm = LLMClient(
            api_keys=self.api_keys,
            model=self.model,
        )
        metrics = CompilationMetrics(model_used=self.model)
        assumptions: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []
        pipeline_start = time.perf_counter()

        # ---- Pre-processing ----
        handler = FailureHandler()
        enhanced_prompt, prompt_assumptions = handler.analyze_prompt(prompt)
        assumptions.extend(a.description for a in prompt_assumptions)

        # ---- Stage 1: Intent Extraction ----
        intent: Optional[IntentResult] = None
        try:
            intent = await self._run_stage(
                "intent_extraction",
                lambda: IntentExtractor().extract(enhanced_prompt, llm),
                llm,
                metrics,
                callback,
            )
            assumptions.extend(a.description for a in intent.assumptions)
        except Exception as exc:
            classified = classify_error(exc, stage="intent_extraction")
            errors.append(f"Intent extraction failed: {classified.message}")
            logger.exception("Stage 1 failed")
            return self._fail(errors, warnings, assumptions, metrics, pipeline_start, classified)

        # ---- Stage 2: System Design ----
        design = None
        try:
            design = await self._run_stage(
                "system_design",
                lambda: SystemDesigner().design(intent, llm),  # type: ignore[arg-type]
                llm,
                metrics,
                callback,
            )
        except Exception as exc:
            classified = classify_error(exc, stage="system_design")
            errors.append(f"System design failed: {classified.message}")
            logger.exception("Stage 2 failed")
            return self._fail(errors, warnings, assumptions, metrics, pipeline_start, classified)

        # ---- Stage 3: Schema Generation ----
        schemas = None
        try:
            schemas = await self._run_stage(
                "schema_generation",
                lambda: SchemaGenerator().generate(design, llm),  # type: ignore[arg-type]
                llm,
                metrics,
                callback,
            )
        except Exception as exc:
            classified = classify_error(exc, stage="schema_generation")
            errors.append(f"Schema generation failed: {classified.message}")
            logger.exception("Stage 3 failed")
            return self._fail(errors, warnings, assumptions, metrics, pipeline_start, classified)

        # ---- Stage 4: Refinement ----
        try:
            schemas = await self._run_stage(
                "refinement",
                lambda: SchemaRefiner().refine(schemas, llm),  # type: ignore[arg-type]
                llm,
                metrics,
                callback,
            )
        except Exception as exc:
            classified = classify_error(exc, stage="refinement")
            warnings.append(f"Refinement failed (non-fatal): {classified.message}")
            logger.warning("Stage 4 failed — continuing with unrefined schemas")

        # ---- Stage 5: Validation & Repair ----
        config = None
        validation_report = ValidationReport(is_valid=False)
        try:
            config, validation_report = await self._run_stage(
                "validation",
                lambda: ValidationEngine().validate_and_repair(
                    schemas,  # type: ignore[arg-type]
                    llm,
                    max_cycles=self.max_repair_cycles,
                    app_name=intent.app_name,  # type: ignore[union-attr]
                    app_description=intent.app_description,  # type: ignore[union-attr]
                    domain=intent.domain,  # type: ignore[union-attr]
                ),
                llm,
                metrics,
                callback,
            )
            metrics.repair_cycles = len(
                [l for l in validation_report.repair_log if l.startswith("Cycle")]
            )
            metrics.validation_checks_passed = sum(
                1 for c in validation_report.checks if c.passed
            )
            metrics.validation_checks_total = len(validation_report.checks)
        except Exception as exc:
            classified = classify_error(exc, stage="validation")
            errors.append(f"Validation failed: {classified.message}")
            logger.exception("Stage 5 failed")
            return self._fail(errors, warnings, assumptions, metrics, pipeline_start, classified)

        # ---- Finalise metrics ----
        metrics.total_duration_ms = (
            time.perf_counter() - pipeline_start
        ) * 1000
        usage = llm.get_token_usage()
        metrics.total_tokens = usage["input"] + usage["output"]
        metrics.estimated_cost_usd = round(llm.estimate_cost(), 6)

        return CompilationResult(
            success=validation_report.is_valid,
            config=config,
            validation_report=validation_report,
            metrics=metrics,
            assumptions=assumptions,
            warnings=warnings,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_stage(
        self,
        name: str,
        coro_factory: Callable[[], Any],
        llm: LLMClient,
        metrics: CompilationMetrics,
        callback: Optional[StageCallback],
    ) -> Any:
        """Execute a single stage, track timing/tokens, and fire callbacks."""
        if callback:
            await callback(name, "started", {})

        tokens_before = llm.total_input_tokens + llm.total_output_tokens
        t0 = time.perf_counter()

        max_attempts = 3
        last_exc = None
        result = None

        for attempt in range(max_attempts):
            try:
                result = await coro_factory()
                break
            except Exception as exc:
                last_exc = exc
                classified = classify_error(exc, stage=name)
                logger.warning(
                    "Stage %s failed on attempt %d/%d: [%s] %s",
                    name, attempt + 1, max_attempts,
                    classified.code.value, classified.message,
                )
                if attempt == max_attempts - 1:
                    # Fire error callback so frontend sees which stage failed & why
                    if callback:
                        elapsed_ms = (time.perf_counter() - t0) * 1000
                        await callback(name, "error", {
                            "duration_ms": round(elapsed_ms, 1),
                            "error_code": classified.code.value,
                            "error_message": classified.message,
                            "error_suggestion": classified.suggestion,
                            "retryable": classified.retryable,
                        })
                    raise exc

        elapsed_ms = (time.perf_counter() - t0) * 1000
        tokens_after = llm.total_input_tokens + llm.total_output_tokens
        stage_tokens = tokens_after - tokens_before

        metrics.stage_durations[name] = round(elapsed_ms, 1)
        metrics.tokens_per_stage[name] = stage_tokens

        if callback:
            await callback(
                name,
                "completed",
                {"duration_ms": round(elapsed_ms, 1), "tokens": stage_tokens},
            )

        logger.info(
            "Stage '%s' completed in %.0f ms (%d tokens)",
            name,
            elapsed_ms,
            stage_tokens,
        )
        return result

    @staticmethod
    def _fail(
        errors: list[str],
        warnings: list[str],
        assumptions: list[str],
        metrics: CompilationMetrics,
        pipeline_start: float,
        classified_error: Optional[PipelineError] = None,
    ) -> CompilationResult:
        metrics.total_duration_ms = (
            time.perf_counter() - pipeline_start
        ) * 1000
        return CompilationResult(
            success=False,
            config=None,
            validation_report=ValidationReport(is_valid=False),
            metrics=metrics,
            assumptions=assumptions,
            warnings=warnings,
            errors=errors,
            error_code=classified_error.code.value if classified_error else None,
            error_message=classified_error.message if classified_error else None,
            error_suggestion=classified_error.suggestion if classified_error else None,
            failed_stage=classified_error.stage if classified_error else None,
            retryable=classified_error.retryable if classified_error else False,
        )
