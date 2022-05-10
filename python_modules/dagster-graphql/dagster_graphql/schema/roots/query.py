# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.definitions.events import AssetKey
from dagster.core.execution.backfill import BulkActionStatus
from dagster.core.host_representation import (
    InstigatorSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster.core.scheduler.instigation import InstigatorType

from ...implementation.external import fetch_repositories, fetch_repository, fetch_workspace
from ...implementation.fetch_assets import get_asset, get_asset_node, get_asset_nodes, get_assets
from ...implementation.fetch_backfills import get_backfill, get_backfills
from ...implementation.fetch_instigators import (
    get_instigator_state_or_error,
    get_unloadable_instigator_states_or_error,
)
from ...implementation.fetch_partition_sets import get_partition_set, get_partition_sets_or_error
from ...implementation.fetch_pipelines import (
    get_pipeline_or_error,
    get_pipeline_snapshot_or_error_from_pipeline_selector,
    get_pipeline_snapshot_or_error_from_snapshot_id,
)
from ...implementation.fetch_runs import (
    get_execution_plan,
    get_run_by_id,
    get_run_group,
    get_run_groups,
    get_run_tags,
    validate_pipeline_config,
)
from ...implementation.fetch_schedules import (
    get_schedule_or_error,
    get_scheduler_or_error,
    get_schedules_or_error,
)
from ...implementation.fetch_sensors import get_sensor_or_error, get_sensors_or_error
from ...implementation.fetch_solids import get_graph_or_error
from ...implementation.loader import BatchMaterializationLoader, CrossRepoAssetDependedByLoader
from ...implementation.run_config_schema import resolve_run_config_schema_or_error
from ...implementation.utils import graph_selector_from_graphql, pipeline_selector_from_graphql
from ..asset_graph import GrapheneAssetNode, GrapheneAssetNodeOrError
from ..backfill import (
    GrapheneBulkActionStatus,
    GraphenePartitionBackfillOrError,
    GraphenePartitionBackfillsOrError,
)
from ..external import (
    GrapheneRepositoriesOrError,
    GrapheneRepositoryConnection,
    GrapheneRepositoryOrError,
    GrapheneWorkspaceOrError,
)
from ..inputs import (
    GrapheneAssetKeyInput,
    GrapheneGraphSelector,
    GrapheneInstigationSelector,
    GraphenePipelineSelector,
    GrapheneRepositorySelector,
    GrapheneRunsFilter,
    GrapheneScheduleSelector,
    GrapheneSensorSelector,
)
from ..instance import GrapheneInstance
from ..instigation import (
    GrapheneInstigationStateOrError,
    GrapheneInstigationStatesOrError,
    GrapheneInstigationType,
)
from ..partition_sets import GraphenePartitionSetOrError, GraphenePartitionSetsOrError
from ..permissions import GraphenePermission
from ..pipelines.config_result import GraphenePipelineConfigValidationResult
from ..pipelines.pipeline import GrapheneRunOrError
from ..pipelines.snapshot import GraphenePipelineSnapshotOrError
from ..run_config import GrapheneRunConfigSchemaOrError
from ..runs import (
    GrapheneRunConfigData,
    GrapheneRunGroupOrError,
    GrapheneRunGroupsOrError,
    GrapheneRuns,
    GrapheneRunsOrError,
    parse_run_config_input,
)
from ..schedules import GrapheneScheduleOrError, GrapheneSchedulerOrError, GrapheneSchedulesOrError
from ..sensors import GrapheneSensorOrError, GrapheneSensorsOrError
from ..tags import GraphenePipelineTagAndValues
from ..util import non_null_list
from .assets import GrapheneAssetOrError, GrapheneAssetsOrError
from .execution_plan import GrapheneExecutionPlanOrError
from .pipeline import GrapheneGraphOrError, GraphenePipelineOrError


class GrapheneDagitQuery(graphene.ObjectType):
    class Meta:
        name = "DagitQuery"

    version = graphene.NonNull(graphene.String)

    repositoriesOrError = graphene.Field(
        graphene.NonNull(GrapheneRepositoriesOrError),
        repositorySelector=graphene.Argument(GrapheneRepositorySelector),
    )

    repositoryOrError = graphene.Field(
        graphene.NonNull(GrapheneRepositoryOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
    )

    workspaceOrError = graphene.NonNull(GrapheneWorkspaceOrError)

    pipelineOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineOrError), params=graphene.NonNull(GraphenePipelineSelector)
    )

    pipelineSnapshotOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineSnapshotOrError),
        snapshotId=graphene.String(),
        activePipelineSelector=graphene.Argument(GraphenePipelineSelector),
    )

    graphOrError = graphene.Field(
        graphene.NonNull(GrapheneGraphOrError),
        selector=graphene.Argument(GrapheneGraphSelector),
    )

    scheduler = graphene.Field(graphene.NonNull(GrapheneSchedulerOrError))

    scheduleOrError = graphene.Field(
        graphene.NonNull(GrapheneScheduleOrError),
        schedule_selector=graphene.NonNull(GrapheneScheduleSelector),
    )

    schedulesOrError = graphene.Field(
        graphene.NonNull(GrapheneSchedulesOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
    )

    sensorOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorOrError),
        sensorSelector=graphene.NonNull(GrapheneSensorSelector),
    )
    sensorsOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorsOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
    )

    instigationStateOrError = graphene.Field(
        graphene.NonNull(GrapheneInstigationStateOrError),
        instigationSelector=graphene.NonNull(GrapheneInstigationSelector),
    )

    unloadableInstigationStatesOrError = graphene.Field(
        graphene.NonNull(GrapheneInstigationStatesOrError),
        instigationType=graphene.Argument(GrapheneInstigationType),
    )

    partitionSetsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionSetsOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        pipelineName=graphene.NonNull(graphene.String),
    )
    partitionSetOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionSetOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        partitionSetName=graphene.String(),
    )

    pipelineRunsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    pipelineRunOrError = graphene.Field(
        graphene.NonNull(GrapheneRunOrError), runId=graphene.NonNull(graphene.ID)
    )
    runsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    runOrError = graphene.Field(
        graphene.NonNull(GrapheneRunOrError), runId=graphene.NonNull(graphene.ID)
    )
    pipelineRunTags = non_null_list(GraphenePipelineTagAndValues)

    runGroupOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupOrError), runId=graphene.NonNull(graphene.ID)
    )

    runGroupsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    isPipelineConfigValid = graphene.Field(
        graphene.NonNull(GraphenePipelineConfigValidationResult),
        args={
            "pipeline": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "runConfigData": graphene.Argument(GrapheneRunConfigData),
            "mode": graphene.Argument(graphene.NonNull(graphene.String)),
        },
    )

    executionPlanOrError = graphene.Field(
        graphene.NonNull(GrapheneExecutionPlanOrError),
        args={
            "pipeline": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "runConfigData": graphene.Argument(GrapheneRunConfigData),
            "mode": graphene.Argument(graphene.NonNull(graphene.String)),
        },
    )

    runConfigSchemaOrError = graphene.Field(
        graphene.NonNull(GrapheneRunConfigSchemaOrError),
        args={
            "selector": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "mode": graphene.Argument(graphene.String),
        },
        description="""Fetch an environment schema given an execution selection and a mode.
        See the descripton on RunConfigSchema for more information.""",
    )

    instance = graphene.NonNull(GrapheneInstance)

    assetsOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetsOrError),
        prefix=graphene.List(graphene.NonNull(graphene.String)),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    assetOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetOrError),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
    )

    assetNodes = graphene.Field(
        non_null_list(GrapheneAssetNode),
        pipeline=graphene.Argument(GraphenePipelineSelector),
        assetKeys=graphene.Argument(graphene.List(graphene.NonNull(GrapheneAssetKeyInput))),
        loadMaterializations=graphene.Boolean(default_value=False),
    )

    assetNodeOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetNodeOrError),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
    )

    partitionBackfillOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillOrError),
        backfillId=graphene.Argument(graphene.NonNull(graphene.String)),
    )

    partitionBackfillsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillsOrError),
        status=graphene.Argument(GrapheneBulkActionStatus),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    permissions = graphene.Field(non_null_list(GraphenePermission))

    def resolve_repositoriesOrError(self, graphene_info, **kwargs):
        if kwargs.get("repositorySelector"):
            return GrapheneRepositoryConnection(
                nodes=[
                    fetch_repository(
                        graphene_info,
                        RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
                    )
                ]
            )
        return fetch_repositories(graphene_info)

    def resolve_repositoryOrError(self, graphene_info, **kwargs):
        return fetch_repository(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    def resolve_workspaceOrError(self, graphene_info):
        return fetch_workspace(graphene_info.context)

    def resolve_pipelineSnapshotOrError(self, graphene_info, **kwargs):
        snapshot_id_arg = kwargs.get("snapshotId")
        pipeline_selector_arg = kwargs.get("activePipelineSelector")
        check.invariant(
            not (snapshot_id_arg and pipeline_selector_arg),
            "Must only pass one of snapshotId or activePipelineSelector",
        )
        check.invariant(
            snapshot_id_arg or pipeline_selector_arg,
            "Must set one of snapshotId or activePipelineSelector",
        )

        if pipeline_selector_arg:
            pipeline_selector = pipeline_selector_from_graphql(kwargs["activePipelineSelector"])
            return get_pipeline_snapshot_or_error_from_pipeline_selector(
                graphene_info, pipeline_selector
            )
        else:
            return get_pipeline_snapshot_or_error_from_snapshot_id(graphene_info, snapshot_id_arg)

    def resolve_graphOrError(self, graphene_info, **kwargs):
        graph_selector = graph_selector_from_graphql(kwargs["selector"])
        return get_graph_or_error(graphene_info, graph_selector)

    def resolve_version(self, graphene_info):
        return graphene_info.context.version

    def resolve_scheduler(self, graphene_info):
        return get_scheduler_or_error(graphene_info)

    def resolve_scheduleOrError(self, graphene_info, schedule_selector):
        return get_schedule_or_error(
            graphene_info, ScheduleSelector.from_graphql_input(schedule_selector)
        )

    def resolve_schedulesOrError(self, graphene_info, **kwargs):
        return get_schedules_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    def resolve_sensorOrError(self, graphene_info, sensorSelector):
        return get_sensor_or_error(graphene_info, SensorSelector.from_graphql_input(sensorSelector))

    def resolve_sensorsOrError(self, graphene_info, **kwargs):
        return get_sensors_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    def resolve_instigationStateOrError(self, graphene_info, instigationSelector):
        return get_instigator_state_or_error(
            graphene_info, InstigatorSelector.from_graphql_input(instigationSelector)
        )

    def resolve_unloadableInstigationStatesOrError(self, graphene_info, **kwargs):
        instigation_type = (
            InstigatorType(kwargs["instigationType"]) if "instigationType" in kwargs else None
        )
        return get_unloadable_instigator_states_or_error(graphene_info, instigation_type)

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline_or_error(
            graphene_info,
            pipeline_selector_from_graphql(kwargs["params"]),
        )

    def resolve_pipelineRunsOrError(self, _graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return GrapheneRuns(
            filters=filters,
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )

    def resolve_pipelineRunOrError(self, graphene_info, runId):
        return get_run_by_id(graphene_info, runId)

    def resolve_runsOrError(self, _graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return GrapheneRuns(
            filters=filters,
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )

    def resolve_runOrError(self, graphene_info, runId):
        return get_run_by_id(graphene_info, runId)

    def resolve_runGroupsOrError(self, graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return GrapheneRunGroupsOrError(
            results=get_run_groups(
                graphene_info, filters, kwargs.get("cursor"), kwargs.get("limit")
            )
        )

    def resolve_partitionSetsOrError(self, graphene_info, **kwargs):
        return get_partition_sets_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
            kwargs.get("pipelineName"),
        )

    def resolve_partitionSetOrError(self, graphene_info, **kwargs):
        return get_partition_set(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
            kwargs.get("partitionSetName"),
        )

    def resolve_pipelineRunTags(self, graphene_info):
        return get_run_tags(graphene_info)

    def resolve_runGroupOrError(self, graphene_info, runId):
        return get_run_group(graphene_info, runId)

    def resolve_isPipelineConfigValid(self, graphene_info, pipeline, **kwargs):
        return validate_pipeline_config(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            parse_run_config_input(kwargs.get("runConfigData", {})),
            kwargs.get("mode"),
        )

    def resolve_executionPlanOrError(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            parse_run_config_input(kwargs.get("runConfigData", {})),
            kwargs.get("mode"),
        )

    def resolve_runConfigSchemaOrError(self, graphene_info, **kwargs):
        return resolve_run_config_schema_or_error(
            graphene_info,
            pipeline_selector_from_graphql(kwargs["selector"]),
            kwargs.get("mode"),
        )

    def resolve_instance(self, graphene_info):
        return GrapheneInstance(graphene_info.context.instance)

    def resolve_assetNodes(self, graphene_info, **kwargs):
        asset_keys = set(
            AssetKey.from_graphql_input(asset_key) for asset_key in kwargs.get("assetKeys", [])
        )

        if "pipeline" in kwargs:
            pipeline_name = kwargs.get("pipeline").get("pipelineName")
            repo_sel = RepositorySelector.from_graphql_input(kwargs.get("pipeline"))
            repo_loc = graphene_info.context.get_repository_location(repo_sel.location_name)
            repo = repo_loc.get_repository(repo_sel.repository_name)
            external_asset_nodes = repo.get_external_asset_nodes(pipeline_name)
            results = (
                [
                    GrapheneAssetNode(repo_loc, repo, asset_node)
                    for asset_node in external_asset_nodes
                ]
                if external_asset_nodes
                else []
            )
        else:
            results = get_asset_nodes(graphene_info)

        # Filter down to requested asset keys
        results = [node for node in results if not asset_keys or node.assetKey in asset_keys]

        if not results:
            return []

        materialization_loader = BatchMaterializationLoader(
            instance=graphene_info.context.instance, asset_keys=[node.assetKey for node in results]
        )

        depended_by_loader = CrossRepoAssetDependedByLoader(context=graphene_info.context)
        return [
            GrapheneAssetNode(
                node.repository_location,
                node.external_repository,
                node.external_asset_node,
                materialization_loader=materialization_loader,
                depended_by_loader=depended_by_loader,
            )
            for node in results
        ]

    def resolve_assetNodeOrError(self, graphene_info, **kwargs):
        return get_asset_node(graphene_info, AssetKey.from_graphql_input(kwargs["assetKey"]))

    def resolve_assetsOrError(self, graphene_info, **kwargs):
        return get_assets(
            graphene_info,
            prefix=kwargs.get("prefix"),
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )

    def resolve_assetOrError(self, graphene_info, **kwargs):
        return get_asset(graphene_info, AssetKey.from_graphql_input(kwargs["assetKey"]))

    def resolve_partitionBackfillOrError(self, graphene_info, backfillId):
        return get_backfill(graphene_info, backfillId)

    def resolve_partitionBackfillsOrError(self, graphene_info, **kwargs):
        status = kwargs.get("status")
        return get_backfills(
            graphene_info,
            status=BulkActionStatus.from_graphql_input(status) if status else None,
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )

    def resolve_permissions(self, graphene_info):
        permissions = graphene_info.context.permissions
        return [GraphenePermission(permission, value) for permission, value in permissions.items()]
