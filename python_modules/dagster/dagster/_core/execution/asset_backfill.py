import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import (
    build_run_requests,
    build_run_requests_with_backfill_policies,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partition_mapping import IdentityPartitionMapping
from dagster._core.definitions.remote_asset_graph import RemoteAssetGraph
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import PartitionsByAssetSelector
from dagster._core.definitions.time_window_partition_mapping import TimeWindowPartitionMapping
from dagster._core.definitions.time_window_partitions import (
    DatetimeFieldSerializer,
    TimeWindowPartitionsSubset,
)
from dagster._core.errors import (
    DagsterAssetBackfillDataLoadError,
    DagsterBackfillFailedError,
    DagsterDefinitionChangedDeserializationError,
    DagsterInvariantViolationError,
)
from dagster._core.event_api import EventRecordsFilter
from dagster._core.events import DagsterEventType
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.dagster_run import (
    CANCELABLE_RUN_STATUSES,
    IN_PROGRESS_RUN_STATUSES,
    DagsterRunStatus,
    RunsFilter,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.workspace.context import (
    BaseWorkspaceRequestContext,
    IWorkspaceProcessContext,
)
from dagster._core.workspace.workspace import IWorkspace
from dagster._serdes import whitelist_for_serdes
from dagster._utils import utc_datetime_from_timestamp
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .submit_asset_runs import submit_asset_runs_in_chunks

if TYPE_CHECKING:
    from .backfill import PartitionBackfill

RUN_CHUNK_SIZE = 25


MAX_RUNS_CANCELED_PER_ITERATION = 50


class AssetBackfillStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    MATERIALIZED = "MATERIALIZED"
    FAILED = "FAILED"


class PartitionedAssetBackfillStatus(
    NamedTuple(
        "_PartitionedAssetBackfillStatus",
        [
            ("asset_key", AssetKey),
            ("num_targeted_partitions", int),
            ("partitions_counts_by_status", Mapping[AssetBackfillStatus, int]),
        ],
    )
):
    def __new__(
        cls,
        asset_key: AssetKey,
        num_targeted_partitions: int,
        partitions_counts_by_status: Mapping[AssetBackfillStatus, int],
    ):
        return super(PartitionedAssetBackfillStatus, cls).__new__(
            cls,
            check.inst_param(asset_key, "asset_key", AssetKey),
            check.int_param(num_targeted_partitions, "num_targeted_partitions"),
            check.mapping_param(
                partitions_counts_by_status,
                "partitions_counts_by_status",
                key_type=AssetBackfillStatus,
                value_type=int,
            ),
        )


class UnpartitionedAssetBackfillStatus(
    NamedTuple(
        "_UnpartitionedAssetBackfillStatus",
        [("asset_key", AssetKey), ("backfill_status", Optional[AssetBackfillStatus])],
    )
):
    def __new__(cls, asset_key: AssetKey, asset_backfill_status: Optional[AssetBackfillStatus]):
        return super(UnpartitionedAssetBackfillStatus, cls).__new__(
            cls,
            check.inst_param(asset_key, "asset_key", AssetKey),
            check.opt_inst_param(
                asset_backfill_status, "asset_backfill_status", AssetBackfillStatus
            ),
        )


@whitelist_for_serdes(field_serializers={"backfill_start_time": DatetimeFieldSerializer})
class AssetBackfillData(NamedTuple):
    """Has custom serialization instead of standard Dagster NamedTuple serialization because the
    asset graph is required to build the AssetGraphSubset objects.
    """

    target_subset: AssetGraphSubset
    requested_runs_for_target_roots: bool
    latest_storage_id: Optional[int]
    materialized_subset: AssetGraphSubset
    requested_subset: AssetGraphSubset
    failed_and_downstream_subset: AssetGraphSubset
    backfill_start_time: datetime

    def replace_requested_subset(self, requested_subset: AssetGraphSubset) -> "AssetBackfillData":
        return AssetBackfillData(
            target_subset=self.target_subset,
            latest_storage_id=self.latest_storage_id,
            requested_runs_for_target_roots=self.requested_runs_for_target_roots,
            materialized_subset=self.materialized_subset,
            failed_and_downstream_subset=self.failed_and_downstream_subset,
            requested_subset=requested_subset,
            backfill_start_time=self.backfill_start_time,
        )

    def with_latest_storage_id(self, latest_storage_id: Optional[int]) -> "AssetBackfillData":
        return self._replace(
            latest_storage_id=latest_storage_id,
        )

    def is_complete(self) -> bool:
        """The asset backfill is complete when all runs to be requested have finished (success,
        failure, or cancellation). Since the AssetBackfillData object stores materialization states
        per asset partition, the daemon continues to update the backfill data until all runs have
        finished in order to display the final partition statuses in the UI.
        """
        return (
            (
                self.materialized_subset | self.failed_and_downstream_subset
            ).num_partitions_and_non_partitioned_assets
            == self.target_subset.num_partitions_and_non_partitioned_assets
        )

    def all_requested_partitions_marked_as_materialized_or_failed(self) -> bool:
        for partition in self.requested_subset.iterate_asset_partitions():
            if (
                partition not in self.materialized_subset
                and partition not in self.failed_and_downstream_subset
            ):
                return False

        return True

    def get_target_root_asset_partitions(
        self, instance_queryer: CachingInstanceQueryer
    ) -> Iterable[AssetKeyPartitionKey]:
        def _get_self_and_downstream_targeted_subset(
            initial_subset: AssetGraphSubset,
        ) -> AssetGraphSubset:
            self_and_downstream = initial_subset
            for asset_key in initial_subset.asset_keys:
                self_and_downstream = self_and_downstream | (
                    instance_queryer.asset_graph.bfs_filter_subsets(
                        instance_queryer,
                        lambda asset_key, _: asset_key in self.target_subset,
                        initial_subset.filter_asset_keys({asset_key}),
                        current_time=instance_queryer.evaluation_time,
                    )
                    & self.target_subset
                )
            return self_and_downstream

        assets_with_no_parents_in_target_subset = {
            asset_key
            for asset_key in self.target_subset.asset_keys
            if all(
                parent not in self.target_subset.asset_keys
                for parent in instance_queryer.asset_graph.get(asset_key).parent_keys
                - {asset_key}  # Do not include an asset as its own parent
            )
        }

        # The partitions that do not have any parents in the target subset
        root_subset = self.target_subset.filter_asset_keys(assets_with_no_parents_in_target_subset)

        # Partitions in root_subset and their downstreams within the target subset
        root_and_downstream_partitions = _get_self_and_downstream_targeted_subset(root_subset)

        # The result of the root_and_downstream_partitions on the previous iteration, used to
        # determine when no new partitions are targeted so we can early exit
        previous_root_and_downstream_partitions = None

        while (
            root_and_downstream_partitions != self.target_subset
            and root_and_downstream_partitions
            != previous_root_and_downstream_partitions  # Check against previous iteration result to exit if no new partitions are targeted
        ):
            # Find the asset graph subset is not yet targeted by the backfill
            unreachable_targets = self.target_subset - root_and_downstream_partitions

            # Find the root assets of the unreachable targets. Any targeted partition in these
            # assets becomes part of the root subset
            unreachable_target_root_subset = unreachable_targets.filter_asset_keys(
                AssetSelection.keys(*unreachable_targets.asset_keys)
                .sources()
                .resolve(instance_queryer.asset_graph)
            )
            root_subset = root_subset | unreachable_target_root_subset

            # Track the previous value of root_and_downstream_partitions.
            # If the values are the same, we know no new partitions have been targeted.
            previous_root_and_downstream_partitions = root_and_downstream_partitions

            # Update root_and_downstream_partitions to include downstreams of the new root subset
            root_and_downstream_partitions = (
                root_and_downstream_partitions
                | _get_self_and_downstream_targeted_subset(unreachable_target_root_subset)
            )

        if root_and_downstream_partitions == previous_root_and_downstream_partitions:
            raise DagsterInvariantViolationError(
                "Unable to determine root partitions for backfill. The following asset partitions"
                " are not targeted:"
                f" \n\n{list((self.target_subset - root_and_downstream_partitions).iterate_asset_partitions())} \n\n"
                " This is likely a system error. Please report this issue to the Dagster team."
            )

        return list(root_subset.iterate_asset_partitions())

    def get_target_partitions_subset(self, asset_key: AssetKey) -> PartitionsSubset:
        # Return the targeted partitions for the root partitioned asset keys
        return self.target_subset.get_partitions_subset(asset_key)

    def get_target_root_partitions_subset(
        self, asset_graph: BaseAssetGraph
    ) -> Optional[PartitionsSubset]:
        """Returns the most upstream partitions subset that was targeted by the backfill."""
        target_partitioned_asset_keys = {
            asset_key for asset_key in self.target_subset.partitions_subsets_by_asset_key
        }

        root_partitioned_asset_keys = (
            AssetSelection.keys(*target_partitioned_asset_keys).sources().resolve(asset_graph)
        )

        # Return the targeted partitions for the root partitioned asset keys
        if root_partitioned_asset_keys:
            return self.target_subset.get_partitions_subset(next(iter(root_partitioned_asset_keys)))

        return None

    def get_num_partitions(self) -> Optional[int]:
        """Only valid when the same number of partitions are targeted in every asset.

        When not valid, returns None.
        """
        asset_partition_nums = {
            len(subset) for subset in self.target_subset.partitions_subsets_by_asset_key.values()
        }
        if len(asset_partition_nums) == 0:
            return 0
        elif len(asset_partition_nums) == 1:
            return next(iter(asset_partition_nums))
        else:
            return None

    def get_targeted_asset_keys_topological_order(
        self, asset_graph: BaseAssetGraph
    ) -> Sequence[AssetKey]:
        """Returns a topological ordering of asset keys targeted by the backfill
        that exist in the asset graph.

        Orders keys in the same topological level alphabetically.
        """
        return [k for k in asset_graph.toposorted_asset_keys if k in self.target_subset.asset_keys]

    def get_backfill_status_per_asset_key(
        self, asset_graph: BaseAssetGraph
    ) -> Sequence[Union[PartitionedAssetBackfillStatus, UnpartitionedAssetBackfillStatus]]:
        """Returns a list containing each targeted asset key's backfill status.
        This list orders assets topologically and only contains statuses for assets that are
        currently existent in the asset graph.
        """

        def _get_status_for_asset_key(
            asset_key: AssetKey,
        ) -> Union[PartitionedAssetBackfillStatus, UnpartitionedAssetBackfillStatus]:
            if asset_graph.get(asset_key).is_partitioned:
                materialized_subset = self.materialized_subset.get_partitions_subset(
                    asset_key, asset_graph
                )
                failed_subset = self.failed_and_downstream_subset.get_partitions_subset(
                    asset_key, asset_graph
                )
                requested_subset = self.requested_subset.get_partitions_subset(
                    asset_key, asset_graph
                )

                # The failed subset includes partitions that failed and their downstream partitions.
                # The downstream partitions are not included in the requested subset, so we determine
                # the in progress subset by subtracting partitions that are failed and requested.
                requested_and_failed_subset = failed_subset & requested_subset
                in_progress_subset = requested_subset - (
                    requested_and_failed_subset | materialized_subset
                )

                return PartitionedAssetBackfillStatus(
                    asset_key,
                    len(self.target_subset.get_partitions_subset(asset_key, asset_graph)),
                    {
                        AssetBackfillStatus.MATERIALIZED: len(materialized_subset),
                        AssetBackfillStatus.FAILED: len(failed_subset - materialized_subset),
                        AssetBackfillStatus.IN_PROGRESS: len(in_progress_subset),
                    },
                )
            else:
                failed = bool(
                    asset_key in self.failed_and_downstream_subset.non_partitioned_asset_keys
                )
                materialized = bool(
                    asset_key in self.materialized_subset.non_partitioned_asset_keys
                )
                in_progress = bool(asset_key in self.requested_subset.non_partitioned_asset_keys)

                if failed:
                    return UnpartitionedAssetBackfillStatus(asset_key, AssetBackfillStatus.FAILED)
                if materialized:
                    return UnpartitionedAssetBackfillStatus(
                        asset_key, AssetBackfillStatus.MATERIALIZED
                    )
                if in_progress:
                    return UnpartitionedAssetBackfillStatus(
                        asset_key, AssetBackfillStatus.IN_PROGRESS
                    )
                return UnpartitionedAssetBackfillStatus(asset_key, None)

        # Only return back statuses for the assets that still exist in the workspace
        topological_order = self.get_targeted_asset_keys_topological_order(asset_graph)
        return [_get_status_for_asset_key(asset_key) for asset_key in topological_order]

    def get_partition_names(self) -> Optional[Sequence[str]]:
        """Only valid when the same number of partitions are targeted in every asset.

        When not valid, returns None.
        """
        subsets = self.target_subset.partitions_subsets_by_asset_key.values()
        if len(subsets) == 0:
            return []

        first_subset = next(iter(subsets))
        if any(subset != first_subset for subset in subsets):
            return None

        return list(first_subset.get_partition_keys())

    @classmethod
    def empty(
        cls,
        target_subset: AssetGraphSubset,
        backfill_start_time: datetime,
        dynamic_partitions_store: DynamicPartitionsStore,
    ) -> "AssetBackfillData":
        return cls(
            target_subset=target_subset,
            requested_runs_for_target_roots=False,
            requested_subset=AssetGraphSubset(),
            materialized_subset=AssetGraphSubset(),
            failed_and_downstream_subset=AssetGraphSubset(),
            latest_storage_id=None,
            backfill_start_time=backfill_start_time,
        )

    @classmethod
    def is_valid_serialization(cls, serialized: str, asset_graph: BaseAssetGraph) -> bool:
        storage_dict = json.loads(serialized)
        return AssetGraphSubset.can_deserialize(
            storage_dict["serialized_target_subset"], asset_graph
        )

    @classmethod
    def from_serialized(
        cls, serialized: str, asset_graph: BaseAssetGraph, backfill_start_timestamp: float
    ) -> "AssetBackfillData":
        storage_dict = json.loads(serialized)

        return cls(
            target_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_target_subset"], asset_graph
            ),
            requested_runs_for_target_roots=storage_dict["requested_runs_for_target_roots"],
            requested_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_requested_subset"], asset_graph
            ),
            materialized_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_materialized_subset"], asset_graph
            ),
            failed_and_downstream_subset=AssetGraphSubset.from_storage_dict(
                storage_dict["serialized_failed_subset"], asset_graph
            ),
            latest_storage_id=storage_dict["latest_storage_id"],
            backfill_start_time=utc_datetime_from_timestamp(backfill_start_timestamp),
        )

    @classmethod
    def from_partitions_by_assets(
        cls,
        asset_graph: BaseAssetGraph,
        dynamic_partitions_store: DynamicPartitionsStore,
        backfill_start_time: datetime,
        partitions_by_assets: Sequence[PartitionsByAssetSelector],
    ) -> "AssetBackfillData":
        """Create an AssetBackfillData object from a list of PartitionsByAssetSelector objects.
        Accepts a list of asset partitions selections, used to determine the target partitions to backfill.
        For targeted assets, if partitioned and no partitions selections are provided, targets all partitions.
        """
        check.sequence_param(partitions_by_assets, "partitions_by_asset", PartitionsByAssetSelector)

        non_partitioned_asset_keys = set()
        partitions_subsets_by_asset_key = dict()
        for partitions_by_asset_selector in partitions_by_assets:
            asset_key = partitions_by_asset_selector.asset_key
            partitions = partitions_by_asset_selector.partitions
            partition_def = asset_graph.get(asset_key).partitions_def
            if partitions and partition_def:
                if partitions.partition_range:
                    # a range of partitions is selected
                    partition_keys_in_range = partition_def.get_partition_keys_in_range(
                        partition_key_range=PartitionKeyRange(
                            start=partitions.partition_range.start,
                            end=partitions.partition_range.end,
                        ),
                        dynamic_partitions_store=dynamic_partitions_store,
                    )
                    partition_subset_in_range = partition_def.subset_with_partition_keys(
                        partition_keys_in_range
                    )
                    partitions_subsets_by_asset_key.update({asset_key: partition_subset_in_range})
                else:
                    raise DagsterBackfillFailedError(
                        "partitions_by_asset_selector does not have a partition range selected"
                    )
            elif partition_def:
                # no partitions selected for partitioned asset, we will select all partitions
                all_partitions = partition_def.subset_with_all_partitions()
                partitions_subsets_by_asset_key.update({asset_key: all_partitions})
            else:
                # asset is not partitioned
                non_partitioned_asset_keys.add(asset_key)

        target_subset = AssetGraphSubset(
            partitions_subsets_by_asset_key=partitions_subsets_by_asset_key,
            non_partitioned_asset_keys=non_partitioned_asset_keys,
        )
        return cls.empty(target_subset, backfill_start_time, dynamic_partitions_store)

    @classmethod
    def from_asset_partitions(
        cls,
        asset_graph: BaseAssetGraph,
        partition_names: Optional[Sequence[str]],
        asset_selection: Sequence[AssetKey],
        dynamic_partitions_store: DynamicPartitionsStore,
        backfill_start_time: datetime,
        all_partitions: bool,
    ) -> "AssetBackfillData":
        check.invariant(
            partition_names is None or all_partitions is False,
            "Can't provide both a set of partitions and all_partitions=True",
        )

        if all_partitions:
            target_subset = AssetGraphSubset.from_asset_keys(
                asset_selection, asset_graph, dynamic_partitions_store, backfill_start_time
            )
        elif partition_names is not None:
            partitioned_asset_keys = {
                asset_key
                for asset_key in asset_selection
                if asset_graph.get(asset_key).is_partitioned
            }

            root_partitioned_asset_keys = (
                AssetSelection.keys(*partitioned_asset_keys).sources().resolve(asset_graph)
            )
            root_partitions_defs = {
                asset_graph.get(asset_key).partitions_def
                for asset_key in root_partitioned_asset_keys
            }
            if len(root_partitions_defs) > 1:
                raise DagsterBackfillFailedError(
                    "All the assets at the root of the backfill must have the same"
                    " PartitionsDefinition"
                )

            root_partitions_def = next(iter(root_partitions_defs))
            if not root_partitions_def:
                raise DagsterBackfillFailedError(
                    "If assets within the backfill have different partitionings, then root assets"
                    " must be partitioned"
                )

            root_partitions_subset = root_partitions_def.subset_with_partition_keys(partition_names)
            target_subset = AssetGraphSubset(
                non_partitioned_asset_keys=set(asset_selection) - partitioned_asset_keys,
            )
            for root_asset_key in root_partitioned_asset_keys:
                target_subset |= asset_graph.bfs_filter_subsets(
                    dynamic_partitions_store,
                    lambda asset_key, _: asset_key in partitioned_asset_keys,
                    AssetGraphSubset(
                        partitions_subsets_by_asset_key={root_asset_key: root_partitions_subset},
                    ),
                    current_time=backfill_start_time,
                )
        else:
            check.failed("Either partition_names must not be None or all_partitions must be True")

        return cls.empty(target_subset, backfill_start_time, dynamic_partitions_store)

    def serialize(
        self, dynamic_partitions_store: DynamicPartitionsStore, asset_graph: BaseAssetGraph
    ) -> str:
        storage_dict = {
            "requested_runs_for_target_roots": self.requested_runs_for_target_roots,
            "serialized_target_subset": self.target_subset.to_storage_dict(
                dynamic_partitions_store=dynamic_partitions_store, asset_graph=asset_graph
            ),
            "latest_storage_id": self.latest_storage_id,
            "serialized_requested_subset": self.requested_subset.to_storage_dict(
                dynamic_partitions_store=dynamic_partitions_store, asset_graph=asset_graph
            ),
            "serialized_materialized_subset": self.materialized_subset.to_storage_dict(
                dynamic_partitions_store=dynamic_partitions_store, asset_graph=asset_graph
            ),
            "serialized_failed_subset": self.failed_and_downstream_subset.to_storage_dict(
                dynamic_partitions_store=dynamic_partitions_store, asset_graph=asset_graph
            ),
        }
        return json.dumps(storage_dict)


