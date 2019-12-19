from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.config import IRunConfig
from dagster.core.types.config.field_utils import (
    check_user_facing_opt_config_param,
    coerce_potential_field,
    is_potential_field,
)
from dagster.core.types.wrapping.builtin_enum import BuiltinEnum
from dagster.core.types.wrapping.mapping import is_supported_config_python_builtin


def resolve_config(config, source):
    if not is_potential_field(config):
        raise DagsterInvalidDefinitionError(
            (
                'You have passed an object {value_repr} of incorrect type '
                '"{type_name}" in the parameter "{param_name}" '
                '{error_context_str} where a Field, dict, or type was expected.'
            ).format(
                error_context_str='of ' + source,
                param_name='config',
                value_repr=repr(config),
                type_name=type(config).__name__,
            )
        )

    def _raise_error(value):
        # https://github.com/dagster-io/dagster/issues/1976
        raise DagsterInvalidDefinitionError(
            (
                'You have passed an object {value_repr} of incorrect type "{type_name}" '
                'somewhere in config structure passed to a {source} where a Field, dict, '
                'or type was expected.'
            ).format(value_repr=repr(value), type_name=type(value).__name__, source=source)
        )

    return coerce_potential_field(config, _raise_error)


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
        config_fn (Callable[[ConfigMappingContext, dict], dict]): The function that will be called
            to map the composite config to a config appropriate for the child solids.
        config_field (Field): The schema of the composite config.
    '''

    def __new__(cls, config_fn, config=None):
        config = check.opt_dict_param(config, 'config')

        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, 'config_fn'),
            config_field=check_user_facing_opt_config_param(config, 'config', 'ConfigMapping'),
        )


class ConfigMappingContext(namedtuple('ConfigMappingContext', 'run_config')):
    '''Config mapping-specific context.

    Attributes:
        run_config (RunConfig): The run config belonging to this pipeline run.
    '''

    def __new__(cls, run_config=None):
        return super(ConfigMappingContext, cls).__new__(
            cls, check.inst_param(run_config, 'run_config', IRunConfig)
        )
