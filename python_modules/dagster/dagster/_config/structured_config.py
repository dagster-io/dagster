from typing import Type

from pydantic import BaseModel
from pydantic.fields import SHAPE_SINGLETON, ModelField

import dagster._check as check
from dagster import Field, Shape
from dagster._config.field_utils import convert_potential_field


class Config(BaseModel):
    """
    Base class for Dagster configuration models.
    """


def _convert_pydantic_field(pydantic_field: ModelField) -> Field:
    """
    Transforms a Pydantic field into a corresponding Dagster config field.
    """

    if issubclass(pydantic_field.type_, Config):
        return infer_schema_from_config_class(pydantic_field.type_)

    dagster_type = pydantic_field.type_
    if pydantic_field.shape == SHAPE_SINGLETON:
        pass
    else:
        raise NotImplementedError(f"Pydantic shape {pydantic_field.shape} not supported.")

    return convert_potential_field(dagster_type)


def infer_schema_from_config_annotation(model_cls: Type) -> Field:
    """
    Parses a structured config class or primitive type and returns a corresponding Dagster config Field.
    """

    try:
        if issubclass(model_cls, Config):
            return infer_schema_from_config_class(model_cls)
    except TypeError:
        # In case a user passes e.g. a Typing type, which is not a class
        # convert_potential_field will produce a more actionable error message
        # than the TypeError that would be raised here
        pass

    return convert_potential_field(model_cls)


def infer_schema_from_config_class(model_cls: Type[Config]) -> Field:
    """
    Parses a structured config class and returns a corresponding Dagster config Field.
    """

    check.param_invariant(
        issubclass(model_cls, Config),
        "Config type annotation must inherit from dagster._config.structured_config.Config",
    )

    fields = {}
    for pydantic_field_name, pydantic_field in model_cls.__fields__.items():
        fields[pydantic_field_name] = _convert_pydantic_field(pydantic_field)

    return Field(config=Shape(fields))