def create_asset_backfill_data_from_asset_partitions(
    asset_graph: RemoteAssetGraph,
    asset_selection: Sequence[AssetKey],
    partition_names: Sequence[str],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> AssetBackfillData:
    backfill_timestamp = pendulum.now("UTC").timestamp()
    return AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=partition_names,
        asset_selection=asset_selection,
        dynamic_partitions_store=dynamic_partitions_store,
        all_partitions=False,
        backfill_start_time=utc_datetime_from_timestamp(backfill_timestamp),
    )


def _get_unloadable_location_names(context: IWorkspace, logger: logging.Logger) -> Sequence[str]:
    location_entries_by_name = {
        location_entry.origin.location_name: location_entry
        for location_entry in context.get_workspace_snapshot().values()
    }
    unloadable_location_names = []

    for location_name, location_entry in location_entries_by_name.items():
        if location_entry.load_error:
            logger.warning(
                f"Failure loading location {location_name} due to error:"
                f" {location_entry.load_error}"
            )
            unloadable_location_names.append(location_name)

    return unloadable_location_names


class AssetBackfillIterationResult(NamedTuple):
    run_requests: Sequence[RunRequest]
    backfill_data: AssetBackfillData


def _get_requested_asset_partitions_from_run_requests(
    run_requests: Sequence[RunRequest],
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
) -> AbstractSet[AssetKeyPartitionKey]:
    requested_partitions = set()
    for run_request in run_requests:
        # Run request targets a range of partitions
        range_start = run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG)
        range_end = run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG)
        if range_start and range_end:
            # When a run request targets a range of partitions, each asset is expected to
            # have the same partitions def
            selected_assets = cast(Sequence[AssetKey], run_request.asset_selection)
            check.invariant(len(selected_assets) > 0)
            partitions_defs = set(
                asset_graph.get(asset_key).partitions_def for asset_key in selected_assets
            )
            check.invariant(
                len(partitions_defs) == 1,
                "Expected all assets selected in partition range run request to have the same"
                " partitions def",
            )

            partitions_def = cast(PartitionsDefinition, next(iter(partitions_defs)))
            partitions_in_range = partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(range_start, range_end), instance_queryer
            )
            requested_partitions = requested_partitions | {
                AssetKeyPartitionKey(asset_key, partition_key)
                for asset_key in selected_assets
                for partition_key in partitions_in_range
            }
        else:
            requested_partitions = requested_partitions | {
                AssetKeyPartitionKey(asset_key, run_request.partition_key)
                for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
            }

    return requested_partitions


