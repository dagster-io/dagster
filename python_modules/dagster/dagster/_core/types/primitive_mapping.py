import dagster._check as check
from dagster._builtins import Bool, Float, Int, String

from .dagster_type import Any as RuntimeAny
from .dagster_type import List
from .python_dict import PythonDict
from .python_set import PythonSet
from .python_tuple import PythonTuple

# Type-ignores below are due to mypy bug tracking names imported from module's named "types".
SUPPORTED_RUNTIME_BUILTINS = {
    int: Int,
    float: Float,
    bool: Bool,
    str: String,
    list: List(RuntimeAny),  # type: ignore
    tuple: PythonTuple,  # type: ignore
    set: PythonSet,  # type: ignore
    dict: PythonDict,  # type: ignore
}


def is_supported_runtime_python_builtin(ttype):
    return ttype in SUPPORTED_RUNTIME_BUILTINS


def remap_python_builtin_for_runtime(ttype):
    """This function remaps a python type to a Dagster type, or passes it through if it cannot be
    remapped.
    """
    from dagster._core.types.dagster_type import resolve_dagster_type

    check.param_invariant(is_supported_runtime_python_builtin(ttype), "ttype")

    return resolve_dagster_type(SUPPORTED_RUNTIME_BUILTINS[ttype])
