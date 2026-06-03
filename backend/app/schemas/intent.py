"""Intent extraction models for Stage 1 of the compilation pipeline."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EntityAttribute(BaseModel):
    """A single attribute on a domain entity."""

    name: str
    type: str = Field(
        description="Data type: string, integer, float, boolean, datetime, text, email, url, phone"
    )
    required: bool = True
    description: str = ""


class Entity(BaseModel):
    """A domain entity discovered from the user prompt."""

    name: str
    description: str
    attributes: list[EntityAttribute]


class FeatureType(str, Enum):
    """Enumeration of recognised application feature types."""

    CRUD = "crud"
    AUTH = "auth"
    DASHBOARD = "dashboard"
    SEARCH = "search"
    PAYMENT = "payment"
    NOTIFICATION = "notification"
    REPORT = "report"
    ANALYTICS = "analytics"
    FILE_UPLOAD = "file_upload"
    EXPORT = "export"
    CALENDAR = "calendar"
    CHAT = "chat"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


class Feature(BaseModel):
    """An application feature derived from the user prompt."""

    name: str
    type: FeatureType
    description: str
    related_entities: list[str] = []
    premium: bool = False


class UserRole(BaseModel):
    """A user role within the application."""

    name: str
    description: str
    is_admin: bool = False
    permissions: list[str] = []


class Constraint(BaseModel):
    """A constraint that bounds the application behaviour."""

    description: str
    type: str = Field(
        description="Type: business, technical, security, ux"
    )


class BusinessRule(BaseModel):
    """A business rule that governs entity behaviour."""

    name: str
    description: str
    condition: str
    action: str
    related_entities: list[str] = []


class Assumption(BaseModel):
    """An assumption made when the user prompt was under-specified."""

    description: str
    reason: str
    impact: str = "low"


class IntentResult(BaseModel):
    """Complete result of intent extraction (Stage 1)."""

    app_name: str
    app_description: str
    domain: str = Field(
        description="App domain: crm, ecommerce, education, healthcare, etc."
    )
    entities: list[Entity]
    features: list[Feature]
    user_roles: list[UserRole]
    constraints: list[Constraint] = []
    business_rules: list[BusinessRule] = []
    assumptions: list[Assumption] = []