def _submit_runs_and_update_backfill_in_chunks(
    instance: DagsterInstance,
    workspace_process_context: IWorkspaceProcessContext,
    backfill_id: str,
    asset_backfill_iteration_result: AssetBackfillIterationResult,
    previous_asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    logger: logging.Logger,
) -> Iterable[Optional[AssetBackfillData]]:
    from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill

    run_requests = asset_backfill_iteration_result.run_requests
    submitted_partitions = previous_asset_backfill_data.requested_subset

    # Initially, the only requested partitions are the partitions requested during the last
    # backfill iteration
    backfill_data_with_submitted_runs = (
        asset_backfill_iteration_result.backfill_data.replace_requested_subset(submitted_partitions)
    )

    # Fetch backfill status
    backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
    mid_iteration_cancel_requested = backfill.status != BulkActionStatus.REQUESTED
    retryable_error_raised = False

    # Iterate through runs to request, submitting runs in chunks.
    # In between each chunk, check that the backfill is still marked as 'requested',
    # to ensure that no more runs are requested if the backfill is marked as canceled/canceling.
    for submit_run_request_chunk_result in submit_asset_runs_in_chunks(
        run_requests=run_requests,
        reserved_run_ids=None,
        chunk_size=RUN_CHUNK_SIZE,
        instance=instance,
        workspace_process_context=workspace_process_context,
        asset_graph=asset_graph,
        logger=logger,
        debug_crash_flags={},
        backfill_id=backfill_id,
    ):
        if submit_run_request_chunk_result is None:
            # allow the daemon to heartbeat
            yield None
            continue

        retryable_error_raised = submit_run_request_chunk_result.retryable_error_raised

        requested_partitions_in_chunk = _get_requested_asset_partitions_from_run_requests(
            [rr for (rr, _) in submit_run_request_chunk_result.chunk_submitted_runs],
            asset_graph,
            instance_queryer,
        )
        submitted_partitions = submitted_partitions | AssetGraphSubset.from_asset_partition_set(
            set(requested_partitions_in_chunk), asset_graph=asset_graph
        )

        # AssetBackfillIterationResult contains the requested subset after all runs are submitted.
        # Replace this value with just the partitions that have been submitted so far.
        backfill_data_with_submitted_runs = (
            asset_backfill_iteration_result.backfill_data.replace_requested_subset(
                submitted_partitions
            )
        )
        if retryable_error_raised:
            # Code server became unavailable mid-backfill. Rewind the cursor back to the cursor
            # from the previous iteration, to allow next iteration to reevaluate the same
            # events.
            backfill_data_with_submitted_runs = (
                backfill_data_with_submitted_runs.with_latest_storage_id(
                    previous_asset_backfill_data.latest_storage_id
                )
            )

        # Refetch, in case the backfill was requested for cancellation in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
        updated_backfill = backfill.with_asset_backfill_data(
            backfill_data_with_submitted_runs,
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        )
        instance.update_backfill(updated_backfill)

        # Refetch backfill status
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill_id))
        if backfill.status != BulkActionStatus.REQUESTED:
            mid_iteration_cancel_requested = True
            break

    if not mid_iteration_cancel_requested and not retryable_error_raised:
        if submitted_partitions != asset_backfill_iteration_result.backfill_data.requested_subset:
            missing_partitions = list(
                (
                    asset_backfill_iteration_result.backfill_data.requested_subset
                    - submitted_partitions
                ).iterate_asset_partitions()
            )
            check.failed(
                "Did not submit run requests for all expected partitions. \n\nPartitions not"
                f" submitted: {missing_partitions}",
            )

    yield backfill_data_with_submitted_runs


