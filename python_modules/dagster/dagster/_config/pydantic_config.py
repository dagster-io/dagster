from typing import Type, Any
from pydantic import BaseModel
from pydantic.fields import ModelField
import dagster._check as check
from dagster._config.field import Field
from dagster._config.field_utils import convert_potential_field
from dagster._config.primitive_mapping import (
    is_supported_config_python_builtin,
    remap_python_builtin_for_config,
)

# todo how to type python classes
def infer_config_field_from_pydanic(cls: Type[Any]) -> Field:
    if is_supported_config_python_builtin(cls):
        return convert_potential_field(cls)

    check.param_invariant(
        issubclass(cls, BaseModel), "If not a primitive, cls must inherit from pydantic.BaseModel"
    )

    # TODO
    # Permissive
    # Selector

    config_schema = {}

    for pydantic_field_name, pydantic_field in cls.__fields__.items():
        config_schema[pydantic_field_name] = pydantic_field.type_
        # TODO check for base model and recurse

    return convert_potential_field(config_schema)
