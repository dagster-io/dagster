from dagster.core.types import Int, Float, Bool, String
from .wrapping import (
    is_python_list_typehint,
    is_python_optional_typehint,
    remap_to_dagster_optional_type,
    remap_to_dagster_list_type,
)


def remap_python_type(type_annotation):

    if type_annotation == int:
        return Int
    if type_annotation == float:
        return Float
    if type_annotation == bool:
        return Bool
    if type_annotation == str:
        return String

    if is_python_list_typehint(type_annotation):
        return remap_to_dagster_list_type(type_annotation)
    if is_python_optional_typehint(type_annotation):
        return remap_to_dagster_optional_type(type_annotation)

    return type_annotation