def _check_target_partitions_subset_is_valid(
    asset_key: AssetKey,
    asset_graph: BaseAssetGraph,
    target_partitions_subset: Optional[PartitionsSubset],
    instance_queryer: CachingInstanceQueryer,
) -> None:
    """Checks for any partitions definition changes since backfill launch that should mark
    the backfill as failed.
    """
    if asset_key not in asset_graph.all_asset_keys:
        raise DagsterDefinitionChangedDeserializationError(
            f"Asset {asset_key} existed at storage-time, but no longer does"
        )

    partitions_def = asset_graph.get(asset_key).partitions_def

    if target_partitions_subset:  # Asset was partitioned at storage time
        if partitions_def is None:
            raise DagsterDefinitionChangedDeserializationError(
                f"Asset {asset_key} had a PartitionsDefinition at storage-time, but no longer"
                " does"
            )

        # If the asset was time-partitioned at storage time but the time partitions def
        # has changed, mark the backfill as failed
        if isinstance(
            target_partitions_subset, TimeWindowPartitionsSubset
        ) and target_partitions_subset.partitions_def.get_serializable_unique_identifier(
            instance_queryer
        ) != partitions_def.get_serializable_unique_identifier(instance_queryer):
            raise DagsterDefinitionChangedDeserializationError(
                f"This partitions definition for asset {asset_key} has changed since this backfill"
                " was stored. Changing the partitions definition for a time-partitioned "
                "asset during a backfill is not supported."
            )

        else:
            # Check that all target partitions still exist. If so, the backfill can continue.a
            existent_partitions_subset = (
                partitions_def.subset_with_all_partitions(
                    current_time=instance_queryer.evaluation_time,
                    dynamic_partitions_store=instance_queryer,
                )
                & target_partitions_subset
            )
            removed_partitions_subset = target_partitions_subset - existent_partitions_subset
            if len(removed_partitions_subset) > 0:
                raise DagsterDefinitionChangedDeserializationError(
                    f"Targeted partitions for asset {asset_key} have been removed since this backfill was stored. "
                    f"The following partitions were removed: {removed_partitions_subset.get_partition_keys()}"
                )

    else:  # Asset unpartitioned at storage time
        if partitions_def is not None:
            raise DagsterDefinitionChangedDeserializationError(
                f"Asset {asset_key} was not partitioned at storage-time, but is now"
            )


