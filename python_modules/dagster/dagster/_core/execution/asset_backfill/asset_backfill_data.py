import json
from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple, Optional, Union, cast

from dagster_shared.record import record

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_subset_view import AssetGraphSubsetView
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.definitions.asset_selection import KeysAssetSelection
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph, BaseAssetNode
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import partition_loading_context
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import PartitionsSubset
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.selector import PartitionsByAssetSelector
from dagster._core.definitions.timestamp import TimestampWithTimezone
from dagster._core.errors import DagsterBackfillFailedError
from dagster._core.execution.asset_backfill.status import (
    AssetBackfillStatus,
    PartitionedAssetBackfillStatus,
    UnpartitionedAssetBackfillStatus,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._core.utils import toposort
from dagster._serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp


@record
class AssetBackfillComputationData:
    """Represents data used within an asset backfill iteration. This serves as a layer over the
    serializable AssetBackfillData object, which enables more convenient subset operations.
    """

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

    def _get_requested_asset_graph_subset_from_run_requests(
        self,
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

    def with_run_requests_submitted(
        self,
        run_requests: Sequence[RunRequest],
        asset_graph_view: AssetGraphView,
    ) -> "AssetBackfillData":
        requested_subset = self._get_requested_asset_graph_subset_from_run_requests(
            run_requests, asset_graph_view
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
        asset_graph: BaseAssetGraph[BaseAssetNode],
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
