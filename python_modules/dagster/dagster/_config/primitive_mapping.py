import dagster._check as check
from dagster._builtins import Bool, Float, Int, String
from dagster._config.config_type import Array, ConfigAnyInstance
from dagster._config.field import resolve_to_config_type
from dagster._config.field_utils import Permissive

SUPPORTED_CONFIG_BUILTIN_MAP = {
    int: Int,
    float: Float,
    bool: Bool,
    str: String,
    list: Array(ConfigAnyInstance),
    dict: Permissive(),
}

SUPPORTED_CONFIG_BUILTINS = [*SUPPORTED_CONFIG_BUILTIN_MAP.keys()]


def is_supported_config_python_builtin(ttype):
    return ttype in SUPPORTED_CONFIG_BUILTINS


def remap_python_builtin_for_config(ttype):
    """This function remaps a python type to a Dagster type, or passes it through if it cannot be
    remapped.
    """
    check.param_invariant(is_supported_config_python_builtin(ttype), "ttype")

    return resolve_to_config_type(SUPPORTED_CONFIG_BUILTIN_MAP[ttype])