def _check_validity_and_deserialize_asset_backfill_data(
    workspace_context: BaseWorkspaceRequestContext,
    backfill: "PartitionBackfill",
    asset_graph: BaseAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    logger: logging.Logger,
) -> Optional[AssetBackfillData]:
    """Attempts to deserialize asset backfill data. If the asset backfill data is valid,
    returns the deserialized data, else returns None.
    """
    unloadable_locations = _get_unloadable_location_names(workspace_context, logger)

    try:
        asset_backfill_data = backfill.get_asset_backfill_data(asset_graph)
        for asset_key in asset_backfill_data.target_subset.asset_keys:
            _check_target_partitions_subset_is_valid(
                asset_key,
                asset_graph,
                asset_backfill_data.target_subset.get_partitions_subset(asset_key)
                if asset_key in asset_backfill_data.target_subset.partitions_subsets_by_asset_key
                else None,
                instance_queryer,
            )
    except DagsterDefinitionChangedDeserializationError as ex:
        unloadable_locations_error = (
            "This could be because it's inside a code location that's failing to load:"
            f" {unloadable_locations}"
            if unloadable_locations
            else ""
        )
        if (
            os.environ.get("DAGSTER_BACKFILL_RETRY_DEFINITION_CHANGED_ERROR")
            and unloadable_locations
        ):
            logger.warning(
                f"Backfill {backfill.backfill_id} was unable to continue due to a missing asset or"
                " partition in the asset graph. The backfill will resume once it is available"
                f" again.\n{ex}. {unloadable_locations_error}"
            )
            return None
        else:
            raise DagsterAssetBackfillDataLoadError(f"{ex}. {unloadable_locations_error}")

    return asset_backfill_data


