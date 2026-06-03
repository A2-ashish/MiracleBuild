"""API schema models for the REST API specification."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class HttpMethod(str, Enum):
    """HTTP methods supported by API endpoints."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class QueryParam(BaseModel):
    """A query-string parameter for an API endpoint."""

    name: str
    type: str
    required: bool = False
    description: str = ""


class FieldSchema(BaseModel):
    """A single field in a request body or response body."""

    name: str
    type: str
    required: bool = True
    description: str = ""


class RequestBody(BaseModel):
    """Request body specification for an endpoint."""

    content_type: str = "application/json"
    fields: list[FieldSchema]


class ResponseSchema(BaseModel):
    """Response body specification for an endpoint."""

    status_code: int = 200
    content_type: str = "application/json"
    fields: list[FieldSchema]
    is_list: bool = False
    paginated: bool = False


class Endpoint(BaseModel):
    """A single API endpoint definition."""

    path: str
    method: HttpMethod
    description: str
    request_body: Optional[RequestBody] = None
    response: ResponseSchema
    auth_required: bool = True
    required_roles: list[str] = []
    query_params: list[QueryParam] = []
    rate_limit: Optional[int] = None
    related_entity: str = ""


class ErrorFormat(BaseModel):
    """Standard error response shape."""

    fields: list[str] = ["error", "message", "status_code", "details"]


class APISchema(BaseModel):
    """Complete API specification."""

    base_url: str = "/api"
    version: str = "v1"
    endpoints: list[Endpoint]
    error_format: ErrorFormat = ErrorFormat()
