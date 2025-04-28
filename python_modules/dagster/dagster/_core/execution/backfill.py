from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional, Union

from dagster import _check as check
from dagster._core.definitions import AssetKey
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.partition import PartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import PartitionsByAssetSelector
from dagster._core.definitions.utils import check_valid_title
from dagster._core.errors import DagsterDefinitionChangedDeserializationError
from dagster._core.execution.asset_backfill import (
    AssetBackfillData,
    PartitionedAssetBackfillStatus,
    UnpartitionedAssetBackfillStatus,
)
from dagster._core.execution.bulk_actions import BulkActionType
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.remote_representation.external_data import job_name_for_partition_set_snap_name
from dagster._core.remote_representation.origin import RemotePartitionSetOrigin
from dagster._core.storage.dagster_run import (
    CANCELABLE_RUN_STATUSES,
    NOT_FINISHED_STATUSES,
    RunsFilter,
)
from dagster._core.storage.tags import BACKFILL_ID_TAG, USER_TAG
from dagster._core.workspace.context import BaseWorkspaceRequestContext
from dagster._record import record
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance

MAX_RUNS_CANCELED_PER_ITERATION = 50


@whitelist_for_serdes
class BulkActionStatus(Enum):
    REQUESTED = "REQUESTED"
    COMPLETED = "COMPLETED"  # deprecated. Use COMPLETED_SUCCESS or COMPLETED_FAILED instead
    FAILED = "FAILED"  # denotes when there is a daemon failure, or some other issue processing the backfill
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_FAILED = "COMPLETED_FAILED"  # denotes that the backfill daemon completed successfully, but some runs failed

    @staticmethod
    def from_graphql_input(graphql_str):
        return BulkActionStatus(graphql_str)


BULK_ACTION_TERMINAL_STATUSES = [
    BulkActionStatus.COMPLETED,
    BulkActionStatus.FAILED,
    BulkActionStatus.CANCELED,
    BulkActionStatus.COMPLETED_SUCCESS,
    BulkActionStatus.COMPLETED_SUCCESS,
    BulkActionStatus.COMPLETED_FAILED,
]


@record
class BulkActionsFilter:
    """Filters to use when querying for bulk actions (i.e. backfills) from the BulkActionsTable.

    Each field of the BulkActionsFilter represents a logical AND with each other. For
    example, if you specify status and created_before, then you will receive only bulk actions
    with the specified states AND the created before created_before. If left blank, then
    all values will be permitted for that field.

    Args:
        statuses (Optional[Sequence[BulkActionStatus]]): A list of statuses to filter by.
        created_before (Optional[DateTime]): Filter by bulk actions that were created before this datetime. Note that the
            create_time for each bulk action is stored in UTC.
        created_after (Optional[DateTime]): Filter by bulk actions that were created after this datetime. Note that the
            create_time for each bulk action is stored in UTC.
        tags (Optional[Dict[str, Union[str, List[str]]]]): A dictionary of tags to query by. All tags specified
            here must be present for a given bulk action to pass the filter.
        job_name (Optional[str]): Name of the job to query for. If blank, all job_names will be accepted.
        backfill_ids (Optional[Sequence[str]]): A list of backfill_ids to filter by. If blank, all backfill_ids will be included
    """

    statuses: Optional[Sequence[BulkActionStatus]] = None
    created_before: Optional[datetime] = None
    created_after: Optional[datetime] = None
    tags: Optional[Mapping[str, Union[str, Sequence[str]]]] = None
    job_name: Optional[str] = None
    backfill_ids: Optional[Sequence[str]] = None