def execute_asset_backfill_iteration(
    backfill: "PartitionBackfill",
    logger: logging.Logger,
    workspace_process_context: IWorkspaceProcessContext,
    instance: DagsterInstance,
) -> Iterable[None]:
    """Runs an iteration of the backfill, including submitting runs and updating the backfill object
    in the DB.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    from dagster._core.execution.backfill import BulkActionStatus, PartitionBackfill

    logger.info(f"Evaluating asset backfill {backfill.backfill_id}")

    workspace_context = workspace_process_context.create_request_context()
    asset_graph = workspace_context.asset_graph

    if not backfill.is_asset_backfill:
        check.failed("Backfill must be an asset backfill")

    backfill_start_time = pendulum.from_timestamp(backfill.backfill_timestamp, "UTC")
    instance_queryer = CachingInstanceQueryer(
        instance=instance, asset_graph=asset_graph, evaluation_time=backfill_start_time
    )

    previous_asset_backfill_data = _check_validity_and_deserialize_asset_backfill_data(
        workspace_context, backfill, asset_graph, instance_queryer, logger
    )
    if previous_asset_backfill_data is None:
        return

    logger.info(
        f"Targets for asset backfill {backfill.backfill_id} are valid. Continuing execution with current status: {backfill.status}."
    )

    if backfill.status == BulkActionStatus.REQUESTED:
        result = None
        for result in execute_asset_backfill_iteration_inner(
            backfill_id=backfill.backfill_id,
            asset_backfill_data=previous_asset_backfill_data,
            instance_queryer=instance_queryer,
            asset_graph=asset_graph,
            run_tags=backfill.tags,
            backfill_start_time=backfill_start_time,
        ):
            yield None

        if not isinstance(result, AssetBackfillIterationResult):
            check.failed(
                "Expected execute_asset_backfill_iteration_inner to return an"
                " AssetBackfillIterationResult"
            )

        updated_asset_backfill_data = result.backfill_data

        if result.run_requests:
            for updated_asset_backfill_data in _submit_runs_and_update_backfill_in_chunks(
                instance,
                workspace_process_context,
                backfill.backfill_id,
                result,
                previous_asset_backfill_data,
                asset_graph,
                instance_queryer,
                logger,
            ):
                yield None

            if not isinstance(updated_asset_backfill_data, AssetBackfillData):
                check.failed(
                    "Expected _submit_runs_and_update_backfill_in_chunks to return an"
                    " AssetBackfillData object"
                )

        # Update the backfill with new asset backfill data
        # Refetch, in case the backfill was canceled in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill.backfill_id))
        updated_backfill = backfill.with_asset_backfill_data(
            updated_asset_backfill_data,
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        )
        if updated_asset_backfill_data.is_complete():
            # The asset backfill is complete when all runs to be requested have finished (success,
            # failure, or cancellation). Since the AssetBackfillData object stores materialization states
            # per asset partition, the daemon continues to update the backfill data until all runs have
            # finished in order to display the final partition statuses in the UI.
            updated_backfill = updated_backfill.with_status(BulkActionStatus.COMPLETED)

        instance.update_backfill(updated_backfill)
        logger.info(
            f"Asset backfill {backfill.backfill_id} completed iteration with status {updated_backfill.status}."
        )
        logger.info(
            f"Updated asset backfill data for {backfill.backfill_id}: {updated_asset_backfill_data}"
        )

    elif backfill.status == BulkActionStatus.CANCELING:
        if not instance.run_coordinator:
            check.failed("The instance must have a run coordinator in order to cancel runs")

        # Query for cancelable runs, enforcing a limit on the number of runs to cancel in an iteration
        # as canceling runs incurs cost
        runs_to_cancel_in_iteration = instance.run_storage.get_run_ids(
            filters=RunsFilter(
                statuses=CANCELABLE_RUN_STATUSES,
                tags={
                    BACKFILL_ID_TAG: backfill.backfill_id,
                },
            ),
            limit=MAX_RUNS_CANCELED_PER_ITERATION,
        )

        yield None

        if runs_to_cancel_in_iteration:
            for run_id in runs_to_cancel_in_iteration:
                instance.run_coordinator.cancel_run(run_id)
                yield None

        # Update the asset backfill data to contain the newly materialized/failed partitions.
        updated_asset_backfill_data = None
        for updated_asset_backfill_data in get_canceling_asset_backfill_iteration_data(
            backfill.backfill_id,
            previous_asset_backfill_data,
            instance_queryer,
            asset_graph,
            backfill_start_time,
        ):
            yield None

        if not isinstance(updated_asset_backfill_data, AssetBackfillData):
            check.failed(
                "Expected get_canceling_asset_backfill_iteration_data to return a PartitionBackfill"
            )

        # Refetch, in case the backfill was forcibly marked as canceled in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill.backfill_id))
        updated_backfill = backfill.with_asset_backfill_data(
            updated_asset_backfill_data,
            dynamic_partitions_store=instance,
            asset_graph=asset_graph,
        )
        # The asset backfill is successfully canceled when all requested runs have finished (success,
        # failure, or cancellation). Since the AssetBackfillData object stores materialization states
        # per asset partition, the daemon continues to update the backfill data until all runs have
        # finished in order to display the final partition statuses in the UI.
        all_partitions_marked_completed = (
            updated_asset_backfill_data.all_requested_partitions_marked_as_materialized_or_failed()
        )
        if all_partitions_marked_completed:
            updated_backfill = updated_backfill.with_status(BulkActionStatus.CANCELED)

        instance.update_backfill(updated_backfill)

        if len(runs_to_cancel_in_iteration) == 0 and not all_partitions_marked_completed:
            in_progress_run_ids = instance.get_run_ids(
                RunsFilter(
                    tags={BACKFILL_ID_TAG: backfill.backfill_id}, statuses=IN_PROGRESS_RUN_STATUSES
                )
            )
            if len(in_progress_run_ids) == 0:
                check.failed(
                    "All runs have completed, but not all requested partitions have been marked as materialized or failed. "
                    "This is likely a system error. Please report this issue to the Dagster team."
                )

        logger.info(
            f"Asset backfill {backfill.backfill_id} completed cancellation iteration with status {updated_backfill.status}."
        )
        logger.debug(
            f"Updated asset backfill data after cancellation iteration: {updated_asset_backfill_data}"
        )
    elif backfill.status == BulkActionStatus.CANCELING:
        # The backfill was forcibly canceled, skip iteration
        pass
    else:
        check.failed(f"Unexpected backfill status: {backfill.status}")


def get_canceling_asset_backfill_iteration_data(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    instance_queryer: CachingInstanceQueryer,
    asset_graph: RemoteAssetGraph,
    backfill_start_time: datetime,
) -> Iterable[Optional[AssetBackfillData]]:
    """For asset backfills in the "canceling" state, fetch the asset backfill data with the updated
    materialized and failed subsets.
    """
    updated_materialized_subset = None
    for updated_materialized_subset in get_asset_backfill_iteration_materialized_partitions(
        backfill_id, asset_backfill_data, asset_graph, instance_queryer
    ):
        yield None

    if not isinstance(updated_materialized_subset, AssetGraphSubset):
        check.failed(
            "Expected get_asset_backfill_iteration_materialized_partitions to return an"
            " AssetGraphSubset object"
        )

    failed_subset = AssetGraphSubset.from_asset_partition_set(
        set(_get_failed_asset_partitions(instance_queryer, backfill_id, asset_graph)), asset_graph
    )
    updated_backfill_data = AssetBackfillData(
        target_subset=asset_backfill_data.target_subset,
        latest_storage_id=asset_backfill_data.latest_storage_id,
        requested_runs_for_target_roots=asset_backfill_data.requested_runs_for_target_roots,
        materialized_subset=updated_materialized_subset,
        failed_and_downstream_subset=asset_backfill_data.failed_and_downstream_subset
        | failed_subset,
        requested_subset=asset_backfill_data.requested_subset,
        backfill_start_time=backfill_start_time,
    )

    yield updated_backfill_data


def get_asset_backfill_iteration_materialized_partitions(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
) -> Iterable[Optional[AssetGraphSubset]]:
    """Returns the partitions that have been materialized by the backfill.

    This function is a generator so we can return control to the daemon and let it heartbeat
    during expensive operations.
    """
    recently_materialized_asset_partitions = AssetGraphSubset()
    for asset_key in asset_backfill_data.target_subset.asset_keys:
        records = instance_queryer.instance.get_event_records(
            EventRecordsFilter(
                event_type=DagsterEventType.ASSET_MATERIALIZATION,
                asset_key=asset_key,
                after_cursor=asset_backfill_data.latest_storage_id,
            )
        )
        records_in_backfill = [
            record
            for record in records
            if instance_queryer.run_has_tag(
                run_id=record.run_id, tag_key=BACKFILL_ID_TAG, tag_value=backfill_id
            )
        ]
        recently_materialized_asset_partitions |= AssetGraphSubset.from_asset_partition_set(
            {
                AssetKeyPartitionKey(asset_key, record.partition_key)
                for record in records_in_backfill
            },
            asset_graph,
        )

        yield None

    updated_materialized_subset = (
        asset_backfill_data.materialized_subset | recently_materialized_asset_partitions
    )

    yield updated_materialized_subset


def _get_failed_and_downstream_asset_partitions(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    backfill_start_time: datetime,
) -> AssetGraphSubset:
    failed_and_downstream_subset = AssetGraphSubset.from_asset_partition_set(
        asset_graph.bfs_filter_asset_partitions(
            instance_queryer,
            lambda asset_partitions, _: any(
                asset_partition in asset_backfill_data.target_subset
                for asset_partition in asset_partitions
            ),
            _get_failed_asset_partitions(instance_queryer, backfill_id, asset_graph),
            evaluation_time=backfill_start_time,
        ),
        asset_graph,
    )
    return failed_and_downstream_subset


def _get_next_latest_storage_id(instance_queryer: CachingInstanceQueryer) -> int:
    # Events are not always guaranteed to be written to the event log in monotonically increasing
    # order, so add a configurable offset to ensure that any stragglers will still be included in
    # the next iteration.
    # This may result in the same event being considered within multiple iterations, but
    # idempotence checks later ensure that the materialization isn't incorrectly
    # double-counted.
    cursor_offset = int(os.getenv("ASSET_BACKFILL_CURSOR_OFFSET", "0"))
    next_latest_storage_id = (
        instance_queryer.instance.event_log_storage.get_maximum_record_id() or 0
    )
    return max(next_latest_storage_id - cursor_offset, 0)


def execute_asset_backfill_iteration_inner(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    run_tags: Mapping[str, str],
    backfill_start_time: datetime,
) -> Iterable[Optional[AssetBackfillIterationResult]]:
    """Core logic of a backfill iteration. Has no side effects.

    Computes which runs should be requested, if any, as well as updated bookkeeping about the status
    of asset partitions targeted by the backfill.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    initial_candidates: Set[AssetKeyPartitionKey] = set()
    request_roots = not asset_backfill_data.requested_runs_for_target_roots
    if request_roots:
        initial_candidates.update(
            asset_backfill_data.get_target_root_asset_partitions(instance_queryer)
        )

        yield None

        updated_materialized_subset = AssetGraphSubset()
        failed_and_downstream_subset = AssetGraphSubset()
        next_latest_storage_id = _get_next_latest_storage_id(instance_queryer)
    else:
        next_latest_storage_id = _get_next_latest_storage_id(instance_queryer)

        cursor_delay_time = int(os.getenv("ASSET_BACKFILL_CURSOR_DELAY_TIME", "0"))
        # Events are not guaranteed to be written to the event log in monotonic increasing order,
        # so we wait to ensure all events up until next_latest_storage_id have been written.
        if cursor_delay_time:
            time.sleep(cursor_delay_time)

        updated_materialized_subset = None
        for updated_materialized_subset in get_asset_backfill_iteration_materialized_partitions(
            backfill_id, asset_backfill_data, asset_graph, instance_queryer
        ):
            yield None

        if not isinstance(updated_materialized_subset, AssetGraphSubset):
            check.failed(
                "Expected get_asset_backfill_iteration_materialized_partitions to return an"
                " AssetGraphSubset"
            )

        parent_materialized_asset_partitions = set().union(
            *(
                instance_queryer.asset_partitions_with_newly_updated_parents_and_new_cursor(
                    latest_storage_id=asset_backfill_data.latest_storage_id,
                    child_asset_key=asset_key,
                )[0]
                for asset_key in asset_backfill_data.target_subset.asset_keys
            )
        )
        initial_candidates.update(parent_materialized_asset_partitions)

        yield None

        failed_and_downstream_subset = _get_failed_and_downstream_asset_partitions(
            backfill_id, asset_backfill_data, asset_graph, instance_queryer, backfill_start_time
        )

        yield None

    asset_partitions_to_request = asset_graph.bfs_filter_asset_partitions(
        instance_queryer,
        lambda unit, visited: should_backfill_atomic_asset_partitions_unit(
            candidates_unit=unit,
            asset_partitions_to_request=visited,
            asset_graph=asset_graph,
            materialized_subset=updated_materialized_subset,
            requested_subset=asset_backfill_data.requested_subset,
            target_subset=asset_backfill_data.target_subset,
            failed_and_downstream_subset=failed_and_downstream_subset,
            dynamic_partitions_store=instance_queryer,
            current_time=backfill_start_time,
        ),
        initial_asset_partitions=initial_candidates,
        evaluation_time=backfill_start_time,
    )

    # check if all assets have backfill policies if any of them do, otherwise, raise error
    asset_backfill_policies = [
        asset_graph.get(asset_key).backfill_policy
        for asset_key in {
            asset_partition.asset_key for asset_partition in asset_partitions_to_request
        }
    ]
    all_assets_have_backfill_policies = all(
        backfill_policy is not None for backfill_policy in asset_backfill_policies
    )
    if all_assets_have_backfill_policies:
        run_requests = build_run_requests_with_backfill_policies(
            asset_partitions=asset_partitions_to_request,
            asset_graph=asset_graph,
            run_tags={**run_tags, BACKFILL_ID_TAG: backfill_id},
            dynamic_partitions_store=instance_queryer,
        )
    else:
        if not all(backfill_policy is None for backfill_policy in asset_backfill_policies):
            # if some assets have backfill policies, but not all of them, raise error
            raise DagsterBackfillFailedError(
                "Either all assets must have backfill policies or none of them must have backfill"
                " policies. To backfill these assets together, either add backfill policies to all"
                " assets, or remove backfill policies from all assets."
            )
        # When any of the assets do not have backfill policies, we fall back to the default behavior of
        # backfilling them partition by partition.
        run_requests = build_run_requests(
            asset_partitions=asset_partitions_to_request,
            asset_graph=asset_graph,
            run_tags={**run_tags, BACKFILL_ID_TAG: backfill_id},
        )

    if request_roots:
        check.invariant(
            len(run_requests) > 0,
            "At least one run should be requested on first backfill iteration",
        )

    updated_asset_backfill_data = AssetBackfillData(
        target_subset=asset_backfill_data.target_subset,
        latest_storage_id=next_latest_storage_id or asset_backfill_data.latest_storage_id,
        requested_runs_for_target_roots=asset_backfill_data.requested_runs_for_target_roots
        or request_roots,
        materialized_subset=updated_materialized_subset,
        failed_and_downstream_subset=failed_and_downstream_subset,
        requested_subset=asset_backfill_data.requested_subset
        | AssetGraphSubset.from_asset_partition_set(set(asset_partitions_to_request), asset_graph),
        backfill_start_time=backfill_start_time,
    )
    yield AssetBackfillIterationResult(run_requests, updated_asset_backfill_data)


