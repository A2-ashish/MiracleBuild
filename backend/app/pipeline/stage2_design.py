"""Stage 2 — System Design.

Transforms a validated ``IntentResult`` into a ``SystemDesign`` document
that describes pages, flows, entity relations, and a permission matrix.
"""
from __future__ import annotations

import logging

from app.llm.client import LLMClient
from app.llm.prompts import SYSTEM_DESIGN_SYSTEM, SYSTEM_DESIGN_USER
from app.llm.response_parser import parse_into_model
from app.schemas.intent import IntentResult
from app.schemas.design import SystemDesign

logger = logging.getLogger(__name__)


class SystemDesigner:
    """Produces an architectural design from an intent specification."""

    async def design(
        self, intent: IntentResult, llm: LLMClient
    ) -> SystemDesign:
        """Generate the system design.

        The method also performs two post-processing steps:
        1. Ensures a ``User`` entity relation exists when auth features
           are present.
        2. Fills gaps in the permission matrix so every role has at least
           read access to every resource.

        Args:
            intent: Validated intent result from Stage 1.
            llm: Configured LLM client.

        Returns:
            Validated ``SystemDesign``.

        Raises:
            ValueError: If the model output cannot be parsed.
        """
        intent_json = intent.model_dump_json(indent=2)
        user_msg = SYSTEM_DESIGN_USER.format(intent_json=intent_json)

        raw = await llm.generate(
            prompt=user_msg,
            system_instruction=SYSTEM_DESIGN_SYSTEM,
        )

        result, errors = parse_into_model(raw, SystemDesign)
        if result is None:
            raise ValueError(
                f"System design failed to parse: {'; '.join(errors)}"
            )

        # --- Post-processing ---
        result = self._ensure_user_entity_relations(result, intent)
        result = self._fill_permission_gaps(result, intent)

        logger.info(
            "System design complete: relations=%d, pages=%d, flows=%d",
            len(result.entity_relations),
            len(result.pages),
            len(result.user_flows),
        )
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_user_entity_relations(
        design: SystemDesign, intent: IntentResult
    ) -> SystemDesign:
        """Add implicit User relations if missing."""
        from app.schemas.design import EntityRelation, RelationType

        entity_names = {e.name.lower() for e in intent.entities}
        relation_pairs = {
            (r.from_entity.lower(), r.to_entity.lower())
            for r in design.entity_relations
        }

        # If there's a User entity and other entities reference it, make sure
        # the relation exists.
        if "user" in entity_names:
            for entity in intent.entities:
                key = entity.name.lower()
                if key == "user":
                    continue
                # Check if any attribute looks like a user FK
                has_user_attr = any(
                    "user" in attr.name.lower() for attr in entity.attributes
                )
                if has_user_attr:
                    pair = ("user", key)
                    reverse = (key, "user")
                    if pair not in relation_pairs and reverse not in relation_pairs:
                        design.entity_relations.append(
                            EntityRelation(
                                from_entity="User",
                                to_entity=entity.name,
                                type=RelationType.ONE_TO_MANY,
                                description=f"A User owns many {entity.name}s",
                            )
                        )

        return design

    @staticmethod
    def _fill_permission_gaps(
        design: SystemDesign, intent: IntentResult
    ) -> SystemDesign:
        """Ensure every role appears in the permission matrix for every resource."""
        from app.schemas.design import PermissionEntry

        role_names = [r.name for r in intent.user_roles]
        resources = {e.name for e in intent.entities}

        # Build lookup of existing permissions
        existing: dict[str, set[str]] = {}
        for entry in design.permission_matrix:
            existing.setdefault(entry.resource, set()).update(entry.roles)

        for resource in resources:
            covered_roles = existing.get(resource, set())
            missing_roles = [r for r in role_names if r not in covered_roles]
            if missing_roles:
                # Grant at least read access
                design.permission_matrix.append(
                    PermissionEntry(
                        resource=resource,
                        actions=["read"],
                        roles=missing_roles,
                    )
                )

        return design
