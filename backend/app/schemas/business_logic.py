"""Business logic schema models."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class RuleType(str, Enum):
    """Categories of business rule."""

    ACCESS_CONTROL = "access_control"
    VALIDATION = "validation"
    AUTOMATION = "automation"
    PREMIUM_GATE = "premium_gate"
    NOTIFICATION = "notification"
    COMPUTATION = "computation"
    WORKFLOW = "workflow"


class Condition(BaseModel):
    """A single condition predicate."""

    field: str
    operator: str  # equals, not_equals, greater_than, less_than, contains, in, not_in
    value: Any


class RuleAction(BaseModel):
    """Action to take when a rule fires."""

    type: str  # allow, deny, notify, compute, redirect, trigger_workflow
    target: str = ""
    params: dict = {}


class BusinessRule(BaseModel):
    """A single business rule definition."""

    id: str
    name: str
    description: str
    type: RuleType
    entity: str
    conditions: list[Condition]
    actions: list[RuleAction]
    priority: int = 0
    enabled: bool = True


class ComputedField(BaseModel):
    """A field whose value is derived from a formula."""

    entity: str
    field_name: str
    formula: str
    dependencies: list[str] = []


class WorkflowStep(BaseModel):
    """A single step in a workflow."""

    name: str
    action: str
    next_step: Optional[str] = None
    condition: Optional[Condition] = None


class Workflow(BaseModel):
    """A multi-step workflow triggered by an event."""

    name: str
    trigger: str
    entity: str
    steps: list[WorkflowStep]


class BusinessLogicSchema(BaseModel):
    """Complete business logic specification."""

    rules: list[BusinessRule] = []
    computed_fields: list[ComputedField] = []
    workflows: list[Workflow] = []
