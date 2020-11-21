from dagster import check
from dagster.core.snap import PipelineSnapshot
from dagster.core.types.dagster_type import DagsterTypeKind
from dagster_graphql import dauphin

from .config_types import DauphinConfigType, to_dauphin_config_type


def config_type_for_schema(pipeline_snapshot, schema_key):
    return (
        to_dauphin_config_type(pipeline_snapshot.config_schema_snapshot, schema_key)
        if schema_key
        else None
    )


def to_dauphin_dagster_type(pipeline_snapshot, dagster_type_key):
    check.str_param(dagster_type_key, "dagster_type_key")
    check.inst_param(pipeline_snapshot, pipeline_snapshot, PipelineSnapshot)

    dagster_type_meta = pipeline_snapshot.dagster_type_namespace_snapshot.get_dagster_type_snap(
        dagster_type_key
    )

    base_args = dict(
        key=dagster_type_meta.key,
        name=dagster_type_meta.name,
        display_name=dagster_type_meta.display_name,
        description=dagster_type_meta.description,
        is_builtin=dagster_type_meta.is_builtin,
        is_nullable=dagster_type_meta.kind == DagsterTypeKind.NULLABLE,
        is_list=dagster_type_meta.kind == DagsterTypeKind.LIST,
        is_nothing=dagster_type_meta.kind == DagsterTypeKind.NOTHING,
        input_schema_type=config_type_for_schema(
            pipeline_snapshot, dagster_type_meta.loader_schema_key,
        ),
        output_schema_type=config_type_for_schema(
            pipeline_snapshot, dagster_type_meta.materializer_schema_key,
        ),
        inner_types=list(
            map(
                lambda key: to_dauphin_dagster_type(pipeline_snapshot, key),
                dagster_type_meta.type_param_keys,
            )
        ),
    )

    if dagster_type_meta.kind == DagsterTypeKind.LIST:
        base_args["of_type"] = to_dauphin_dagster_type(
            pipeline_snapshot, dagster_type_meta.type_param_keys[0]
        )
        return DauphinListDagsterType(**base_args)
    elif dagster_type_meta.kind == DagsterTypeKind.NULLABLE:
        base_args["of_type"] = to_dauphin_dagster_type(
            pipeline_snapshot, dagster_type_meta.type_param_keys[0]
        )
        return DauphinNullableDagsterType(**base_args)
    else:
        return DauphinRegularDagsterType(**base_args)


class DauphinDagsterType(dauphin.Interface):
    class Meta:
        name = "DagsterType"

    key = dauphin.NonNull(dauphin.String)
    name = dauphin.String()
    display_name = dauphin.NonNull(dauphin.String)
    description = dauphin.String()

    is_nullable = dauphin.NonNull(dauphin.Boolean)
    is_list = dauphin.NonNull(dauphin.Boolean)
    is_builtin = dauphin.NonNull(dauphin.Boolean)
    is_nothing = dauphin.NonNull(dauphin.Boolean)

    input_schema_type = dauphin.Field(DauphinConfigType)
    output_schema_type = dauphin.Field(DauphinConfigType)

    inner_types = dauphin.non_null_list("DagsterType")


class DauphinRegularDagsterType(dauphin.ObjectType):
    class Meta:
        name = "RegularDagsterType"
        interfaces = [DauphinDagsterType]


class DauphinWrappingDagsterType(dauphin.Interface):
    class Meta:
        name = "WrappingDagsterType"

    of_type = dauphin.Field(dauphin.NonNull(DauphinDagsterType))


class DauphinListDagsterType(dauphin.ObjectType):
    class Meta:
        name = "ListDagsterType"
        interfaces = [DauphinDagsterType, DauphinWrappingDagsterType]


class DauphinNullableDagsterType(dauphin.ObjectType):
    class Meta:
        name = "NullableDagsterType"
        interfaces = [DauphinDagsterType, DauphinWrappingDagsterType]
