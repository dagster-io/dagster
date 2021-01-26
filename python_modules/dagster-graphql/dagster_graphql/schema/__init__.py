import graphene

from .roots.mutation import GrapheneMutation
from .roots.query import GrapheneQuery
from .roots.subscription import GrapheneSubscription


def types():
    from .logs import types as log_types
    from .pipelines import types as pipelines_types
    from .roots import types as roots_types
    from .schedules import types as schedules_types
    from .asset_key import GrapheneAssetKey
    from .backfill import GraphenePartitionBackfillResult, GraphenePartitionBackfillSuccess
    from .config_type_or_error import GrapheneConfigTypeOrError
    from .config_types import types as config_types
    from .dagster_types import types as dagster_types_types
    from .errors import types as errors_types
    from .execution import types as execution_types
    from .external import types as external_types
    from .inputs import types as inputs_types
    from .instance import (
        GrapheneDaemonHealth,
        GrapheneDaemonStatus,
        GrapheneInstance,
        GrapheneRunLauncher,
    )
    from .jobs import types as jobs_types
    from .metadata import GrapheneMetadataItemDefinition
    from .paging import GrapheneCursor
    from .partition_sets import types as partition_sets_types
    from .repository_origin import GrapheneRepositoryOrigin, GrapheneRepositoryMetadata
    from .run_config import GrapheneRunConfigSchema, GrapheneRunConfigSchemaOrError
    from .runs import types as runs_types
    from .sensors import types as sensors_types
    from .solids import types as solids_types
    from .tags import GraphenePipelineTag, GraphenePipelineTagAndValues
    from .used_solid import GrapheneSolidInvocationSite, GrapheneUsedSolid

    return (
        log_types()
        + pipelines_types()
        + roots_types()
        + schedules_types()
        + [GrapheneAssetKey]
        + [GraphenePartitionBackfillResult, GraphenePartitionBackfillSuccess]
        + [GrapheneConfigTypeOrError]
        + config_types
        + dagster_types_types
        + errors_types
        + execution_types
        + external_types
        + inputs_types
        + [GrapheneDaemonHealth, GrapheneDaemonStatus, GrapheneInstance, GrapheneRunLauncher]
        + jobs_types
        + [GrapheneMetadataItemDefinition]
        + [GrapheneCursor]
        + partition_sets_types
        + [GrapheneRepositoryOrigin, GrapheneRepositoryMetadata]
        + [GrapheneRunConfigSchema, GrapheneRunConfigSchemaOrError]
        + runs_types
        + sensors_types
        + solids_types
        + [GraphenePipelineTag, GraphenePipelineTagAndValues]
        + [GrapheneSolidInvocationSite, GrapheneUsedSolid]
    )


def create_schema():
    return graphene.Schema(
        query=GrapheneQuery,
        mutation=GrapheneMutation,
        subscription=GrapheneSubscription,
        types=types(),
    )
