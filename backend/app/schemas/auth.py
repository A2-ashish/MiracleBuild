"""Authentication and authorisation schema models."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class Permission(BaseModel):
    """Permission on a specific resource."""

    resource: str
    actions: list[str]  # create, read, update, delete, export, manage


class Role(BaseModel):
    """An application role with its permissions."""

    name: str
    display_name: str
    description: str = ""
    permissions: list[Permission]
    is_default: bool = False
    is_admin: bool = False


class PasswordPolicy(BaseModel):
    """Password strength requirements."""

    min_length: int = 8
    require_uppercase: bool = True
    require_number: bool = True
    require_special: bool = False


class SessionConfig(BaseModel):
    """Session / token configuration."""

    token_type: str = "JWT"
    expiry_hours: int = 24
    refresh_enabled: bool = True


class AuthSchema(BaseModel):
    """Complete authentication specification."""

    roles: list[Role]
    password_policy: PasswordPolicy = PasswordPolicy()
    session_config: SessionConfig = SessionConfig()
    registration_enabled: bool = True
    default_role: str = "user"
    oauth_providers: list[str] = []
