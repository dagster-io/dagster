from dagster import check
from dagster.core.types.config import ConfigType


def iterate_config_types(config_type):
    check.inst_param(config_type, 'config_type', ConfigType)
    if config_type.is_list or config_type.is_nullable:
        # Descend to inner types but do not yield lists and nullables
        # They are empheral and not returned to clients
        for inner_type in iterate_config_types(config_type.inner_type):
            yield inner_type
        return

    if config_type.has_fields:
        for field_type in config_type.fields.values():
            for inner_type in iterate_config_types(field_type.config_type):
                yield inner_type

    yield config_type
