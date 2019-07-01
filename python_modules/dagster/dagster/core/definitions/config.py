from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
from dagster.core.execution.config import RunConfig
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
    '''By specifying a config mapping, you can override the configuration for child solids
    contained within this composite solid. Config mappings require both a configuration field to be
    specified, which is exposed as the configuration for this composite solid, and a configuration
    mapping function, which maps the parent configuration of this solid into a configuration that is
    applied to any child solids.
    '''

    def __new__(cls, config_fn, config):
        check.dict_param(config, 'config')
        check.invariant(config, 'Cannot specify empty config for ConfigMapping')

        return super(ConfigMapping, cls).__new__(
            cls,
            config_fn=check.callable_param(config_fn, 'config_fn'),
            config_field=resolve_config_field(None, config, 'ConfigMapping'),
        )


class ConfigMappingContext(namedtuple('ConfigMappingContext', 'run_config')):
    '''
    Config mapping context provided as input to config mapping functions.
    '''

    def __new__(cls, run_config=None):
        return super(ConfigMappingContext, cls).__new__(
            cls, check.inst_param(run_config, 'run_config', RunConfig)
        )
