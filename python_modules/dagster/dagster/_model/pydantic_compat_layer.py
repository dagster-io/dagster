import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Sequence, Type, Union

import pydantic
from pydantic import BaseModel, ValidationError

USING_PYDANTIC_1 = int(pydantic.__version__.split(".")[0]) == 1
USING_PYDANTIC_2 = int(pydantic.__version__.split(".")[0]) >= 2

PydanticUndefined = None
if USING_PYDANTIC_2:
    from pydantic_core import PydanticUndefined as _PydanticUndefined  # type: ignore

    PydanticUndefined = _PydanticUndefined


if TYPE_CHECKING:
    from pydantic.fields import ModelField


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
        if USING_PYDANTIC_2:
            return self.field.alias
        else:
            return self.field.alias if self.field.alias != self.field.name else None

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
        if USING_PYDANTIC_2:
            return getattr(self.field, "description", None)
        else:
            field_info = getattr(self.field, "field_info", None)
            return field_info.description if field_info else None

    def is_required(self) -> bool:
        if USING_PYDANTIC_2:
            return self.field.is_required()  # type: ignore
        else:
            # required is of type 'BoolUndefined', which is a Union of bool and pydantic 1.x's UndefinedType
            return self.field.required if isinstance(self.field.required, bool) else False

    @property
    def discriminator(self) -> Optional[str]:
        if USING_PYDANTIC_2:
            if hasattr(self.field, "discriminator"):
                return self.field.discriminator if hasattr(self.field, "discriminator") else None  # type: ignore
        else:
            return getattr(self.field, "discriminator_key", None)


def model_fields(model) -> Dict[str, ModelFieldCompat]:
    """Returns a dictionary of fields for a given pydantic model, wrapped
    in a compat class to provide a consistent interface between Pydantic 1 and 2.
    """
    fields = getattr(model, "model_fields", None)
    if not fields:
        fields = getattr(model, "__fields__")

    return {k: ModelFieldCompat(v) for k, v in fields.items()}


class Pydantic1ConfigWrapper:
    """Config wrapper for Pydantic 1 style model config, which provides a
    Pydantic 2 style interface for accessing mopdel config values.
    """

    def __init__(self, config):
        self._config = config

    def get(self, key):
        return getattr(self._config, key)


def model_config(model: Type[BaseModel]):
    """Returns the config for a given pydantic model, wrapped such that it has
    a Pydantic 2-style interface for accessing config values.
    """
    if USING_PYDANTIC_2:
        return getattr(model, "model_config")
    else:
        return Pydantic1ConfigWrapper(getattr(model, "__config__"))


try:
    # Pydantic 2.x
    from pydantic import model_validator as model_validator  # type: ignore
except ImportError:
    # Pydantic 1.x
    from pydantic import root_validator

    def model_validator(mode="before"):
        """Mimics the Pydantic 2.x model_validator decorator, which is used to
        define validation logic for a Pydantic model. This decorator is used
        to wrap a validation function which is called before or after the
        model is constructed.
        """

        def _decorate(func):
            return (
                root_validator(pre=True)(func)
                if mode == "before"
                else root_validator(post=False)(func)
            )

        return _decorate


compat_model_validator = model_validator


def build_validation_error(
    base_error: ValidationError,
    line_errors: List,
    hide_input: bool,
    input_type: Literal["python", "json"],
) -> ValidationError:
    if USING_PYDANTIC_1:
        return ValidationError(errors=line_errors, model=base_error.model)  # type: ignore
    else:
        return ValidationError.from_exception_data(  # type: ignore
            title=base_error.title,  # type: ignore
            line_errors=line_errors,
            input_type=input_type,
            hide_input=hide_input,
        )


def json_schema_from_type(model_type: Union[Type[BaseModel], Type[Sequence[BaseModel]]]):
    """Pydantic version stable way to get the JSON schema for a Pydantic model."""
    # This nicely handles the case where the per_file_blueprint_type is actually
    # a union type etc.
    if USING_PYDANTIC_1:
        from pydantic.tools import schema_json_of

        return json.loads(schema_json_of(model_type))

    else:
        from pydantic import TypeAdapter  # type: ignore

        return TypeAdapter(model_type).json_schema()
