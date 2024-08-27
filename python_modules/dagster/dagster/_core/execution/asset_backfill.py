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
    Tuple,
    Union,
    cast,
)

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import (
    build_run_requests,
    build_run_requests_with_backfill_policies,
)
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_selection import KeysAssetSelection
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
    BaseTimeWindowPartitionsSubset,
    TimeWindowPartitionsDefinition,
    TimeWindowPartitionsSubset,
)
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import (
    DagsterAssetBackfillDataLoadError,
    DagsterBackfillFailedError,
    DagsterDefinitionChangedDeserializationError,
    DagsterInvariantViolationError,
)
from dagster._core.event_api import AssetRecordsFilter
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
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._core.workspace.workspace import IWorkspace
from dagster._serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp, get_current_timestamp
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .submit_asset_runs import submit_asset_run

if TYPE_CHECKING:
    from .backfill import PartitionBackfill


def get_asset_backfill_run_chunk_size():
    return int(os.getenv("DAGSTER_ASSET_BACKFILL_RUN_CHUNK_SIZE", "25"))


MATERIALIZATION_CHUNK_SIZE = 1000

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


@whitelist_for_serdes
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
    backfill_start_time: TimestampWithTimezone

    @property
    def backfill_start_timestamp(self) -> float:
        return self.backfill_start_time.timestamp

    @property
    def backfill_start_datetime(self) -> datetime:
        return datetime_from_timestamp(self.backfill_start_time.timestamp)

    def replace_requested_subset(self, requested_subset: AssetGraphSubset) -> "AssetBackfillData":
        return self._replace(requested_subset=requested_subset)

    def with_latest_storage_id(self, latest_storage_id: Optional[int]) -> "AssetBackfillData":
        return self._replace(
            latest_storage_id=latest_storage_id,
        )

    def with_requested_runs_for_target_roots(self, requested_runs_for_target_roots: bool):
        return self._replace(requested_runs_for_target_roots=requested_runs_for_target_roots)

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

    def with_run_requests_submitted(
        self,
        run_requests: Sequence[RunRequest],
        asset_graph: RemoteAssetGraph,
        instance_queryer: CachingInstanceQueryer,
    ) -> "AssetBackfillData":
        requested_partitions = get_requested_asset_partitions_from_run_requests(
            run_requests,
            asset_graph,
            instance_queryer,
        )

        submitted_partitions = self.requested_subset | AssetGraphSubset.from_asset_partition_set(
            set(requested_partitions), asset_graph=asset_graph
        )

        return self.replace_requested_subset(submitted_partitions)

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
                KeysAssetSelection(selected_keys=list(unreachable_targets.asset_keys))
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
            KeysAssetSelection(selected_keys=list(target_partitioned_asset_keys))
            .sources()
            .resolve(asset_graph)
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
        backfill_start_timestamp: float,
        dynamic_partitions_store: DynamicPartitionsStore,
    ) -> "AssetBackfillData":
        return cls(
            target_subset=target_subset,
            requested_runs_for_target_roots=False,
            requested_subset=AssetGraphSubset(),
            materialized_subset=AssetGraphSubset(),
            failed_and_downstream_subset=AssetGraphSubset(),
            latest_storage_id=None,
            backfill_start_time=TimestampWithTimezone(backfill_start_timestamp, "UTC"),
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
            backfill_start_time=TimestampWithTimezone(backfill_start_timestamp, "UTC"),
        )

    @classmethod
    def from_partitions_by_assets(
        cls,
        asset_graph: BaseAssetGraph,
        dynamic_partitions_store: DynamicPartitionsStore,
        backfill_start_timestamp: float,
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
            partitions_def = asset_graph.get(asset_key).partitions_def
            if partitions and partitions_def:
                partitions_subset = partitions_def.empty_subset()
                for partition_range in partitions.ranges:
                    partitions_subset = partitions_subset.with_partition_key_range(
                        partitions_def=partitions_def,
                        partition_key_range=PartitionKeyRange(
                            start=partition_range.start,
                            end=partition_range.end,
                        ),
                        dynamic_partitions_store=dynamic_partitions_store,
                    )
                    partitions_subsets_by_asset_key[asset_key] = partitions_subset
            elif partitions_def:
                # no partitions selected for partitioned asset, we will select all partitions
                all_partitions = partitions_def.subset_with_all_partitions()
                partitions_subsets_by_asset_key[asset_key] = all_partitions
            else:
                # asset is not partitioned
                non_partitioned_asset_keys.add(asset_key)

        target_subset = AssetGraphSubset(
            partitions_subsets_by_asset_key=partitions_subsets_by_asset_key,
            non_partitioned_asset_keys=non_partitioned_asset_keys,
        )
        return cls.empty(target_subset, backfill_start_timestamp, dynamic_partitions_store)

    @classmethod
    def from_asset_partitions(
        cls,
        asset_graph: BaseAssetGraph,
        partition_names: Optional[Sequence[str]],
        asset_selection: Sequence[AssetKey],
        dynamic_partitions_store: DynamicPartitionsStore,
        backfill_start_timestamp: float,
        all_partitions: bool,
    ) -> "AssetBackfillData":
        check.invariant(
            partition_names is None or all_partitions is False,
            "Can't provide both a set of partitions and all_partitions=True",
        )

        backfill_start_datetime = datetime_from_timestamp(backfill_start_timestamp)

        if all_partitions:
            target_subset = AssetGraphSubset.from_asset_keys(
                asset_selection,
                asset_graph,
                dynamic_partitions_store,
                backfill_start_datetime,
            )
        elif partition_names is not None:
            partitioned_asset_keys = {
                asset_key
                for asset_key in asset_selection
                if asset_graph.get(asset_key).is_partitioned
            }

            root_partitioned_asset_keys = (
                KeysAssetSelection(selected_keys=list(partitioned_asset_keys))
                .sources()
                .resolve(asset_graph)
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
                    current_time=backfill_start_datetime,
                )
        else:
            check.failed("Either partition_names must not be None or all_partitions must be True")

        return cls.empty(target_subset, backfill_start_timestamp, dynamic_partitions_store)

    @classmethod
    def from_asset_graph_subset(
        cls,
        asset_graph_subset: AssetGraphSubset,
        dynamic_partitions_store: DynamicPartitionsStore,
        backfill_start_timestamp: float,
    ) -> "AssetBackfillData":
        return cls.empty(asset_graph_subset, backfill_start_timestamp, dynamic_partitions_store)

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
    backfill_timestamp = get_current_timestamp()
    return AssetBackfillData.from_asset_partitions(
        asset_graph=asset_graph,
        partition_names=partition_names,
        asset_selection=asset_selection,
        dynamic_partitions_store=dynamic_partitions_store,
        all_partitions=False,
        backfill_start_timestamp=backfill_timestamp,
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
    reserved_run_ids: Sequence[str]


def get_requested_asset_partitions_from_run_requests(
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


def _write_updated_backfill_data(
    instance: DagsterInstance,
    backfill_id: str,
    updated_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    updated_run_requests: Sequence[RunRequest],
    updated_reserved_run_ids: Sequence[str],
):
    backfill = check.not_none(instance.get_backfill(backfill_id))
    updated_backfill = backfill.with_asset_backfill_data(
        updated_backfill_data,
        dynamic_partitions_store=instance,
        asset_graph=asset_graph,
    ).with_submitting_run_requests(
        updated_run_requests,
        updated_reserved_run_ids,
    )
    instance.update_backfill(updated_backfill)
    return updated_backfill


def _submit_runs_and_update_backfill_in_chunks(
    instance: DagsterInstance,
    workspace_process_context: IWorkspaceProcessContext,
    backfill_id: str,
    asset_backfill_iteration_result: AssetBackfillIterationResult,
    asset_graph: RemoteAssetGraph,
    logger: logging.Logger,
    run_tags: Mapping[str, str],
    instance_queryer: CachingInstanceQueryer,
) -> Iterable[None]:
    from dagster._core.execution.backfill import BulkActionStatus

    run_requests = asset_backfill_iteration_result.run_requests

    # Iterate through runs to request, submitting runs in chunks.
    # In between each chunk, check that the backfill is still marked as 'requested',
    # to ensure that no more runs are requested if the backfill is marked as canceled/canceling.

    updated_backfill_data = asset_backfill_iteration_result.backfill_data

    num_submitted = 0

    reserved_run_ids = asset_backfill_iteration_result.reserved_run_ids

    run_request_execution_data_cache = {}

    chunk_size = get_asset_backfill_run_chunk_size()

    for run_request_idx, run_request in enumerate(run_requests):
        run_id = reserved_run_ids[run_request_idx] if reserved_run_ids else None
        try:
            submit_asset_run(
                run_id,
                run_request._replace(
                    tags={
                        **run_request.tags,
                        **run_tags,
                        BACKFILL_ID_TAG: backfill_id,
                    }
                ),
                run_request_idx,
                instance,
                workspace_process_context,
                asset_graph,
                run_request_execution_data_cache,
                {},
                logger,
            )
        except Exception:
            logger.exception(
                "Error while submitting run - updating the backfill data before re-raising"
            )
            # Write the runs that we submitted before hitting an error
            _write_updated_backfill_data(
                instance,
                backfill_id,
                updated_backfill_data,
                asset_graph,
                run_requests[num_submitted:],
                asset_backfill_iteration_result.reserved_run_ids[num_submitted:],
            )
            raise
        yield None

        num_submitted += 1

        updated_backfill_data: AssetBackfillData = (
            updated_backfill_data.with_run_requests_submitted(
                [run_request],
                asset_graph,
                instance_queryer,
            )
        )

        # After each chunk or on the final request, write the updated backfill data
        # and check to make sure we weren't interrupted
        if (num_submitted % chunk_size == 0) or num_submitted == len(run_requests):
            backfill = _write_updated_backfill_data(
                instance,
                backfill_id,
                updated_backfill_data,
                asset_graph,
                run_requests[num_submitted:],
                asset_backfill_iteration_result.reserved_run_ids[num_submitted:],
            )

            if backfill.status != BulkActionStatus.REQUESTED:
                break

        yield None

    yield None
    return


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

    backfill_start_datetime = datetime_from_timestamp(backfill.backfill_timestamp)
    instance_queryer = CachingInstanceQueryer(
        instance=instance, asset_graph=asset_graph, evaluation_time=backfill_start_datetime
    )

    previous_asset_backfill_data = _check_validity_and_deserialize_asset_backfill_data(
        workspace_context, backfill, asset_graph, instance_queryer, logger
    )
    if previous_asset_backfill_data is None:
        return

    logger.info(
        f"Assets targeted by backfill {backfill.backfill_id} are valid. Continuing execution with current status: {backfill.status}."
    )

    if backfill.status == BulkActionStatus.REQUESTED:
        if backfill.submitting_run_requests:
            # interrupted in the middle of executing run requests - re-construct the in-progress iteration result
            logger.warn(
                f"Resuming previous backfill iteration and re-submitting {len(backfill.submitting_run_requests)} runs."
            )
            result = AssetBackfillIterationResult(
                run_requests=backfill.submitting_run_requests,
                backfill_data=previous_asset_backfill_data,
                reserved_run_ids=backfill.reserved_run_ids,
            )

            updated_backfill = backfill
        else:
            # Generate a new set of run requests to launch, and update the materialized and failed
            # subsets
            result = None

            for result in execute_asset_backfill_iteration_inner(
                backfill_id=backfill.backfill_id,
                asset_backfill_data=previous_asset_backfill_data,
                instance_queryer=instance_queryer,
                asset_graph=asset_graph,
                backfill_start_timestamp=backfill.backfill_timestamp,
                logger=logger,
            ):
                yield None

            if not isinstance(result, AssetBackfillIterationResult):
                check.failed(
                    "Expected execute_asset_backfill_iteration_inner to return an"
                    " AssetBackfillIterationResult"
                )

            # Write the updated asset backfill data with in progress run requests before we launch anything, for idempotency
            # Make sure we didn't get canceled in the interim
            updated_backfill: PartitionBackfill = check.not_none(
                instance.get_backfill(backfill.backfill_id)
            )
            if updated_backfill.status != BulkActionStatus.REQUESTED:
                logger.info("Backfill was canceled mid-iteration, returning")
                return

            updated_backfill = (
                updated_backfill.with_asset_backfill_data(
                    result.backfill_data,
                    dynamic_partitions_store=instance,
                    asset_graph=asset_graph,
                )
                .with_submitting_run_requests(result.run_requests, result.reserved_run_ids)
                .with_failure_count(0)
            )

            instance.update_backfill(updated_backfill)

        if result.run_requests:
            yield from _submit_runs_and_update_backfill_in_chunks(
                instance,
                workspace_process_context,
                updated_backfill.backfill_id,
                result,
                asset_graph,
                logger,
                run_tags=updated_backfill.tags,
                instance_queryer=instance_queryer,
            )

        updated_backfill = cast(
            PartitionBackfill, instance.get_backfill(updated_backfill.backfill_id)
        )
        if updated_backfill.status == BulkActionStatus.REQUESTED:
            check.invariant(
                not updated_backfill.submitting_run_requests,
                "All run requests should have been submitted",
            )

        updated_backfill_data = updated_backfill.get_asset_backfill_data(asset_graph)

        if updated_backfill_data.is_complete():
            # The asset backfill is complete when all runs to be requested have finished (success,
            # failure, or cancellation). Since the AssetBackfillData object stores materialization states
            # per asset partition, the daemon continues to update the backfill data until all runs have
            # finished in order to display the final partition statuses in the UI.
            updated_backfill: PartitionBackfill = updated_backfill.with_status(
                BulkActionStatus.COMPLETED
            )
            instance.update_backfill(updated_backfill)

        new_materialized_partitions = (
            updated_backfill_data.materialized_subset
            - previous_asset_backfill_data.materialized_subset
        )
        new_failed_partitions = (
            updated_backfill_data.failed_and_downstream_subset
            - previous_asset_backfill_data.failed_and_downstream_subset
        )
        updated_backfill_in_progress = (
            updated_backfill_data.requested_subset - updated_backfill_data.materialized_subset
        )
        previous_backfill_in_progress = (
            previous_asset_backfill_data.requested_subset
            - previous_asset_backfill_data.materialized_subset
        )
        new_requested_partitions = updated_backfill_in_progress - previous_backfill_in_progress
        logger.info(
            f"Asset backfill {updated_backfill.backfill_id} completed iteration with status {updated_backfill.status}."
        )
        logger.info(
            "Backfill iteration summary:\n"
            f"**Assets materialized since last iteration:**\n{_asset_graph_subset_to_str(new_materialized_partitions, asset_graph) if new_materialized_partitions.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
            f"**Assets failed since last iteration and their downstream assets:**\n{_asset_graph_subset_to_str(new_failed_partitions, asset_graph) if new_failed_partitions.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
            f"**Assets requested by this iteration:**\n{_asset_graph_subset_to_str(new_requested_partitions, asset_graph) if new_requested_partitions.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
        )
        logger.info(
            "Overall backfill status:\n"
            f"**Materialized assets:**\n{_asset_graph_subset_to_str(updated_backfill_data.materialized_subset, asset_graph) if updated_backfill_data.materialized_subset.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
            f"**Failed assets and their downstream assets:**\n{_asset_graph_subset_to_str(updated_backfill_data.failed_and_downstream_subset, asset_graph) if updated_backfill_data.failed_and_downstream_subset.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
            f"**Assets requested or in progress:**\n{_asset_graph_subset_to_str(updated_backfill_in_progress, asset_graph) if updated_backfill_in_progress.num_partitions_and_non_partitioned_assets > 0 else 'None'}\n"
        )
        logger.debug(
            f"Updated asset backfill data for {updated_backfill.backfill_id}: {updated_backfill_data}"
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

        waiting_for_runs_to_finish_after_cancelation = False
        if runs_to_cancel_in_iteration:
            for run_id in runs_to_cancel_in_iteration:
                instance.run_coordinator.cancel_run(run_id)
                yield None
        else:
            # Check at the beginning of the tick whether there are any runs that we are still
            # waiting to move into a terminal state. If there are none and the backfill data is
            # still missing partitions at the end of the tick, that indicates a framework problem.
            # (It's important that we check for these runs before updating the backfill data -
            # if we did them in the reverse order, a run that finishes between the two checks
            # might not be incorporated into the backfill data, causing us to incorrectly decide
            # there was a framework error.
            run_waiting_to_cancel = instance.get_run_ids(
                RunsFilter(
                    tags={BACKFILL_ID_TAG: backfill.backfill_id}, statuses=IN_PROGRESS_RUN_STATUSES
                ),
                limit=1,
            )
            waiting_for_runs_to_finish_after_cancelation = len(run_waiting_to_cancel) > 0

        # Update the asset backfill data to contain the newly materialized/failed partitions.
        updated_asset_backfill_data = None
        for updated_asset_backfill_data in get_canceling_asset_backfill_iteration_data(
            backfill.backfill_id,
            previous_asset_backfill_data,
            instance_queryer,
            asset_graph,
            backfill.backfill_timestamp,
        ):
            yield None

        if not isinstance(updated_asset_backfill_data, AssetBackfillData):
            check.failed(
                "Expected get_canceling_asset_backfill_iteration_data to return an AssetBackfillData"
            )

        # Refetch, in case the backfill was forcibly marked as canceled in the meantime
        backfill = cast(PartitionBackfill, instance.get_backfill(backfill.backfill_id))
        updated_backfill: PartitionBackfill = backfill.with_asset_backfill_data(
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

        if (
            len(runs_to_cancel_in_iteration) == 0
            and not all_partitions_marked_completed
            and not waiting_for_runs_to_finish_after_cancelation
        ):
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
    elif backfill.status == BulkActionStatus.CANCELED:
        # The backfill was forcibly canceled, skip iteration
        pass
    else:
        check.failed(f"Unexpected backfill status: {backfill.status}")


def get_canceling_asset_backfill_iteration_data(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    instance_queryer: CachingInstanceQueryer,
    asset_graph: RemoteAssetGraph,
    backfill_start_timestamp: float,
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
        backfill_start_time=TimestampWithTimezone(backfill_start_timestamp, "UTC"),
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
        cursor = None
        has_more = True
        while has_more:
            result = instance_queryer.instance.fetch_materializations(
                AssetRecordsFilter(
                    asset_key=asset_key,
                    after_storage_id=asset_backfill_data.latest_storage_id,
                ),
                cursor=cursor,
                limit=MATERIALIZATION_CHUNK_SIZE,
            )
            records_in_backfill = [
                record
                for record in result.records
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
            cursor = result.cursor
            has_more = result.has_more
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
    backfill_start_timestamp: float,
) -> AssetGraphSubset:
    failed_and_downstream_subset = AssetGraphSubset.from_asset_partition_set(
        asset_graph.bfs_filter_asset_partitions(
            instance_queryer,
            lambda asset_partitions, _: (
                any(
                    asset_partition in asset_backfill_data.target_subset
                    for asset_partition in asset_partitions
                ),
                "",
            ),
            _get_failed_asset_partitions(instance_queryer, backfill_id, asset_graph),
            evaluation_time=datetime_from_timestamp(backfill_start_timestamp),
        )[0],
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


def _partition_subset_str(
    partition_subset: PartitionsSubset,
    partitions_def: PartitionsDefinition,
):
    if isinstance(partition_subset, BaseTimeWindowPartitionsSubset) and isinstance(
        partitions_def, TimeWindowPartitionsDefinition
    ):
        return ", ".join(
            f"{partitions_def.get_num_partitions_in_window(time_window.to_public_time_window())} partitions: {time_window.start} -> {time_window.end}"
            for time_window in partition_subset.included_time_windows
        )

    return ", ".join(partition_subset.get_partition_keys())


def _asset_graph_subset_to_str(
    asset_graph_subset: AssetGraphSubset,
    asset_graph: BaseAssetGraph,
) -> str:
    return_str = ""
    asset_subsets = asset_graph_subset.iterate_asset_subsets(asset_graph)
    for subset in asset_subsets:
        if subset.is_partitioned:
            partitions_def = asset_graph.get(subset.asset_key).partitions_def
            partition_ranges_str = _partition_subset_str(subset.subset_value, partitions_def)
            return_str += f"- {subset.asset_key.to_user_string()}: {{{partition_ranges_str}}}\n"
        else:
            return_str += f"- {subset.asset_key.to_user_string()}\n"

    return return_str


def execute_asset_backfill_iteration_inner(
    backfill_id: str,
    asset_backfill_data: AssetBackfillData,
    asset_graph: RemoteAssetGraph,
    instance_queryer: CachingInstanceQueryer,
    backfill_start_timestamp: float,
    logger: logging.Logger,
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
        logger.info(
            "Not all root assets (assets in backfill that do not have parents in the backill) have been requested, finding root assets."
        )
        target_roots = asset_backfill_data.get_target_root_asset_partitions(instance_queryer)
        initial_candidates.update(target_roots)
        logger.info(
            f"Root assets that have not yet been requested:\n {_asset_graph_subset_to_str(AssetGraphSubset.from_asset_partition_set(set(target_roots), asset_graph), asset_graph)}"
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

        materialized_since_last_tick = (
            updated_materialized_subset - asset_backfill_data.materialized_subset
        )
        logger.info(
            f"Assets materialized since last tick:\n {_asset_graph_subset_to_str(materialized_since_last_tick, asset_graph)}"
            if materialized_since_last_tick
            else "No relevant assets materialized since last tick."
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
            backfill_id,
            asset_backfill_data,
            asset_graph,
            instance_queryer,
            backfill_start_timestamp,
        )

        yield None

    backfill_start_datetime = datetime_from_timestamp(backfill_start_timestamp)

    asset_partitions_to_request, not_requested_and_reasons = (
        asset_graph.bfs_filter_asset_partitions(
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
                current_time=backfill_start_datetime,
            ),
            initial_asset_partitions=initial_candidates,
            evaluation_time=backfill_start_datetime,
        )
    )

    logger.info(
        f"Asset partitions to request:\n {_asset_graph_subset_to_str(AssetGraphSubset.from_asset_partition_set(asset_partitions_to_request, asset_graph), asset_graph)}"
        if asset_partitions_to_request
        else "No asset partitions to request."
    )
    if len(not_requested_and_reasons) > 0:

        def _format_keys(keys: Iterable[AssetKeyPartitionKey]):
            return ", ".join(
                f"({key.asset_key.to_user_string()}, {key.partition_key})"
                if key.partition_key
                else key.asset_key.to_user_string()
                for key in keys
            )

        not_requested_str = "\n".join(
            [
                f"[{_format_keys(keys)}] - Reason: {reason}."
                for keys, reason in not_requested_and_reasons
            ]
        )
        logger.info(
            f"The following assets were considered for materialization but not requested:\n\n{not_requested_str}"
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
            run_tags={},
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
        requested_subset=asset_backfill_data.requested_subset,
        backfill_start_time=TimestampWithTimezone(backfill_start_timestamp, "UTC"),
    )
    yield AssetBackfillIterationResult(
        run_requests,
        updated_asset_backfill_data,
        reserved_run_ids=[make_new_run_id() for _ in range(len(run_requests))],
    )


def can_run_with_parent(
    parent: AssetKeyPartitionKey,
    candidate: AssetKeyPartitionKey,
    candidates_unit: Iterable[AssetKeyPartitionKey],
    asset_graph: RemoteAssetGraph,
    target_subset: AssetGraphSubset,
    asset_partitions_to_request_map: Mapping[AssetKey, AbstractSet[Optional[str]]],
) -> Tuple[bool, str]:
    """Returns if a given candidate can be materialized in the same run as a given parent on
    this tick, and the reason it cannot be materialized, if applicable.
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
    if parent_node.backfill_policy != candidate_node.backfill_policy:
        return (
            False,
            f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different backfill policies so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key} is materialized.",
        )
    if parent_node.priority_repository_handle is not candidate_node.priority_repository_handle:
        return (
            False,
            f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} are in different code locations so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized.",
        )
    if parent_node.partitions_def != candidate_node.partitions_def:
        return (
            False,
            f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different partitions definitions so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized.",
        )
    if (
        parent.partition_key not in asset_partitions_to_request_map[parent.asset_key]
        and parent not in candidates_unit
    ):
        return (
            False,
            f"parent {parent.asset_key.to_user_string()} with partition key {parent.partition_key} is not requested in this iteration",
        )
    if (
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
            and len(asset_partitions_to_request_map[parent.asset_key]) == parent_target_subset.size
        )
    ):
        return True, ""
    else:
        failed_reason = (
            f"partition mapping between {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} is not simple and "
            f"{parent_node.key.to_user_string()} does not meet requirements of: targeting the same partitions as "
            f"{candidate_node.key.to_user_string()}, have all of its partitions requested in this iteration, having "
            "a backfill policy, and that backfill policy size limit is not exceeded by adding "
            f"{candidate_node.key.to_user_string()} to the run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."
        )
        return False, failed_reason


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
) -> Tuple[bool, str]:
    """Args:
    candidates_unit: A set of asset partitions that must all be materialized if any is
        materialized.

    returns if the candidates_unit can be materialized in this tick of the backfill, and the reason
    it cannot, if applicable
    """
    for candidate in candidates_unit:
        candidate_asset_partition_string = f"Asset {candidate.asset_key.to_user_string()} {f'with partition {candidate.partition_key}' if candidate.partition_key is not None else ''}"
        if candidate not in target_subset:
            return False, f"{candidate_asset_partition_string} is not targeted by backfill"
        elif candidate in failed_and_downstream_subset:
            return (
                False,
                f"{candidate_asset_partition_string} has failed or is downstream of a failed asset",
            )
        elif candidate in materialized_subset:
            return False, f"{candidate_asset_partition_string} was already materialized by backfill"
        elif candidate in requested_subset:
            return False, f"{candidate_asset_partition_string} was already requested by backfill"

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
            if parent in target_subset and parent not in materialized_subset:
                can_run, failed_reason = can_run_with_parent(
                    parent,
                    candidate,
                    candidates_unit,
                    asset_graph,
                    target_subset,
                    asset_partitions_to_request_map,
                )
                if not can_run:
                    return False, failed_reason

    return True, ""


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
        planned_asset_keys = instance_queryer.get_planned_materializations_for_run(
            run_id=run.run_id
        )
        completed_asset_keys = instance_queryer.get_current_materializations_for_run(
            run_id=run.run_id
        )
        failed_asset_keys = planned_asset_keys - completed_asset_keys

        if (
            run.tags.get(ASSET_PARTITION_RANGE_START_TAG)
            and run.tags.get(ASSET_PARTITION_RANGE_END_TAG)
            and run.tags.get(PARTITION_NAME_TAG) is None
        ):
            # reconstruct the partition keys from a chunked backfill run
            partition_range = PartitionKeyRange(
                start=run.tags[ASSET_PARTITION_RANGE_START_TAG],
                end=run.tags[ASSET_PARTITION_RANGE_END_TAG],
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
            result.extend(
                AssetKeyPartitionKey(asset_key, partition_key) for asset_key in failed_asset_keys
            )

    return result
