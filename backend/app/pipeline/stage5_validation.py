"""Stage 5 — Validation & Repair Loop.

Builds an ``AppConfig`` from schemas, runs all cross-layer and semantic
validation checks, and invokes the repair engine for up to *max_cycles*
iterations until the config passes or the budget is exhausted.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.llm.client import LLMClient
from app.schemas.app_config import (
    AppConfig,
    AppMetadata,
    ValidationCheck,
    ValidationReport,
)
from app.schemas.database import DatabaseSchema
from app.schemas.api import APISchema
from app.schemas.ui import UISchema
from app.schemas.auth import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema
from app.validation.cross_layer import run_all_checks
from app.validation.semantic_validator import (
    check_naming_conventions,
    check_orphaned_entities,
    check_logical_consistency,
)
from app.validation.repair_engine import RepairEngine

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Validates an assembled config and orchestrates repair cycles."""

    def __init__(self) -> None:
        self._repair = RepairEngine()

    async def validate_and_repair(
        self,
        schemas: dict,
        llm: LLMClient,
        max_cycles: int = 3,
        app_name: str = "App",
        app_description: str = "",
        domain: str = "",
    ) -> tuple[Optional[AppConfig], ValidationReport]:
        """Build, validate, and optionally repair the application config.

        Args:
            schemas: Dict with keys ``database``, ``api``, ``ui``,
                ``auth``, ``business_logic``.
            llm: LLM client for repair prompts.
            max_cycles: Maximum repair iterations.
            app_name: Human-readable application name.
            app_description: Application description.
            domain: Application domain tag.

        Returns:
            A tuple of ``(AppConfig | None, ValidationReport)``.
        """
        config = self._build_config(schemas, app_name, app_description, domain)
        repair_log: list[str] = []
        cycle = 0

        while cycle < max_cycles:
            checks = self._run_all_checks(config)
            failures = [c for c in checks if not c.passed]

            if not failures:
                logger.info("Validation passed on cycle %d", cycle)
                report = self._build_report(checks, repair_log, is_valid=True)
                return config, report

            logger.info(
                "Cycle %d: %d/%d checks failed — attempting repair",
                cycle,
                len(failures),
                len(checks),
            )
            repair_log.append(
                f"Cycle {cycle}: {len(failures)} failures detected"
            )

            try:
                config = await self._repair.repair(config, failures, llm)
                for f in failures:
                    repair_log.append(f"  Attempted fix: {f.name} — {f.message}")
            except Exception as exc:
                repair_log.append(f"Repair failed on cycle {cycle}: {exc}")
                logger.exception("Repair cycle %d failed", cycle)

            cycle += 1

        # Final check after all cycles
        final_checks = self._run_all_checks(config)
        final_failures = [c for c in final_checks if not c.passed]
        is_valid = len(final_failures) == 0

        report = self._build_report(final_checks, repair_log, is_valid=is_valid)
        report.repair_log.append(
            f"Exhausted {max_cycles} repair cycles — "
            f"{'all checks pass' if is_valid else f'{len(final_failures)} still failing'}"
        )

        return config if is_valid else None, report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_config(
        schemas: dict,
        app_name: str,
        app_description: str,
        domain: str,
    ) -> AppConfig:
        return AppConfig(
            metadata=AppMetadata(
                name=app_name,
                description=app_description,
                domain=domain,
            ),
            database=schemas["database"],
            api=schemas["api"],
            ui=schemas["ui"],
            auth=schemas["auth"],
            business_logic=schemas["business_logic"],
        )

    @staticmethod
    def _run_all_checks(config: AppConfig) -> list[ValidationCheck]:
        """Run cross-layer + semantic checks."""
        checks = run_all_checks(config)
        checks.append(check_naming_conventions(config))
        checks.append(check_orphaned_entities(config))
        checks.append(check_logical_consistency(config))
        return checks

    @staticmethod
    def _build_report(
        checks: list[ValidationCheck],
        repair_log: list[str],
        is_valid: bool,
    ) -> ValidationReport:
        passed = sum(1 for c in checks if c.passed)
        total = len(checks)
        score = (passed / total * 100) if total else 0.0
        return ValidationReport(
            is_valid=is_valid,
            checks=checks,
            repair_log=repair_log,
            overall_score=round(score, 1),
        )
