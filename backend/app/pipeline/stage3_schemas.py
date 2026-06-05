"""Stage 3 — Schema Generation.

Generates the five concrete schemas (database, API, UI, auth, business logic)
from a ``SystemDesign``. Each sub-schema is generated sequentially because
later schemas depend on earlier ones (e.g. API depends on DB).
"""
from __future__ import annotations

import logging

from app.llm.client import LLMClient
from app.llm.prompts import (
    DB_SCHEMA_SYSTEM,
    DB_SCHEMA_USER,
    API_SCHEMA_SYSTEM,
    API_SCHEMA_USER,
    UI_SCHEMA_SYSTEM,
    UI_SCHEMA_USER,
    AUTH_SCHEMA_SYSTEM,
    AUTH_SCHEMA_USER,
    BUSINESS_LOGIC_SYSTEM,
    BUSINESS_LOGIC_USER,
)
from app.llm.response_parser import parse_into_model
from app.schemas.design import SystemDesign
from app.schemas.database import DatabaseSchema
from app.schemas.api import APISchema
from app.schemas.ui import UISchema
from app.schemas.auth import AuthSchema
from app.schemas.business_logic import BusinessLogicSchema

logger = logging.getLogger(__name__)


class SchemaGenerator:
    """Generates all five sub-schemas from a system design."""

    async def generate(
        self, design: SystemDesign, llm: LLMClient
    ) -> dict:
        """Generate all schemas sequentially.

        Order: DB → API → UI → Auth → Business Logic.

        Args:
            design: Validated system design from Stage 2.
            llm: Configured LLM client.

        Returns:
            Dict with keys ``database``, ``api``, ``ui``, ``auth``,
            ``business_logic``, each holding the corresponding Pydantic model.
        """
        design_json = design.model_dump_json(indent=2)

        # 1. Database — no dependencies
        db_schema = await self._generate_db_schema(design_json, llm)
        logger.info("DB schema generated: %d tables", len(db_schema.tables))

        # 2. API — depends on DB
        db_json = db_schema.model_dump_json(indent=2)
        api_schema = await self._generate_api_schema(design_json, db_json, llm)
        logger.info(
            "API schema generated: %d endpoints", len(api_schema.endpoints)
        )

        # 3. UI — depends on API
        api_json = api_schema.model_dump_json(indent=2)
        ui_schema = await self._generate_ui_schema(design_json, api_json, llm)
        logger.info("UI schema generated: %d pages", len(ui_schema.pages))

        # 4. Auth — depends only on design
        auth_schema = await self._generate_auth_schema(design_json, llm)
        logger.info("Auth schema generated: %d roles", len(auth_schema.roles))

        # 5. Business Logic — depends on design + DB
        biz_schema = await self._generate_business_logic(
            design_json, db_json, llm
        )
        logger.info(
            "Business logic generated: %d rules", len(biz_schema.rules)
        )

        return {
            "database": db_schema,
            "api": api_schema,
            "ui": ui_schema,
            "auth": auth_schema,
            "business_logic": biz_schema,
        }

    # ------------------------------------------------------------------
    # Private generators
    # ------------------------------------------------------------------

    async def _generate_db_schema(
        self, design_json: str, llm: LLMClient
    ) -> DatabaseSchema:
        user_msg = DB_SCHEMA_USER.format(design_json=design_json)
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=DB_SCHEMA_SYSTEM,
        )
        result, errors = parse_into_model(raw, DatabaseSchema)
        if result is None:
            raise ValueError(
                f"DB schema generation failed: {'; '.join(errors)}"
            )
        return result

    async def _generate_api_schema(
        self, design_json: str, db_schema_json: str, llm: LLMClient
    ) -> APISchema:
        user_msg = API_SCHEMA_USER.format(
            design_json=design_json, db_schema_json=db_schema_json
        )
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=API_SCHEMA_SYSTEM,
        )
        result, errors = parse_into_model(raw, APISchema)
        if result is None:
            raise ValueError(
                f"API schema generation failed: {'; '.join(errors)}"
            )
        return result

    async def _generate_ui_schema(
        self, design_json: str, api_schema_json: str, llm: LLMClient
    ) -> UISchema:
        user_msg = UI_SCHEMA_USER.format(
            design_json=design_json, api_schema_json=api_schema_json
        )
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=UI_SCHEMA_SYSTEM,
        )
        result, errors = parse_into_model(raw, UISchema)
        if result is None:
            raise ValueError(
                f"UI schema generation failed: {'; '.join(errors)}"
            )
        return result

    async def _generate_auth_schema(
        self, design_json: str, llm: LLMClient
    ) -> AuthSchema:
        user_msg = AUTH_SCHEMA_USER.format(design_json=design_json)
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=AUTH_SCHEMA_SYSTEM,
        )
        result, errors = parse_into_model(raw, AuthSchema)
        if result is None:
            raise ValueError(
                f"Auth schema generation failed: {'; '.join(errors)}"
            )
        return result

    async def _generate_business_logic(
        self, design_json: str, db_schema_json: str, llm: LLMClient
    ) -> BusinessLogicSchema:
        user_msg = BUSINESS_LOGIC_USER.format(
            design_json=design_json, db_schema_json=db_schema_json
        )
        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=BUSINESS_LOGIC_SYSTEM,
        )
        result, errors = parse_into_model(raw, BusinessLogicSchema)
        if result is None:
            raise ValueError(
                f"Business logic generation failed: {'; '.join(errors)}"
            )
        return result
