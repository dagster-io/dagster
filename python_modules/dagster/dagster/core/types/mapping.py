from dagster.core.types import Bool, Float, Int, PythonDict, PythonSet, PythonTuple, String

from .typing_api import (
    is_closed_python_optional_type,
    is_python_list_type,
    is_python_set_type,
    is_python_tuple_type,
)
from .wrapping import (
    remap_to_dagster_list_type,
    remap_to_dagster_optional_type,
    remap_to_dagster_set_type,
    remap_to_dagster_tuple_type,
)


def remap_python_type(ttype):
    '''This function remaps a python type to a Dagster type, or passes it through if it cannot be
    remapped.
    '''

    if ttype == int:
        return Int
    if ttype == float:
        return Float
    if ttype == bool:
        return Bool
    if ttype == str:
        return String
    if ttype == dict:
        return PythonDict
    if ttype == tuple:
        return PythonTuple
    if ttype == set:
        return PythonSet

    if is_python_list_type(ttype):
        return remap_to_dagster_list_type(ttype)
    if is_python_tuple_type(ttype):
        return remap_to_dagster_tuple_type(ttype)
    if is_python_set_type(ttype):
        return remap_to_dagster_set_type(ttype)
    if is_closed_python_optional_type(ttype):
        return remap_to_dagster_optional_type(ttype)

    return ttype