@whitelist_for_serdes
class PartitionBackfill(
    NamedTuple(
        "_PartitionBackfill",
        [
            ("backfill_id", str),
            ("status", BulkActionStatus),
            ("from_failure", bool),
            ("tags", Mapping[str, str]),
            ("backfill_timestamp", float),
            ("error", Optional[SerializableErrorInfo]),
            ("asset_selection", Optional[Sequence[AssetKey]]),
            ("title", Optional[str]),
            ("description", Optional[str]),
            # fields that are only used by job backfills
            ("partition_set_origin", Optional[RemotePartitionSetOrigin]),
            ("partition_names", Optional[Sequence[str]]),
            ("last_submitted_partition_name", Optional[str]),
            ("reexecution_steps", Optional[Sequence[str]]),
            # only used by asset backfills
            ("serialized_asset_backfill_data", Optional[str]),
            ("asset_backfill_data", Optional[AssetBackfillData]),
            ("failure_count", int),
            ("submitting_run_requests", Sequence[RunRequest]),
            ("reserved_run_ids", Sequence[str]),
            ("backfill_end_timestamp", Optional[float]),
        ],
    ),
):
    def __new__(
        cls,
        backfill_id: str,
        status: BulkActionStatus,
        from_failure: bool,
        tags: Optional[Mapping[str, str]],
        backfill_timestamp: float,
        error: Optional[SerializableErrorInfo] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        partition_set_origin: Optional[RemotePartitionSetOrigin] = None,
        partition_names: Optional[Sequence[str]] = None,
        last_submitted_partition_name: Optional[str] = None,
        reexecution_steps: Optional[Sequence[str]] = None,
        serialized_asset_backfill_data: Optional[str] = None,
        asset_backfill_data: Optional[AssetBackfillData] = None,
        failure_count: Optional[int] = None,
        submitting_run_requests: Optional[Sequence[RunRequest]] = None,
        reserved_run_ids: Optional[Sequence[str]] = None,
        backfill_end_timestamp: Optional[float] = None,
    ):
        check.invariant(
            not (asset_selection and reexecution_steps),
            "Can't supply both an asset_selection and reexecution_steps to a PartitionBackfill.",
        )

        if serialized_asset_backfill_data is not None:
            check.invariant(partition_set_origin is None)
            check.invariant(partition_names is None)
            check.invariant(last_submitted_partition_name is None)
            check.invariant(reexecution_steps is None)

        return super().__new__(
            cls,
            backfill_id=check.str_param(backfill_id, "backfill_id"),
            status=check.inst_param(status, "status", BulkActionStatus),
            from_failure=check.bool_param(from_failure, "from_failure"),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            backfill_timestamp=check.float_param(backfill_timestamp, "backfill_timestamp"),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            asset_selection=check.opt_nullable_sequence_param(
                asset_selection, "asset_selection", of_type=AssetKey
            ),
            title=check_valid_title(title),
            description=check.opt_str_param(description, "description"),
            partition_set_origin=check.opt_inst_param(
                partition_set_origin, "partition_set_origin", RemotePartitionSetOrigin
            ),
            partition_names=check.opt_nullable_sequence_param(
                partition_names, "partition_names", of_type=str
            ),
            last_submitted_partition_name=check.opt_str_param(
                last_submitted_partition_name, "last_submitted_partition_name"
            ),
            reexecution_steps=check.opt_nullable_sequence_param(
                reexecution_steps, "reexecution_steps", of_type=str
            ),
            serialized_asset_backfill_data=check.opt_str_param(
                serialized_asset_backfill_data, "serialized_asset_backfill_data"
            ),
            asset_backfill_data=check.opt_inst_param(
                asset_backfill_data, "asset_backfill_data", AssetBackfillData
            ),
            failure_count=check.opt_int_param(failure_count, "failure_count", 0),
            submitting_run_requests=check.opt_sequence_param(
                submitting_run_requests, "submitting_run_requests", of_type=RunRequest
            ),
            reserved_run_ids=check.opt_sequence_param(
                reserved_run_ids, "reserved_run_ids", of_type=str
            ),
            backfill_end_timestamp=check.opt_float_param(
                backfill_end_timestamp, "backfill_end_timestamp"
            ),
        )

    @property
    def selector_id(self):
        return self.partition_set_origin.get_selector_id() if self.partition_set_origin else None

    @property
    def is_asset_backfill(self) -> bool:
        return (
            self.serialized_asset_backfill_data is not None or self.asset_backfill_data is not None
        )

    def get_asset_backfill_data(self, asset_graph: BaseAssetGraph) -> AssetBackfillData:
        if self.serialized_asset_backfill_data:
            asset_backfill_data = AssetBackfillData.from_serialized(
                self.serialized_asset_backfill_data, asset_graph, self.backfill_timestamp
            )
        elif self.asset_backfill_data:
            asset_backfill_data = self.asset_backfill_data
        else:
            check.failed("Expected either serialized_asset_backfill_data or asset_backfill_data")

        return asset_backfill_data

    @property
    def bulk_action_type(self) -> BulkActionType:
        if self.is_asset_backfill:
            return BulkActionType.MULTI_RUN_ASSET_ACTION
        else:
            return BulkActionType.PARTITION_BACKFILL

    @property
    def partition_set_name(self) -> Optional[str]:
        if self.partition_set_origin is None:
            return None

        return self.partition_set_origin.partition_set_name

    @property
    def job_name(self) -> Optional[str]:
        if self.is_asset_backfill:
            return None
        return (
            job_name_for_partition_set_snap_name(self.partition_set_name)
            if self.partition_set_name
            else None
        )

    @property
    def log_storage_prefix(self) -> Sequence[str]:
        return ["backfill", self.backfill_id]

    @property
    def user(self) -> Optional[str]:
        if self.tags:
            return self.tags.get(USER_TAG)
        return None

    def is_valid_serialization(self, workspace: BaseWorkspaceRequestContext) -> bool:
        if self.is_asset_backfill:
            if self.serialized_asset_backfill_data:
                return AssetBackfillData.is_valid_serialization(
                    self.serialized_asset_backfill_data,
                    workspace.asset_graph,
                )
            else:
                return True
        else:
            return True

    def get_backfill_status_per_asset_key(
        self, workspace: BaseWorkspaceRequestContext
    ) -> Sequence[Union[PartitionedAssetBackfillStatus, UnpartitionedAssetBackfillStatus]]:
        """Returns a sequence of backfill statuses for each targeted asset key in the asset graph,
        in topological order.
        """
        if not self.is_valid_serialization(workspace):
            return []

        if self.is_asset_backfill:
            asset_graph = workspace.asset_graph
            try:
                asset_backfill_data = self.get_asset_backfill_data(asset_graph)
            except DagsterDefinitionChangedDeserializationError:
                return []

            return asset_backfill_data.get_backfill_status_per_asset_key(asset_graph)
        else:
            return []

    def get_target_partitions_subset(
        self, workspace: BaseWorkspaceRequestContext, asset_key: AssetKey
    ) -> Optional[PartitionsSubset]:
        if not self.is_valid_serialization(workspace):
            return None

        if self.is_asset_backfill:
            asset_graph = workspace.asset_graph
            try:
                asset_backfill_data = self.get_asset_backfill_data(asset_graph)
            except DagsterDefinitionChangedDeserializationError:
                return None

            return asset_backfill_data.get_target_partitions_subset(asset_key)
        else:
            return None

    def get_target_root_partitions_subset(
        self, workspace: BaseWorkspaceRequestContext
    ) -> Optional[PartitionsSubset]:
        if not self.is_valid_serialization(workspace):
            return None

        if self.is_asset_backfill:
            asset_graph = workspace.asset_graph
            try:
                asset_backfill_data = self.get_asset_backfill_data(asset_graph)
            except DagsterDefinitionChangedDeserializationError:
                return None

            return asset_backfill_data.get_target_root_partitions_subset(asset_graph)
        else:
            return None

    def get_num_partitions(self, workspace: BaseWorkspaceRequestContext) -> Optional[int]:
        if not self.is_valid_serialization(workspace):
            return 0

        if self.is_asset_backfill:
            asset_graph = workspace.asset_graph
            try:
                asset_backfill_data = self.get_asset_backfill_data(asset_graph)
            except DagsterDefinitionChangedDeserializationError:
                return 0

            return asset_backfill_data.get_num_partitions()
        else:
            if self.partition_names is None:
                check.failed("Non-asset backfills should have a non-null partition_names field")

            return len(self.partition_names)

    def get_partition_names(
        self, workspace: BaseWorkspaceRequestContext
    ) -> Optional[Sequence[str]]:
        if not self.is_valid_serialization(workspace):
            return []

        if self.is_asset_backfill:
            asset_graph = workspace.asset_graph
            try:
                asset_backfill_data = self.get_asset_backfill_data(asset_graph)
            except DagsterDefinitionChangedDeserializationError:
                return None

            return asset_backfill_data.get_partition_names()
        else:
            if self.partition_names is None:
                check.failed("Non-asset backfills should have a non-null partition_names field")

            return self.partition_names

    def get_num_cancelable(self) -> int:
        """This method is only valid for job backfills. It eturns the number of partitions that are have
        not yet been requested by the backfill.

        For asset backfills, returns 0.
        """
        if self.is_asset_backfill:
            return 0

        if self.status != BulkActionStatus.REQUESTED:
            return 0

        if self.partition_names is None:
            check.failed("Expected partition_names to not be None for job backfill")

        checkpoint = self.last_submitted_partition_name
        total_count = len(self.partition_names)
        checkpoint_idx = (
            self.partition_names.index(checkpoint) + 1
            if checkpoint and checkpoint in self.partition_names
            else 0
        )
        return max(0, total_count - checkpoint_idx)

    def with_status(self, status):
        check.inst_param(status, "status", BulkActionStatus)
        return self._replace(status=status)

    def with_partition_checkpoint(self, last_submitted_partition_name):
        check.opt_str_param(last_submitted_partition_name, "last_submitted_partition_name")
        return self._replace(last_submitted_partition_name=last_submitted_partition_name)

    def with_submitting_run_requests(
        self, submitting_run_requests: Sequence[RunRequest], reserved_run_ids: Sequence[str]
    ) -> "PartitionBackfill":
        return self._replace(
            submitting_run_requests=submitting_run_requests,
            reserved_run_ids=reserved_run_ids,
        )

    def with_failure_count(self, new_failure_count: int):
        return self._replace(failure_count=new_failure_count)

    def with_error(self, error):
        check.opt_inst_param(error, "error", SerializableErrorInfo)
        return self._replace(error=error)

    def with_end_timestamp(self, end_timestamp: float) -> "PartitionBackfill":
        check.float_param(end_timestamp, "end_timestamp")
        return self._replace(backfill_end_timestamp=end_timestamp)

    def with_asset_backfill_data(
        self,
        asset_backfill_data: AssetBackfillData,
        dynamic_partitions_store: DynamicPartitionsStore,
        asset_graph: BaseAssetGraph,
    ) -> "PartitionBackfill":
        is_backcompat = self.serialized_asset_backfill_data is not None
        return self._replace(
            serialized_asset_backfill_data=(
                asset_backfill_data.serialize(
                    dynamic_partitions_store=dynamic_partitions_store, asset_graph=asset_graph
                )
                if is_backcompat
                else None
            ),
            asset_backfill_data=(asset_backfill_data if not is_backcompat else None),
        )

    @classmethod
    def from_asset_partitions(
        cls,
        backfill_id: str,
        asset_graph: BaseAssetGraph,
        partition_names: Optional[Sequence[str]],
        asset_selection: Sequence[AssetKey],
        backfill_timestamp: float,
        tags: Mapping[str, str],
        dynamic_partitions_store: DynamicPartitionsStore,
        all_partitions: bool,
        title: Optional[str],
        description: Optional[str],
    ) -> "PartitionBackfill":
        """If all the selected assets that have PartitionsDefinitions have the same partitioning, then
        the backfill will target the provided partition_names for all those assets.

        Otherwise, the backfill must consist of a partitioned "anchor" asset and a set of other
        assets that descend from it. In that case, the backfill will target the partition_names of
        the anchor asset, as well as all partitions of other selected assets that are downstream
        of those partitions of the anchor asset.
        """
        asset_backfill_data = AssetBackfillData.from_asset_partitions(
            asset_graph=asset_graph,
            partition_names=partition_names,
            asset_selection=asset_selection,
            dynamic_partitions_store=dynamic_partitions_store,
            all_partitions=all_partitions,
            backfill_start_timestamp=backfill_timestamp,
        )
        return cls(
            backfill_id=backfill_id,
            status=BulkActionStatus.REQUESTED,
            from_failure=False,
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            asset_selection=asset_selection,
            serialized_asset_backfill_data=None,
            asset_backfill_data=asset_backfill_data,
            title=title,
            description=description,
        )

    @classmethod
    def from_partitions_by_assets(
        cls,
        backfill_id: str,
        asset_graph: BaseAssetGraph,
        backfill_timestamp: float,
        tags: Mapping[str, str],
        dynamic_partitions_store: DynamicPartitionsStore,
        partitions_by_assets: Sequence[PartitionsByAssetSelector],
        title: Optional[str],
        description: Optional[str],
    ):
        asset_backfill_data = AssetBackfillData.from_partitions_by_assets(
            asset_graph=asset_graph,
            dynamic_partitions_store=dynamic_partitions_store,
            backfill_start_timestamp=backfill_timestamp,
            partitions_by_assets=partitions_by_assets,
        )
        return cls(
            backfill_id=backfill_id,
            status=BulkActionStatus.REQUESTED,
            from_failure=False,
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            serialized_asset_backfill_data=None,
            asset_backfill_data=asset_backfill_data,
            asset_selection=[selector.asset_key for selector in partitions_by_assets],
            title=title,
            description=description,
        )

    @classmethod
    def from_asset_graph_subset(
        cls,
        backfill_id: str,
        backfill_timestamp: float,
        tags: Mapping[str, str],
        dynamic_partitions_store: DynamicPartitionsStore,
        asset_graph_subset: AssetGraphSubset,
        title: Optional[str],
        description: Optional[str],
    ):
        asset_backfill_data = AssetBackfillData.from_asset_graph_subset(
            asset_graph_subset=asset_graph_subset,
            dynamic_partitions_store=dynamic_partitions_store,
            backfill_start_timestamp=backfill_timestamp,
        )
        return cls(
            backfill_id=backfill_id,
            status=BulkActionStatus.REQUESTED,
            from_failure=False,
            tags=tags,
            backfill_timestamp=backfill_timestamp,
            serialized_asset_backfill_data=None,
            asset_backfill_data=asset_backfill_data,
            asset_selection=list(asset_graph_subset.asset_keys),
            title=title,
            description=description,
        )


