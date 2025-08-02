import json
import logging
import os
import sys
import time
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional, Union, cast

from dagster_shared.record import record

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_subset_view import AssetGraphSubsetView
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.asset_graph_view.serializable_entity_subset import EntitySubsetValue
from dagster._core.definitions.asset_selection import KeysAssetSelection
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.assets.graph.remote_asset_graph import (
    RemoteAssetGraph,
    RemoteWorkspaceAssetGraph,
)
from dagster._core.definitions.automation_tick_evaluation_context import (
    build_run_requests_with_backfill_policies,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.mapping import (
    IdentityPartitionMapping,
    TimeWindowPartitionMapping,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import PartitionsSubset, TimeWindowPartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import PartitionsByAssetSelector
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import (
    DagsterAssetBackfillDataLoadError,
    DagsterBackfillFailedError,
    DagsterDefinitionChangedDeserializationError,
    DagsterInvariantViolationError,
)
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.execution.submit_asset_runs import submit_asset_run
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.dagster_run import NOT_FINISHED_STATUSES, DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    BACKFILL_ID_TAG,
    PARTITION_NAME_TAG,
    WILL_RETRY_TAG,
)
from dagster._core.utils import make_new_run_id, toposort
from dagster._core.workspace.context import BaseWorkspaceRequestContext, IWorkspaceProcessContext
from dagster._serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp, get_current_timestamp
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

if TYPE_CHECKING:
    from dagster._core.execution.backfill import PartitionBackfill


def get_asset_backfill_run_chunk_size():
    return int(os.getenv("DAGSTER_ASSET_BACKFILL_RUN_CHUNK_SIZE", "25"))


MATERIALIZATION_CHUNK_SIZE = int(
    os.getenv("DAGSTER_ASSET_BACKFILL_MATERIALIZATION_CHUNK_SIZE", "1000")
)


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
        return super().__new__(
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
        return super().__new__(
            cls,
            check.inst_param(asset_key, "asset_key", AssetKey),
            check.opt_inst_param(
                asset_backfill_status, "asset_backfill_status", AssetBackfillStatus
            ),
        )


@record
class AssetBackfillComputationResult:
    """Represents the result of a backfill computation. Contains information about the subset of
    the asset that should be backfilled this tick, and reasons why unselected subsets will not be
    backfilled on this tick.
    """

    to_request: EntitySubset[AssetKey]
    rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]]


