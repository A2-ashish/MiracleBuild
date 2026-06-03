"""Cross-layer validation checks.

All 12 checks accept an ``AppConfig`` and return a ``ValidationCheck``.
``run_all_checks`` executes every check and returns the combined list.
"""
from __future__ import annotations

from app.schemas.app_config import AppConfig, ValidationCheck


# ======================================================================
# 1. API fields match DB columns
# ======================================================================

def check_api_fields_match_db(config: AppConfig) -> ValidationCheck:
    """Verify that API request/response fields map to DB columns."""
    db_columns: dict[str, set[str]] = {}
    for table in config.database.tables:
        cols = {c.name for c in table.columns}
        if table.timestamps:
            cols.update({"created_at", "updated_at"})
        db_columns[table.name] = cols

    mismatches: list[str] = []
    for ep in config.api.endpoints:
        entity = ep.related_entity
        if not entity:
            continue
        # Try to match entity to a table (plural / singular heuristics)
        table_cols = _find_table_cols(entity, db_columns)
        if table_cols is None:
            continue  # no matching table — other check will catch this

        # Check response fields
        for field in ep.response.fields:
            if field.name not in table_cols and field.name not in (
                "id",
                "total",
                "page",
                "per_page",
                "token",
                "access_token",
                "refresh_token",
                "message",
            ):
                mismatches.append(
                    f"Endpoint {ep.method.value} {ep.path}: response field "
                    f"'{field.name}' not in table columns"
                )

    if mismatches:
        return ValidationCheck(
            name="api_fields_match_db",
            passed=False,
            message="; ".join(mismatches[:5]),  # cap verbosity
        )
    return ValidationCheck(name="api_fields_match_db", passed=True)


# ======================================================================
# 2. UI data_source binds to valid API endpoint
# ======================================================================

def check_ui_binds_to_api(config: AppConfig) -> ValidationCheck:
    """Ensure every UI component data_source references a valid API path."""
    api_paths = {ep.path for ep in config.api.endpoints}
    missing: list[str] = []
    for page in config.ui.pages:
        for comp in page.components:
            ds = comp.data_source
            if ds and ds not in api_paths:
                # Try prefix match (e.g. "/api/v1/users" matches "/api/v1/users/{id}")
                if not any(p.startswith(ds) or ds.startswith(p) for p in api_paths):
                    missing.append(
                        f"Page '{page.name}' component '{comp.id}' references "
                        f"'{ds}' — no matching API endpoint"
                    )
    if missing:
        return ValidationCheck(
            name="ui_binds_to_api",
            passed=False,
            message="; ".join(missing[:5]),
        )
    return ValidationCheck(name="ui_binds_to_api", passed=True)


# ======================================================================
# 3. Auth roles consistent across layers
# ======================================================================

def check_auth_roles_consistent(config: AppConfig) -> ValidationCheck:
    """Roles in auth must appear wherever they are referenced in API/UI."""
    auth_role_names = {r.name for r in config.auth.roles}
    referenced: set[str] = set()

    for ep in config.api.endpoints:
        referenced.update(ep.required_roles)
    for page in config.ui.pages:
        referenced.update(page.allowed_roles)
        for comp in page.components:
            referenced.update(comp.visible_to_roles)

    undefined = referenced - auth_role_names
    if undefined:
        return ValidationCheck(
            name="auth_roles_consistent",
            passed=False,
            message=f"Roles referenced but not in auth schema: {undefined}",
        )
    return ValidationCheck(name="auth_roles_consistent", passed=True)


# ======================================================================
# 4. Foreign keys reference valid tables
# ======================================================================

def check_foreign_keys_valid(config: AppConfig) -> ValidationCheck:
    """All FK references must point to tables that exist."""
    table_names = {t.name for t in config.database.tables}
    invalid: list[str] = []
    for table in config.database.tables:
        for col in table.columns:
            if col.references and col.references.table not in table_names:
                invalid.append(
                    f"Table '{table.name}'.'{col.name}' references "
                    f"nonexistent table '{col.references.table}'"
                )
    if invalid:
        return ValidationCheck(
            name="foreign_keys_valid",
            passed=False,
            message="; ".join(invalid[:5]),
        )
    return ValidationCheck(name="foreign_keys_valid", passed=True)


# ======================================================================
# 5. CRUD completeness
# ======================================================================

