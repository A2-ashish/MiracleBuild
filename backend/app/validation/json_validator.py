"""Generic JSON / Pydantic structural validation utilities."""
from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, ValidationError

from app.schemas.app_config import ValidationCheck


def validate_json_structure(
    data: dict[str, Any], model_class: Type[BaseModel]
) -> list[ValidationCheck]:
    """Try to parse *data* into *model_class* and report per-field results.

    Args:
        data: Raw dictionary to validate.
        model_class: Target Pydantic model class.

    Returns:
        A list of ``ValidationCheck`` entries — one "pass" entry when
        successful, or one entry per validation error on failure.
    """
    checks: list[ValidationCheck] = []
    try:
        model_class.model_validate(data)
        checks.append(
            ValidationCheck(
                name=f"json_structure_{model_class.__name__}",
                passed=True,
                message=f"{model_class.__name__} parsed successfully",
            )
        )
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(l) for l in err["loc"])
            checks.append(
                ValidationCheck(
                    name=f"json_field_{model_class.__name__}_{loc}",
                    passed=False,
                    message=f"{loc}: {err['msg']}",
                )
            )
    return checks