def can_run_with_parent(
    parent: AssetKeyPartitionKey,
    candidate: AssetKeyPartitionKey,
    candidates_unit: Iterable[AssetKeyPartitionKey],
    asset_graph: RemoteAssetGraph,
    target_subset: AssetGraphSubset,
    asset_partitions_to_request_map: Mapping[AssetKey, AbstractSet[Optional[str]]],
) -> bool:
    """Returns if a given candidate can be materialized in the same run as a given parent on
    this tick.
    """
    parent_target_subset = target_subset.get_asset_subset(parent.asset_key, asset_graph)
    candidate_target_subset = target_subset.get_asset_subset(candidate.asset_key, asset_graph)
    partition_mapping = asset_graph.get_partition_mapping(
        candidate.asset_key, parent_asset_key=parent.asset_key
    )

    parent_node = asset_graph.get(parent.asset_key)
    candidate_node = asset_graph.get(candidate.asset_key)
    # checks if there is a simple partition mapping between the parent and the child
    has_identity_partition_mapping = (
        # both unpartitioned
        not candidate_node.is_partitioned
        and not parent_node.is_partitioned
        # normal identity partition mapping
        or isinstance(partition_mapping, IdentityPartitionMapping)
        # for assets with the same time partitions definition, a non-offset partition
        # mapping functions as an identity partition mapping
        or (
            isinstance(partition_mapping, TimeWindowPartitionMapping)
            and partition_mapping.start_offset == 0
            and partition_mapping.end_offset == 0
        )
    )
    return (
        parent_node.backfill_policy == candidate_node.backfill_policy
        and parent_node.priority_repository_handle is candidate_node.priority_repository_handle
        and parent_node.partitions_def == candidate_node.partitions_def
        and (
            parent.partition_key in asset_partitions_to_request_map[parent.asset_key]
            or parent in candidates_unit
        )
        and (
            # if there is a simple mapping between the parent and the child, then
            # with the parent
            has_identity_partition_mapping
            # if there is not a simple mapping, we can only materialize this asset with its
            # parent if...
            or (
                # there is a backfill policy for the parent
                parent_node.backfill_policy is not None
                # the same subset of parents is targeted as the child
                and parent_target_subset.value == candidate_target_subset.value
                and (
                    # there is no limit on the size of a single run or...
                    parent_node.backfill_policy.max_partitions_per_run is None
                    # a single run can materialize all requested parent partitions
                    or parent_node.backfill_policy.max_partitions_per_run
                    > len(asset_partitions_to_request_map[parent.asset_key])
                )
                # all targeted parents are being requested this tick
                and len(asset_partitions_to_request_map[parent.asset_key])
                == parent_target_subset.size
            )
            # if all the above are true, then a single run can be launched this tick which
            # will materialize all requested partitions
        )
    )