def cancel_backfill_runs_and_cancellation_complete(
    instance: "DagsterInstance", backfill_id: str
) -> Iterator[Union[None, bool]]:
    """Cancels MAX_RUNS_CANCELED_PER_ITERATION runs associated with the backfill_id. Ensures that
    all runs for the backfill are in a terminal state before indicating that the backfill can be marked
    CANCELED.
    Yields a boolean indicating the backfill can be considered canceled (ie all runs are canceled).
    """
    if not instance.run_coordinator:
        check.failed("The instance must have a run coordinator in order to cancel runs")

    # Query for cancelable runs, enforcing a limit on the number of runs to cancel in an iteration
    # as canceling runs incurs cost
    runs_to_cancel_in_iteration = instance.run_storage.get_run_ids(
        filters=RunsFilter(
            statuses=CANCELABLE_RUN_STATUSES,
            tags={
                BACKFILL_ID_TAG: backfill_id,
            },
        ),
        limit=MAX_RUNS_CANCELED_PER_ITERATION,
    )

    yield None

    if runs_to_cancel_in_iteration:
        # since we are canceling some runs in this iteration, we know that there is more work to do.
        # Either cancelling more runs, or waiting for the canceled runs to get to a terminal state
        work_done = False
        for run_id in runs_to_cancel_in_iteration:
            instance.run_coordinator.cancel_run(run_id)
            yield None
    else:
        # If there are no runs to cancel, check if there are any runs still in progress. If there are,
        # then we want to wait for them to reach a terminal state before the backfill is marked CANCELED.
        run_waiting_to_cancel = instance.get_run_ids(
            RunsFilter(
                tags={BACKFILL_ID_TAG: backfill_id},
                statuses=NOT_FINISHED_STATUSES,
            ),
            limit=1,
        )
        work_done = len(run_waiting_to_cancel) == 0

    yield work_done
