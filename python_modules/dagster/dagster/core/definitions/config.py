from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.config import IRunConfig
from dagster.core.types import Dict, Field


def resolve_config_field(config_field, config, source):
    if config_field is not None and config is not None:
        raise DagsterInvalidDefinitionError(
            'Must only provide one of config_field or config but not both in {}.'
            'Using the config arg is equivalent to config_field=Field(Dict(...)).'.format(source)
        )

    if config_field:
        return config_field

    if config:
        return Field(Dict(config))

    return None


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
            config_field=resolve_config_field(None, config, 'ConfigMapping'),
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