def should_backfill_atomic_asset_partitions_unit(
    asset_graph: RemoteAssetGraph,
    candidates_unit: Iterable[AssetKeyPartitionKey],
    asset_partitions_to_request: AbstractSet[AssetKeyPartitionKey],
    target_subset: AssetGraphSubset,
    requested_subset: AssetGraphSubset,
    materialized_subset: AssetGraphSubset,
    failed_and_downstream_subset: AssetGraphSubset,
    dynamic_partitions_store: DynamicPartitionsStore,
    current_time: datetime,
) -> bool:
    """Args:
    candidates_unit: A set of asset partitions that must all be materialized if any is
        materialized.
    """
    for candidate in candidates_unit:
        if (
            candidate not in target_subset
            or candidate in failed_and_downstream_subset
            or candidate in materialized_subset
            or candidate in requested_subset
        ):
            return False

        parent_partitions_result = asset_graph.get_parents_partitions(
            dynamic_partitions_store, current_time, *candidate
        )
        if parent_partitions_result.required_but_nonexistent_parents_partitions:
            raise DagsterInvariantViolationError(
                f"Asset partition {candidate}"
                " depends on invalid partition keys"
                f" {parent_partitions_result.required_but_nonexistent_parents_partitions}"
            )

        asset_partitions_to_request_map: Dict[AssetKey, Set[Optional[str]]] = defaultdict(set)
        for asset_partition in asset_partitions_to_request:
            asset_partitions_to_request_map[asset_partition.asset_key].add(
                asset_partition.partition_key
            )

        for parent in parent_partitions_result.parent_partitions:
            if (
                parent in target_subset
                and parent not in materialized_subset
                and not can_run_with_parent(
                    parent,
                    candidate,
                    candidates_unit,
                    asset_graph,
                    target_subset,
                    asset_partitions_to_request_map,
                )
            ):
                return False

    return True


def _get_failed_asset_partitions(
    instance_queryer: CachingInstanceQueryer, backfill_id: str, asset_graph: RemoteAssetGraph
) -> Sequence[AssetKeyPartitionKey]:
    """Returns asset partitions that materializations were requested for as part of the backfill, but
    will not be materialized.

    Includes canceled asset partitions. Implementation assumes that successful runs won't have any
    failed partitions.
    """
    runs = instance_queryer.instance.get_runs(
        filters=RunsFilter(
            tags={BACKFILL_ID_TAG: backfill_id},
            statuses=[DagsterRunStatus.CANCELED, DagsterRunStatus.FAILURE],
        )
    )

    result: List[AssetKeyPartitionKey] = []

    for run in runs:
        if (
            run.tags.get(ASSET_PARTITION_RANGE_START_TAG)
            and run.tags.get(ASSET_PARTITION_RANGE_END_TAG)
            and run.tags.get(PARTITION_NAME_TAG) is None
        ):
            # it was a chunked backfill run previously, so we need to reconstruct the partition keys
            planned_asset_keys = instance_queryer.get_planned_materializations_for_run(
                run_id=run.run_id
            )
            completed_asset_keys = instance_queryer.get_current_materializations_for_run(
                run_id=run.run_id
            )
            failed_asset_keys = planned_asset_keys - completed_asset_keys

            if failed_asset_keys:
                partition_range = PartitionKeyRange(
                    start=check.not_none(run.tags.get(ASSET_PARTITION_RANGE_START_TAG)),
                    end=check.not_none(run.tags.get(ASSET_PARTITION_RANGE_END_TAG)),
                )
                for asset_key in failed_asset_keys:
                    result.extend(
                        asset_graph.get_partitions_in_range(
                            asset_key, partition_range, instance_queryer
                        )
                    )
        else:
            # a regular backfill run that run on a single partition
            partition_key = run.tags.get(PARTITION_NAME_TAG)
            planned_asset_keys = instance_queryer.get_planned_materializations_for_run(
                run_id=run.run_id
            )
            completed_asset_keys = instance_queryer.get_current_materializations_for_run(
                run_id=run.run_id
            )
            result.extend(
                AssetKeyPartitionKey(asset_key, partition_key)
                for asset_key in planned_asset_keys - completed_asset_keys
            )

    return result