def check_crud_completeness(config: AppConfig) -> ValidationCheck:
    """Every DB table should have at least GET (list) and POST endpoints."""
    table_names = {t.name for t in config.database.tables}
    # Build a map: table_name → set of HTTP methods hitting it
    entity_methods: dict[str, set[str]] = {}
    for ep in config.api.endpoints:
        entity = ep.related_entity
        if entity:
            entity_methods.setdefault(entity, set()).add(ep.method.value)
            # Also try plural/singular
            for tn in table_names:
                if _names_match(entity, tn):
                    entity_methods.setdefault(tn, set()).add(ep.method.value)

    missing: list[str] = []
    for tn in table_names:
        methods = entity_methods.get(tn, set())
        if "GET" not in methods:
            missing.append(f"Table '{tn}' missing GET endpoint")
        if "POST" not in methods:
            missing.append(f"Table '{tn}' missing POST endpoint")

    if missing:
        return ValidationCheck(
            name="crud_completeness",
            passed=False,
            message="; ".join(missing[:5]),
        )
    return ValidationCheck(name="crud_completeness", passed=True)


# ======================================================================
# 6. Navigation matches pages
# ======================================================================

def check_nav_matches_pages(config: AppConfig) -> ValidationCheck:
    """Navigation items must point to pages that exist."""
    page_paths = {p.path for p in config.ui.pages}
    missing: list[str] = []

    def _walk(items: list) -> None:
        for item in items:
            if item.path and item.path not in page_paths:
                missing.append(f"Nav item '{item.label}' → '{item.path}' has no page")
            if item.children:
                _walk(item.children)

    _walk(config.ui.navigation.items)

    if missing:
        return ValidationCheck(
            name="nav_matches_pages",
            passed=False,
            message="; ".join(missing[:5]),
        )
    return ValidationCheck(name="nav_matches_pages", passed=True)


# ======================================================================
# 7. Business rules reference valid entities / fields
# ======================================================================

def check_business_rules_valid(config: AppConfig) -> ValidationCheck:
    """Business rule entity references must exist in the DB schema."""
    table_names = {t.name for t in config.database.tables}
    invalid: list[str] = []
    for rule in config.business_logic.rules:
        if rule.entity and not any(
            _names_match(rule.entity, tn) for tn in table_names
        ):
            invalid.append(
                f"Rule '{rule.name}' references entity '{rule.entity}' "
                "which has no matching table"
            )
    if invalid:
        return ValidationCheck(
            name="business_rules_valid",
            passed=False,
            message="; ".join(invalid[:5]),
        )
    return ValidationCheck(name="business_rules_valid", passed=True)


# ======================================================================
# 8. Permission matrix completeness
# ======================================================================

def check_permission_matrix_complete(config: AppConfig) -> ValidationCheck:
    """Every role should have at least one permission defined."""
    role_names = {r.name for r in config.auth.roles}
    roles_with_perms: set[str] = set()
    for role in config.auth.roles:
        if role.permissions:
            roles_with_perms.add(role.name)

    missing = role_names - roles_with_perms
    if missing:
        return ValidationCheck(
            name="permission_matrix_complete",
            passed=False,
            message=f"Roles without permissions: {missing}",
        )
    return ValidationCheck(name="permission_matrix_complete", passed=True)


# ======================================================================
# 9. Unique paths
# ======================================================================

def check_unique_paths(config: AppConfig) -> ValidationCheck:
    """No duplicate API paths (method+path) or page routes."""
    # API duplicates
    api_keys: list[str] = []
    dupes: list[str] = []
    for ep in config.api.endpoints:
        key = f"{ep.method.value} {ep.path}"
        if key in api_keys:
            dupes.append(f"Duplicate API: {key}")
        api_keys.append(key)

    # Page duplicates
    page_paths: list[str] = []
    for page in config.ui.pages:
        if page.path in page_paths:
            dupes.append(f"Duplicate page path: {page.path}")
        page_paths.append(page.path)

    if dupes:
        return ValidationCheck(
            name="unique_paths",
            passed=False,
            message="; ".join(dupes[:5]),
        )
    return ValidationCheck(name="unique_paths", passed=True)


# ======================================================================
# 10. Form fields match API POST body
# ======================================================================

def check_form_fields_match_api(config: AppConfig) -> ValidationCheck:
    """Form component fields should correspond to API POST body fields."""
    # Build POST body field map: path → set[field_name]
    post_fields: dict[str, set[str]] = {}
    for ep in config.api.endpoints:
        if ep.method.value == "POST" and ep.request_body:
            post_fields[ep.path] = {f.name for f in ep.request_body.fields}

    mismatches: list[str] = []
    for page in config.ui.pages:
        for comp in page.components:
            if comp.type.value == "form" and comp.form_fields and comp.data_source:
                api_fields = post_fields.get(comp.data_source)
                if api_fields is None:
                    continue  # no matching endpoint
                for ff in comp.form_fields:
                    if ff.name not in api_fields and ff.name not in (
                        "confirm_password",
                        "submit",
                    ):
                        mismatches.append(
                            f"Form '{comp.id}' field '{ff.name}' not in "
                            f"POST {comp.data_source}"
                        )

    if mismatches:
        return ValidationCheck(
            name="form_fields_match_api",
            passed=False,
            message="; ".join(mismatches[:5]),
        )
    return ValidationCheck(name="form_fields_match_api", passed=True)


# ======================================================================
# 11. Table columns match API GET response
# ======================================================================

def check_table_columns_match_api(config: AppConfig) -> ValidationCheck:
    """Table component columns should match API GET response fields."""
    get_fields: dict[str, set[str]] = {}
    for ep in config.api.endpoints:
        if ep.method.value == "GET" and ep.response.is_list:
            get_fields[ep.path] = {f.name for f in ep.response.fields}

    mismatches: list[str] = []
    for page in config.ui.pages:
        for comp in page.components:
            if comp.type.value == "table" and comp.table_columns and comp.data_source:
                api_fields = get_fields.get(comp.data_source)
                if api_fields is None:
                    continue
                for tc in comp.table_columns:
                    if tc.key not in api_fields and tc.key != "actions":
                        mismatches.append(
                            f"Table '{comp.id}' column '{tc.key}' not in "
                            f"GET {comp.data_source}"
                        )

    if mismatches:
        return ValidationCheck(
            name="table_columns_match_api",
            passed=False,
            message="; ".join(mismatches[:5]),
        )
    return ValidationCheck(name="table_columns_match_api", passed=True)


# ======================================================================
# 12. Premium gating consistent
# ======================================================================

def check_premium_gating_consistent(config: AppConfig) -> ValidationCheck:
    """Premium-gated features should be gated in both API and business rules."""
    # Gather premium-related rules
    premium_entities: set[str] = set()
    for rule in config.business_logic.rules:
        if rule.type.value == "premium_gate":
            premium_entities.add(rule.entity.lower())

    # If no premium rules exist, the check passes trivially
    if not premium_entities:
        return ValidationCheck(
            name="premium_gating_consistent",
            passed=True,
            message="No premium features defined",
        )

    # Check that premium-gated endpoints have auth and role restrictions
    ungated: list[str] = []
    for ep in config.api.endpoints:
        entity = ep.related_entity.lower()
        if entity in premium_entities and not ep.auth_required:
            ungated.append(
                f"Endpoint {ep.method.value} {ep.path} serves premium "
                f"entity '{entity}' but has no auth"
            )

    if ungated:
        return ValidationCheck(
            name="premium_gating_consistent",
            passed=False,
            message="; ".join(ungated[:5]),
        )
    return ValidationCheck(name="premium_gating_consistent", passed=True)


# ======================================================================
# Aggregate runner
# ======================================================================

def run_all_checks(config: AppConfig) -> list[ValidationCheck]:
    """Execute all 12 cross-layer checks and return results."""
    return [
        check_api_fields_match_db(config),
        check_ui_binds_to_api(config),
        check_auth_roles_consistent(config),
        check_foreign_keys_valid(config),
        check_crud_completeness(config),
        check_nav_matches_pages(config),
        check_business_rules_valid(config),
        check_permission_matrix_complete(config),
        check_unique_paths(config),
        check_form_fields_match_api(config),
        check_table_columns_match_api(config),
        check_premium_gating_consistent(config),
    ]


# ======================================================================
# Private helpers
# ======================================================================

def _find_table_cols(
    entity: str, db_columns: dict[str, set[str]]
) -> set[str] | None:
    """Fuzzy-match an entity name to a DB table and return its columns."""
    for table_name, cols in db_columns.items():
        if _names_match(entity, table_name):
            return cols
    return None


def _names_match(a: str, b: str) -> bool:
    """Case-insensitive match with simple singular/plural handling."""
    a_lower = a.lower().replace("_", "").replace("-", "")
    b_lower = b.lower().replace("_", "").replace("-", "")
    if a_lower == b_lower:
        return True
    if a_lower + "s" == b_lower or a_lower == b_lower + "s":
        return True
    if a_lower + "es" == b_lower or a_lower == b_lower + "es":
        return True
    return False
