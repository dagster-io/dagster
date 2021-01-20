from collections import namedtuple
from typing import Any, Callable, Dict, Optional, Union

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.primitive_mapping import is_supported_config_python_builtin

from .definition_config_schema import convert_user_facing_definition_config_schema


def is_callable_valid_config_arg(config: Dict[str, Any]) -> bool:
    return BuiltinEnum.contains(config) or is_supported_config_python_builtin(config)


class ConfigMapping(namedtuple("_ConfigMapping", "config_fn config_schema")):
    """Defines a config mapping for a composite solid.

    By specifying a config mapping function, you can override the configuration for the child
    solids contained within a composite solid.

    Config mappings require the configuration schema to be specified as ``config_schema``, which will
    be exposed as the configuration schema for the composite solid, as well as a configuration mapping
    function, ``config_fn``, which maps the config provided to the composite solid to the config
    that will be provided to the child solids.

    Args:
        config_fn (Callable[[dict], dict]): The function that will be called
            to map the composite config to a config appropriate for the child solids.
        config_schema (ConfigSchema): The schema of the composite config.
    """

    def __new__(
        cls,
        config_fn: Callable[[Union[Any, Dict[str, Any]]], Union[Any, Dict[str, Any]]],
        config_schema: Optional[Union[Any, Dict[str, Any]]] = None,
    ):
        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, "config_fn"),
            config_schema=convert_user_facing_definition_config_schema(config_schema),
        )
