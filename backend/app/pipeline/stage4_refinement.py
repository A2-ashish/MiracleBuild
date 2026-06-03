"""Stage 4 — Schema Refinement.

Cross-references all five sub-schemas and fixes inconsistencies such as
missing endpoints, mismatched data sources, and gaps in role definitions.
"""
from __future__ import annotations

import json
import logging

from app.llm.client import LLMClient
from app.llm.prompts import REFINEMENT_SYSTEM, REFINEMENT_USER
from app.llm.response_parser import parse_json, parse_into_model
from app.schemas.database import DatabaseSchema
from app.schemas.api import APISchema
from app.schemas.ui import UISchema
from app.schemas.auth import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema

logger = logging.getLogger(__name__)


class SchemaRefiner:
    """Performs LLM-assisted cross-layer refinement of all schemas."""

    async def refine(self, schemas: dict, llm: LLMClient) -> dict:
        """Refine schemas for consistency.

        If the LLM refinement call fails or produces unparseable output the
        original schemas are returned unchanged — refinement is best-effort.

        Args:
            schemas: Dict with ``database``, ``api``, ``ui``, ``auth``,
                ``business_logic`` values.
            llm: Configured LLM client.

        Returns:
            Refined schemas dict with the same keys.
        """
        db_json = schemas["database"].model_dump_json(indent=2)
        api_json = schemas["api"].model_dump_json(indent=2)
        ui_json = schemas["ui"].model_dump_json(indent=2)
        auth_json = schemas["auth"].model_dump_json(indent=2)
        biz_json = schemas["business_logic"].model_dump_json(indent=2)

        user_msg = REFINEMENT_USER.format(
            db_schema_json=db_json,
            api_schema_json=api_json,
            ui_schema_json=ui_json,
            auth_schema_json=auth_json,
            business_logic_json=biz_json,
        )

        try:
            raw = await llm.generate(
                prompt=user_msg,
                system_instruction=REFINEMENT_SYSTEM,
            )
            data, json_errors = parse_json(raw)
            if json_errors or data is None:
                logger.warning(
                    "Refinement JSON parse failed — keeping originals: %s",
                    json_errors,
                )
                return self._apply_local_fixes(schemas)

            refined = self._parse_refined(data, schemas)
            logger.info("Schema refinement complete")
            return refined

        except Exception:
            logger.exception("Refinement LLM call failed — keeping originals")
            return self._apply_local_fixes(schemas)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_refined(self, data: dict, originals: dict) -> dict:
        """Attempt to parse each sub-key; fall back to originals on error."""
        mapping: list[tuple[str, type]] = [
            ("database", DatabaseSchema),
            ("api", APISchema),
            ("ui", UISchema),
            ("auth", AuthSchema),
            ("business_logic", BusinessLogicSchema),
        ]
        result: dict = {}
        for key, model_cls in mapping:
            sub = data.get(key)
            if sub is None:
                logger.warning("Refinement missing key '%s' — keeping original", key)
                result[key] = originals[key]
                continue
            try:
                result[key] = model_cls.model_validate(sub)
            except Exception:
                logger.warning(
                    "Refinement key '%s' failed validation — keeping original",
                    key,
                )
                result[key] = originals[key]
        return result

    # ------------------------------------------------------------------
    # Local (non-LLM) fixes
    # ------------------------------------------------------------------

    def _apply_local_fixes(self, schemas: dict) -> dict:
        """Apply deterministic fixes without calling the LLM."""
        schemas = dict(schemas)  # shallow copy

        # Ensure pagination on list endpoints
        api: APISchema = schemas["api"]
        from app.schemas.api import QueryParam

        for ep in api.endpoints:
            if ep.method.value == "GET" and ep.response.is_list:
                param_names = {p.name for p in ep.query_params}
                if "page" not in param_names:
                    ep.query_params.append(
                        QueryParam(
                            name="page",
                            type="integer",
                            required=False,
                            description="Page number",
                        )
                    )
                if "per_page" not in param_names:
                    ep.query_params.append(
                        QueryParam(
                            name="per_page",
                            type="integer",
                            required=False,
                            description="Items per page",
                        )
                    )
                if not ep.response.paginated:
                    ep.response.paginated = True

        # Ensure timestamps on all tables
        db: DatabaseSchema = schemas["database"]
        for table in db.tables:
            table.timestamps = True

        return schemas
