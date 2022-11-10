from typing import Any, Mapping, Type
from typing_extensions import Final
import dagster._check as check
from dagster._builtins import Bool, Float, Int, String

from .config_type import Array, ConfigAnyInstance, ConfigType
from .field import normalize_config_type
from .field_utils import Permissive

SUPPORTED_CONFIG_BUILTIN_MAP: Final[Mapping[Type[Any], ConfigType]] = {
    int: Int,
    float: Float,
    bool: Bool,
    str: String,
    list: Array(ConfigAnyInstance),  # type: ignore
    dict: Permissive(),
}

SUPPORTED_CONFIG_BUILTINS = [*SUPPORTED_CONFIG_BUILTIN_MAP.keys()]


def is_supported_config_python_builtin(ttype):
    return ttype in SUPPORTED_CONFIG_BUILTINS


def remap_python_builtin_for_config(ttype: Type[Any]) -> ConfigType:
    """This function remaps a python type to a Dagster type, or passes it through if it cannot be
    remapped.
    """
    check.param_invariant(is_supported_config_python_builtin(ttype), "ttype")

    return normalize_config_type(SUPPORTED_CONFIG_BUILTIN_MAP[ttype])
