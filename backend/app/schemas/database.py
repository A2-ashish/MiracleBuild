"""Database schema models for the DB layer specification."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class ColumnType(str, Enum):
    """Supported column data types."""

    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    EMAIL = "email"
    ENUM = "enum"
    DECIMAL = "decimal"


class ForeignKey(BaseModel):
    """Foreign-key reference to another table."""

    table: str
    column: str = "id"
    on_delete: str = "CASCADE"


class Column(BaseModel):
    """A single column in a database table."""

    name: str
    type: ColumnType
    nullable: bool = False
    unique: bool = False
    default: Optional[Any] = None
    references: Optional[ForeignKey] = None
    enum_values: Optional[list[str]] = None
    description: str = ""


class Index(BaseModel):
    """A database index on one or more columns."""

    columns: list[str]
    unique: bool = False
    name: Optional[str] = None


class Table(BaseModel):
    """A database table definition."""

    name: str
    description: str = ""
    columns: list[Column]
    primary_key: str = "id"
    indexes: list[Index] = []
    timestamps: bool = True


class Relation(BaseModel):
    """A relational link between two tables."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str = "id"
    type: str  # one_to_one, one_to_many, many_to_many
    junction_table: Optional[str] = None


class DatabaseSchema(BaseModel):
    """Complete database schema specification."""

    tables: list[Table]
    relations: list[Relation] = []
