import dagster._check as check
from dagster._config import Array
from dagster._config import ConfigAnyInstance as ConfigAny
from dagster._config import Permissive

from .builtins import Bool, Float, Int, String
from .core.types.dagster_type import Any as RuntimeAny
from .core.types.dagster_type import List
from .core.types.python_dict import PythonDict
from .core.types.python_set import PythonSet
from .core.types.python_tuple import PythonTuple

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
    from dagster.core.types.dagster_type import resolve_dagster_type

    check.param_invariant(is_supported_runtime_python_builtin(ttype), "ttype")

    return resolve_dagster_type(SUPPORTED_RUNTIME_BUILTINS[ttype])


SUPPORTED_CONFIG_BUILTINS = {
    int: Int,
    float: Float,
    bool: Bool,
    str: String,
    list: Array(ConfigAny),
    dict: Permissive(),
}


def is_supported_config_python_builtin(ttype):
    return ttype in SUPPORTED_CONFIG_BUILTINS


def remap_python_builtin_for_config(ttype):
    """This function remaps a python type to a Dagster type, or passes it through if it cannot be
    remapped.
    """
    from dagster._config import resolve_to_config_type

    check.param_invariant(is_supported_config_python_builtin(ttype), "ttype")

    return resolve_to_config_type(SUPPORTED_CONFIG_BUILTINS[ttype])
