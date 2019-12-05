from dagster import check
from dagster.core.types.config import ConfigType


def iterate_config_types(config_type):

    # TODO: Investigate during config refactor. Very sketchy -- schrockn 12/05/19
    # Looping over this should be done at callsites
    if isinstance(config_type, list):
        check.list_param(config_type, 'config_type', of_type=ConfigType)
        for config_type_item in config_type:
            for inner_type in iterate_config_types(config_type_item):
                yield inner_type

    check.inst_param(config_type, 'config_type', ConfigType)
    if config_type.is_list or config_type.is_nullable:
        for inner_type in iterate_config_types(config_type.inner_type):
            yield inner_type

    if config_type.has_fields:
        for field_type in config_type.fields.values():
            for inner_type in iterate_config_types(field_type.config_type):
                yield inner_type

    yield config_type
