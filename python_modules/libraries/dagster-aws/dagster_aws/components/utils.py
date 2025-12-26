from typing import Any, cast

from pydantic import BaseModel


def copy_fields_from_model(source: type[BaseModel]) -> dict[str, tuple[type, Any]]:
    """Extract field definitions from a Pydantic model for use with create_model."""
    return {
        field_name: (cast("type", field.annotation), field)
        for field_name, field in source.model_fields.items()
    }
