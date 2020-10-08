from dagster import check

from .config_type import ConfigType, ConfigTypeKind
from .snap import ConfigSchemaSnapshot, snap_from_config_type


def iterate_config_types(config_type):
    check.inst_param(config_type, "config_type", ConfigType)
    if config_type.kind == ConfigTypeKind.ARRAY or config_type.kind == ConfigTypeKind.NONEABLE:
        for inner_type in iterate_config_types(config_type.inner_type):
            yield inner_type

    if ConfigTypeKind.has_fields(config_type.kind):
        for field_type in config_type.fields.values():
            for inner_type in iterate_config_types(field_type.config_type):
                yield inner_type

    if config_type.kind == ConfigTypeKind.SCALAR_UNION:
        yield config_type.scalar_type
        for inner_type in iterate_config_types(config_type.non_scalar_type):
            yield inner_type

    yield config_type


def config_schema_snapshot_from_config_type(config_type):
    check.inst_param(config_type, "config_type", ConfigType)
    return ConfigSchemaSnapshot(
        {ct.key: snap_from_config_type(ct) for ct in iterate_config_types(config_type)}
    )
