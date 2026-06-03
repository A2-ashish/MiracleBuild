"""Top-level application configuration and compilation result models."""
from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

from .database import DatabaseSchema
from .api import APISchema
from .ui import UISchema
from .auth import AuthSchema
from .business_logic import BusinessLogicSchema


class AppMetadata(BaseModel):
    """Metadata about the generated application."""

    name: str
    description: str
    version: str = "1.0.0"
    domain: str = ""
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    generator_version: str = "1.0.0"


class CompilationMetrics(BaseModel):
    """Performance and cost metrics for a compilation run."""

    total_duration_ms: float = 0
    stage_durations: dict[str, float] = {}
    total_tokens: int = 0
    tokens_per_stage: dict[str, int] = {}
    estimated_cost_usd: float = 0
    repair_cycles: int = 0
    validation_checks_passed: int = 0
    validation_checks_total: int = 0
    model_used: str = ""


class ValidationCheck(BaseModel):
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str = ""
    repaired: bool = False
    repair_action: str = ""


class ValidationReport(BaseModel):
    """Aggregate report of all validation checks."""

    is_valid: bool
    checks: list[ValidationCheck] = []
    repair_log: list[str] = []
    overall_score: float = 0.0  # 0-100


class AppConfig(BaseModel):
    """The full generated application configuration."""

    metadata: AppMetadata
    database: DatabaseSchema
    api: APISchema
    ui: UISchema
    auth: AuthSchema
    business_logic: BusinessLogicSchema


class CompilationResult(BaseModel):
    """Final output of the compiler pipeline."""

    success: bool
    config: Optional[AppConfig] = None
    validation_report: ValidationReport
    metrics: CompilationMetrics
    assumptions: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []
