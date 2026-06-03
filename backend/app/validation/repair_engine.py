"""Repair engine — applies targeted fixes to a failing ``AppConfig``.

For deterministic issues the engine applies rule-based patches.  For complex
or ambiguous failures it delegates to the LLM for a scoped repair.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.llm.client import LLMClient
from app.llm.prompts import REPAIR_SYSTEM, REPAIR_USER
from app.llm.response_parser import parse_json
from app.schemas.app_config import AppConfig, ValidationCheck
from app.schemas.database import DatabaseSchema
from app.schemas.api import (
    APISchema,
    Endpoint,
    HttpMethod,
    ResponseSchema,
    FieldSchema,
    RequestBody,
    QueryParam,
)
from app.schemas.ui import UISchema
from app.schemas.auth import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema

logger = logging.getLogger(__name__)


class RepairEngine:
    """Attempts targeted fixes for validation failures."""

    async def repair(
        self,
        config: AppConfig,
        errors: list[ValidationCheck],
        llm: LLMClient,
    ) -> AppConfig:
        """Repair *config* in-place for every failing *error*.

        Strategy:
        1. Try deterministic (rule-based) fixes first.
        2. Fall back to an LLM-based repair for anything left.

        Returns:
            A (potentially) repaired ``AppConfig``.
        """
        config = self._apply_deterministic_fixes(config, errors)

        # Collect errors that could not be fixed deterministically
        remaining = [
            e for e in errors if not e.repaired
        ]

        if remaining:
            config = await self._llm_repair(config, remaining, llm)

        return config

    # ------------------------------------------------------------------
    # Deterministic rule-based fixes
    # ------------------------------------------------------------------

    def _apply_deterministic_fixes(
        self, config: AppConfig, errors: list[ValidationCheck]
    ) -> AppConfig:
        for err in errors:
            if err.passed:
                continue

            name = err.name

            if name == "foreign_keys_valid":
                config = self._fix_foreign_keys(config, err)
            elif name == "crud_completeness":
                config = self._fix_crud_completeness(config, err)
            elif name == "nav_matches_pages":
                config = self._fix_nav_pages(config, err)
            elif name == "unique_paths":
                config = self._fix_duplicate_paths(config, err)
            elif name == "permission_matrix_complete":
                config = self._fix_permission_matrix(config, err)
            elif name == "logical_consistency":
                config = self._fix_logical_consistency(config, err)
            elif name == "naming_conventions":
                # Naming fixes are complex — delegate to LLM
                pass
            # Other checks fall through to LLM repair

        return config

    # ---- Individual fixers ----

    @staticmethod
    def _fix_foreign_keys(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Remove FK references that point to nonexistent tables."""
        table_names = {t.name for t in config.database.tables}
        for table in config.database.tables:
            for col in table.columns:
                if col.references and col.references.table not in table_names:
                    logger.info(
                        "Removing invalid FK: %s.%s → %s",
                        table.name,
                        col.name,
                        col.references.table,
                    )
                    col.references = None
        err.repaired = True
        err.repair_action = "Removed invalid foreign key references"
        return config

    @staticmethod
    def _fix_crud_completeness(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Add missing GET/POST stubs for tables without them."""
        table_names = {t.name for t in config.database.tables}
        existing_routes: set[str] = set()
        entity_methods: dict[str, set[str]] = {}

        for ep in config.api.endpoints:
            existing_routes.add(f"{ep.method.value} {ep.path}")
            if ep.related_entity:
                entity_methods.setdefault(ep.related_entity, set()).add(
                    ep.method.value
                )

        for table in config.database.tables:
            methods = entity_methods.get(table.name, set())
            # Also check singular form
            singular = table.name.rstrip("s")
            methods |= entity_methods.get(singular, set())

            base_path = f"/api/v1/{table.name}"

            if "GET" not in methods:
                id_field = FieldSchema(name="id", type="string")
                response_fields = [id_field] + [
                    FieldSchema(name=c.name, type=c.type.value)
                    for c in table.columns
                    if c.name != "id"
                ]
                config.api.endpoints.append(
                    Endpoint(
                        path=base_path,
                        method=HttpMethod.GET,
                        description=f"List all {table.name}",
                        response=ResponseSchema(
                            fields=response_fields,
                            is_list=True,
                            paginated=True,
                        ),
                        related_entity=table.name,
                        query_params=[
                            QueryParam(name="page", type="integer"),
                            QueryParam(name="per_page", type="integer"),
                        ],
                    )
                )

            if "POST" not in methods:
                writable = [
                    FieldSchema(name=c.name, type=c.type.value)
                    for c in table.columns
                    if c.name not in ("id", "created_at", "updated_at")
                ]
                config.api.endpoints.append(
                    Endpoint(
                        path=base_path,
                        method=HttpMethod.POST,
                        description=f"Create a {singular}",
                        request_body=RequestBody(fields=writable),
                        response=ResponseSchema(
                            fields=[FieldSchema(name="id", type="string")],
                            status_code=201,
                        ),
                        related_entity=table.name,
                    )
                )

        err.repaired = True
        err.repair_action = "Added missing GET/POST endpoints"
        return config

    @staticmethod
    def _fix_nav_pages(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Remove nav items that point to nonexistent pages."""
        page_paths = {p.path for p in config.ui.pages}

        def _filter(items: list) -> list:
            kept = []
            for item in items:
                if item.path and item.path not in page_paths:
                    logger.info("Removing orphan nav item: %s", item.path)
                    continue
                if item.children:
                    item.children = _filter(item.children)
                kept.append(item)
            return kept

        config.ui.navigation.items = _filter(config.ui.navigation.items)
        err.repaired = True
        err.repair_action = "Removed nav items with no matching page"
        return config

    @staticmethod
    def _fix_duplicate_paths(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Deduplicate API endpoints and page paths."""
        seen_api: set[str] = set()
        unique_eps: list[Endpoint] = []
        for ep in config.api.endpoints:
            key = f"{ep.method.value} {ep.path}"
            if key not in seen_api:
                seen_api.add(key)
                unique_eps.append(ep)
        config.api.endpoints = unique_eps

        seen_pages: set[str] = set()
        unique_pages = []
        for page in config.ui.pages:
            if page.path not in seen_pages:
                seen_pages.add(page.path)
                unique_pages.append(page)
        config.ui.pages = unique_pages

        err.repaired = True
        err.repair_action = "Removed duplicate endpoints/pages"
        return config

    @staticmethod
    def _fix_permission_matrix(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Give every role at least a self-read permission."""
        from app.schemas.auth import Permission

        for role in config.auth.roles:
            if not role.permissions:
                role.permissions = [
                    Permission(resource="self", actions=["read", "update"])
                ]
        err.repaired = True
        err.repair_action = "Added default permissions to empty roles"
        return config

    @staticmethod
    def _fix_logical_consistency(config: AppConfig, err: ValidationCheck) -> AppConfig:
        """Fix simple logical issues."""
        # Ensure admin pages require auth
        admin_roles = {r.name for r in config.auth.roles if r.is_admin}
        for page in config.ui.pages:
            if admin_roles & set(page.allowed_roles):
                page.requires_auth = True

        # Ensure at least one default page
        if not any(p.is_default for p in config.ui.pages):
            if config.ui.pages:
                config.ui.pages[0].is_default = True

        err.repaired = True
        err.repair_action = "Fixed admin auth and default page flags"
        return config

    # ------------------------------------------------------------------
    # LLM-based repair
    # ------------------------------------------------------------------

    async def _llm_repair(
        self,
        config: AppConfig,
        errors: list[ValidationCheck],
        llm: LLMClient,
    ) -> AppConfig:
        """Use the LLM to fix remaining failures."""
        config_data = {
            "database": config.database.model_dump(),
            "api": config.api.model_dump(),
            "ui": config.ui.model_dump(),
            "auth": config.auth.model_dump(),
            "business_logic": config.business_logic.model_dump(),
        }
        errors_data = [
            {"name": e.name, "message": e.message} for e in errors
        ]

        user_msg = REPAIR_USER.format(
            config_json=json.dumps(config_data, indent=2),
            errors_json=json.dumps(errors_data, indent=2),
        )

        try:
            raw = await llm.generate(
                prompt=user_msg, system_instruction=REPAIR_SYSTEM
            )
            data, parse_errors = parse_json(raw)
            if parse_errors or data is None:
                logger.warning("LLM repair produced unparseable JSON")
                return config

            # Parse each sub-schema with fallback
            mapping: list[tuple[str, str, type]] = [
                ("database", "database", DatabaseSchema),
                ("api", "api", APISchema),
                ("ui", "ui", UISchema),
                ("auth", "auth", AuthSchema),
                ("business_logic", "business_logic", BusinessLogicSchema),
            ]
            for key, attr, cls in mapping:
                sub = data.get(key)
                if sub is not None:
                    try:
                        setattr(config, attr, cls.model_validate(sub))
                    except Exception:
                        logger.warning(
                            "LLM repair: failed to parse '%s' — keeping original",
                            key,
                        )

            for e in errors:
                e.repaired = True
                e.repair_action = "LLM-based repair applied"

        except Exception:
            logger.exception("LLM repair call failed")

        return config
