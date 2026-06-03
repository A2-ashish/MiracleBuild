"""Public re-exports for all schema models."""
from __future__ import annotations

# Intent (Stage 1)
from .intent import (
    EntityAttribute,
    Entity,
    FeatureType,
    Feature,
    UserRole,
    Constraint,
    BusinessRule as IntentBusinessRule,
    Assumption,
    IntentResult,
)

# Design (Stage 2)
from .design import (
    RelationType,
    EntityRelation,
    UserFlow,
    PageSpec,
    PermissionEntry,
    SystemDesign,
)

# Database
from .database import (
    ColumnType,
    ForeignKey,
    Column,
    Index,
    Table,
    Relation,
    DatabaseSchema,
)

# API
from .api import (
    HttpMethod,
    QueryParam,
    FieldSchema,
    RequestBody,
    ResponseSchema,
    Endpoint,
    ErrorFormat,
    APISchema,
)

# UI
from .ui import (
    ComponentType,
    FormField,
    TableColumn,
    ChartConfig,
    Action,
    Component,
    ThemeColors,
    Theme,
    NavItem,
    Navigation,
    Page,
    UISchema,
)

# Auth
from .auth import (
    Permission,
    Role,
    PasswordPolicy,
    SessionConfig,
    AuthSchema,
)

# Business Logic
from .business_logic import (
    RuleType,
    Condition,
    RuleAction,
    BusinessRule,
    ComputedField,
    WorkflowStep,
    Workflow,
    BusinessLogicSchema,
)

# App Config (top-level)
from .app_config import (
    AppMetadata,
    CompilationMetrics,
    ValidationCheck,
    ValidationReport,
    AppConfig,
    CompilationResult,
)

__all__ = [
    # Intent
    "EntityAttribute",
    "Entity",
    "FeatureType",
    "Feature",
    "UserRole",
    "Constraint",
    "IntentBusinessRule",
    "Assumption",
    "IntentResult",
    # Design
    "RelationType",
    "EntityRelation",
    "UserFlow",
    "PageSpec",
    "PermissionEntry",
    "SystemDesign",
    # Database
    "ColumnType",
    "ForeignKey",
    "Column",
    "Index",
    "Table",
    "Relation",
    "DatabaseSchema",
    # API
    "HttpMethod",
    "QueryParam",
    "FieldSchema",
    "RequestBody",
    "ResponseSchema",
    "Endpoint",
    "ErrorFormat",
    "APISchema",
    # UI
    "ComponentType",
    "FormField",
    "TableColumn",
    "ChartConfig",
    "Action",
    "Component",
    "ThemeColors",
    "Theme",
    "NavItem",
    "Navigation",
    "Page",
    "UISchema",
    # Auth
    "Permission",
    "Role",
    "PasswordPolicy",
    "SessionConfig",
    "AuthSchema",
    # Business Logic
    "RuleType",
    "Condition",
    "RuleAction",
    "BusinessRule",
    "ComputedField",
    "WorkflowStep",
    "Workflow",
    "BusinessLogicSchema",
    # App Config
    "AppMetadata",
    "CompilationMetrics",
    "ValidationCheck",
    "ValidationReport",
    "AppConfig",
    "CompilationResult",
]
