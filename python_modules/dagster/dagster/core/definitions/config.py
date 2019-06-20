from collections import namedtuple

from dagster import check
from dagster.core.errors import DagsterInvalidDefinitionError
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


class ConfigMapping(namedtuple('_ConfigMapping', 'config_mapping_fn config_field')):
    '''By specifying a config mapping, you can override the configuration for child solids
    contained within this composite solid. Config mappings require both a configuration field to be
    specified, which is exposed as the configuration for this composite solid, and a configuration
    mapping function, which maps the parent configuration of this solid into a configuration that is
    applied to any child solids.
    '''

    def __new__(cls, config_mapping_fn, config=None, config_field=None):
        return super(ConfigMapping, cls).__new__(
            cls,
            config_mapping_fn=check.callable_param(config_mapping_fn, 'config_mapping_fn'),
            config_field=resolve_config_field(config_field, config, 'ConfigMapping'),
        )
