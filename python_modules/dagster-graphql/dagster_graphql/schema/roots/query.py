from typing import Any, Dict, Sequence

import dagster._check as check
import graphene
from dagster._core.definitions.events import AssetKey
from dagster._core.execution.backfill import BulkActionStatus
from dagster._core.host_representation import (
    InstigatorSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.nux import get_has_seen_nux
from dagster._core.scheduler.instigation import InstigatorType

from dagster_graphql.implementation.fetch_logs import get_captured_log_metadata
from dagster_graphql.implementation.fetch_runs import get_assets_latest_info

from ...implementation.external import (
    fetch_location_statuses,
    fetch_repositories,
    fetch_repository,
    fetch_workspace,
)
from ...implementation.fetch_assets import (
    get_asset,
    get_asset_node,
    get_asset_node_definition_collisions,
    get_asset_nodes,
    get_assets,
    unique_repos,
)
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
    get_logs_for_run,
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
from ...implementation.loader import (
    BatchMaterializationLoader,
    CrossRepoAssetDependedByLoader,
    ProjectedLogicalVersionLoader,
)
from ...implementation.run_config_schema import resolve_run_config_schema_or_error
from ...implementation.utils import graph_selector_from_graphql, pipeline_selector_from_graphql
from ..asset_graph import (
    GrapheneAssetLatestInfo,
    GrapheneAssetNode,
    GrapheneAssetNodeDefinitionCollision,
    GrapheneAssetNodeOrError,
)
from ..backfill import (
    GrapheneBulkActionStatus,
    GraphenePartitionBackfillOrError,
    GraphenePartitionBackfillsOrError,
)
from ..external import (
    GrapheneRepositoriesOrError,
    GrapheneRepositoryConnection,
    GrapheneRepositoryOrError,
    GrapheneWorkspaceLocationStatusEntriesOrError,
    GrapheneWorkspaceOrError,
)
from ..inputs import (
    GrapheneAssetGroupSelector,
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
from ..logs.compute_logs import (
    GrapheneCapturedLogs,
    GrapheneCapturedLogsMetadata,
    from_captured_log_data,
)
from ..partition_sets import GraphenePartitionSetOrError, GraphenePartitionSetsOrError
from ..permissions import GraphenePermission
from ..pipelines.config_result import GraphenePipelineConfigValidationResult
from ..pipelines.pipeline import GrapheneEventConnectionOrError, GrapheneRunOrError
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
from ..util import HasContext, non_null_list
from .assets import GrapheneAssetOrError, GrapheneAssetsOrError
from .execution_plan import GrapheneExecutionPlanOrError
from .pipeline import GrapheneGraphOrError, GraphenePipelineOrError


class GrapheneDagitQuery(graphene.ObjectType):
    """The root for all queries to retrieve data from the Dagster instance."""

    class Meta:
        name = "DagitQuery"

    version = graphene.Field(
        graphene.NonNull(graphene.String),
        description="Retrieve the version of Dagster running in the Dagster deployment.",
    )

    repositoriesOrError = graphene.Field(
        graphene.NonNull(GrapheneRepositoriesOrError),
        repositorySelector=graphene.Argument(GrapheneRepositorySelector),
        description="Retrieve all the repositories.",
    )

    repositoryOrError = graphene.Field(
        graphene.NonNull(GrapheneRepositoryOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        description="Retrieve a repository by its location name and repository name.",
    )

    workspaceOrError = graphene.Field(
        graphene.NonNull(GrapheneWorkspaceOrError),
        description="Retrieve the workspace and its locations.",
    )

    locationStatusesOrError = graphene.Field(
        graphene.NonNull(GrapheneWorkspaceLocationStatusEntriesOrError),
        description="Retrieve location status for workspace locations",
    )

    pipelineOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineOrError),
        params=graphene.NonNull(GraphenePipelineSelector),
        description="Retrieve a job by its location name, repository name, and job name.",
    )

    pipelineSnapshotOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineSnapshotOrError),
        snapshotId=graphene.String(),
        activePipelineSelector=graphene.Argument(GraphenePipelineSelector),
        description=(
            "Retrieve a job snapshot by its id or location name, repository name, and job name."
        ),
    )

    graphOrError = graphene.Field(
        graphene.NonNull(GrapheneGraphOrError),
        selector=graphene.Argument(GrapheneGraphSelector),
        description="Retrieve a graph by its location name, repository name, and graph name.",
    )

    scheduler = graphene.Field(
        graphene.NonNull(GrapheneSchedulerOrError),
        description="Retrieve the name of the scheduler running in the Dagster deployment.",
    )

    scheduleOrError = graphene.Field(
        graphene.NonNull(GrapheneScheduleOrError),
        schedule_selector=graphene.NonNull(GrapheneScheduleSelector),
        description="Retrieve a schedule by its location name, repository name, and schedule name.",
    )

    schedulesOrError = graphene.Field(
        graphene.NonNull(GrapheneSchedulesOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        description="Retrieve all the schedules.",
    )

    sensorOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorOrError),
        sensorSelector=graphene.NonNull(GrapheneSensorSelector),
        description="Retrieve a sensor by its location name, repository name, and sensor name.",
    )
    sensorsOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorsOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        description="Retrieve all the sensors.",
    )

    instigationStateOrError = graphene.Field(
        graphene.NonNull(GrapheneInstigationStateOrError),
        instigationSelector=graphene.NonNull(GrapheneInstigationSelector),
        description=(
            "Retrieve the state for a schedule or sensor by its location name, repository name, and"
            " schedule/sensor name."
        ),
    )

    unloadableInstigationStatesOrError = graphene.Field(
        graphene.NonNull(GrapheneInstigationStatesOrError),
        instigationType=graphene.Argument(GrapheneInstigationType),
        description=(
            "Retrieve the running schedules and sensors that are missing from the workspace."
        ),
    )

    partitionSetsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionSetsOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        pipelineName=graphene.NonNull(graphene.String),
        description=(
            "Retrieve the partition sets for a job by its location name, repository name, and job"
            " name."
        ),
    )
    partitionSetOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionSetOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        partitionSetName=graphene.String(),
        description=(
            "Retrieve a partition set by its location name, repository name, and partition set"
            " name."
        ),
    )

    pipelineRunsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve runs after applying a filter, cursor, and limit.",
    )
    pipelineRunOrError = graphene.Field(
        graphene.NonNull(GrapheneRunOrError),
        runId=graphene.NonNull(graphene.ID),
        description="Retrieve a run by its run id.",
    )
    runsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve runs after applying a filter, cursor, and limit.",
    )
    runOrError = graphene.Field(
        graphene.NonNull(GrapheneRunOrError),
        runId=graphene.NonNull(graphene.ID),
        description="Retrieve a run by its run id.",
    )
    pipelineRunTags = graphene.Field(
        non_null_list(GraphenePipelineTagAndValues),
        description="Retrieve all the distinct key-value tags from all runs.",
    )

    runGroupOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupOrError),
        runId=graphene.NonNull(graphene.ID),
        description="Retrieve a group of runs with the matching root run id.",
    )

    runGroupsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve groups of runs after applying a filter, cursor, and limit.",
    )

    isPipelineConfigValid = graphene.Field(
        graphene.NonNull(GraphenePipelineConfigValidationResult),
        args={
            "pipeline": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "runConfigData": graphene.Argument(GrapheneRunConfigData),
            "mode": graphene.Argument(graphene.NonNull(graphene.String)),
        },
        description="Retrieve whether the run configuration is valid or invalid.",
    )

    executionPlanOrError = graphene.Field(
        graphene.NonNull(GrapheneExecutionPlanOrError),
        args={
            "pipeline": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "runConfigData": graphene.Argument(GrapheneRunConfigData),
            "mode": graphene.Argument(graphene.NonNull(graphene.String)),
        },
        description="Retrieve the execution plan for a job and its run configuration.",
    )

    runConfigSchemaOrError = graphene.Field(
        graphene.NonNull(GrapheneRunConfigSchemaOrError),
        args={
            "selector": graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
            "mode": graphene.Argument(graphene.String),
        },
        description="Retrieve the run configuration schema for a job.",
    )

    instance = graphene.Field(
        graphene.NonNull(GrapheneInstance),
        description="Retrieve the instance configuration for the Dagster deployment.",
    )

    assetsOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetsOrError),
        prefix=graphene.List(graphene.NonNull(graphene.String)),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve assets after applying a prefix filter, cursor, and limit.",
    )

    assetOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetOrError),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        description="Retrieve an asset by asset key.",
    )

    assetNodes = graphene.Field(
        non_null_list(GrapheneAssetNode),
        group=graphene.Argument(GrapheneAssetGroupSelector),
        pipeline=graphene.Argument(GraphenePipelineSelector),
        assetKeys=graphene.Argument(graphene.List(graphene.NonNull(GrapheneAssetKeyInput))),
        loadMaterializations=graphene.Boolean(default_value=False),
        description=(
            "Retrieve asset nodes after applying a filter on asset group, job, and asset keys."
        ),
    )

    assetNodeOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetNodeOrError),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        description="Retrieve an asset node by asset key.",
    )

    assetNodeDefinitionCollisions = graphene.Field(
        non_null_list(GrapheneAssetNodeDefinitionCollision),
        assetKeys=graphene.Argument(graphene.List(graphene.NonNull(GrapheneAssetKeyInput))),
        description=(
            "Retrieve a list of asset keys where two or more repos provide an asset definition."
            " Note: Assets should "
        )
        + "not be defined in more than one repository - this query is used to present warnings and"
        " errors in Dagit.",
    )

    partitionBackfillOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillOrError),
        backfillId=graphene.Argument(graphene.NonNull(graphene.String)),
        description="Retrieve a backfill by backfill id.",
    )

    partitionBackfillsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillsOrError),
        status=graphene.Argument(GrapheneBulkActionStatus),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve backfills after applying a status filter, cursor, and limit.",
    )

    permissions = graphene.Field(
        non_null_list(GraphenePermission),
        description="Retrieve the set of permissions for the Dagster deployment.",
    )

    assetsLatestInfo = graphene.Field(
        non_null_list(GrapheneAssetLatestInfo),
        assetKeys=graphene.Argument(non_null_list(GrapheneAssetKeyInput)),
        description="Retrieve the latest materializations for a set of assets by asset keys.",
    )

    logsForRun = graphene.Field(
        graphene.NonNull(GrapheneEventConnectionOrError),
        runId=graphene.NonNull(graphene.ID),
        afterCursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve event logs after applying a run id filter, cursor, and limit.",
    )

    capturedLogsMetadata = graphene.Field(
        graphene.NonNull(GrapheneCapturedLogsMetadata),
        logKey=graphene.Argument(non_null_list(graphene.String)),
        description="Retrieve the captured log metadata for a given log key.",
    )
    capturedLogs = graphene.Field(
        graphene.NonNull(GrapheneCapturedLogs),
        logKey=graphene.Argument(non_null_list(graphene.String)),
        cursor=graphene.Argument(graphene.String),
        limit=graphene.Argument(graphene.Int),
        description="Captured logs are the stdout/stderr logs for a given log key",
    )

    shouldShowNux = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        description="Whether or not the NUX should be shown to the user",
    )

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

    def resolve_locationStatusesOrError(self, graphene_info):
        return fetch_location_statuses(graphene_info.context)

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
            parse_run_config_input(kwargs.get("runConfigData", {}), raise_on_error=False),
            kwargs.get("mode"),
        )

    def resolve_executionPlanOrError(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            parse_run_config_input(kwargs.get("runConfigData", {}), raise_on_error=True),
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

        repo = None
        if "group" in kwargs:
            group_name = kwargs.get("group").get("groupName")
            repo_sel = RepositorySelector.from_graphql_input(kwargs.get("group"))
            repo_loc = graphene_info.context.get_repository_location(repo_sel.location_name)
            repo = repo_loc.get_repository(repo_sel.repository_name)
            external_asset_nodes = repo.get_external_asset_nodes()
            results = (
                [
                    GrapheneAssetNode(repo_loc, repo, asset_node)
                    for asset_node in external_asset_nodes
                    if asset_node.group_name == group_name
                ]
                if external_asset_nodes
                else []
            )
        elif "pipeline" in kwargs:
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

        if repo is not None:
            repos = [repo]
        else:
            repos = unique_repos(result.external_repository for result in results)

        projected_logical_version_loader = ProjectedLogicalVersionLoader(
            instance=graphene_info.context.instance,
            key_to_node_map={node.assetKey: node.external_asset_node for node in results},
            repositories=repos,
        )

        return [
            GrapheneAssetNode(
                node.repository_location,
                node.external_repository,
                node.external_asset_node,
                materialization_loader=materialization_loader,
                depended_by_loader=depended_by_loader,
                projected_logical_version_loader=projected_logical_version_loader,
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

    def resolve_assetNodeDefinitionCollisions(self, graphene_info, **kwargs):
        asset_keys = set(
            AssetKey.from_graphql_input(asset_key) for asset_key in kwargs.get("assetKeys", [])
        )
        return get_asset_node_definition_collisions(graphene_info, asset_keys)

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

    def resolve_assetsLatestInfo(self, graphene_info: HasContext, **kwargs: Any):
        asset_keys = set(
            AssetKey.from_graphql_input(asset_key)
            for asset_key in check.not_none(kwargs.get("assetKeys"))  # type: ignore
        )

        results = get_asset_nodes(graphene_info)

        # Filter down to requested asset keys
        # Build mapping of asset key to the step keys required to generate the asset
        step_keys_by_asset: Dict[AssetKey, Sequence[str]] = {  # type: ignore
            node.external_asset_node.asset_key: node.external_asset_node.op_names
            for node in results
            if node.assetKey in asset_keys
        }

        return get_assets_latest_info(graphene_info, step_keys_by_asset)

    def resolve_logsForRun(self, graphene_info, runId, afterCursor=None, limit=None):
        return get_logs_for_run(graphene_info, runId, afterCursor, limit)

    def resolve_capturedLogsMetadata(self, graphene_info, logKey):
        return get_captured_log_metadata(graphene_info, logKey)

    def resolve_capturedLogs(self, graphene_info, logKey, cursor=None, limit=None):
        log_data = graphene_info.context.instance.compute_log_manager.get_log_data(
            logKey, cursor=cursor, max_bytes=limit
        )
        return from_captured_log_data(log_data)

    def resolve_shouldShowNux(self, graphene_info):
        return graphene_info.context.instance.nux_enabled and not get_has_seen_nux()
