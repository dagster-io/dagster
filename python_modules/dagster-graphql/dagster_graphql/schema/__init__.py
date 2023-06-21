import graphene

from .roots.mutation import GrapheneDagitMutation
from .roots.query import GrapheneDagitQuery
from .roots.subscription import GrapheneDagitSubscription


def types():
    from .asset_key import GrapheneAssetKey
    from .backfill import GrapheneLaunchBackfillResult, GrapheneLaunchBackfillSuccess
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
    from .instigation import types as instigation_types
    from .logs import types as log_types
    from .metadata import types as metadata_types
    from .paging import GrapheneCursor
    from .partition_sets import types as partition_sets_types
    from .pipelines import types as pipelines_types
    from .repository_origin import GrapheneRepositoryMetadata, GrapheneRepositoryOrigin
    from .roots import types as roots_types
    from .run_config import GrapheneRunConfigSchema, GrapheneRunConfigSchemaOrError
    from .runs import types as runs_types
    from .schedules import types as schedules_types
    from .sensors import types as sensors_types
    from .solids import types as solids_types
    from .table import types as table_types
    from .tags import GraphenePipelineTag, GraphenePipelineTagAndValues
    from .used_solid import GrapheneNodeInvocationSite, GrapheneUsedSolid

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
        + [GrapheneCursor]
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
        query=GrapheneDagitQuery,
        mutation=GrapheneDagitMutation,
        subscription=GrapheneDagitSubscription,
        types=types(),
    )