@record
class AssetBackfillComputationData:
    view: AssetGraphView
    backfill_id: str
    backfill_start_timestamp: float
    latest_storage_id: Optional[int]
    target_subset: AssetGraphSubsetView[AssetKey]
    requested_subset: AssetGraphSubsetView[AssetKey]
    materialized_subset: AssetGraphSubsetView[AssetKey]
    failed_and_downstream_subset: AssetGraphSubsetView[AssetKey]

    def get_candidate_subset(self) -> AssetGraphSubsetView[AssetKey]:
        """We consider executing any partition in the target subset that has not already
        been requested, or is downstream of a partition that has failed.
        """
        return self.target_subset.compute_difference(self.requested_subset).compute_difference(
            self.failed_and_downstream_subset
        )

    def to_asset_backfill_data(
        self, newly_requested_subset: AssetGraphSubsetView[AssetKey]
    ) -> "AssetBackfillData":
        return AssetBackfillData(
            target_subset=self.target_subset.to_asset_graph_subset(),
            latest_storage_id=self.latest_storage_id,
            materialized_subset=self.materialized_subset.to_asset_graph_subset(),
            failed_and_downstream_subset=self.failed_and_downstream_subset.to_asset_graph_subset(),
            requested_subset=self.requested_subset.compute_union(
                newly_requested_subset
            ).to_asset_graph_subset(),
            backfill_start_time=TimestampWithTimezone(self.backfill_start_timestamp, "UTC"),
            # legacy, no longer used
            requested_runs_for_target_roots=True,
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

    def get_computation_data(
        self, asset_graph_view: AssetGraphView, backfill_id: str
    ) -> AssetBackfillComputationData:
        return AssetBackfillComputationData(
            view=asset_graph_view,
            backfill_id=backfill_id,
            backfill_start_timestamp=self.backfill_start_timestamp,
            latest_storage_id=self.latest_storage_id,
            target_subset=AssetGraphSubsetView.from_serializable_subset(
                asset_graph_view, self.target_subset
            ),
            requested_subset=AssetGraphSubsetView.from_serializable_subset(
                asset_graph_view, self.requested_subset
            ),
            materialized_subset=AssetGraphSubsetView.from_serializable_subset(
                asset_graph_view, self.materialized_subset
            ),
            failed_and_downstream_subset=AssetGraphSubsetView.from_serializable_subset(
                asset_graph_view, self.failed_and_downstream_subset
            ),
        )

    def replace_requested_subset(self, requested_subset: AssetGraphSubset) -> "AssetBackfillData":
        return self._replace(requested_subset=requested_subset)

    def with_latest_storage_id(self, latest_storage_id: Optional[int]) -> "AssetBackfillData":
        return self._replace(
            latest_storage_id=latest_storage_id,
        )

    def all_targeted_partitions_have_materialization_status(self) -> bool:
        """The asset backfill is complete when all runs to be requested have finished (success,
        failure, or cancellation). Since the AssetBackfillData object stores materialization states
        per asset partition, we can use the materialization states and whether any runs for the backfill are
        not finished to determine if the backfill is complete. We want the daemon to continue to update
        the backfill data until all runs have finished in order to display the final partition statuses in the UI.
        """
        return (
            (
                self.materialized_subset | self.failed_and_downstream_subset
            ).num_partitions_and_non_partitioned_assets
            == self.target_subset.num_partitions_and_non_partitioned_assets
        )

    def all_requested_partitions_marked_as_materialized_or_failed(self) -> bool:
        return (
            len(
                (
                    self.requested_subset
                    - self.materialized_subset
                    - self.failed_and_downstream_subset
                ).asset_keys
            )
            == 0
        )

    def with_run_requests_submitted(
        self,
        run_requests: Sequence[RunRequest],
        asset_graph_view: AssetGraphView,
    ) -> "AssetBackfillData":
        requested_subset = _get_requested_asset_graph_subset_from_run_requests(
            run_requests,
            asset_graph_view,
        )

        submitted_partitions = self.requested_subset | requested_subset

        return self.replace_requested_subset(submitted_partitions)

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
            .roots()
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
        nodes: list[BaseAssetNode] = [asset_graph.get(key) for key in self.target_subset.asset_keys]
        return [
            item
            for items_by_level in toposort({node.key: node.parent_keys for node in nodes})
            for item in sorted(items_by_level)
            if item in self.target_subset.asset_keys
        ]

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
        cls,
        serialized: str,
        asset_graph: BaseAssetGraph,
        backfill_start_timestamp: float,
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

        with partition_loading_context(backfill_start_datetime, dynamic_partitions_store):
            if all_partitions:
                target_subset = AssetGraphSubset.from_asset_keys(asset_selection, asset_graph)
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

                root_partitions_subset = root_partitions_def.subset_with_partition_keys(
                    partition_names
                )
                target_subset = AssetGraphSubset(
                    non_partitioned_asset_keys=set(asset_selection) - partitioned_asset_keys,
                )
                for root_asset_key in root_partitioned_asset_keys:
                    target_subset |= asset_graph.bfs_filter_subsets(
                        lambda asset_key, _: asset_key in partitioned_asset_keys,
                        AssetGraphSubset(
                            partitions_subsets_by_asset_key={
                                root_asset_key: root_partitions_subset
                            },
                        ),
                    )
            else:
                check.failed(
                    "Either partition_names must not be None or all_partitions must be True"
                )

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
        self,
        dynamic_partitions_store: DynamicPartitionsStore,
        asset_graph: BaseAssetGraph,
    ) -> str:
        with partition_loading_context(
            effective_dt=self.backfill_start_datetime,
            dynamic_partitions_store=dynamic_partitions_store,
        ):
            storage_dict = {
                "requested_runs_for_target_roots": self.requested_runs_for_target_roots,
                "serialized_target_subset": self.target_subset.to_storage_dict(
                    asset_graph=asset_graph
                ),
                "latest_storage_id": self.latest_storage_id,
                "serialized_requested_subset": self.requested_subset.to_storage_dict(
                    asset_graph=asset_graph
                ),
                "serialized_materialized_subset": self.materialized_subset.to_storage_dict(
                    asset_graph=asset_graph
                ),
                "serialized_failed_subset": self.failed_and_downstream_subset.to_storage_dict(
                    asset_graph=asset_graph
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


def _get_unloadable_location_names(
    context: BaseWorkspaceRequestContext, logger: logging.Logger
) -> Sequence[str]:
    location_entries_by_name = {
        location_entry.origin.location_name: location_entry
        for location_entry in context.get_code_location_entries().values()
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


def _get_requested_asset_graph_subset_from_run_requests(
    run_requests: Sequence[RunRequest],
    asset_graph_view: AssetGraphView,
) -> AssetGraphSubset:
    asset_graph = asset_graph_view.asset_graph
    requested_subset = AssetGraphSubset.create_empty_subset()
    for run_request in run_requests:
        # Run request targets a range of partitions
        range_start = run_request.tags.get(ASSET_PARTITION_RANGE_START_TAG)
        range_end = run_request.tags.get(ASSET_PARTITION_RANGE_END_TAG)
        if range_start and range_end:
            # When a run request targets a range of partitions, each asset is expected to
            # have the same partitions def
            selected_assets = cast("Sequence[AssetKey]", run_request.asset_selection)
            check.invariant(len(selected_assets) > 0)
            partition_range = PartitionKeyRange(range_start, range_end)
            entity_subsets = [
                asset_graph_view.get_entity_subset_in_range(asset_key, partition_range)
                for asset_key in selected_assets
            ]
            requested_subset = requested_subset | AssetGraphSubset.from_entity_subsets(
                entity_subsets
            )
        else:
            requested_subset = requested_subset | AssetGraphSubset.from_asset_partition_set(
                {
                    AssetKeyPartitionKey(asset_key, run_request.partition_key)
                    for asset_key in cast("Sequence[AssetKey]", run_request.asset_selection)
                },
                asset_graph,
                # don't need expensive checks for whether the partition keys are still in the subset
                # when just determining what was previously requested in this backfill
                validate_time_range=False,
            )

    return requested_subset


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


async def _submit_runs_and_update_backfill_in_chunks(
    asset_graph_view: AssetGraphView,
    workspace_process_context: IWorkspaceProcessContext,
    backfill_id: str,
    asset_backfill_iteration_result: AssetBackfillIterationResult,
    logger: logging.Logger,
    run_tags: Mapping[str, str],
) -> None:
    from dagster._core.execution.backfill import BulkActionStatus
    from dagster._daemon.utils import DaemonErrorCapture

    asset_graph = cast("RemoteWorkspaceAssetGraph", asset_graph_view.asset_graph)
    instance = asset_graph_view.instance

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
            # create a new request context for each run in case the code location server
            # is swapped out in the middle of the submission process
            workspace = workspace_process_context.create_request_context()
            await submit_asset_run(
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
                workspace,
                run_request_execution_data_cache,
                {},
                logger,
            )
        except Exception:
            DaemonErrorCapture.process_exception(
                sys.exc_info(),
                logger=logger,
                log_message="Error while submitting run - updating the backfill data before re-raising",
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

        num_submitted += 1

        updated_backfill_data: AssetBackfillData = (
            updated_backfill_data.with_run_requests_submitted(
                [run_request],
                asset_graph_view,
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
    if not asset_graph.has(asset_key):
        raise DagsterDefinitionChangedDeserializationError(
            f"Asset {asset_key} existed at storage-time, but no longer does"
        )

    partitions_def = asset_graph.get(asset_key).partitions_def

    if target_partitions_subset:  # Asset was partitioned at storage time
        if partitions_def is None:
            raise DagsterDefinitionChangedDeserializationError(
                f"Asset {asset_key} had a PartitionsDefinition at storage-time, but no longer does"
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
                partitions_def.subset_with_all_partitions() & target_partitions_subset
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
    asset_graph: RemoteWorkspaceAssetGraph,
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


def backfill_is_complete(
    backfill_id: str,
    backfill_data: AssetBackfillData,
    instance: DagsterInstance,
    logger: logging.Logger,
):
    """A backfill is complete when:
    1. all asset partitions in the target subset have a materialization state (successful, failed, downstream of a failed partition).
    2. there are no in progress runs for the backfill.
    3. there are no failed runs that will result in an automatic retry, but have not yet been retried.

    Condition 1 ensures that for each asset partition we have attempted to materialize it or have determined we
    cannot materialize it because of a failed dependency. Condition 2 ensures that no retries of failed runs are
    in progress. Condition 3 guards against a race condition where a failed run could be automatically retried
    but it was not added into the queue in time to be caught by condition 2.

    Since the AssetBackfillData object stores materialization states per asset partition, we want to ensure the
    daemon continues to update the backfill data until all runs have finished in order to display the
    final partition statuses in the UI.
    """
    # Condition 1 - if any asset partitions in the target subset do not have a materialization state, the backfill
    # is not complete
    if not backfill_data.all_targeted_partitions_have_materialization_status():
        logger.info(
            "Not all targeted asset partitions have a materialization status. Backfill is still in progress."
        )
        return False
    # Condition 2 - if there are in progress runs for the backfill, the backfill is not complete
    if (
        len(
            instance.get_run_ids(
                filters=RunsFilter(
                    statuses=NOT_FINISHED_STATUSES,
                    tags={BACKFILL_ID_TAG: backfill_id},
                ),
                limit=1,
            )
        )
        > 0
    ):
        logger.info("Backfill has in progress runs. Backfill is still in progress.")
        return False
    # Condition 3 - if there are runs that will be retried, but have not yet been retried, the backfill is not complete
    runs_waiting_to_retry = [
        run.run_id
        for run in instance.get_runs(
            filters=RunsFilter(
                tags={BACKFILL_ID_TAG: backfill_id, WILL_RETRY_TAG: "true"},
                statuses=[DagsterRunStatus.FAILURE],
            )
        )
        if run.is_complete_and_waiting_to_retry
    ]
    if len(runs_waiting_to_retry) > 0:
        num_runs_to_log = 20
        formatted_runs = "\n".join(runs_waiting_to_retry[:num_runs_to_log])
        if len(runs_waiting_to_retry) > num_runs_to_log:
            formatted_runs += f"\n... {len(runs_waiting_to_retry) - num_runs_to_log} more"
        logger.info(
            f"The following runs for the backfill will be retried, but retries have not been launched. Backfill is still in progress:\n{formatted_runs}"
        )
        return False
    return True


async def execute_asset_backfill_iteration(
    backfill: "PartitionBackfill",
    logger: logging.Logger,
    workspace_process_context: IWorkspaceProcessContext,
    instance: DagsterInstance,
) -> None:
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

    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=backfill_start_datetime,
            last_event_id=None,
        ),
        instance=instance,
        asset_graph=asset_graph,
    )

    instance_queryer = asset_graph_view.get_inner_queryer_for_back_compat()

    previous_asset_backfill_data = _check_validity_and_deserialize_asset_backfill_data(
        workspace_context, backfill, asset_graph, instance_queryer, logger
    )
    if previous_asset_backfill_data is None:
        return
    previous_data = previous_asset_backfill_data.get_computation_data(
        asset_graph_view, backfill.backfill_id
    )

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
            result = execute_asset_backfill_iteration_inner(
                previous_data=previous_data, logger=logger
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
            await _submit_runs_and_update_backfill_in_chunks(
                asset_graph_view,
                workspace_process_context,
                updated_backfill.backfill_id,
                result,
                logger,
                run_tags=updated_backfill.tags,
            )

        updated_backfill = cast(
            "PartitionBackfill", instance.get_backfill(updated_backfill.backfill_id)
        )
        if updated_backfill.status == BulkActionStatus.REQUESTED:
            check.invariant(
                not updated_backfill.submitting_run_requests,
                "All run requests should have been submitted",
            )

        updated_backfill_data = updated_backfill.get_asset_backfill_data(asset_graph)

        if backfill_is_complete(
            backfill_id=backfill.backfill_id,
            backfill_data=updated_backfill_data,
            instance=instance,
            logger=logger,
        ):
            if (
                updated_backfill_data.failed_and_downstream_subset.num_partitions_and_non_partitioned_assets
                > 0
            ):
                updated_backfill = updated_backfill.with_status(BulkActionStatus.COMPLETED_FAILED)
            else:
                updated_backfill: PartitionBackfill = updated_backfill.with_status(
                    BulkActionStatus.COMPLETED_SUCCESS
                )

            updated_backfill = updated_backfill.with_end_timestamp(get_current_timestamp())
            instance.update_backfill(updated_backfill)

        logger.info(
            f"Asset backfill {updated_backfill.backfill_id} completed iteration with status {updated_backfill.status}."
        )
        _log_summary(
            previous_data,
            updated_backfill_data.get_computation_data(asset_graph_view, backfill.backfill_id),
            logger,
        )

    elif backfill.status == BulkActionStatus.CANCELING:
        from dagster._core.execution.backfill import cancel_backfill_runs_and_cancellation_complete

        all_runs_canceled = cancel_backfill_runs_and_cancellation_complete(
            instance=instance, backfill_id=backfill.backfill_id
        )

        # Update the asset backfill data to contain the newly materialized/failed partitions.
        updated_asset_backfill_data = get_canceling_asset_backfill_iteration_data(previous_data)

        # Refetch, in case the backfill was forcibly marked as canceled in the meantime
        backfill = cast("PartitionBackfill", instance.get_backfill(backfill.backfill_id))
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
            updated_backfill = updated_backfill.with_status(
                BulkActionStatus.CANCELED
            ).with_end_timestamp(get_current_timestamp())

        if all_runs_canceled and not all_partitions_marked_completed:
            logger.warning(
                "All runs have completed, but not all requested partitions have been marked as materialized or failed. "
                "This may indicate that some runs succeeded without materializing their expected partitions."
            )
            updated_backfill = updated_backfill.with_status(
                BulkActionStatus.CANCELED
            ).with_end_timestamp(get_current_timestamp())

        instance.update_backfill(updated_backfill)

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


def _log_results(
    to_request_subset: AssetGraphSubsetView[AssetKey],
    rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]],
    logger: logging.Logger,
):
    logger.info(
        f"Asset partitions to request:\n{to_request_subset!s}"
        if not to_request_subset.is_empty
        else "No asset partitions to request."
    )

    if len(rejected_subsets_with_reasons) > 0:
        not_requested_str = "\n\n".join(
            [
                f"{asset_graph_subset!s}\nReason: {reason}"
                for asset_graph_subset, reason in rejected_subsets_with_reasons
            ]
        )
        logger.info(
            f"The following assets were considered for materialization but not requested:\n\n{not_requested_str}"
        )


def _log_summary(
    previous_data: AssetBackfillComputationData,
    updated_data: AssetBackfillComputationData,
    logger: logging.Logger,
) -> None:
    new_materialized_partitions = updated_data.materialized_subset.compute_difference(
        previous_data.materialized_subset
    )
    new_failed_partitions = updated_data.failed_and_downstream_subset.compute_difference(
        previous_data.failed_and_downstream_subset
    )
    updated_backfill_in_progress = updated_data.requested_subset.compute_difference(
        updated_data.materialized_subset.compute_union(updated_data.failed_and_downstream_subset)
    )
    previous_backfill_in_progress = updated_data.requested_subset.compute_difference(
        updated_data.materialized_subset
    )
    new_requested_partitions = updated_backfill_in_progress.compute_difference(
        previous_backfill_in_progress
    )
    logger.info(
        "Backfill iteration summary:\n"
        f"**Assets materialized since last iteration:**\n{str(new_materialized_partitions) if not new_materialized_partitions.is_empty else 'None'}\n"
        f"**Assets failed since last iteration and their downstream assets:**\n{str(new_failed_partitions) if not new_failed_partitions.is_empty else 'None'}\n"
        f"**Assets requested by this iteration:**\n{str(new_requested_partitions) if not new_requested_partitions.is_empty else 'None'}\n"
    )
    logger.info(
        "Overall backfill status:\n"
        f"**Materialized assets:**\n{str(updated_data.materialized_subset) if not updated_data.materialized_subset.is_empty else 'None'}\n"
        f"**Failed assets and their downstream assets:**\n{str(updated_data.failed_and_downstream_subset) if not updated_data.failed_and_downstream_subset.is_empty else 'None'}\n"
        f"**Assets requested or in progress:**\n{str(updated_backfill_in_progress) if not updated_backfill_in_progress.is_empty else 'None'}\n"
    )
    logger.debug(f"Updated asset backfill data for {updated_data.backfill_id}: {updated_data}")


def get_canceling_asset_backfill_iteration_data(
    previous_data: AssetBackfillComputationData,
) -> AssetBackfillData:
    """For asset backfills in the "canceling" state, fetch the asset backfill data with the updated
    materialized and failed subsets.
    """
    updated_materialized_subset = get_updated_materialized_subset(previous_data)
    failed_subset = _get_failed_asset_graph_subset(previous_data, updated_materialized_subset)

    # we fetch the failed_subset to get any new assets that have failed and add that to the set of
    # assets we already know failed and their downstreams. However we need to remove any assets in
    # updated_materialized_subset to account for the case where a run retry successfully
    # materialized a previously failed asset.
    original_failed_subset = previous_data.failed_and_downstream_subset
    updated_failed_subset = original_failed_subset.compute_union(failed_subset)
    updated_failed_subset = updated_failed_subset.compute_difference(updated_materialized_subset)

    return AssetBackfillData(
        target_subset=previous_data.target_subset.to_asset_graph_subset(),
        latest_storage_id=previous_data.latest_storage_id,
        requested_runs_for_target_roots=True,
        materialized_subset=updated_materialized_subset.to_asset_graph_subset(),
        failed_and_downstream_subset=updated_failed_subset.to_asset_graph_subset(),
        requested_subset=previous_data.requested_subset.to_asset_graph_subset(),
        backfill_start_time=TimestampWithTimezone(previous_data.backfill_start_timestamp, "UTC"),
    )


def get_updated_materialized_subset(
    previous_data: AssetBackfillComputationData,
) -> AssetGraphSubsetView[AssetKey]:
    """Returns the partitions that have been materialized by the backfill.

    This function is a generator so we can return control to the daemon and let it heartbeat
    during expensive operations.
    """
    recently_materialized_asset_partitions = AssetGraphSubsetView.empty(previous_data.view)
    for asset_key in previous_data.target_subset.keys:
        cursor = None
        has_more = True
        while has_more:
            materializations_result = previous_data.view.instance.fetch_materializations(
                AssetRecordsFilter(
                    asset_key=asset_key, after_storage_id=previous_data.latest_storage_id
                ),
                cursor=cursor,
                limit=MATERIALIZATION_CHUNK_SIZE,
            )

            cursor = materializations_result.cursor
            has_more = materializations_result.has_more

            run_ids = [record.run_id for record in materializations_result.records if record.run_id]
            if run_ids:
                run_records = previous_data.view.instance.get_run_records(
                    filters=RunsFilter(run_ids=run_ids),
                )
                run_ids_in_backfill = {
                    run_record.dagster_run.run_id
                    for run_record in run_records
                    if run_record.dagster_run.tags.get(BACKFILL_ID_TAG) == previous_data.backfill_id
                }

                materialization_records_in_backfill = [
                    record
                    for record in materializations_result.records
                    if record.run_id in run_ids_in_backfill
                ]
                materialized_for_run = AssetGraphSubsetView.from_asset_partitions(
                    previous_data.view,
                    {
                        AssetKeyPartitionKey(asset_key, record.partition_key)
                        for record in materialization_records_in_backfill
                    },
                )
                recently_materialized_asset_partitions = (
                    recently_materialized_asset_partitions.compute_union(materialized_for_run)
                )

    return previous_data.materialized_subset.compute_union(recently_materialized_asset_partitions)


def execute_asset_backfill_iteration_inner(
    previous_data: AssetBackfillComputationData, logger: logging.Logger
) -> AssetBackfillIterationResult:
    """Core logic of a backfill iteration. Has no side effects.

    Computes which runs should be requested, if any, as well as updated bookkeeping about the status
    of asset partitions targeted by the backfill.

    This is a generator so that we can return control to the daemon and let it heartbeat during
    expensive operations.
    """
    # ensures that all partition operations use the same effective_dt and share a dynamic partition cache
    with partition_loading_context(
        effective_dt=previous_data.view.effective_dt,
        dynamic_partitions_store=previous_data.view.get_inner_queryer_for_back_compat(),
    ):
        return _execute_asset_backfill_iteration_inner(previous_data, logger)


def _get_updated_data(
    previous_data: AssetBackfillComputationData, logger: logging.Logger
) -> AssetBackfillComputationData:
    # Events are not always guaranteed to be written to the event log in monotonically increasing
    # order, so add a configurable offset to ensure that any stragglers will still be included in
    # the next iteration.
    # This may result in the same event being considered within multiple iterations, but
    # idempotence checks later ensure that the materialization isn't incorrectly
    # double-counted.
    cursor_offset = int(os.getenv("ASSET_BACKFILL_CURSOR_OFFSET", "0"))
    next_latest_storage_id = (
        previous_data.view.instance.event_log_storage.get_maximum_record_id() or 0
    )
    next_latest_storage_id = max(next_latest_storage_id - cursor_offset, 0)

    cursor_delay_time = int(os.getenv("ASSET_BACKFILL_CURSOR_DELAY_TIME", "0"))
    # Events are not guaranteed to be written to the event log in monotonic increasing order,
    # so we wait to ensure all events up until next_latest_storage_id have been written.
    if cursor_delay_time:
        time.sleep(cursor_delay_time)

    updated_materialized_subset = get_updated_materialized_subset(previous_data)
    updated_failed_subset = _get_failed_asset_graph_subset(
        previous_data, updated_materialized_subset
    )

    materialized_since_last_tick = updated_materialized_subset.compute_difference(
        previous_data.materialized_subset
    )
    logger.info(
        f"Assets materialized since last tick:\n{materialized_since_last_tick!s}"
        if not materialized_since_last_tick.is_empty
        else "No relevant assets materialized since last tick."
    )

    return AssetBackfillComputationData(
        view=previous_data.view,
        latest_storage_id=next_latest_storage_id,
        backfill_start_timestamp=previous_data.backfill_start_timestamp,
        backfill_id=previous_data.backfill_id,
        target_subset=previous_data.target_subset,
        requested_subset=previous_data.requested_subset,
        materialized_subset=updated_materialized_subset,
        failed_and_downstream_subset=updated_failed_subset.compute_downstream_subset(),
    )


def _execute_asset_backfill_iteration_inner(
    previous_data: AssetBackfillComputationData, logger: logging.Logger
) -> AssetBackfillIterationResult:
    # query the instance to find any updates to the set of materialized and failed partitions
    updated_data = _get_updated_data(previous_data, logger)
    candidate_graph_subset = updated_data.get_candidate_subset()

    logger.info(
        f"Considering the following candidate subset:\n{candidate_graph_subset!s}"
        if not candidate_graph_subset.is_empty
        else "Candidate subset is empty."
    )

    # iterate over the keys in topological order, and evaluate the candidates for that
    # key, determining which of the candidates should be requested.
    asset_graph_view = updated_data.view
    to_request_subset = AssetGraphSubsetView.empty(asset_graph_view)
    rejected_subsets_with_reasons = []
    for asset_key in asset_graph_view.asset_graph.toposorted_asset_keys:
        candidate_subset = candidate_graph_subset.get(asset_key)
        if candidate_subset.is_empty:
            continue

        result = _should_backfill_entity_subset(updated_data, candidate_subset, to_request_subset)
        to_request_subset = to_request_subset.compute_union(result.to_request)
        rejected_subsets_with_reasons.extend(result.rejected_subsets_with_reasons)

    _log_results(to_request_subset, rejected_subsets_with_reasons, logger)

    # construct run requests for the requested partitions
    run_requests = build_run_requests_with_backfill_policies(
        asset_graph=asset_graph_view.asset_graph,
        asset_partitions=set(to_request_subset.to_asset_graph_subset().iterate_asset_partitions()),
    )

    return AssetBackfillIterationResult(
        run_requests,
        updated_data.to_asset_backfill_data(to_request_subset),
        reserved_run_ids=[make_new_run_id() for _ in range(len(run_requests))],
    )


def _should_backfill_entity_subset(
    data: AssetBackfillComputationData,
    candidate_subset: EntitySubset[AssetKey],
    to_request_subset: AssetGraphSubsetView[AssetKey],
) -> AssetBackfillComputationResult:
    rejected_subsets_with_reasons: list[tuple[EntitySubsetValue, str]] = []

    key = candidate_subset.key
    missing_in_target_partitions = candidate_subset.compute_difference(data.target_subset.get(key))
    if not missing_in_target_partitions.is_empty:
        # Don't include a failure reason for this subset since it is unlikely to be
        # useful to know that an untargeted subset was not included
        candidate_subset = candidate_subset.compute_difference(missing_in_target_partitions)

    failed_and_downstream_partitions = candidate_subset.compute_intersection(
        data.failed_and_downstream_subset.get(key)
    )
    if not failed_and_downstream_partitions.is_empty:
        # Similar to above, only include a failure reason for 'interesting' failure reasons
        candidate_subset = candidate_subset.compute_difference(failed_and_downstream_partitions)

    materialized_partitions = candidate_subset.compute_intersection(
        data.materialized_subset.get(key)
    )
    if not materialized_partitions.is_empty:
        # Similar to above, only include a failure reason for 'interesting' failure reasons
        candidate_subset = candidate_subset.compute_difference(materialized_partitions)

    requested_partitions = candidate_subset.compute_intersection(to_request_subset.get(key))

    if not requested_partitions.is_empty:
        # Similar to above, only include a failure reason for 'interesting' failure reasons
        candidate_subset = candidate_subset.compute_difference(requested_partitions)

    parent_keys = data.view.asset_graph.get(candidate_subset.key).parent_keys
    has_any_parent_being_requested_this_tick = any(
        not to_request_subset.get(parent_key).is_empty for parent_key in parent_keys
    )

    for parent_key in sorted(parent_keys):
        if candidate_subset.is_empty:
            break

        parent_subset, required_but_nonexistent_subset = (
            data.view.compute_parent_subset_and_required_but_nonexistent_subset(
                parent_key, candidate_subset
            )
        )

        if not required_but_nonexistent_subset.is_empty:
            raise DagsterInvariantViolationError(
                f"Asset partition subset {candidate_subset}"
                f" depends on invalid partitions {required_but_nonexistent_subset}"
            )

        parent_materialized_subset = data.materialized_subset.get(parent_key)

        # Children with parents that are targeted but not materialized are eligible
        # to be filtered out if the parent has not run yet
        targeted_but_not_materialized_parent_subset: EntitySubset[AssetKey] = (
            parent_subset.compute_intersection(data.target_subset.get(parent_key))
        ).compute_difference(parent_materialized_subset)

        possibly_waiting_for_parent_subset = (
            targeted_but_not_materialized_parent_subset.compute_child_subset(candidate_subset.key)
        ).compute_intersection(candidate_subset)

        if not possibly_waiting_for_parent_subset.is_empty:
            cant_run_with_parent_reason = _get_cant_run_with_parent_reason(
                data, candidate_subset, parent_subset, to_request_subset
            )
            is_self_dependency = parent_key == candidate_subset.key

            if cant_run_with_parent_reason is not None:
                # if any parents are also being requested this tick and there is any reason to
                # believe that any parent can't be materialized with its child subset, then filter out
                # the whole child subset for now, to ensure that the parent and child aren't submitted
                # with different subsets which would incorrectly launch them in different runs
                # despite the child depending on the parent. Otherwise, we can just filter out the
                # specific ineligible child keys (to ensure that they aren't required before
                # their parents materialize)
                if not is_self_dependency and has_any_parent_being_requested_this_tick:
                    rejected_subsets_with_reasons.append(
                        (
                            candidate_subset.get_internal_value(),
                            cant_run_with_parent_reason,
                        )
                    )
                    candidate_subset = data.view.get_empty_subset(key=candidate_subset.key)
                else:
                    candidate_subset = candidate_subset.compute_difference(
                        possibly_waiting_for_parent_subset
                    )
                    rejected_subsets_with_reasons.append(
                        (
                            possibly_waiting_for_parent_subset.get_internal_value(),
                            cant_run_with_parent_reason,
                        )
                    )

            if is_self_dependency:
                self_dependent_node = data.view.asset_graph.get(candidate_subset.key)
                # ensure that we don't produce more than max_partitions_per_run partitions
                # if a backfill policy is set
                if (
                    self_dependent_node.backfill_policy is not None
                    and self_dependent_node.backfill_policy.max_partitions_per_run is not None
                ):
                    # only the first N partitions can be requested
                    num_allowed_partitions = (
                        self_dependent_node.backfill_policy.max_partitions_per_run
                    )
                    # TODO add a method for paginating through the keys in order
                    # and returning the first N instead of listing all of them
                    # (can't use expensively_compute_asset_partitions because it returns
                    # an unordered set)
                    internal_value = candidate_subset.get_internal_value()
                    partition_keys_to_include = (
                        list(internal_value.get_partition_keys())
                        if isinstance(internal_value, PartitionsSubset)
                        else [None]
                    )[:num_allowed_partitions]
                    partition_subset_to_include = AssetGraphSubset.from_asset_partition_set(
                        {
                            AssetKeyPartitionKey(self_dependent_node.key, partition_key)
                            for partition_key in partition_keys_to_include
                        },
                        asset_graph=data.view.asset_graph,
                    )
                    entity_subset_to_include = data.view.get_entity_subset_from_asset_graph_subset(
                        partition_subset_to_include, self_dependent_node.key
                    )

                    rejected_subset = candidate_subset.compute_difference(entity_subset_to_include)

                    if not rejected_subset.is_empty:
                        rejected_subsets_with_reasons.append(
                            (
                                rejected_subset.get_internal_value(),
                                "Respecting the maximum number of partitions per run for the backfill policy of a self-dependant asset",
                            )
                        )

                    candidate_subset = entity_subset_to_include

    return AssetBackfillComputationResult(
        to_request=candidate_subset,
        rejected_subsets_with_reasons=rejected_subsets_with_reasons,
    )


def _get_cant_run_with_parent_reason(
    data: AssetBackfillComputationData,
    candidate_subset: EntitySubset[AssetKey],
    parent_subset: EntitySubset[AssetKey],
    to_request_subset: AssetGraphSubsetView[AssetKey],
) -> Optional[str]:
    candidate_key = candidate_subset.key
    parent_key = parent_subset.key

    assert isinstance(data.view.asset_graph, RemoteWorkspaceAssetGraph)
    asset_graph = cast("RemoteWorkspaceAssetGraph", data.view.asset_graph)

    parent_node = asset_graph.get(parent_key)
    candidate_node = asset_graph.get(candidate_key)
    partition_mapping = asset_graph.get_partition_mapping(
        candidate_key, parent_asset_key=parent_key
    )

    # First filter out cases where even if the parent was requested this iteration, it wouldn't
    # matter, because the parent and child can't execute in the same run

    # checks if there is a simple partition mapping between the parent and the child
    has_identity_partition_mapping = (
        # both unpartitioned
        (not candidate_node.is_partitioned and not parent_node.is_partitioned)
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
        return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different backfill policies so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key} is materialized."

    if (
        parent_node.resolve_to_singular_repo_scoped_node().repository_handle
        != candidate_node.resolve_to_singular_repo_scoped_node().repository_handle
    ):
        return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} are in different code locations so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."

    if parent_node.partitions_def != candidate_node.partitions_def:
        return f"parent {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} have different partitions definitions so they cannot be materialized in the same run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."

    parent_target_subset = data.target_subset.get(parent_key)
    candidate_target_subset = data.target_subset.get(candidate_key)

    num_parent_partitions_being_requested_this_tick = parent_target_subset.size

    is_self_dependency = parent_key == candidate_key

    has_self_dependency = any(
        parent_key == candidate_key for parent_key in candidate_node.parent_keys
    )

    # launching a self-dependant asset with a non-self-dependant asset can result in invalid
    # runs being launched that don't respect lineage
    if (
        has_self_dependency
        and parent_key not in candidate_node.execution_set_asset_keys
        and num_parent_partitions_being_requested_this_tick > 0
    ):
        return "Self-dependant assets cannot be materialized in the same run as other assets."

    if not (
        # this check is here to guard against cases where the parent asset has a superset of
        # the child asset's asset partitions, which will mean that the runs that would be created
        # would not combine the parent and child assets into a single run. this is not relevant
        # for self-dependencies, because the parent and child are the same asset.
        is_self_dependency
        or (
            # in the typical case, we will only allow this candidate subset to be requested if
            # it contains exactly the same partitions as its parent asset for this evaluation,
            # otherwise they may end up in different runs
            to_request_subset.get(parent_key).get_internal_value()
            == candidate_subset.get_internal_value()
        )
    ):
        return (
            f"parent {parent_node.key.to_user_string()} is requesting a different set of partitions from "
            f"{candidate_node.key.to_user_string()}, meaning they cannot be grouped together in the same run."
        )

    if is_self_dependency:
        if parent_node.backfill_policy is None:
            required_parent_subset = parent_subset
        else:
            # with a self dependency, all of its parent partitions need to either have already
            # been materialized or be in the candidate subset
            required_parent_subset = parent_subset.compute_difference(
                candidate_subset
            ).compute_difference(data.materialized_subset.get(parent_key))

        if not required_parent_subset.is_empty:
            return f"Waiting for the following parent partitions of a self-dependant asset to materialize: {required_parent_subset!s}"
        else:
            return None

    if not (
        # if there is a simple mapping between the parent and the child, then
        # with the parent
        has_identity_partition_mapping
        # if there is not a simple mapping, we can only materialize this asset with its
        # parent if...
        or (
            # there is a backfill policy for the parent
            parent_node.backfill_policy is not None
            # the same subset of parents is targeted as the child
            and parent_target_subset.get_internal_value()
            == candidate_target_subset.get_internal_value()
            and (
                # there is no limit on the size of a single run or...
                parent_node.backfill_policy.max_partitions_per_run is None
                # a single run can materialize all requested parent partitions
                or parent_node.backfill_policy.max_partitions_per_run
                > num_parent_partitions_being_requested_this_tick
            )
            # all targeted parents are being requested this tick
            and num_parent_partitions_being_requested_this_tick == parent_target_subset.size
        )
    ):
        failed_reason = (
            f"partition mapping between {parent_node.key.to_user_string()} and {candidate_node.key.to_user_string()} is not simple and "
            f"{parent_node.key.to_user_string()} does not meet requirements of: targeting the same partitions as "
            f"{candidate_node.key.to_user_string()}, have all of its partitions requested in this iteration, having "
            "a backfill policy, and that backfill policy size limit is not exceeded by adding "
            f"{candidate_node.key.to_user_string()} to the run. {candidate_node.key.to_user_string()} can be materialized once {parent_node.key.to_user_string()} is materialized."
        )
        return failed_reason

    return None


def _get_failed_asset_graph_subset(
    previous_data: AssetBackfillComputationData,
    updated_materialized_subset: AssetGraphSubsetView[AssetKey],
) -> AssetGraphSubsetView[AssetKey]:
    """Returns asset subset that materializations were requested for as part of the backfill, but were
    not successfully materialized.

    This function gets a list of all runs for the backfill that have failed and extracts the asset partitions
    that were not materialized from those runs. However, we need to account for retried runs. If a run was
    successfully retried, the original failed run will still be processed in this function. So we check the
    failed asset partitions against the list of successfully materialized asset partitions. If an asset partition
    is in the materialized_subset, it means the failed run was retried and the asset partition was materialized.

    Includes canceled asset partitions. Implementation assumes that successful runs won't have any
    failed partitions.
    """
    runs = previous_data.view.instance.get_runs(
        filters=RunsFilter(
            tags={BACKFILL_ID_TAG: previous_data.backfill_id},
            statuses=[DagsterRunStatus.CANCELED, DagsterRunStatus.FAILURE],
        )
    )

    result: AssetGraphSubsetView[AssetKey] = AssetGraphSubsetView(
        asset_graph_view=previous_data.view, subsets=[]
    )
    instance_queryer = previous_data.view.get_inner_queryer_for_back_compat()
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
            candidate_subset = AssetGraphSubsetView(
                asset_graph_view=previous_data.view,
                subsets=[
                    previous_data.view.get_entity_subset_in_range(asset_key, partition_range)
                    for asset_key in failed_asset_keys
                ],
            )

        else:
            # a regular backfill run that run on a single partition
            partition_key = run.tags.get(PARTITION_NAME_TAG)
            candidate_subset = AssetGraphSubsetView.from_asset_partitions(
                previous_data.view,
                {AssetKeyPartitionKey(asset_key, partition_key) for asset_key in failed_asset_keys},
            )

        asset_subset_still_failed = candidate_subset.compute_difference(updated_materialized_subset)
        result = result.compute_union(asset_subset_still_failed)

    return result
