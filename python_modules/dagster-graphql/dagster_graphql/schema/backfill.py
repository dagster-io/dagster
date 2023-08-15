from typing import TYPE_CHECKING, Optional, Sequence

import dagster._check as check
import graphene
from dagster._core.definitions.time_window_partitions import (
    TimeWindowPartitionsSubset,
)
from dagster._core.execution.asset_backfill import (
    AssetBackfillStatus,
    PartitionedAssetBackfillStatus,
    UnpartitionedAssetBackfillStatus,
)
from dagster._core.execution.backfill import (
    BulkActionStatus,
    PartitionBackfill,
)
from dagster._core.host_representation.external import ExternalPartitionSet
from dagster._core.storage.dagster_run import RunPartitionData, RunRecord, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.workspace.permissions import Permissions

from ..implementation.fetch_partition_sets import (
    partition_status_counts_from_run_partition_data,
    partition_statuses_from_run_partition_data,
)
from .asset_key import GrapheneAssetKey
from .errors import (
    GrapheneError,
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
from .util import ResolveInfo, non_null_list

if TYPE_CHECKING:
    from dagster_graphql.schema.partition_sets import (
        GraphenePartitionStatusCounts,
    )

    from ..schema.partition_sets import (
        GraphenePartitionSet,
    )
    from .pipelines.pipeline import GrapheneRun

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
    CANCELING = "CANCELING"

    class Meta:
        name = "BulkActionStatus"


class GrapheneAssetBackfillData(graphene.ObjectType):
    class Meta:
        name = "AssetBackfillData"

    assetBackfillStatuses = non_null_list(
        "dagster_graphql.schema.partition_sets.GrapheneAssetBackfillStatus"
    )
    rootAssetTargetedRanges = graphene.List(
        graphene.NonNull("dagster_graphql.schema.partition_sets.GraphenePartitionKeyRange")
    )
    rootAssetTargetedPartitions = graphene.List(graphene.NonNull(graphene.String))


class GraphenePartitionBackfill(graphene.ObjectType):
    class Meta:
        name = "PartitionBackfill"

    id = graphene.NonNull(graphene.String)
    status = graphene.NonNull(GrapheneBulkActionStatus)
    partitionNames = graphene.List(graphene.NonNull(graphene.String))
    isValidSerialization = graphene.NonNull(graphene.Boolean)
    numPartitions = graphene.Field(graphene.Int)
    numCancelable = graphene.NonNull(graphene.Int)
    fromFailure = graphene.NonNull(graphene.Boolean)
    reexecutionSteps = graphene.List(graphene.NonNull(graphene.String))
    assetSelection = graphene.List(graphene.NonNull(GrapheneAssetKey))
    partitionSetName = graphene.Field(graphene.String)
    timestamp = graphene.NonNull(graphene.Float)
    endTimestamp = graphene.Field(graphene.Float)
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
    partitionStatuses = graphene.Field(
        "dagster_graphql.schema.partition_sets.GraphenePartitionStatuses"
    )
    partitionStatusCounts = non_null_list(
        "dagster_graphql.schema.partition_sets.GraphenePartitionStatusCounts"
    )
    isAssetBackfill = graphene.NonNull(graphene.Boolean)
    assetBackfillData = graphene.Field(GrapheneAssetBackfillData)

    hasCancelPermission = graphene.NonNull(graphene.Boolean)
    hasResumePermission = graphene.NonNull(graphene.Boolean)
    user = graphene.Field(graphene.String)

    def __init__(self, backfill_job: PartitionBackfill):
        self._backfill_job = check.inst_param(backfill_job, "backfill_job", PartitionBackfill)

        self._records = None
        self._partition_run_data = None

        super().__init__(
            id=backfill_job.backfill_id,
            partitionSetName=backfill_job.partition_set_name,
            status=backfill_job.status.value,
            fromFailure=bool(backfill_job.from_failure),
            reexecutionSteps=backfill_job.reexecution_steps,
            timestamp=backfill_job.backfill_timestamp,
            assetSelection=backfill_job.asset_selection,
        )

    def _get_partition_set(self, graphene_info: ResolveInfo) -> Optional[ExternalPartitionSet]:
        if self._backfill_job.partition_set_origin is None:
            return None

        origin = self._backfill_job.partition_set_origin
        location_name = origin.external_repository_origin.code_location_origin.location_name
        repository_name = origin.external_repository_origin.repository_name
        if not graphene_info.context.has_code_location(location_name):
            return None

        location = graphene_info.context.get_code_location(location_name)
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

    def _get_records(self, graphene_info: ResolveInfo) -> Sequence[RunRecord]:
        if self._records is None:
            filters = RunsFilter.for_backfill(self._backfill_job.backfill_id)
            self._records = graphene_info.context.instance.get_run_records(
                filters=filters,
            )
        return self._records

    def _get_partition_run_data(self, graphene_info: ResolveInfo) -> Sequence[RunPartitionData]:
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

    def resolve_unfinishedRuns(self, graphene_info: ResolveInfo) -> Sequence["GrapheneRun"]:
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records if not record.dagster_run.is_finished]

    def resolve_runs(self, graphene_info: ResolveInfo) -> "Sequence[GrapheneRun]":
        from .pipelines.pipeline import GrapheneRun

        records = self._get_records(graphene_info)
        return [GrapheneRun(record) for record in records]

    def resolve_endTimestamp(self, graphene_info: ResolveInfo) -> Optional[float]:
        if self._backfill_job.status == BulkActionStatus.REQUESTED:
            # if it's still in progress then there is no end time
            return None
        records = self._get_records(graphene_info)
        max_end_time = 0
        for record in records:
            max_end_time = max(record.end_time or 0, max_end_time)
        return max_end_time

    def resolve_isValidSerialization(self, _graphene_info: ResolveInfo) -> bool:
        return self._backfill_job.is_valid_serialization(_graphene_info.context)

    def resolve_partitionNames(self, _graphene_info: ResolveInfo) -> Optional[Sequence[str]]:
        return self._backfill_job.get_partition_names(_graphene_info.context)

    def resolve_numPartitions(self, _graphene_info: ResolveInfo) -> Optional[int]:
        return self._backfill_job.get_num_partitions(_graphene_info.context)

    def resolve_numCancelable(self, _graphene_info: ResolveInfo) -> int:
        return self._backfill_job.get_num_cancelable()

    def resolve_partitionSet(self, graphene_info: ResolveInfo) -> Optional["GraphenePartitionSet"]:
        from ..schema.partition_sets import GraphenePartitionSet

        partition_set = self._get_partition_set(graphene_info)

        if not partition_set:
            return None

        return GraphenePartitionSet(
            external_repository_handle=partition_set.repository_handle,
            external_partition_set=partition_set,
        )

    def resolve_partitionStatuses(self, graphene_info: ResolveInfo):
        if self._backfill_job.is_asset_backfill:
            return None

        partition_set_origin = self._backfill_job.partition_set_origin
        partition_set_name = (
            partition_set_origin.partition_set_name if partition_set_origin else None
        )
        partition_run_data = self._get_partition_run_data(graphene_info)
        return partition_statuses_from_run_partition_data(
            partition_set_name,
            partition_run_data,
            check.not_none(self._backfill_job.get_partition_names(graphene_info.context)),
            backfill_id=self._backfill_job.backfill_id,
        )

    def resolve_partitionStatusCounts(
        self, graphene_info: ResolveInfo
    ) -> Sequence["GraphenePartitionStatusCounts"]:
        partition_run_data = self._get_partition_run_data(graphene_info)
        return partition_status_counts_from_run_partition_data(
            partition_run_data,
            check.not_none(self._backfill_job.get_partition_names(graphene_info.context)),
        )

    def resolve_isAssetBackfill(self, _graphene_info: ResolveInfo) -> bool:
        return self._backfill_job.is_asset_backfill

    def resolve_assetBackfillData(
        self, graphene_info: ResolveInfo
    ) -> Optional[GrapheneAssetBackfillData]:
        from dagster_graphql.schema.partition_sets import (
            GrapheneAssetPartitionsStatusCounts,
            GraphenePartitionKeyRange,
            GrapheneUnpartitionedAssetStatus,
        )

        if not self._backfill_job.is_asset_backfill:
            return None

        status_per_asset = self._backfill_job.get_backfill_status_per_asset_key(
            graphene_info.context
        )

        asset_partition_status_counts = []

        for asset_status in status_per_asset:
            if isinstance(asset_status, PartitionedAssetBackfillStatus):
                asset_partition_status_counts.append(
                    GrapheneAssetPartitionsStatusCounts(
                        assetKey=asset_status.asset_key,
                        numPartitionsTargeted=asset_status.num_targeted_partitions,
                        numPartitionsInProgress=asset_status.partitions_counts_by_status[
                            AssetBackfillStatus.IN_PROGRESS
                        ],
                        numPartitionsMaterialized=asset_status.partitions_counts_by_status[
                            AssetBackfillStatus.MATERIALIZED
                        ],
                        numPartitionsFailed=asset_status.partitions_counts_by_status[
                            AssetBackfillStatus.FAILED
                        ],
                    )
                )
            else:
                if not isinstance(asset_status, UnpartitionedAssetBackfillStatus):
                    check.failed(f"Unexpected asset status type {type(asset_status)}")

                asset_partition_status_counts.append(
                    GrapheneUnpartitionedAssetStatus(
                        assetKey=asset_status.asset_key,
                        inProgress=asset_status.backfill_status is AssetBackfillStatus.IN_PROGRESS,
                        materialized=asset_status.backfill_status
                        is AssetBackfillStatus.MATERIALIZED,
                        failed=asset_status.backfill_status is AssetBackfillStatus.FAILED,
                    )
                )

        root_partitions_subset = self._backfill_job.get_target_root_partitions_subset(
            graphene_info.context
        )

        if not root_partitions_subset:
            root_targeted_ranges = None
            root_targeted_partitions = None
        elif isinstance(root_partitions_subset, TimeWindowPartitionsSubset):
            root_targeted_ranges = [
                GraphenePartitionKeyRange(start, end)
                for start, end in root_partitions_subset.get_partition_key_ranges()
            ]
            root_targeted_partitions = None
        else:  # Default partitions subset
            root_targeted_ranges = None
            root_targeted_partitions = root_partitions_subset.get_partition_keys()

        return GrapheneAssetBackfillData(
            assetBackfillStatuses=asset_partition_status_counts,
            rootAssetTargetedRanges=root_targeted_ranges,
            rootAssetTargetedPartitions=root_targeted_partitions,
        )

    def resolve_error(self, _graphene_info: ResolveInfo) -> Optional[GraphenePythonError]:
        if self._backfill_job.error:
            return GraphenePythonError(self._backfill_job.error)
        return None

    def resolve_hasCancelPermission(self, graphene_info: ResolveInfo) -> bool:
        if self._backfill_job.partition_set_origin is None:
            return graphene_info.context.has_permission(Permissions.CANCEL_PARTITION_BACKFILL)
        location_name = self._backfill_job.partition_set_origin.selector.location_name
        return graphene_info.context.has_permission_for_location(
            Permissions.CANCEL_PARTITION_BACKFILL, location_name
        )

    def resolve_hasResumePermission(self, graphene_info: ResolveInfo) -> bool:
        if self._backfill_job.partition_set_origin is None:
            return graphene_info.context.has_permission(Permissions.LAUNCH_PARTITION_BACKFILL)
        location_name = self._backfill_job.partition_set_origin.selector.location_name
        return graphene_info.context.has_permission_for_location(
            Permissions.LAUNCH_PARTITION_BACKFILL, location_name
        )

    def resolve_user(self, _graphene_info: ResolveInfo) -> Optional[str]:
        return self._backfill_job.user


class GrapheneBackfillNotFoundError(graphene.ObjectType):
    class Meta:
        interfaces = (GrapheneError,)
        name = "BackfillNotFoundError"

    backfill_id = graphene.NonNull(graphene.String)

    def __init__(self, backfill_id: str):
        super().__init__()
        self.backfill_id = backfill_id
        self.message = f"Backfill {backfill_id} could not be found."


class GraphenePartitionBackfillOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionBackfill, GrapheneBackfillNotFoundError, GraphenePythonError)
        name = "PartitionBackfillOrError"


class GraphenePartitionBackfills(graphene.ObjectType):
    results = non_null_list(GraphenePartitionBackfill)

    class Meta:
        name = "PartitionBackfills"


class GraphenePartitionBackfillsOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionBackfills, GraphenePythonError)
        name = "PartitionBackfillsOrError"
