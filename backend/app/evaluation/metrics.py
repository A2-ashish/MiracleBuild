"""Metrics collection and aggregation for evaluation runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.schemas.app_config import CompilationResult


@dataclass
class PromptResult:
    """Outcome of a single prompt evaluation."""

    prompt_id: str
    prompt_text: str
    category: str
    success: bool
    duration_ms: float
    total_tokens: int
    estimated_cost_usd: float
    repair_cycles: int
    validation_score: float
    entity_count: int
    expected_entities_min: int
    errors: list[str]
    warnings: list[str]


class MetricsCollector:
    """Aggregates results across multiple compilation runs."""

    def __init__(self) -> None:
        self._results: list[PromptResult] = []

    def add_result(
        self,
        prompt_id: str,
        prompt_text: str,
        category: str,
        expected_entities_min: int,
        compilation: CompilationResult,
    ) -> None:
        """Record a single compilation result."""
        entity_count = 0
        if compilation.config and compilation.config.database:
            entity_count = len(compilation.config.database.tables)

        self._results.append(
            PromptResult(
                prompt_id=prompt_id,
                prompt_text=prompt_text[:120],
                category=category,
                success=compilation.success,
                duration_ms=compilation.metrics.total_duration_ms,
                total_tokens=compilation.metrics.total_tokens,
                estimated_cost_usd=compilation.metrics.estimated_cost_usd,
                repair_cycles=compilation.metrics.repair_cycles,
                validation_score=compilation.validation_report.overall_score,
                entity_count=entity_count,
                expected_entities_min=expected_entities_min,
                errors=compilation.errors,
                warnings=compilation.warnings,
            )
        )

    def get_per_prompt_results(self) -> list[dict[str, Any]]:
        """Return per-prompt breakdown as dicts."""
        return [
            {
                "id": r.prompt_id,
                "category": r.category,
                "success": r.success,
                "duration_ms": round(r.duration_ms, 1),
                "tokens": r.total_tokens,
                "cost_usd": round(r.estimated_cost_usd, 6),
                "repair_cycles": r.repair_cycles,
                "validation_score": r.validation_score,
                "entities": r.entity_count,
                "expected_min": r.expected_entities_min,
                "entity_check_passed": r.entity_count >= r.expected_entities_min,
                "errors": r.errors,
            }
            for r in self._results
        ]

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate statistics across all recorded results."""
        total = len(self._results)
        if total == 0:
            return {"total": 0, "success_rate": 0}

        successes = sum(1 for r in self._results if r.success)
        durations = [r.duration_ms for r in self._results]
        tokens = [r.total_tokens for r in self._results]
        costs = [r.estimated_cost_usd for r in self._results]
        retries = [r.repair_cycles for r in self._results]

        # Failure type breakdown
        failure_types: dict[str, int] = {}
        for r in self._results:
            if not r.success:
                for e in r.errors:
                    key = e.split(":")[0].strip() if ":" in e else "unknown"
                    failure_types[key] = failure_types.get(key, 0) + 1

        return {
            "total": total,
            "successes": successes,
            "failures": total - successes,
            "success_rate": round(successes / total * 100, 1),
            "avg_duration_ms": round(sum(durations) / total, 1),
            "min_duration_ms": round(min(durations), 1),
            "max_duration_ms": round(max(durations), 1),
            "avg_tokens": round(sum(tokens) / total),
            "avg_cost_usd": round(sum(costs) / total, 6),
            "total_cost_usd": round(sum(costs), 4),
            "avg_retries": round(sum(retries) / total, 2),
            "failure_type_breakdown": failure_types,
            "entity_check_pass_rate": round(
                sum(
                    1
                    for r in self._results
                    if r.entity_count >= r.expected_entities_min
                )
                / total
                * 100,
                1,
            ),
        }
