"""UI schema models for the front-end specification."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class ComponentType(str, Enum):
    """Types of UI component available."""

    FORM = "form"
    TABLE = "table"
    CHART = "chart"
    CARD = "card"
    STAT_CARD = "stat_card"
    LIST = "list"
    MODAL = "modal"
    TABS = "tabs"
    CALENDAR = "calendar"
    KANBAN = "kanban"
    TIMELINE = "timeline"
    MAP = "map"
    FILE_UPLOAD = "file_upload"
    RICH_TEXT = "rich_text"


class FormField(BaseModel):
    """A field inside a form component."""

    name: str
    label: str
    type: str  # text, email, password, number, date, select, textarea, checkbox, file
    required: bool = True
    placeholder: str = ""
    options: Optional[list[dict]] = None  # For select fields
    validation: Optional[dict] = None


class TableColumn(BaseModel):
    """A column inside a table component."""

    key: str
    label: str
    type: str = "text"  # text, number, date, badge, actions, link, image
    sortable: bool = True
    filterable: bool = False
    width: Optional[str] = None


class ChartConfig(BaseModel):
    """Configuration for a chart component."""

    type: str  # bar, line, pie, doughnut, area
    data_key: str
    label_key: str
    title: str = ""


class Action(BaseModel):
    """An action button or trigger on a component."""

    label: str
    type: str  # navigate, submit, delete, modal, export
    target: str = ""  # URL or modal name
    confirm: bool = False
    icon: Optional[str] = None


class Component(BaseModel):
    """A single UI component placed on a page."""

    id: str
    type: ComponentType
    title: str = ""
    data_source: str = ""  # API endpoint path
    props: dict = {}
    form_fields: Optional[list[FormField]] = None
    table_columns: Optional[list[TableColumn]] = None
    chart_config: Optional[ChartConfig] = None
    actions: list[Action] = []
    grid_span: int = 12  # 1-12 grid system
    visible_to_roles: list[str] = []


class ThemeColors(BaseModel):
    """Colour palette for the UI theme."""

    primary: str = "#6366f1"
    secondary: str = "#8b5cf6"
    accent: str = "#06b6d4"
    background: str = "#0f172a"
    surface: str = "#1e293b"
    text: str = "#f8fafc"
    text_secondary: str = "#94a3b8"
    success: str = "#22c55e"
    warning: str = "#f59e0b"
    error: str = "#ef4444"


class Theme(BaseModel):
    """UI theme configuration."""

    colors: ThemeColors = ThemeColors()
    font_family: str = "Inter, sans-serif"
    border_radius: str = "12px"
    dark_mode: bool = True


class NavItem(BaseModel):
    """A single navigation menu item."""

    label: str
    path: str
    icon: str = ""
    children: list[NavItem] = []
    roles: list[str] = []
    badge: Optional[str] = None


class Navigation(BaseModel):
    """Application navigation structure."""

    type: str = "sidebar"  # sidebar, topbar, hybrid
    items: list[NavItem]
    logo_text: str = ""


class Page(BaseModel):
    """A full page / view in the application."""

    name: str
    path: str
    title: str
    layout: str = "dashboard"  # dashboard, form, list, detail, split, landing
    components: list[Component]
    requires_auth: bool = True
    allowed_roles: list[str] = []
    is_default: bool = False


class UISchema(BaseModel):
    """Complete UI specification."""

    app_name: str
    theme: Theme = Theme()
    navigation: Navigation
    pages: list[Page]
