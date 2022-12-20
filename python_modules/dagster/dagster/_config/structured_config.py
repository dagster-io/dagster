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

    if _safe_is_subclass(pydantic_field.type_, Config):
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

    if _safe_is_subclass(model_cls, Config):
        return infer_schema_from_config_class(model_cls)

    return convert_potential_field(model_cls)


def _safe_is_subclass(cls: Type, possible_parent_cls: Type) -> bool:
    """Safe version of issubclass that returns False if cls is not a class."""
    try:
        return issubclass(cls, possible_parent_cls)
    except TypeError:
        return False


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
