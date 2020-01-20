from collections import namedtuple

from dagster import check
from dagster.builtins import BuiltinEnum
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.primitive_mapping import is_supported_config_python_builtin


def is_callable_valid_config_arg(config):
    return BuiltinEnum.contains(config) or is_supported_config_python_builtin(config)


class ConfigMapping(namedtuple('_ConfigMapping', 'config_fn config_field')):
    '''Defines a config mapping for a composite solid.

    By specifying a config mapping function, you can override the configuration for the child
    solids contained within a composite solid.

    Config mappings require the configuration field to be specified as ``config``, which will be
    exposed as the configuration field for the composite solid, as well as a configuration mapping
    function, ``config_fn``, which maps the config provided to the composite solid to the config
    that will be provided to the child solids.

    Args:
        config_fn (Callable[[dict], dict]): The function that will be called
            to map the composite config to a config appropriate for the child solids.
        config_field (Field): The schema of the composite config.
    '''

    def __new__(cls, config_fn, config=None):
        config = check.opt_dict_param(config, 'config')

        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, 'config_fn'),
            config_field=check_user_facing_opt_config_param(config, 'config'),
        )
