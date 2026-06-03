"""System design models for Stage 2 of the compilation pipeline."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RelationType(str, Enum):
    """Cardinality between two entities."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class EntityRelation(BaseModel):
    """A relationship between two domain entities."""

    from_entity: str
    to_entity: str
    type: RelationType
    description: str = ""


class UserFlow(BaseModel):
    """An end-to-end user flow through the application."""

    name: str
    description: str
    steps: list[str]
    roles: list[str]
    pages_involved: list[str] = []


class PageSpec(BaseModel):
    """High-level specification for a single page / screen."""

    name: str
    path: str
    description: str
    layout: str = Field(
        description="dashboard, form, list, detail, split, landing"
    )
    requires_auth: bool = True
    allowed_roles: list[str] = []
    components_needed: list[str] = []


class PermissionEntry(BaseModel):
    """Maps a resource + action set to roles."""

    resource: str
    actions: list[str]  # create, read, update, delete, export
    roles: list[str]


class SystemDesign(BaseModel):
    """Complete system design produced by Stage 2."""

    app_name: str
    entity_relations: list[EntityRelation]
    user_flows: list[UserFlow]
    pages: list[PageSpec]
    permission_matrix: list[PermissionEntry]
    navigation_structure: dict  # hierarchical nav
