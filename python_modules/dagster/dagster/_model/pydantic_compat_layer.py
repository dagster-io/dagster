from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Sequence, Type, Union

from pydantic import (
    BaseModel,
    TypeAdapter,
    ValidationError,
    model_validator as model_validator,
)
from pydantic_core import PydanticUndefined as _PydanticUndefined

PydanticUndefined = _PydanticUndefined


if TYPE_CHECKING:
    from pydantic.fields import ModelField  # type: ignore


class ModelFieldCompat:
    """Wraps a Pydantic model field to provide a consistent interface for accessing
    metadata and annotations between Pydantic 1 and 2.
    """

    def __init__(self, field) -> None:
        self.field: "ModelField" = field

    @property
    def annotation(self) -> Type:
        return self.field.annotation

    @property
    def metadata(self) -> List[str]:
        return getattr(self.field, "metadata", [])

    @property
    def alias(self) -> Optional[str]:
        return self.field.alias

    @property
    def serialization_alias(self) -> Optional[str]:
        return getattr(self.field, "serialization_alias", None)

    @property
    def validation_alias(self) -> Optional[str]:
        return getattr(self.field, "validation_alias", None)

    @property
    def default(self) -> Any:
        return self.field.default

    @property
    def description(self) -> Optional[str]:
        return getattr(self.field, "description", None)

    def is_required(self) -> bool:
        return self.field.is_required()

    @property
    def discriminator(self) -> Optional[str]:
        if hasattr(self.field, "discriminator"):
            return self.field.discriminator if hasattr(self.field, "discriminator") else None


def model_fields(model) -> Dict[str, ModelFieldCompat]:
    """Returns a dictionary of fields for a given pydantic model, wrapped
    in a compat class to provide a consistent interface between Pydantic 1 and 2.
    """
    fields = getattr(model, "model_fields", None)
    if not fields:
        fields = getattr(model, "__fields__")

    return {k: ModelFieldCompat(v) for k, v in fields.items()}


def model_config(model: Type[BaseModel]):
    """Returns the config for a given pydantic model, wrapped such that it has
    a Pydantic 2-style interface for accessing config values.
    """
    return getattr(model, "model_config")


def build_validation_error(
    base_error: ValidationError,
    line_errors: List,
    hide_input: bool,
    input_type: Literal["python", "json"],
) -> ValidationError:
    return ValidationError.from_exception_data(
        title=base_error.title,
        line_errors=line_errors,
        input_type=input_type,
        hide_input=hide_input,
    )


def json_schema_from_type(model_type: Union[Type[BaseModel], Type[Sequence[BaseModel]]]):
    """Pydantic version stable way to get the JSON schema for a Pydantic model."""
    # This nicely handles the case where the per_file_blueprint_type is actually
    # a union type etc.
    return TypeAdapter(model_type).json_schema()
