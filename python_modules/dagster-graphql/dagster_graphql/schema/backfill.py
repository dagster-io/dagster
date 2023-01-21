import dagster._check as check
import graphene
from dagster._core.execution.backfill import PartitionBackfill
from dagster._core.storage.pipeline_run import RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG

from ..implementation.fetch_partition_sets import (
    partition_status_counts_from_run_partition_data,
    partition_statuses_from_run_partition_data,
)
from .asset_key import GrapheneAssetKey
from .errors import (
    GrapheneInvalidOutputError,
    GrapheneInvalidStepError,
    GrapheneInvalidSubsetError,
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
    GrapheneInvalidSubsetError,
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


class GraphenePartitionBackfill(graphene.ObjectType):
    class Meta:
        name = "PartitionBackfill"

    backfillId = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneBulkActionStatus)
    partitionNames = non_null_list(graphene.String)
    numPartitions = graphene.NonNull(graphene.Int)
    numCancelable = graphene.NonNull(graphene.Int)
    fromFailure = graphene.NonNull(graphene.Boolean)
    reexecutionSteps = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))
    partitionSetName = graphene.Field(graphene.String)
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
    partitionStatuses = graphene.NonNull(
        "dagster_graphql.schema.partition_sets.GraphenePartitionStatuses"
    )
    partitionStatusCounts = non_null_list(
        "dagster_graphql.schema.partition_sets.GraphenePartitionStatusCounts"
    )

    def __init__(self, backfill_job):
        self._backfill_job = check.opt_inst_param(backfill_job, "backfill_job", PartitionBackfill)

        self._records = None
        self._partition_run_data = None

        super().__init__(
            backfillId=backfill_job.backfill_id,
            partitionSetName=backfill_job.partition_set_name,
            status=backfill_job.status.value,
            fromFailure=bool(backfill_job.from_failure),
            reexecutionSteps=backfill_job.reexecution_steps,
            timestamp=backfill_job.backfill_timestamp,
            assetSelection=backfill_job.asset_selection,
        )

    def _get_partition_set(self, graphene_info):
        if self._backfill_job.partition_set_origin is None:
            return None

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

        return external_partition_sets[0]

    def _get_records(self, graphene_info):
        if self._records is None:
            filters = RunsFilter.for_backfill(self._backfill_job.backfill_id)
            self._records = graphene_info.context.instance.get_run_records(
                filters=filters,
            )
        return self._records

    def _get_partition_run_data(self, graphene_info):
        if self._partition_run_data is None:
            self._partition_run_data = (
                graphene_info.context.instance.run_storage.get_run_partition_data(
                    runs_filter=RunsFilter(
                        tags={
                            BACKFILL_ID_TAG: self._backfill_job.backfill_id,
                        }
                    )
                )
            )
        return self._partition_run_data

    def resolve_unfinishedRuns(self, graphene_info):
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records if not record.pipeline_run.is_finished]

    def resolve_runs(self, graphene_info):
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records]

    def resolve_partitionNames(self, _graphene_info):
        return self._backfill_job.get_partition_names(_graphene_info.context)

    def resolve_numPartitions(self, _graphene_info):
        return self._backfill_job.get_num_partitions(_graphene_info.context)

    def resolve_numCancelable(self, _graphene_info):
        return self._backfill_job.get_num_cancelable()

    def resolve_partitionSet(self, graphene_info):
        from ..schema.partition_sets import GraphenePartitionSet

        partition_set = self._get_partition_set(graphene_info)

        if not partition_set:
            return None

        return GraphenePartitionSet(
            external_repository_handle=partition_set.repository_handle,
            external_partition_set=partition_set,
        )

    def resolve_partitionStatuses(self, graphene_info):
        partition_set_origin = self._backfill_job.partition_set_origin
        partition_set_name = (
            partition_set_origin.partition_set_name if partition_set_origin else None
        )
        partition_run_data = self._get_partition_run_data(graphene_info)
        return partition_statuses_from_run_partition_data(
            partition_set_name,
            partition_run_data,
            self._backfill_job.get_partition_names(graphene_info.context),
            backfill_id=self._backfill_job.backfill_id,
        )

    def resolve_partitionStatusCounts(self, graphene_info):
        partition_run_data = self._get_partition_run_data(graphene_info)
        return partition_status_counts_from_run_partition_data(
            partition_run_data, self._backfill_job.get_partition_names(graphene_info.context)
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
