from dagster import check
from dagster.core.types.runtime import RuntimeType
from dagit.schema import dauphin

from .config_types import DauphinConfigType, to_dauphin_config_type


def config_type_for_schema(schema):
    return to_dauphin_config_type(schema.schema_type) if schema else None


def to_dauphin_runtime_type(runtime_type):
    check.inst_param(runtime_type, 'runtime_type', RuntimeType)

    return DauphinRuntimeType(
        name=runtime_type.name,
        description=runtime_type.description,
        is_nullable=runtime_type.is_nullable,
        is_list=runtime_type.is_list,
        input_schema_type=config_type_for_schema(runtime_type.input_schema),
        output_schema_type=config_type_for_schema(runtime_type.output_schema),
    )


class DauphinRuntimeType(dauphin.ObjectType):
    class Meta:
        name = 'RuntimeType'

    name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)

    input_schema_type = dauphin.Field(DauphinConfigType)
    output_schema_type = dauphin.Field(DauphinConfigType)
