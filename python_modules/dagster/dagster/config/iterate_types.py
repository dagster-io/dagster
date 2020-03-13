from dagster import check

from .config_type import ConfigType, ConfigTypeKind


def iterate_config_types(config_type):
    # TODO: Investigate during config refactor. Very sketchy -- schrockn 12/05/19
    # Looping over this should be done at callsites
    if isinstance(config_type, list):
        check.list_param(config_type, 'config_type', of_type=ConfigType)
        for config_type_item in config_type:
            for inner_type in iterate_config_types(config_type_item):
                yield inner_type

    check.inst_param(config_type, 'config_type', ConfigType)
    if config_type.kind == ConfigTypeKind.ARRAY or config_type.kind == ConfigTypeKind.NONEABLE:
        for inner_type in iterate_config_types(config_type.inner_type):
            yield inner_type

    if ConfigTypeKind.has_fields(config_type.kind):
        for field_type in config_type.fields.values():
            for inner_type in iterate_config_types(field_type.config_type):
                yield inner_type

    if config_type.kind == ConfigTypeKind.SCALAR_UNION:
        yield config_type.scalar_type
        yield config_type.non_scalar_type

    yield config_type
