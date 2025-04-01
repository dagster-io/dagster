import graphene

from dagster_graphql.schema.roots.mutation import GrapheneMutation
from dagster_graphql.schema.roots.query import GrapheneQuery
from dagster_graphql.schema.roots.subscription import GrapheneSubscription


def types():
    from dagster_graphql.schema.backfill import (
        GrapheneLaunchBackfillResult,
        GrapheneLaunchBackfillSuccess,
    )
    from dagster_graphql.schema.config_type_or_error import GrapheneConfigTypeOrError
    from dagster_graphql.schema.config_types import types as config_types
    from dagster_graphql.schema.dagster_types import types as dagster_types_types
    from dagster_graphql.schema.entity_key import GrapheneAssetKey
    from dagster_graphql.schema.errors import types as errors_types
    from dagster_graphql.schema.execution import types as execution_types
    from dagster_graphql.schema.external import types as external_types
    from dagster_graphql.schema.inputs import types as inputs_types
    from dagster_graphql.schema.instance import (
        GrapheneDaemonHealth,
        GrapheneDaemonStatus,
        GrapheneInstance,
        GrapheneRunLauncher,
    )
    from dagster_graphql.schema.instigation import types as instigation_types
    from dagster_graphql.schema.logs import types as log_types
    from dagster_graphql.schema.metadata import types as metadata_types
    from dagster_graphql.schema.partition_sets import types as partition_sets_types
    from dagster_graphql.schema.pipelines import types as pipelines_types
    from dagster_graphql.schema.repository_origin import (
        GrapheneRepositoryMetadata,
        GrapheneRepositoryOrigin,
    )
    from dagster_graphql.schema.roots import types as roots_types
    from dagster_graphql.schema.run_config import (
        GrapheneRunConfigSchema,
        GrapheneRunConfigSchemaOrError,
    )
    from dagster_graphql.schema.runs import types as runs_types
    from dagster_graphql.schema.schedules import types as schedules_types
    from dagster_graphql.schema.sensors import types as sensors_types
    from dagster_graphql.schema.solids import types as solids_types
    from dagster_graphql.schema.table import types as table_types
    from dagster_graphql.schema.tags import GraphenePipelineTag, GraphenePipelineTagAndValues
    from dagster_graphql.schema.used_solid import GrapheneNodeInvocationSite, GrapheneUsedSolid

    return (
        log_types()
        + pipelines_types()
        + roots_types()
        + schedules_types()
        + [GrapheneAssetKey]
        + [GrapheneLaunchBackfillResult, GrapheneLaunchBackfillSuccess]
        + [GrapheneConfigTypeOrError]
        + config_types
        + dagster_types_types
        + errors_types
        + execution_types
        + external_types
        + inputs_types
        + [GrapheneDaemonHealth, GrapheneDaemonStatus, GrapheneInstance, GrapheneRunLauncher]
        + instigation_types
        + metadata_types()
        + partition_sets_types
        + [GrapheneRepositoryOrigin, GrapheneRepositoryMetadata]
        + [GrapheneRunConfigSchema, GrapheneRunConfigSchemaOrError]
        + runs_types
        + sensors_types
        + solids_types
        + table_types
        + [GraphenePipelineTag, GraphenePipelineTagAndValues]
        + [GrapheneNodeInvocationSite, GrapheneUsedSolid]
    )


def create_schema() -> graphene.Schema:
    return graphene.Schema(
        query=GrapheneQuery,
        mutation=GrapheneMutation,
        subscription=GrapheneSubscription,
        types=types(),
    )
