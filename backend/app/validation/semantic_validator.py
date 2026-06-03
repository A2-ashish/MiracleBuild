"""Semantic validation checks.

These checks go beyond structural cross-referencing and look at naming
conventions, orphaned entities, and logical consistency.
"""
from __future__ import annotations

import re

from app.schemas.app_config import AppConfig, ValidationCheck


def check_naming_conventions(config: AppConfig) -> ValidationCheck:
    """Verify snake_case for DB columns/tables and kebab-case for paths.

    Reports up to 5 violations.
    """
    violations: list[str] = []
    snake = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")

    # DB tables & columns
    for table in config.database.tables:
        if not snake.match(table.name):
            violations.append(f"Table name '{table.name}' is not snake_case")
        for col in table.columns:
            if not snake.match(col.name):
                violations.append(
                    f"Column '{table.name}.{col.name}' is not snake_case"
                )

    if violations:
        return ValidationCheck(
            name="naming_conventions",
            passed=False,
            message="; ".join(violations[:5]),
        )
    return ValidationCheck(name="naming_conventions", passed=True)


def check_orphaned_entities(config: AppConfig) -> ValidationCheck:
    """Detect DB tables that are never referenced by API endpoints or UI.

    Tables used only as junction tables or referenced by foreign keys are
    *not* considered orphaned.
    """
    table_names = {t.name for t in config.database.tables}

    referenced: set[str] = set()

    # Referenced by API
    for ep in config.api.endpoints:
        if ep.related_entity:
            for tn in table_names:
                if _fuzzy(ep.related_entity, tn):
                    referenced.add(tn)
        # Also scan the path for table names
        for tn in table_names:
            if tn in ep.path or tn.rstrip("s") in ep.path:
                referenced.add(tn)

    # Referenced by FK
    for table in config.database.tables:
        for col in table.columns:
            if col.references:
                referenced.add(col.references.table)

    # Referenced by relations
    for rel in config.database.relations:
        referenced.add(rel.from_table)
        referenced.add(rel.to_table)
        if rel.junction_table:
            referenced.add(rel.junction_table)

    orphaned = table_names - referenced
    if orphaned:
        return ValidationCheck(
            name="orphaned_entities",
            passed=False,
            message=f"Orphaned tables (no API / FK reference): {orphaned}",
        )
    return ValidationCheck(name="orphaned_entities", passed=True)


def check_logical_consistency(config: AppConfig) -> ValidationCheck:
    """High-level logic checks.

    Currently verifies:
    - Admin-only pages require auth.
    - At least one page is marked as default.
    """
    issues: list[str] = []

    # Admin pages should require auth
    admin_roles = {r.name for r in config.auth.roles if r.is_admin}
    for page in config.ui.pages:
        if admin_roles & set(page.allowed_roles) and not page.requires_auth:
            issues.append(
                f"Page '{page.name}' is admin-only but requires_auth=false"
            )

    # At least one default page
    if not any(p.is_default for p in config.ui.pages):
        issues.append("No page is marked as is_default=true")

    if issues:
        return ValidationCheck(
            name="logical_consistency",
            passed=False,
            message="; ".join(issues[:5]),
        )
    return ValidationCheck(name="logical_consistency", passed=True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _fuzzy(a: str, b: str) -> bool:
    a_l = a.lower().replace("_", "").replace("-", "")
    b_l = b.lower().replace("_", "").replace("-", "")
    return (
        a_l == b_l
        or a_l + "s" == b_l
        or a_l == b_l + "s"
        or a_l + "es" == b_l
        or a_l == b_l + "es"
    )
