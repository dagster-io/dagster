from dagster.core.types import Dict, Field

from dagster.core.errors import DagsterInvalidDefinitionError


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
