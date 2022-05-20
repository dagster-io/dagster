# pylint: disable=missing-graphene-docstring
import graphene

import dagster._check as check
from dagster.core.execution.backfill import BulkActionStatus, PartitionBackfill
from dagster.core.storage.pipeline_run import PipelineRunStatus, RunsFilter
from dagster.core.storage.tags import PARTITION_NAME_TAG

from .errors import (
    GrapheneInvalidOutputError,
    GrapheneInvalidStepError,
    GraphenePartitionSetNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
    GrapheneRunConflict,
    GrapheneUnauthorizedError,
    create_execution_params_error_types,
)
from .pipelines.config import GrapheneRunConfigValidationInvalid
from .util import non_null_list

pipeline_execution_error_types = (
    GrapheneInvalidStepError,
    GrapheneInvalidOutputError,
    GrapheneRunConfigValidationInvalid,
    GraphenePipelineNotFoundError,
    GrapheneRunConflict,
    GrapheneUnauthorizedError,
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
        types = (GrapheneCancelBackfillSuccess, GrapheneUnauthorizedError, GraphenePythonError)
        name = "CancelBackfillResult"


class GrapheneResumeBackfillSuccess(graphene.ObjectType):
    backfill_id = graphene.NonNull(graphene.String)

    class Meta:
        name = "ResumeBackfillSuccess"


class GrapheneResumeBackfillResult(graphene.Union):
    class Meta:
        types = (GrapheneResumeBackfillSuccess, GrapheneUnauthorizedError, GraphenePythonError)
        name = "ResumeBackfillResult"


class GrapheneBulkActionStatus(graphene.Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

    class Meta:
        name = "BulkActionStatus"


class GrapheneBackfillStatus(graphene.Enum):
    REQUESTED = "REQUESTED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    INCOMPLETE = "INCOMPLETE"

    class Meta:
        name = "BackfillStatus"


class GrapheneBackfillRunStats(graphene.ObjectType):
    class Meta:
        name = "BackfillRunStats"

    numQueued = graphene.NonNull(graphene.Int)
    numInProgress = graphene.NonNull(graphene.Int)
    numSucceeded = graphene.NonNull(graphene.Int)
    numFailed = graphene.NonNull(graphene.Int)
    numPartitionsWithRuns = graphene.NonNull(graphene.Int)
    numTotalRuns = graphene.NonNull(graphene.Int)


class GraphenePartitionBackfill(graphene.ObjectType):
    class Meta:
        name = "PartitionBackfill"

    backfillId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneBulkActionStatus)
    backfillStatus = graphene.NonNull(GrapheneBackfillStatus)
    partitionNames = non_null_list(graphene.String)
    numPartitions = graphene.NonNull(graphene.Int)
    numRequested = graphene.NonNull(graphene.Int)
    fromFailure = graphene.NonNull(graphene.Boolean)
    reexecutionSteps = non_null_list(graphene.String)
    partitionSetName = graphene.NonNull(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)
    partitionSet = graphene.Field("dagster_graphql.schema.partition_sets.GraphenePartitionSet")
    runs = graphene.Field(
        non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun"),
        limit=graphene.Int(),
    )
    unfinishedRuns = graphene.Field(
        non_null_list("dagster_graphql.schema.pipelines.pipeline.GrapheneRun"),
        limit=graphene.Int(),
    )
    error = graphene.Field(GraphenePythonError)
    partitionRunStats = graphene.NonNull(GrapheneBackfillRunStats)

    def __init__(self, backfill_job):
        self._backfill_job = check.opt_inst_param(backfill_job, "backfill_job", PartitionBackfill)

        self._records = None

        super().__init__(
            backfillId=backfill_job.backfill_id,
            partitionSetName=backfill_job.partition_set_origin.partition_set_name,
            status=backfill_job.status,
            fromFailure=bool(backfill_job.from_failure),
            reexecutionSteps=backfill_job.reexecution_steps,
            partitionNames=backfill_job.partition_names,
            timestamp=backfill_job.backfill_timestamp,
        )

    def _get_records(self, graphene_info):
        if self._records == None:
            filters = RunsFilter.for_backfill(self._backfill_job.backfill_id)
            self._records = graphene_info.context.instance.get_run_records(
                filters=filters,
            )
        return self._records

    def resolve_unfinishedRuns(self, graphene_info):
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records if not record.pipeline_run.is_finished]

    def resolve_backfillStatus(self, graphene_info):
        if self._backfill_job.status == BulkActionStatus.REQUESTED:
            return GrapheneBackfillStatus.REQUESTED
        if self._backfill_job.status == BulkActionStatus.CANCELED:
            return GrapheneBackfillStatus.CANCELED
        if self._backfill_job.status == BulkActionStatus.FAILED:
            return GrapheneBackfillStatus.FAILED
        if self._backfill_job.status == BulkActionStatus.COMPLETED:
            records = self._get_records(graphene_info)

            is_done = all(record.pipeline_run.is_finished for record in records)
            if not is_done:
                return GrapheneBackfillStatus.IN_PROGRESS
            else:
                num_success = len(
                    [
                        record
                        for record in records
                        if record.pipeline_run.status == PipelineRunStatus.SUCCESS
                    ]
                )
                if num_success == len(self._backfill_job.partition_names):
                    return GrapheneBackfillStatus.COMPLETED
                else:
                    return GrapheneBackfillStatus.INCOMPLETE

    def resolve_partitionRunStats(self, graphene_info):
        records = self._get_records(graphene_info)

        by_partition_records = {}

        for record in records:
            partition = record.pipeline_run.tags.get(PARTITION_NAME_TAG)
            if partition and partition not in by_partition_records:  # get latest for each partition
                by_partition_records[partition] = record

        num_queued = 0
        num_in_progress = 0
        num_succeeded = 0
        num_failed = 0

        for _partition, record in by_partition_records.items():
            status = record.pipeline_run.status
            if status == PipelineRunStatus.QUEUED:
                num_queued = num_queued + 1
            elif not record.pipeline_run.is_finished:
                num_in_progress = num_in_progress + 1
            elif status == PipelineRunStatus.SUCCESS:
                num_succeeded = num_succeeded + 1
            elif status in {PipelineRunStatus.FAILURE, PipelineRunStatus.CANCELED}:
                num_failed = num_failed + 1
            else:
                check.invariant(False, f"Unexpected PipelineRunStatus {status}")

        return GrapheneBackfillRunStats(
            numQueued=num_queued,
            numInProgress=num_in_progress,
            numSucceeded=num_succeeded,
            numFailed=num_failed,
            numPartitionsWithRuns=len(by_partition_records),
            numTotalRuns=len(records),
        )

    def resolve_runs(self, graphene_info):
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records]

    def resolve_numPartitions(self, _graphene_info):
        return len(self._backfill_job.partition_names)

    def resolve_numRequested(self, graphene_info):
        if self._backfill_job.status == BulkActionStatus.COMPLETED:
            return len(self._backfill_job.partition_names)

        records = self._get_records(graphene_info)

        run_count = len(records)
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
