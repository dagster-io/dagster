from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import graphene
from dagster._config.snap import ConfigTypeSnap
from dagster._core.types.dagster_type import DagsterTypeKind
from typing_extensions import TypeAlias

from dagster_graphql.implementation.events import iterate_metadata_entries
from dagster_graphql.schema.config_types import (
    GrapheneConfigType,
    GrapheneConfigTypeUnion,
    to_config_type,
)
from dagster_graphql.schema.errors import (
    GrapheneDagsterTypeNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from dagster_graphql.schema.metadata import GrapheneMetadataEntry
from dagster_graphql.schema.util import non_null_list

if TYPE_CHECKING:
    from dagster._core.snap.dagster_types import DagsterTypeSnap

GrapheneDagsterTypeUnion: TypeAlias = Union[
    "GrapheneListDagsterType", "GrapheneNullableDagsterType", "GrapheneRegularDagsterType"
]


def config_type_for_schema(
    get_config_type: Callable[[str], ConfigTypeSnap],
    schema_key: Optional[str],
) -> Optional[GrapheneConfigTypeUnion]:
    return to_config_type(get_config_type, schema_key) if schema_key else None


def to_dagster_type(
    get_dagster_type: Callable[[str], "DagsterTypeSnap"],
    get_config_type: Callable[[str], ConfigTypeSnap],
    dagster_type_key: str,
) -> GrapheneDagsterTypeUnion:
    dagster_type_meta = get_dagster_type(dagster_type_key)

    base_args: dict[str, Any] = dict(
        key=dagster_type_meta.key,
        name=dagster_type_meta.name,
        display_name=dagster_type_meta.display_name,
        description=dagster_type_meta.description,
        is_builtin=dagster_type_meta.is_builtin,
        is_nullable=dagster_type_meta.kind == DagsterTypeKind.NULLABLE,
        is_list=dagster_type_meta.kind == DagsterTypeKind.LIST,
        is_nothing=dagster_type_meta.kind == DagsterTypeKind.NOTHING,
        input_schema_type=config_type_for_schema(
            get_config_type,
            dagster_type_meta.loader_schema_key,
        ),
        inner_types=list(
            map(
                lambda key: to_dagster_type(get_dagster_type, get_config_type, key),
                dagster_type_meta.type_param_keys,
            )
        ),
        metadata_entries=list(iterate_metadata_entries(dagster_type_meta.metadata)),
    )

    if dagster_type_meta.kind == DagsterTypeKind.LIST:
        base_args["of_type"] = to_dagster_type(
            get_dagster_type,
            get_config_type,
            dagster_type_meta.type_param_keys[0],
        )
        return GrapheneListDagsterType(**base_args)
    elif dagster_type_meta.kind == DagsterTypeKind.NULLABLE:
        base_args["of_type"] = to_dagster_type(
            get_dagster_type,
            get_config_type,
            dagster_type_meta.type_param_keys[0],
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
    metadata_entries = non_null_list(GrapheneMetadataEntry)

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
