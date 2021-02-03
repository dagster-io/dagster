import graphene
from dagster import check
from dagster.core.snap import PipelineSnapshot
from dagster.core.types.dagster_type import DagsterTypeKind

from .config_types import GrapheneConfigType, to_config_type
from .errors import (
    GrapheneDagsterTypeNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from .util import non_null_list


def config_type_for_schema(pipeline_snapshot, schema_key):
    return (
        to_config_type(pipeline_snapshot.config_schema_snapshot, schema_key) if schema_key else None
    )


def to_dagster_type(pipeline_snapshot, dagster_type_key):
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
            pipeline_snapshot,
            dagster_type_meta.loader_schema_key,
        ),
        output_schema_type=config_type_for_schema(
            pipeline_snapshot,
            dagster_type_meta.materializer_schema_key,
        ),
        inner_types=list(
            map(
                lambda key: to_dagster_type(pipeline_snapshot, key),
                dagster_type_meta.type_param_keys,
            )
        ),
    )

    if dagster_type_meta.kind == DagsterTypeKind.LIST:
        base_args["of_type"] = to_dagster_type(
            pipeline_snapshot, dagster_type_meta.type_param_keys[0]
        )
        return GrapheneListDagsterType(**base_args)
    elif dagster_type_meta.kind == DagsterTypeKind.NULLABLE:
        base_args["of_type"] = to_dagster_type(
            pipeline_snapshot, dagster_type_meta.type_param_keys[0]
        )
        return GrapheneNullableDagsterType(**base_args)
    else:
        return GrapheneRegularDagsterType(**base_args)


class GrapheneDagsterType(graphene.Interface):
    key = graphene.NonNull(graphene.String)
    name = graphene.String()
    display_name = graphene.NonNull(graphene.String)
    description = graphene.String()

    is_nullable = graphene.NonNull(graphene.Boolean)
    is_list = graphene.NonNull(graphene.Boolean)
    is_builtin = graphene.NonNull(graphene.Boolean)
    is_nothing = graphene.NonNull(graphene.Boolean)

    input_schema_type = graphene.Field(GrapheneConfigType)
    output_schema_type = graphene.Field(GrapheneConfigType)

    inner_types = non_null_list(lambda: GrapheneDagsterType)

    class Meta:
        name = "DagsterType"


class GrapheneRegularDagsterType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneDagsterType,)
        name = "RegularDagsterType"


class GrapheneWrappingDagsterType(graphene.Interface):
    of_type = graphene.Field(graphene.NonNull(GrapheneDagsterType))

    class Meta:
        name = "WrappingDagsterType"


class GrapheneListDagsterType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneDagsterType, GrapheneWrappingDagsterType)
        name = "ListDagsterType"


class GrapheneNullableDagsterType(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneDagsterType, GrapheneWrappingDagsterType)
        name = "NullableDagsterType"


class GrapheneDagsterTypeOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneRegularDagsterType,
            GraphenePipelineNotFoundError,
            GrapheneDagsterTypeNotFoundError,
            GraphenePythonError,
        )
        name = "DagsterTypeOrError"


types = [
    GrapheneDagsterType,
    GrapheneDagsterTypeOrError,
    GrapheneListDagsterType,
    GrapheneNullableDagsterType,
    GrapheneRegularDagsterType,
    GrapheneWrappingDagsterType,
]
