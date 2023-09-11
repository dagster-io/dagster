from typing import (
    Dict,
    Type,
)

import pydantic

PydanticUndefined = None
try:
    from pydantic_core import PydanticUndefined as _PydanticUndefined  # type: ignore

    PydanticUndefined = _PydanticUndefined
except:
    pass


from pydantic import BaseModel

from .attach_other_object_to_context import (
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
)

USING_PYDANTIC_2 = int(pydantic.__version__.split(".")[0]) >= 2


class ModelFieldCompat:
    """Wraps a Pydantic model field to provide a consistent interface for accessing
    metadata and annotations between Pydantic 1 and 2.
    """

    def __init__(self, field):
        self.field = field

    @property
    def annotation(self):
        return self.field.annotation

    @property
    def metadata(self):
        return getattr(self.field, "metadata", None)

    @property
    def alias(self):
        return self.field.alias

    @property
    def default(self):
        return self.field.default

    @property
    def description(self):
        # Pydantic 1.x
        field_info = getattr(self.field, "field_info", None)
        if field_info:
            return field_info.description

        # Pydantic 2.x
        return getattr(self.field, "description", None)

    def is_required(self):
        # Pydantic 2.x
        if hasattr(self.field, "is_required"):
            return self.field.is_required()

        # Pydantic 1.x
        return self.field.required

    @property
    def discriminator(self):
        # Pydantic 2.x
        if hasattr(self.field, "discriminator"):
            return self.field.discriminator

        # Pydantic 1.x
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
    # Pydantic 2.x
    if hasattr(model, "model_config"):
        return getattr(model, "model_config")

    # Pydantic 1.x
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
