import graphene
from dagster import check
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.storage.pipeline_run import PipelineRunsFilter

from .errors import (
    GrapheneInvalidOutputError,
    GrapheneInvalidStepError,
    GraphenePartitionSetNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePipelineRunConflict,
    GraphenePythonError,
    create_execution_params_error_types,
)
from .pipelines.config import GraphenePipelineConfigValidationInvalid
from .util import non_null_list

pipeline_execution_error_types = (
    GrapheneInvalidStepError,
    GrapheneInvalidOutputError,
    GraphenePipelineConfigValidationInvalid,
    GraphenePipelineNotFoundError,
    GraphenePipelineRunConflict,
    GraphenePythonError,
) + create_execution_params_error_types


class GrapheneLaunchBackfillSuccess(graphene.ObjectType):
    backfill_id = graphene.NonNull(graphene.String)
    launched_run_ids = graphene.List(graphene.String)

    class Meta:
        name = "LaunchBackfillSuccess"


class GrapheneLaunchBackfillResult(graphene.Union):
    class Meta:
        types = (
            GrapheneLaunchBackfillSuccess,
            GraphenePartitionSetNotFoundError,
        ) + pipeline_execution_error_types
        name = "LaunchBackfillResult"


class GrapheneCancelBackfillSuccess(graphene.ObjectType):
    backfill_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "CancelBackfillSuccess"


class GrapheneCancelBackfillResult(graphene.Union):
    class Meta:
        types = (GrapheneCancelBackfillSuccess, GraphenePythonError)
        name = "CancelBackfillResult"


class GrapheneBulkActionStatus(graphene.Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

    class Meta:
        name = "BulkActionStatus"


class GraphenePartitionBackfill(graphene.ObjectType):
    class Meta:
        name = "PartitionBackfill"

    backfillId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneBulkActionStatus)
    numRequested = graphene.NonNull(graphene.Int)
    numTotal = graphene.NonNull(graphene.Int)
    fromFailure = graphene.NonNull(graphene.Boolean)
    reexecutionSteps = non_null_list(graphene.String)
    partitionSetName = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)
    partitionSet = graphene.Field("dagster_graphql.schema.partition_sets.GraphenePartitionSet")
    runs = graphene.Field(
        non_null_list("dagster_graphql.schema.pipelines.pipeline.GraphenePipelineRun"),
        limit=graphene.Int(),
    )
    error = graphene.Field(GraphenePythonError)

    def __init__(self, backfill_job):
        self._backfill_job = check.opt_inst_param(backfill_job, "backfill_job", PartitionBackfill)

        super().__init__(
            backfillId=backfill_job.backfill_id,
            partitionSetName=backfill_job.partition_set_origin.partition_set_name,
            status=backfill_job.status,
            numTotal=len(backfill_job.partition_names),
            fromFailure=bool(backfill_job.from_failure),
            reexecutionSteps=backfill_job.reexecution_steps,
            timestamp=backfill_job.backfill_timestamp,
        )

    def resolve_runs(self, graphene_info, **kwargs):
        from .pipelines.pipeline import GraphenePipelineRun

        filters = PipelineRunsFilter.for_backfill(self._backfill_job.backfill_id)
        return [
            GraphenePipelineRun(r)
            for r in graphene_info.context.instance.get_runs(
                filters=filters,
                limit=kwargs.get("limit"),
            )
        ]

    def resolve_numRequested(self, graphene_info):
        filters = PipelineRunsFilter.for_backfill(self._backfill_job.backfill_id)
        run_count = graphene_info.context.instance.get_runs_count(filters)
        if self._backfill_job.status == BulkActionStatus.COMPLETED:
            return len(self._backfill_job.partition_names)

        checkpoint = self._backfill_job.last_submitted_partition_name
        return max(
            run_count,
            self._backfill_job.partition_names.index(checkpoint) + 1
            if checkpoint and checkpoint in self._backfill_job.partition_names
            else 0,
        )

    def resolve_partitionSet(self, graphene_info):
        from ..schema.partition_sets import GraphenePartitionSet

        origin = self._backfill_job.partition_set_origin
        location_name = origin.external_repository_origin.repository_location_origin.location_name
        repository_name = origin.external_repository_origin.repository_name
        if not graphene_info.context.has_repository_location(location_name):
            return None

        location = graphene_info.context.get_repository_location(location_name)
        if not location.has_repository(repository_name):
            return None

        repository = location.get_repository(repository_name)
        external_partition_sets = [
            partition_set
            for partition_set in repository.get_external_partition_sets()
            if partition_set.name == origin.partition_set_name
        ]
        if not external_partition_sets:
            return None

        partition_set = external_partition_sets[0]
        return GraphenePartitionSet(
            external_repository_handle=repository.handle,
            external_partition_set=partition_set,
        )

    def resolve_error(self, _):
        if self._backfill_job.error:
            return GraphenePythonError(self._backfill_job.error)
        return None


class GraphenePartitionBackfillOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionBackfill, GraphenePythonError)
        name = "PartitionBackfillOrError"


class GraphenePartitionBackfills(graphene.ObjectType):
    results = non_null_list(GraphenePartitionBackfill)

    class Meta:
        name = "PartitionBackfills"


class GraphenePartitionBackfillsOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionBackfills, GraphenePythonError)
        name = "PartitionBackfillsOrError"
