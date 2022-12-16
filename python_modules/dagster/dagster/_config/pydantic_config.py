from typing import Any, Type, cast

from pydantic import BaseModel, Extra
from pydantic.fields import SHAPE_SINGLETON, SHAPE_LIST, SHAPE_MAPPING, SHAPE_DICT, ModelField

import dagster._check as check
from dagster import Field, Permissive, Shape, Array, Map
from dagster._config.field_utils import FIELD_NO_DEFAULT_PROVIDED, convert_potential_field
from dagster._config.primitive_mapping import (
    is_supported_config_python_builtin,
    remap_python_builtin_for_config,
)


def _convert_pydantic_field(pydantic_field: ModelField) -> Field:
    if issubclass(pydantic_field.type_, BaseModel):
        return infer_config_field_from_pydanic(pydantic_field.type_)

    dagster_type = pydantic_field.type_
    if pydantic_field.shape == SHAPE_SINGLETON:
        pass
    elif pydantic_field.shape == SHAPE_LIST:
        dagster_type = Array(dagster_type)
    elif pydantic_field.shape == SHAPE_MAPPING or pydantic_field.shape == SHAPE_DICT:
        dagster_type = Map(str, dagster_type)
    else:
        raise NotImplementedError(f"Pydantic shape {pydantic_field.shape} not supported.")

    inner_config_type = convert_potential_field(dagster_type).config_type
    return Field(
        config=inner_config_type,
        description=pydantic_field.field_info.description,
        default_value=pydantic_field.default
        if pydantic_field.default
        else FIELD_NO_DEFAULT_PROVIDED,
    )


# todo how to type python classes
def infer_config_field_from_pydanic(cls: Type[Any]) -> Field:
    if is_supported_config_python_builtin(cls):
        return convert_potential_field(cls)

    check.param_invariant(
        issubclass(cls, BaseModel), "If not a primitive, cls must inherit from pydantic.BaseModel"
    )
    model_cls = cast(Type[BaseModel], cls)

    # TODO
    # Selector

    fields = {}

    for pydantic_field_name, pydantic_field in model_cls.__fields__.items():
        fields[pydantic_field_name] = _convert_pydantic_field(pydantic_field)

    shape_type = Permissive if model_cls.__config__.extra == Extra.allow else Shape
    config_type = shape_type(fields)

    potential_field = Field(
        config=config_type, description=model_cls.__doc__.strip() if model_cls.__doc__ else None
    )
    return potential_field
