import graphene
from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.host_representation import (
    JobSelector,
    RepositorySelector,
    ScheduleSelector,
    SensorSelector,
)
from dagster.core.scheduler.job import JobType

from ...implementation.external import (
    fetch_repositories,
    fetch_repository,
    fetch_repository_locations,
)
from ...implementation.fetch_assets import get_asset, get_assets
from ...implementation.fetch_backfills import get_backfill, get_backfills
from ...implementation.fetch_jobs import get_job_state_or_error, get_unloadable_job_states_or_error
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
from ...implementation.run_config_schema import resolve_run_config_schema_or_error
from ...implementation.utils import pipeline_selector_from_graphql
from ..backfill import GraphenePartitionBackfillOrError, GraphenePartitionBackfillsOrError
from ..external import (
    GrapheneRepositoriesOrError,
    GrapheneRepositoryLocationsOrError,
    GrapheneRepositoryOrError,
)
from ..inputs import (
    GrapheneAssetKeyInput,
    GrapheneJobSelector,
    GraphenePipelineRunsFilter,
    GraphenePipelineSelector,
    GrapheneRepositorySelector,
    GrapheneScheduleSelector,
    GrapheneSensorSelector,
)
from ..instance import GrapheneInstance
from ..jobs import GrapheneJobStateOrError, GrapheneJobStatesOrError, GrapheneJobType
from ..partition_sets import GraphenePartitionSetOrError, GraphenePartitionSetsOrError
from ..pipelines.config_result import GraphenePipelineConfigValidationResult
from ..pipelines.pipeline import GraphenePipelineRunOrError
from ..pipelines.snapshot import GraphenePipelineSnapshotOrError
from ..run_config import GrapheneRunConfigSchemaOrError
from ..runs import (
    GraphenePipelineRuns,
    GraphenePipelineRunsOrError,
    GrapheneRunConfigData,
    GrapheneRunGroupOrError,
    GrapheneRunGroupsOrError,
)
from ..schedules import GrapheneScheduleOrError, GrapheneSchedulerOrError, GrapheneSchedulesOrError
from ..sensors import GrapheneSensorOrError, GrapheneSensorsOrError
from ..tags import GraphenePipelineTagAndValues
from ..util import non_null_list
from .assets import GrapheneAssetOrError, GrapheneAssetsOrError
from .execution_plan import GrapheneExecutionPlanOrError
from .pipeline import GraphenePipelineOrError


class GrapheneQuery(graphene.ObjectType):
    version = graphene.NonNull(graphene.String)

    repositoriesOrError = graphene.NonNull(GrapheneRepositoriesOrError)
    repositoryOrError = graphene.Field(
        graphene.NonNull(GrapheneRepositoryOrError),
        repositorySelector=graphene.NonNull(GrapheneRepositorySelector),
    )

    repositoryLocationsOrError = graphene.NonNull(GrapheneRepositoryLocationsOrError)

    pipelineOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineOrError), params=graphene.NonNull(GraphenePipelineSelector)
    )

    pipelineSnapshotOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineSnapshotOrError),
        snapshotId=graphene.String(),
        activePipelineSelector=graphene.Argument(GraphenePipelineSelector),
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

    jobStateOrError = graphene.Field(
        graphene.NonNull(GrapheneJobStateOrError),
        jobSelector=graphene.NonNull(GrapheneJobSelector),
    )

    unloadableJobStatesOrError = graphene.Field(
        graphene.NonNull(GrapheneJobStatesOrError), jobType=graphene.Argument(GrapheneJobType)
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
        graphene.NonNull(GraphenePipelineRunsOrError),
        filter=graphene.Argument(GraphenePipelineRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    pipelineRunOrError = graphene.Field(
        graphene.NonNull(GraphenePipelineRunOrError), runId=graphene.NonNull(graphene.ID)
    )

    pipelineRunTags = non_null_list(GraphenePipelineTagAndValues)

    runGroupOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupOrError), runId=graphene.NonNull(graphene.ID)
    )

    runGroupsOrError = graphene.Field(
        graphene.NonNull(GrapheneRunGroupsOrError),
        filter=graphene.Argument(GraphenePipelineRunsFilter),
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

    assetsOrError = graphene.NonNull(GrapheneAssetsOrError)

    assetOrError = graphene.Field(
        graphene.NonNull(GrapheneAssetOrError),
        assetKey=graphene.Argument(graphene.NonNull(GrapheneAssetKeyInput)),
    )

    partitionBackfillOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillOrError),
        backfillId=graphene.Argument(graphene.NonNull(graphene.String)),
    )

    partitionBackfillsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionBackfillsOrError),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    class Meta:
        name = "Query"

    def resolve_repositoriesOrError(self, graphene_info):
        return fetch_repositories(graphene_info)

    def resolve_repositoryOrError(self, graphene_info, **kwargs):
        return fetch_repository(
            graphene_info,
            RepositorySelector.from_graphql_input(kwargs.get("repositorySelector")),
        )

    def resolve_repositoryLocationsOrError(self, graphene_info):
        return fetch_repository_locations(graphene_info.context)

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

    def resolve_jobStateOrError(self, graphene_info, jobSelector):
        return get_job_state_or_error(graphene_info, JobSelector.from_graphql_input(jobSelector))

    def resolve_unloadableJobStatesOrError(self, graphene_info, **kwargs):
        job_type = JobType(kwargs["jobType"]) if "jobType" in kwargs else None
        return get_unloadable_job_states_or_error(graphene_info, job_type)

    def resolve_pipelineOrError(self, graphene_info, **kwargs):
        return get_pipeline_or_error(
            graphene_info,
            pipeline_selector_from_graphql(kwargs["params"]),
        )

    def resolve_pipelineRunsOrError(self, _graphene_info, **kwargs):
        filters = kwargs.get("filter")
        if filters is not None:
            filters = filters.to_selector()

        return GraphenePipelineRuns(
            filters=filters,
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )

    def resolve_pipelineRunOrError(self, graphene_info, runId):
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
            kwargs.get("runConfigData"),
            kwargs.get("mode"),
        )

    def resolve_executionPlanOrError(self, graphene_info, pipeline, **kwargs):
        return get_execution_plan(
            graphene_info,
            pipeline_selector_from_graphql(pipeline),
            kwargs.get("runConfigData"),
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

    def resolve_assetsOrError(self, graphene_info):
        return get_assets(graphene_info)

    def resolve_assetOrError(self, graphene_info, **kwargs):
        return get_asset(graphene_info, AssetKey.from_graphql_input(kwargs["assetKey"]))

    def resolve_partitionBackfillOrError(self, graphene_info, backfillId):
        return get_backfill(graphene_info, backfillId)

    def resolve_partitionBackfillsOrError(self, graphene_info, **kwargs):
        return get_backfills(
            graphene_info,
            cursor=kwargs.get("cursor"),
            limit=kwargs.get("limit"),
        )
