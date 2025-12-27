from typing import Any, Optional

from pydantic import BaseModel


def copy_fields_from_model(model: type[BaseModel]) -> dict[str, tuple[type, Any]]:
    """Extracts fields from a Pydantic model and returns them in a format
    suitable for create_model, forcing all fields to be Optional.
    """
    fields = {}
    for name, field in model.model_fields.items():
        fields[name] = (Optional[field.annotation], None)
    return fields
