from typing import Any, Dict, List, Mapping, Optional, Sequence, cast

import dagster._check as check
import graphene
from dagster import AssetCheckKey
from dagster._core.definitions.asset_graph_differ import AssetGraphDiffer
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partition import CachingDynamicPartitionsLoader
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.definitions.selector import (
    InstigatorSelector,
    RepositorySelector,
    ResourceSelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster._core.execution.backfill import BulkActionStatus
from dagster._core.nux import get_has_seen_nux
from dagster._core.scheduler.instigation import (
    InstigatorStatus,
    InstigatorType,
)
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.asset_checks_loader import AssetChecksLoader
from dagster_graphql.implementation.execution.backfill import get_asset_backfill_preview
from dagster_graphql.implementation.fetch_asset_condition_evaluations import (
    fetch_asset_condition_evaluation_record_for_partition,
    fetch_asset_condition_evaluation_records_for_asset_key,
    fetch_asset_condition_evaluation_records_for_evaluation_id,
)
from dagster_graphql.implementation.fetch_auto_materialize_asset_evaluations import (
    fetch_auto_materialize_asset_evaluations,
    fetch_auto_materialize_asset_evaluations_for_evaluation_id,
)
from dagster_graphql.implementation.fetch_env_vars import get_utilized_env_vars_or_error
from dagster_graphql.implementation.fetch_logs import get_captured_log_metadata
from dagster_graphql.implementation.fetch_runs import get_assets_latest_info
from dagster_graphql.schema.asset_condition_evaluations import (
    GrapheneAssetConditionEvaluation,
    GrapheneAssetConditionEvaluationRecordsOrError,
)
from dagster_graphql.schema.auto_materialize_asset_evaluations import (
    GrapheneAutoMaterializeAssetEvaluationRecordsOrError,
)
from dagster_graphql.schema.env_vars import GrapheneEnvVarWithConsumersListOrError

from ...implementation.external import (
    fetch_location_statuses,
    fetch_repositories,
    fetch_repository,
    fetch_workspace,
)
from ...implementation.fetch_asset_checks import fetch_asset_check_executions
from ...implementation.fetch_assets import (
    get_additional_required_keys,
    get_asset,
    get_asset_node,
    get_asset_node_definition_collisions,
    get_asset_nodes,
    get_assets,
)
from ...implementation.fetch_backfills import get_backfill, get_backfills
from ...implementation.fetch_instigators import (
    get_instigator_state_or_error,
)
from ...implementation.fetch_partition_sets import get_partition_set, get_partition_sets_or_error
from ...implementation.fetch_pipelines import (
    get_job_or_error,
    get_job_snapshot_or_error_from_job_selector,
    get_job_snapshot_or_error_from_snapshot_id,
)
from ...implementation.fetch_resources import (
    get_resource_or_error,
    get_top_level_resources_or_error,
)
from ...implementation.fetch_runs import (
    get_execution_plan,
    get_logs_for_run,
    get_run_by_id,
    get_run_group,
    get_run_tag_keys,
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
from ...implementation.fetch_ticks import get_instigation_ticks
from ...implementation.loader import (
    BatchMaterializationLoader,
    CrossRepoAssetDependedByLoader,
    StaleStatusLoader,
)
from ...implementation.run_config_schema import resolve_run_config_schema_or_error
from ...implementation.utils import (
    capture_error,
    graph_selector_from_graphql,
    pipeline_selector_from_graphql,
)
from ..asset_checks import GrapheneAssetCheckExecution
from ..asset_graph import (
    GrapheneAssetKey,
    GrapheneAssetLatestInfo,
    GrapheneAssetNode,
    GrapheneAssetNodeDefinitionCollision,
    GrapheneAssetNodeOrError,
)
from ..backfill import (
    GrapheneAssetPartitions,
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
    GrapheneAssetBackfillPreviewParams,
    GrapheneAssetGroupSelector,
    GrapheneAssetKeyInput,
    GrapheneGraphSelector,
    GrapheneInstigationSelector,
    GraphenePipelineSelector,
    GrapheneRepositorySelector,
    GrapheneResourceSelector,
    GrapheneRunsFilter,
    GrapheneScheduleSelector,
    GrapheneSensorSelector,
)
from ..instance import GrapheneInstance
from ..instigation import (
    GrapheneInstigationStateOrError,
    GrapheneInstigationStatus,
    GrapheneInstigationTick,
    GrapheneInstigationTickStatus,
)
from ..logs.compute_logs import (
    GrapheneCapturedLogs,
    GrapheneCapturedLogsMetadata,
    from_captured_log_data,
)
from ..partition_sets import (
    GraphenePartitionSetOrError,
    GraphenePartitionSetsOrError,
)
from ..permissions import GraphenePermission
from ..pipelines.config_result import GraphenePipelineConfigValidationResult
from ..pipelines.pipeline import GrapheneEventConnectionOrError, GrapheneRunOrError
from ..pipelines.snapshot import GraphenePipelineSnapshotOrError
from ..resources import GrapheneResourceDetailsListOrError, GrapheneResourceDetailsOrError
from ..run_config import GrapheneRunConfigSchemaOrError
from ..runs import (
    GrapheneRunConfigData,
    GrapheneRunGroupOrError,
    GrapheneRunIds,
    GrapheneRunIdsOrError,
    GrapheneRuns,
    GrapheneRunsOrError,
    GrapheneRunTagKeysOrError,
    GrapheneRunTagsOrError,
    parse_run_config_input,
)
from ..schedules import GrapheneScheduleOrError, GrapheneSchedulerOrError, GrapheneSchedulesOrError
from ..sensors import GrapheneSensorOrError, GrapheneSensorsOrError
from ..test import GrapheneTestFields
from ..util import ResolveInfo, get_compute_log_manager, non_null_list
from .assets import GrapheneAssetOrError, GrapheneAssetsOrError
from .execution_plan import GrapheneExecutionPlanOrError
from .pipeline import GrapheneGraphOrError, GraphenePipelineOrError


class GrapheneQuery(graphene.ObjectType):
    """The root for all queries to retrieve data from the Dagster instance."""

    class Meta:
        name = "Query"

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
        scheduleStatus=graphene.Argument(GrapheneInstigationStatus),
        description="Retrieve all the schedules.",
    )

    topLevelResourceDetailsOrError = graphene.Field(
        graphene.NonNull(GrapheneResourceDetailsOrError),
        resourceSelector=graphene.NonNull(GrapheneResourceSelector),
        description=(
            "Retrieve a top level resource by its location name, repository name, and resource"
            " name."
        ),
    )

    allTopLevelResourceDetailsOrError = graphene.Field(
        graphene.NonNull(GrapheneResourceDetailsListOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        description="Retrieve all the top level resources.",
    )

    utilizedEnvVarsOrError = graphene.Field(
        graphene.NonNull(GrapheneEnvVarWithConsumersListOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        description="Retrieve all the utilized environment variables for the given repo.",
    )

    sensorOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorOrError),
        sensorSelector=graphene.NonNull(GrapheneSensorSelector),
        description="Retrieve a sensor by its location name, repository name, and sensor name.",
    )
    sensorsOrError = graphene.Field(
        graphene.NonNull(GrapheneSensorsOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
        sensorStatus=graphene.Argument(GrapheneInstigationStatus),
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
    runTagKeysOrError = graphene.Field(
        GrapheneRunTagKeysOrError, description="Retrieve the distinct tag keys from all runs."
    )
    runTagsOrError = graphene.Field(
        GrapheneRunTagsOrError,
        tagKeys=graphene.Argument(graphene.List(graphene.NonNull(graphene.String))),
        valuePrefix=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve all the distinct key-value tags from all runs.",
    )
    runIdsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunIdsOrError),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
        description="Retrieve run IDs after applying a filter, cursor, and limit.",
    )

    runGroupOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupOrError),
        runId=graphene.NonNull(graphene.ID),
        description="Retrieve a group of runs with the matching root run id.",
    )

    isPipelineConfigValid = graphene.Field(
        graphene.NonNull(GraphenePipelineConfigValidationResult),
        pipeline=graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
        mode=graphene.Argument(graphene.NonNull(graphene.String)),
        runConfigData=graphene.Argument(GrapheneRunConfigData),
        description="Retrieve whether the run configuration is valid or invalid.",
    )

    executionPlanOrError = graphene.Field(
        graphene.NonNull(GrapheneExecutionPlanOrError),
        pipeline=graphene.Argument(graphene.NonNull(GraphenePipelineSelector)),
        mode=graphene.Argument(graphene.NonNull(graphene.String)),
        runConfigData=graphene.Argument(GrapheneRunConfigData),
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

    assetNodeAdditionalRequiredKeys = graphene.Field(
        non_null_list(GrapheneAssetKey),
        assetKeys=graphene.Argument(non_null_list(GrapheneAssetKeyInput)),
        description="Retrieve a list of additional asset keys that must be materialized with the provided selection (due to @multi_assets with can_subset=False constraints.)",
    )

    assetNodeDefinitionCollisions = graphene.Field(
        non_null_list(GrapheneAssetNodeDefinitionCollision),
        assetKeys=graphene.Argument(non_null_list(GrapheneAssetKeyInput)),
        description=(
            "Retrieve a list of asset keys where two or more repos provide an asset definition."
            " Note: Assets should "
        )
        + "not be defined in more than one repository - this query is used to present warnings and"
        " errors in the Dagster UI.",
    )

    partitionBackfillOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillOrError),
        backfillId=graphene.Argument(graphene.NonNull(graphene.String)),
        description="Retrieve a backfill by backfill id.",
    )

    assetBackfillPreview = graphene.Field(
        non_null_list(GrapheneAssetPartitions),
        params=graphene.Argument(graphene.NonNull(GrapheneAssetBackfillPreviewParams)),
        description="Fetch the partitions that would be targeted by a backfill, given the root partitions targeted.",
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

    canBulkTerminate = graphene.Field(
        graphene.NonNull(graphene.Boolean),
        description="Returns whether the user has permission to terminate runs in the deployment",
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

    test = graphene.Field(
        GrapheneTestFields,
        description="Provides fields for testing behavior",
    )

    autoMaterializeAssetEvaluationsOrError = graphene.Field(
        GrapheneAutoMaterializeAssetEvaluationRecordsOrError,
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        limit=graphene.Argument(graphene.NonNull(graphene.Int)),
        cursor=graphene.Argument(graphene.String),
        description="Retrieve the auto materialization evaluation records for an asset.",
    )

    autoMaterializeEvaluationsForEvaluationId = graphene.Field(
        GrapheneAutoMaterializeAssetEvaluationRecordsOrError,
        evaluationId=graphene.Argument(graphene.NonNull(graphene.Int)),
        description=(
            "Retrieve the auto materialization evaluation records for a given evaluation ID."
        ),
    )

    assetConditionEvaluationForPartition = graphene.Field(
        GrapheneAssetConditionEvaluation,
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        evaluationId=graphene.Argument(graphene.NonNull(graphene.Int)),
        partition=graphene.Argument(graphene.NonNull(graphene.String)),
        description="Retrieve the condition evaluation for an asset and partition.",
    )

    assetConditionEvaluationRecordsOrError = graphene.Field(
        GrapheneAssetConditionEvaluationRecordsOrError,
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        limit=graphene.Argument(graphene.NonNull(graphene.Int)),
        cursor=graphene.Argument(graphene.String),
        description="Retrieve the condition evaluation records for an asset.",
    )

    assetConditionEvaluationsForEvaluationId = graphene.Field(
        GrapheneAssetConditionEvaluationRecordsOrError,
        evaluationId=graphene.Argument(graphene.NonNull(graphene.Int)),
        description=("Retrieve the condition evaluation records for a given evaluation ID."),
    )

    autoMaterializeTicks = graphene.Field(
        non_null_list(GrapheneInstigationTick),
        dayRange=graphene.Int(),
        dayOffset=graphene.Int(),
        limit=graphene.Int(),
        cursor=graphene.String(),
        statuses=graphene.List(graphene.NonNull(GrapheneInstigationTickStatus)),
        beforeTimestamp=graphene.Float(),
        afterTimestamp=graphene.Float(),
        description="Fetch the history of auto-materialization ticks",
    )

    assetCheckExecutions = graphene.Field(
        non_null_list(GrapheneAssetCheckExecution),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
        checkName=graphene.Argument(graphene.NonNull(graphene.String)),
        limit=graphene.NonNull(graphene.Int),
        cursor=graphene.String(),
        description="Retrieve the executions for a given asset check.",
    )

    @capture_error
    def resolve_repositoriesOrError(
        self,
        graphene_info: ResolveInfo,
        repositorySelector: Optional[GrapheneRepositorySelector] = None,
    ):
        if repositorySelector:
            return GrapheneRepositoryConnection(
                nodes=[
                    fetch_repository(
                        graphene_info,
                        RepositorySelector.from_graphql_input(repositorySelector),
                    )
                ]
            )
        return fetch_repositories(graphene_info)

    @capture_error
    def resolve_repositoryOrError(
        self, graphene_info: ResolveInfo, repositorySelector: GrapheneRepositorySelector
    ):
        return fetch_repository(
            graphene_info, RepositorySelector.from_graphql_input(repositorySelector)
        )

    @capture_error
    def resolve_workspaceOrError(self, graphene_info: ResolveInfo):
        return fetch_workspace(graphene_info.context)

    @capture_error
    def resolve_locationStatusesOrError(self, graphene_info: ResolveInfo):
        return fetch_location_statuses(graphene_info.context)

    @capture_error
    def resolve_pipelineSnapshotOrError(
        self,
        graphene_info: ResolveInfo,
        snapshotId: Optional[str] = None,
        activePipelineSelector: Optional[GraphenePipelineSelector] = None,
    ):
        check.invariant(
            not (snapshotId and activePipelineSelector),
            "Must only pass one of snapshotId or activePipelineSelector",
        )

        if activePipelineSelector:
            pipeline_selector = pipeline_selector_from_graphql(activePipelineSelector)
            return get_job_snapshot_or_error_from_job_selector(graphene_info, pipeline_selector)
        elif snapshotId:
            return get_job_snapshot_or_error_from_snapshot_id(graphene_info, snapshotId)
        else:
            check.failed(
                "Must set one of snapshotId or activePipelineSelector",
            )

    @capture_error
    def resolve_graphOrError(
        self, graphene_info: ResolveInfo, selector: Optional[GrapheneGraphSelector] = None
    ):
        assert selector is not None
        graph_selector = graph_selector_from_graphql(selector)
        return get_graph_or_error(graphene_info, graph_selector)

    def resolve_version(self, graphene_info: ResolveInfo):
        return graphene_info.context.version

    @capture_error
    def resolve_scheduler(self, graphene_info: ResolveInfo):
        return get_scheduler_or_error(graphene_info)

    @capture_error
    def resolve_scheduleOrError(
        self, graphene_info: ResolveInfo, schedule_selector: GrapheneScheduleSelector
    ):
        return get_schedule_or_error(
            graphene_info, ScheduleSelector.from_graphql_input(schedule_selector)
        )

    @capture_error
    def resolve_schedulesOrError(
        self,
        graphene_info: ResolveInfo,
        repositorySelector: GrapheneRepositorySelector,
        scheduleStatus: Optional[GrapheneInstigationStatus] = None,
    ):
        if scheduleStatus == GrapheneInstigationStatus.RUNNING:
            instigator_statuses = {InstigatorStatus.RUNNING, InstigatorStatus.DECLARED_IN_CODE}
        elif scheduleStatus == GrapheneInstigationStatus.STOPPED:
            instigator_statuses = {InstigatorStatus.STOPPED}
        else:
            instigator_statuses = None

        return get_schedules_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(repositorySelector),
            instigator_statuses,
        )

    @capture_error
    def resolve_topLevelResourceDetailsOrError(self, graphene_info: ResolveInfo, resourceSelector):
        return get_resource_or_error(
            graphene_info, ResourceSelector.from_graphql_input(resourceSelector)
        )

    def resolve_allTopLevelResourceDetailsOrError(self, graphene_info: ResolveInfo, **kwargs):
        return get_top_level_resources_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    @capture_error
    def resolve_utilizedEnvVarsOrError(self, graphene_info: ResolveInfo, **kwargs):
        return get_utilized_env_vars_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    @capture_error
    def resolve_sensorOrError(
        self, graphene_info: ResolveInfo, sensorSelector: GrapheneRepositorySelector
    ):
        return get_sensor_or_error(graphene_info, SensorSelector.from_graphql_input(sensorSelector))

    @capture_error
    def resolve_sensorsOrError(
        self,
        graphene_info,
        repositorySelector: GrapheneRepositorySelector,
        sensorStatus: Optional[GrapheneInstigationStatus] = None,
    ):
        if sensorStatus == GrapheneInstigationStatus.RUNNING:
            instigator_statuses = {InstigatorStatus.RUNNING, InstigatorStatus.DECLARED_IN_CODE}
        elif sensorStatus == GrapheneInstigationStatus.STOPPED:
            instigator_statuses = {InstigatorStatus.STOPPED}
        else:
            instigator_statuses = None
        return get_sensors_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(repositorySelector),
            instigator_statuses,
        )

    @capture_error
    def resolve_instigationStateOrError(
        self, graphene_info: ResolveInfo, instigationSelector: GrapheneInstigationSelector
    ):
        return get_instigator_state_or_error(
            graphene_info, InstigatorSelector.from_graphql_input(instigationSelector)
        )

    @capture_error
    def resolve_pipelineOrError(self, graphene_info: ResolveInfo, params: GraphenePipelineSelector):
        return get_job_or_error(
            graphene_info,
            pipeline_selector_from_graphql(params),
        )

    def resolve_pipelineRunsOrError(
        self,
        _graphene_info: ResolveInfo,
        filter: Optional[GrapheneRunsFilter] = None,  # noqa: A002
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        selector = filter.to_selector() if filter is not None else None

        return GrapheneRuns(
            filters=selector,
            cursor=cursor,
            limit=limit,
        )

    def resolve_pipelineRunOrError(self, graphene_info: ResolveInfo, runId: graphene.ID):
        return get_run_by_id(graphene_info, runId)

    def resolve_runsOrError(
        self,
        _graphene_info: ResolveInfo,
        filter: Optional[GrapheneRunsFilter] = None,  # noqa: A002
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        selector = filter.to_selector() if filter is not None else None

        return GrapheneRuns(
            filters=selector,
            cursor=cursor,
            limit=limit,
        )

    def resolve_runIdsOrError(
        self,
        _graphene_info: ResolveInfo,
        filter: Optional[GrapheneRunsFilter] = None,  # noqa: A002
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        selector = filter.to_selector() if filter is not None else None

        return GrapheneRunIds(
            filters=selector,
            cursor=cursor,
            limit=limit,
        )

    def resolve_runOrError(self, graphene_info: ResolveInfo, runId):
        return get_run_by_id(graphene_info, runId)

    @capture_error
    def resolve_partitionSetsOrError(
        self, graphene_info: ResolveInfo, repositorySelector: RepositorySelector, pipelineName: str
    ):
        return get_partition_sets_or_error(
            graphene_info,
            RepositorySelector.from_graphql_input(repositorySelector),
            pipelineName,
        )

    @capture_error
    def resolve_partitionSetOrError(
        self,
        graphene_info: ResolveInfo,
        repositorySelector: RepositorySelector,
        partitionSetName: Optional[str] = None,
    ):
        return get_partition_set(
            graphene_info,
            RepositorySelector.from_graphql_input(repositorySelector),
            # partitionSetName should prob be required
            partitionSetName,  # type: ignore
        )

    @capture_error
    def resolve_runTagKeysOrError(self, graphene_info: ResolveInfo):
        return get_run_tag_keys(graphene_info)

    @capture_error
    def resolve_runTagsOrError(
        self,
        graphene_info: ResolveInfo,
        tagKeys: List[str],
        valuePrefix: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        return get_run_tags(graphene_info, tagKeys, valuePrefix, limit)

    @capture_error
    def resolve_runGroupOrError(self, graphene_info: ResolveInfo, runId):
        return get_run_group(graphene_info, runId)

    @capture_error
    def resolve_isPipelineConfigValid(
        self,
        graphene_info: ResolveInfo,
        pipeline: GraphenePipelineSelector,
        mode: str,
        runConfigData: Optional[Any] = None,  # custom scalar (GrapheneRunConfigData)
    ):
        return validate_pipeline_config(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            parse_run_config_input(runConfigData or {}, raise_on_error=False),
        )

    @capture_error
    def resolve_executionPlanOrError(
        self,
        graphene_info: ResolveInfo,
        pipeline: GraphenePipelineSelector,
        mode: str,
        runConfigData: Optional[Any] = None,  # custom scalar (GrapheneRunConfigData)
    ):
        return get_execution_plan(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            parse_run_config_input(runConfigData or {}, raise_on_error=True),  # type: ignore  # (possible str)
        )

    @capture_error
    def resolve_runConfigSchemaOrError(
        self,
        graphene_info: ResolveInfo,
        selector: GraphenePipelineSelector,
        mode: Optional[str] = None,
    ):
        return resolve_run_config_schema_or_error(
            graphene_info, pipeline_selector_from_graphql(selector), mode
        )

    def resolve_instance(self, graphene_info: ResolveInfo):
        return GrapheneInstance(graphene_info.context.instance)

    def resolve_assetNodes(
        self,
        graphene_info: ResolveInfo,
        loadMaterializations: bool,
        group: Optional[GrapheneAssetGroupSelector] = None,
        pipeline: Optional[GraphenePipelineSelector] = None,
        assetKeys: Optional[Sequence[GrapheneAssetKeyInput]] = None,
    ) -> Sequence[GrapheneAssetNode]:
        if assetKeys == []:
            return []
        elif not assetKeys:
            use_all_asset_keys = True
            resolved_asset_keys = None
        else:
            use_all_asset_keys = False
            resolved_asset_keys = set(
                AssetKey.from_graphql_input(asset_key_input) for asset_key_input in assetKeys or []
            )

        repo = None

        dynamic_partitions_loader = CachingDynamicPartitionsLoader(graphene_info.context.instance)
        if group is not None:
            group_name = group.groupName
            repo_sel = RepositorySelector.from_graphql_input(group)
            repo_loc = graphene_info.context.get_code_location(repo_sel.location_name)
            repo = repo_loc.get_repository(repo_sel.repository_name)
            external_asset_nodes = repo.get_external_asset_nodes()
            asset_checks_loader = AssetChecksLoader(
                context=graphene_info.context,
                asset_keys=[node.asset_key for node in external_asset_nodes],
            )
            results = (
                [
                    GrapheneAssetNode(
                        repo_loc,
                        repo,
                        asset_node,
                        asset_checks_loader=asset_checks_loader,
                        dynamic_partitions_loader=dynamic_partitions_loader,
                    )
                    for asset_node in external_asset_nodes
                    if asset_node.group_name == group_name
                ]
                if external_asset_nodes
                else []
            )
        elif pipeline is not None:
            job_name = pipeline.pipelineName
            repo_sel = RepositorySelector.from_graphql_input(pipeline)
            repo_loc = graphene_info.context.get_code_location(repo_sel.location_name)
            repo = repo_loc.get_repository(repo_sel.repository_name)
            external_asset_nodes = repo.get_external_asset_nodes(job_name)
            asset_checks_loader = AssetChecksLoader(
                context=graphene_info.context,
                asset_keys=[node.asset_key for node in external_asset_nodes],
            )
            results = (
                [
                    GrapheneAssetNode(
                        repo_loc,
                        repo,
                        asset_node,
                        asset_checks_loader=asset_checks_loader,
                        dynamic_partitions_loader=dynamic_partitions_loader,
                    )
                    for asset_node in external_asset_nodes
                ]
                if external_asset_nodes
                else []
            )
        else:
            results = get_asset_nodes(graphene_info)

        # Filter down to requested asset keys
        results = [
            node
            for node in results
            if use_all_asset_keys or node.assetKey in check.not_none(resolved_asset_keys)
        ]

        if not results:
            return []

        materialization_loader = BatchMaterializationLoader(
            instance=graphene_info.context.instance,
            asset_keys=[node.assetKey for node in results],
        )
        asset_checks_loader = AssetChecksLoader(
            context=graphene_info.context,
            asset_keys=[node.assetKey for node in results],
        )

        depended_by_loader = CrossRepoAssetDependedByLoader(context=graphene_info.context)

        def load_asset_graph() -> RemoteAssetGraph:
            if repo is not None:
                return repo.asset_graph
            else:
                return graphene_info.context.asset_graph

        stale_status_loader = StaleStatusLoader(
            instance=graphene_info.context.instance,
            asset_graph=load_asset_graph,
        )

        base_deployment_context = graphene_info.context.get_base_deployment_context()

        nodes = [
            GrapheneAssetNode(
                node.repository_location,
                node.external_repository,
                node.external_asset_node,
                asset_checks_loader=asset_checks_loader,
                materialization_loader=materialization_loader,
                depended_by_loader=depended_by_loader,
                stale_status_loader=stale_status_loader,
                dynamic_partitions_loader=dynamic_partitions_loader,
                # base_deployment_context will be None if we are not in a branch deployment
                asset_graph_differ=AssetGraphDiffer.from_external_repositories(
                    code_location_name=node.repository_location.name,
                    repository_name=node.external_repository.name,
                    branch_workspace=graphene_info.context,
                    base_workspace=base_deployment_context,
                )
                if base_deployment_context is not None
                else None,
            )
            for node in results
        ]
        return sorted(nodes, key=lambda node: node.id)

    def resolve_assetNodeOrError(self, graphene_info: ResolveInfo, assetKey: GrapheneAssetKeyInput):
        asset_key_input = cast(Mapping[str, Sequence[str]], assetKey)
        return get_asset_node(graphene_info, AssetKey.from_graphql_input(asset_key_input))

    @capture_error
    def resolve_assetsOrError(
        self,
        graphene_info: ResolveInfo,
        prefix: Optional[Sequence[str]] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        return get_assets(
            graphene_info,
            prefix=prefix,
            cursor=cursor,
            limit=limit,
        )

    def resolve_assetOrError(self, graphene_info: ResolveInfo, assetKey: GrapheneAssetKeyInput):
        return get_asset(graphene_info, AssetKey.from_graphql_input(assetKey))

    def resolve_assetNodeAdditionalRequiredKeys(
        self,
        graphene_info: ResolveInfo,
        assetKeys: Sequence[GrapheneAssetKeyInput],
    ):
        assert assetKeys is not None
        raw_asset_keys = cast(Sequence[Mapping[str, Sequence[str]]], assetKeys)
        asset_keys = set(AssetKey.from_graphql_input(asset_key) for asset_key in raw_asset_keys)
        return get_additional_required_keys(graphene_info, asset_keys)

    def resolve_assetNodeDefinitionCollisions(
        self,
        graphene_info: ResolveInfo,
        assetKeys: Sequence[GrapheneAssetKeyInput],
    ):
        assert assetKeys is not None
        raw_asset_keys = cast(Sequence[Mapping[str, Sequence[str]]], assetKeys)
        asset_keys = set(AssetKey.from_graphql_input(asset_key) for asset_key in raw_asset_keys)
        return get_asset_node_definition_collisions(graphene_info, asset_keys)

    @capture_error
    def resolve_partitionBackfillOrError(self, graphene_info: ResolveInfo, backfillId: str):
        return get_backfill(graphene_info, backfillId)

    @capture_error
    def resolve_partitionBackfillsOrError(
        self,
        graphene_info: ResolveInfo,
        status: Optional[GrapheneBulkActionStatus] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        return get_backfills(
            graphene_info,
            status=BulkActionStatus.from_graphql_input(status) if status else None,
            cursor=cursor,
            limit=limit,
        )

    def resolve_assetBackfillPreview(
        self, graphene_info: ResolveInfo, params: GrapheneAssetBackfillPreviewParams
    ) -> Sequence[GrapheneAssetPartitions]:
        return get_asset_backfill_preview(graphene_info, params)

    def resolve_permissions(self, graphene_info: ResolveInfo):
        permissions = graphene_info.context.permissions
        return [GraphenePermission(permission, value) for permission, value in permissions.items()]

    def resolve_canBulkTerminate(self, graphene_info: ResolveInfo) -> bool:
        return graphene_info.context.has_permission(Permissions.TERMINATE_PIPELINE_EXECUTION)

    def resolve_assetsLatestInfo(
        self, graphene_info: ResolveInfo, assetKeys: Sequence[GrapheneAssetKeyInput]
    ):
        asset_keys = set(AssetKey.from_graphql_input(asset_key) for asset_key in assetKeys)

        results = get_asset_nodes(graphene_info)

        # Filter down to requested asset keys
        # Build mapping of asset key to the step keys required to generate the asset
        step_keys_by_asset: Dict[AssetKey, Sequence[str]] = {
            node.external_asset_node.asset_key: node.external_asset_node.op_names
            for node in results
            if node.assetKey in asset_keys
        }

        return get_assets_latest_info(graphene_info, step_keys_by_asset)

    @capture_error
    def resolve_logsForRun(
        self,
        graphene_info: ResolveInfo,
        runId: str,
        afterCursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        return get_logs_for_run(graphene_info, runId, afterCursor, limit)

    def resolve_capturedLogsMetadata(
        self, graphene_info: ResolveInfo, logKey: Sequence[str]
    ) -> GrapheneCapturedLogsMetadata:
        return get_captured_log_metadata(graphene_info, logKey)

    def resolve_capturedLogs(
        self,
        graphene_info: ResolveInfo,
        logKey: Sequence[str],
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> GrapheneCapturedLogs:
        # Type-ignore because `get_log_data` returns a `ComputeLogManager` but in practice this is
        # always also an instance of `CapturedLogManager`, which defines `get_log_data`. Probably
        # `ComputeLogManager` should subclass `CapturedLogManager`.
        log_data = get_compute_log_manager(graphene_info).get_log_data(
            logKey, cursor=cursor, max_bytes=limit
        )
        return from_captured_log_data(log_data)

    def resolve_shouldShowNux(self, graphene_info):
        return graphene_info.context.instance.nux_enabled and not get_has_seen_nux()

    def resolve_test(self, _):
        return GrapheneTestFields()

    def resolve_autoMaterializeAssetEvaluationsOrError(
        self,
        graphene_info: ResolveInfo,
        assetKey: GrapheneAssetKeyInput,
        limit: int,
        cursor: Optional[str] = None,
    ):
        return fetch_auto_materialize_asset_evaluations(
            graphene_info=graphene_info, graphene_asset_key=assetKey, cursor=cursor, limit=limit
        )

    def resolve_autoMaterializeEvaluationsForEvaluationId(
        self,
        graphene_info: ResolveInfo,
        evaluationId: int,
    ):
        return fetch_auto_materialize_asset_evaluations_for_evaluation_id(
            graphene_info=graphene_info, evaluation_id=evaluationId
        )

    def resolve_assetConditionEvaluationForPartition(
        self,
        graphene_info: ResolveInfo,
        assetKey: GrapheneAssetKeyInput,
        evaluationId: int,
        partition: str,
    ):
        return fetch_asset_condition_evaluation_record_for_partition(
            graphene_info=graphene_info,
            graphene_asset_key=assetKey,
            evaluation_id=evaluationId,
            partition_key=partition,
        )

    def resolve_assetConditionEvaluationRecordsOrError(
        self,
        graphene_info: ResolveInfo,
        assetKey: GrapheneAssetKeyInput,
        limit: int,
        cursor: Optional[str] = None,
    ):
        return fetch_asset_condition_evaluation_records_for_asset_key(
            graphene_info=graphene_info, graphene_asset_key=assetKey, cursor=cursor, limit=limit
        )

    def resolve_assetConditionEvaluationsForEvaluationId(
        self, graphene_info: ResolveInfo, evaluationId: int
    ):
        return fetch_asset_condition_evaluation_records_for_evaluation_id(
            graphene_info=graphene_info, evaluation_id=evaluationId
        )

    def resolve_autoMaterializeTicks(
        self,
        graphene_info,
        dayRange=None,
        dayOffset=None,
        limit=None,
        cursor=None,
        statuses=None,
        beforeTimestamp=None,
        afterTimestamp=None,
    ):
        # Only valid for ticks from before auto-materialize was moved to be powered by multiple
        # sensors
        from dagster._daemon.asset_daemon import (
            _PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            _PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
        )

        return get_instigation_ticks(
            graphene_info=graphene_info,
            instigator_type=InstigatorType.AUTO_MATERIALIZE,
            instigator_origin_id=_PRE_SENSOR_AUTO_MATERIALIZE_ORIGIN_ID,
            selector_id=_PRE_SENSOR_AUTO_MATERIALIZE_SELECTOR_ID,
            batch_loader=None,
            dayRange=dayRange,
            dayOffset=dayOffset,
            limit=limit,
            cursor=cursor,
            status_strings=statuses,
            before=beforeTimestamp,
            after=afterTimestamp,
        )

    def resolve_assetCheckExecutions(
        self,
        graphene_info: ResolveInfo,
        assetKey: GrapheneAssetKeyInput,
        checkName: str,
        limit: int,
        cursor: Optional[str] = None,
    ):
        return fetch_asset_check_executions(
            graphene_info.context.instance,
            asset_check_key=AssetCheckKey(
                asset_key=AssetKey.from_graphql_input(assetKey), name=checkName
            ),
            limit=limit,
            cursor=cursor,
        )
