from typing import Dict, Generator, cast

import dagster._check as check
from dagster.config.field import Field

from .config_type import ConfigType, ConfigTypeKind
from .snap import ConfigSchemaSnapshot, snap_from_config_type


def iterate_config_types(config_type: ConfigType) -> Generator[ConfigType, None, None]:
    check.inst_param(config_type, "config_type", ConfigType)

    # type-ignore comments below are because static type checkers don't
    # understand the `ConfigTypeKind` system.
    if config_type.kind == ConfigTypeKind.MAP:
        yield from iterate_config_types(config_type.key_type)  # type: ignore
        yield from iterate_config_types(config_type.inner_type)  # type: ignore

    if config_type.kind == ConfigTypeKind.ARRAY or config_type.kind == ConfigTypeKind.NONEABLE:
        yield from iterate_config_types(config_type.inner_type)  # type: ignore

    if ConfigTypeKind.has_fields(config_type.kind):
        fields = cast(Dict[str, Field], config_type.fields)  # type: ignore
        for field in fields.values():
            yield from iterate_config_types(field.config_type)

    if config_type.kind == ConfigTypeKind.SCALAR_UNION:
        yield config_type.scalar_type  # type: ignore
        yield from iterate_config_types(config_type.non_scalar_type)  # type: ignore

    yield config_type


def config_schema_snapshot_from_config_type(
    config_type: ConfigType,
) -> ConfigSchemaSnapshot:
    check.inst_param(config_type, "config_type", ConfigType)
    return ConfigSchemaSnapshot(
        {ct.key: snap_from_config_type(ct) for ct in iterate_config_types(config_type)}
    )
