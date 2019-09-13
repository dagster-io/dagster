from dagster.core.types import Bool, Float, Int, PythonDict, String

from .typing_api import is_closed_python_optional_type, is_python_list_type
from .wrapping import remap_to_dagster_list_type, remap_to_dagster_optional_type


def remap_python_type(ttype):

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

    if is_python_list_type(ttype):
        return remap_to_dagster_list_type(ttype)
    if is_closed_python_optional_type(ttype):
        return remap_to_dagster_optional_type(ttype)

    return ttype
