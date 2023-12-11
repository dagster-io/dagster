import datetime
import itertools
import logging
import os
import time
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import pendulum

import dagster._check as check
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.time_window_partitions import (
    get_time_partitions_def,
)
from dagster._core.instance import DynamicPartitionsStore
from dagster._utils.cached_method import cached_method

from ... import PartitionKeyRange
from ..storage.tags import ASSET_PARTITION_RANGE_END_TAG, ASSET_PARTITION_RANGE_START_TAG
from .asset_condition import AssetConditionEvaluation
from .asset_condition_evaluation_context import RootAssetConditionEvaluationContext
from .asset_daemon_cursor import AssetDaemonAssetCursor, AssetDaemonCursor
from .asset_graph import AssetGraph
from .auto_materialize_rule import AutoMaterializeRule
from .backfill_policy import BackfillPolicy, BackfillPolicyType
from .freshness_based_auto_materialize import get_expected_data_time_for_asset_key
from .partition import PartitionsDefinition, ScheduleType

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


def get_implicit_auto_materialize_policy(
    asset_key: AssetKey, asset_graph: AssetGraph
) -> Optional[AutoMaterializePolicy]:
    """For backcompat with pre-auto materialize policy graphs, assume a default scope of 1 day."""
    auto_materialize_policy = asset_graph.get_auto_materialize_policy(asset_key)
    if auto_materialize_policy is None:
        time_partitions_def = get_time_partitions_def(asset_graph.get_partitions_def(asset_key))
        if time_partitions_def is None:
            max_materializations_per_minute = None
        elif time_partitions_def.schedule_type == ScheduleType.HOURLY:
            max_materializations_per_minute = 24
        else:
            max_materializations_per_minute = 1
        rules = {
            AutoMaterializeRule.materialize_on_missing(),
            AutoMaterializeRule.materialize_on_required_for_freshness(),
            AutoMaterializeRule.skip_on_parent_outdated(),
            AutoMaterializeRule.skip_on_parent_missing(),
            AutoMaterializeRule.skip_on_required_but_nonexistent_parents(),
            AutoMaterializeRule.skip_on_backfill_in_progress(),
        }
        if not bool(asset_graph.get_downstream_freshness_policies(asset_key=asset_key)):
            rules.add(AutoMaterializeRule.materialize_on_parent_updated())
        return AutoMaterializePolicy(
            rules=rules,
            max_materializations_per_minute=max_materializations_per_minute,
        )
    return auto_materialize_policy


class AssetDaemonContext:
    def __init__(
        self,
        evaluation_id: int,
        instance: "DagsterInstance",
        asset_graph: AssetGraph,
        cursor: AssetDaemonCursor,
        materialize_run_tags: Optional[Mapping[str, str]],
        observe_run_tags: Optional[Mapping[str, str]],
        auto_observe_asset_keys: Optional[AbstractSet[AssetKey]],
        auto_materialize_asset_keys: Optional[AbstractSet[AssetKey]],
        respect_materialization_data_versions: bool,
        logger: logging.Logger,
        evaluation_time: Optional[datetime.datetime] = None,
    ):
        from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

        self._evaluation_id = evaluation_id
        self._instance_queryer = CachingInstanceQueryer(
            instance, asset_graph, evaluation_time=evaluation_time, logger=logger
        )
        self._data_time_resolver = CachingDataTimeResolver(self.instance_queryer)
        self._cursor = cursor
        self._auto_materialize_asset_keys = auto_materialize_asset_keys or set()
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe_asset_keys = auto_observe_asset_keys or set()
        self._respect_materialization_data_versions = respect_materialization_data_versions
        self._logger = logger

        self._verbose_log_fn = (
            self._logger.info if os.getenv("ASSET_DAEMON_VERBOSE_LOGS") else self._logger.debug
        )

        # cache data before the tick starts
        self.prefetch()

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self._instance_queryer

    @property
    def data_time_resolver(self) -> CachingDataTimeResolver:
        return self._data_time_resolver

    @property
    def cursor(self) -> AssetDaemonCursor:
        return self._cursor

    @property
    def asset_graph(self) -> AssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def latest_storage_id(self) -> Optional[int]:
        return self.cursor.latest_storage_id

    @property
    def auto_materialize_asset_keys(self) -> AbstractSet[AssetKey]:
        return self._auto_materialize_asset_keys

    @property
    def auto_materialize_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        return {
            parent
            for asset_key in self.auto_materialize_asset_keys
            for parent in self.asset_graph.get_parents(asset_key)
        } | self.auto_materialize_asset_keys

    @property
    def asset_records_to_prefetch(self) -> Sequence[AssetKey]:
        return [
            key
            for key in self.auto_materialize_asset_keys_and_parents
            if not self.asset_graph.is_source(key)
        ]

    @property
    def respect_materialization_data_versions(self) -> bool:
        return self._respect_materialization_data_versions

    @property
    def auto_materialize_run_tags(self) -> Mapping[str, str]:
        return self._materialize_run_tags or {}

    def prefetch(self) -> None:
        """Pre-populate the cached values here to avoid situations in which the new latest_storage_id
        value is calculated using information that comes in after the set of asset partitions with
        new parent materializations is calculated, as this can result in materializations being
        ignored if they happen between the two calculations.
        """
        self._verbose_log_fn(
            f"Prefetching asset records for {len(self.asset_records_to_prefetch)} records."
        )
        self.instance_queryer.prefetch_asset_records(self.asset_records_to_prefetch)
        self._verbose_log_fn("Done prefetching asset records.")
        self._verbose_log_fn(
            f"Calculated a new latest_storage_id value of {self.get_new_latest_storage_id()}.\n"
            f"Precalculating updated parents for {len(self.auto_materialize_asset_keys)} assets using previous "
            f"latest_storage_id of {self.latest_storage_id}."
        )
        for asset_key in self.auto_materialize_asset_keys:
            self.instance_queryer.asset_partitions_with_newly_updated_parents(
                latest_storage_id=self.latest_storage_id, child_asset_key=asset_key
            )
        self._verbose_log_fn("Done precalculating updated parents.")

    @cached_method
    def get_new_latest_storage_id(self) -> Optional[int]:
        """Get the latest storage id across all cached asset records. We use this method as it uses
        identical data to what is used to calculate assets with updated parents, and therefore
        avoids certain classes of race conditions.
        """
        new_latest_storage_id = self.latest_storage_id
        for asset_key in self.auto_materialize_asset_keys_and_parents:
            # ignore non-observable sources
            if self.asset_graph.is_source(asset_key) and not self.asset_graph.is_observable(
                asset_key
            ):
                continue
            # ignore cases where we know for sure there's no new event
            if not self.instance_queryer.asset_partition_has_materialization_or_observation(
                AssetKeyPartitionKey(asset_key), after_cursor=self.latest_storage_id
            ):
                continue
            # get the latest overall storage id for this asset key
            asset_latest_storage_id = (
                self.instance_queryer.get_latest_materialization_or_observation_storage_id(
                    AssetKeyPartitionKey(asset_key)
                )
            )
            new_latest_storage_id = max(
                filter(None, [new_latest_storage_id, asset_latest_storage_id]), default=None
            )

        return new_latest_storage_id

    def evaluate_asset(
        self,
        asset_key: AssetKey,
        evaluation_results_by_key: Mapping[AssetKey, AssetConditionEvaluation],
        expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
    ) -> Tuple[AssetConditionEvaluation, AssetDaemonAssetCursor, Optional[datetime.datetime]]:
        """Evaluates the auto materialize policy of a given asset key.

        Params:
            - asset_key: The asset key to evaluate.
            - will_materialize_mapping: A mapping of AssetKey to the set of AssetKeyPartitionKeys
                that will be materialized this tick. As this function is called in topological order,
                this mapping will contain the expected materializations of all upstream assets.
            - expected_data_time_mapping: A mapping of AssetKey to the expected data time of the
                asset after this tick. As this function is called in topological order, this mapping
                will contain the expected data times of all upstream assets.

        """
        # convert the legacy AutoMaterializePolicy to an Evaluator
        asset_condition = check.not_none(
            self.asset_graph.auto_materialize_policies_by_key.get(asset_key)
        ).to_asset_condition()

        context = RootAssetConditionEvaluationContext(
            asset_key=asset_key,
            asset_cursor=self.cursor.asset_cursor_for_key(asset_key, self.asset_graph),
            root_condition=asset_condition,
            instance_queryer=self.instance_queryer,
            data_time_resolver=self.data_time_resolver,
            daemon_context=self,
            evaluation_results_by_key=evaluation_results_by_key,
            expected_data_time_mapping=expected_data_time_mapping,
        )
        condition_context = context.get_root_condition_context()

        evaluation = asset_condition.evaluate(condition_context)
        asset_cursor = context.get_new_asset_cursor(evaluation=evaluation)

        expected_data_time = get_expected_data_time_for_asset_key(
            context, will_materialize=evaluation.true_subset.size > 0
        )
        return evaluation, asset_cursor, expected_data_time

    def get_asset_condition_evaluations(
        self,
    ) -> Tuple[
        Sequence[AssetConditionEvaluation],
        Sequence[AssetDaemonAssetCursor],
        AbstractSet[AssetKeyPartitionKey],
    ]:
        """Returns a mapping from asset key to the AutoMaterializeAssetEvaluation for that key, a
        sequence of new per-asset cursors, and the set of all asset partitions that should be
        materialized or discarded this tick.
        """
        asset_cursors: List[AssetDaemonAssetCursor] = []

        evaluation_results_by_key: Dict[AssetKey, AssetConditionEvaluation] = {}
        expected_data_time_mapping: Dict[AssetKey, Optional[datetime.datetime]] = defaultdict()
        to_request: Set[AssetKeyPartitionKey] = set()

        num_checked_assets = 0
        num_auto_materialize_asset_keys = len(self.auto_materialize_asset_keys)

        visited_multi_asset_keys = set()
        for asset_key in itertools.chain(*self.asset_graph.toposort_asset_keys()):
            # an asset may have already been visited if it was part of a non-subsettable multi-asset
            if asset_key not in self.auto_materialize_asset_keys:
                continue

            num_checked_assets = num_checked_assets + 1
            start_time = time.time()
            self._verbose_log_fn(
                "Evaluating asset"
                f" {asset_key.to_user_string()} ({num_checked_assets}/{num_auto_materialize_asset_keys})"
            )

            if asset_key in visited_multi_asset_keys:
                self._verbose_log_fn(f"Asset {asset_key.to_user_string()} already visited")
                continue

            (evaluation, asset_cursor_for_asset, expected_data_time) = self.evaluate_asset(
                asset_key, evaluation_results_by_key, expected_data_time_mapping
            )

            num_requested = evaluation.true_subset.size
            log_fn = self._logger.info if num_requested > 0 else self._logger.debug

            to_request_asset_partitions = evaluation.true_subset.asset_partitions
            to_request_str = ",".join(
                [(ap.partition_key or "No partition") for ap in to_request_asset_partitions]
            )
            to_request |= to_request_asset_partitions

            log_fn(
                f"Asset {asset_key.to_user_string()} evaluation result: {num_requested}"
                f" requested ({to_request_str}) ({format(time.time()-start_time, '.3f')} seconds)"
            )

            evaluation_results_by_key[asset_key] = evaluation
            expected_data_time_mapping[asset_key] = expected_data_time
            asset_cursors.append(asset_cursor_for_asset)

            # if we need to materialize any partitions of a non-subsettable multi-asset, we need to
            # materialize all of them
            if num_requested > 0:
                for neighbor_key in self.asset_graph.get_required_multi_asset_keys(asset_key):
                    expected_data_time_mapping[neighbor_key] = expected_data_time
                    visited_multi_asset_keys.add(neighbor_key)
                    to_request |= {
                        ap._replace(asset_key=neighbor_key)
                        for ap in evaluation.true_subset.asset_partitions
                    }

        return (list(evaluation_results_by_key.values()), asset_cursors, to_request)

    def evaluate(
        self,
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AssetConditionEvaluation]]:
        observe_request_timestamp = pendulum.now().timestamp()
        auto_observe_run_requests = (
            get_auto_observe_run_requests(
                asset_graph=self.asset_graph,
                last_observe_request_timestamp_by_asset_key=self.cursor.last_observe_request_timestamp_by_asset_key,
                current_timestamp=observe_request_timestamp,
                run_tags=self._observe_run_tags,
                auto_observe_asset_keys=self._auto_observe_asset_keys,
            )
            if self._auto_observe_asset_keys
            else []
        )

        evaluations, asset_cursors, to_request = self.get_asset_condition_evaluations()

        run_requests = [
            *build_run_requests(
                asset_partitions=to_request,
                asset_graph=self.asset_graph,
                run_tags=self.auto_materialize_run_tags,
            ),
            *auto_observe_run_requests,
        ]

        return (
            run_requests,
            self.cursor.with_updates(
                latest_storage_id=self.get_new_latest_storage_id(),
                evaluation_id=self._evaluation_id,
                newly_observe_requested_asset_keys=[
                    asset_key
                    for run_request in auto_observe_run_requests
                    for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
                ],
                observe_request_timestamp=observe_request_timestamp,
                evaluations=evaluations,
                evaluation_time=self.instance_queryer.evaluation_time,
                asset_cursors=asset_cursors,
            ),
            # only record evaluations where something changed
            [
                evaluation
                for evaluation in evaluations
                if not evaluation.equivalent_to_stored_evaluation(
                    self.cursor.latest_evaluation_by_asset_key.get(evaluation.asset_key)
                )
            ],
        )


def build_run_requests(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: AssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    assets_to_reconcile_by_partitions_def_partition_key: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
    ] = defaultdict(set)

    for asset_partition in asset_partitions:
        assets_to_reconcile_by_partitions_def_partition_key[
            asset_graph.get_partitions_def(asset_partition.asset_key), asset_partition.partition_key
        ].add(asset_partition.asset_key)

    run_requests = []

    for (
        partitions_def,
        partition_key,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_key.items():
        tags = {**(run_tags or {})}
        if partition_key is not None:
            if partitions_def is None:
                check.failed("Partition key provided for unpartitioned asset")
            tags.update({**partitions_def.get_tags_for_partition_key(partition_key)})

        for asset_keys_in_repo in asset_graph.split_asset_keys_by_repository(asset_keys):
            run_requests.append(
                # Do not call run_request.with_resolved_tags_and_config as the partition key is
                # valid and there is no config.
                # Calling with_resolved_tags_and_config is costly in asset reconciliation as it
                # checks for valid partition keys.
                RunRequest(
                    asset_selection=list(asset_keys_in_repo),
                    partition_key=partition_key,
                    tags=tags,
                )
            )

    return run_requests


def build_run_requests_with_backfill_policies(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: AssetGraph,
    run_tags: Optional[Mapping[str, str]],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Sequence[RunRequest]:
    """If all assets have backfill policies, we should respect them and materialize them according
    to their backfill policies.
    """
    run_requests = []

    asset_partition_keys: Mapping[AssetKey, Set[str]] = {
        asset_key_partition.asset_key: set() for asset_key_partition in asset_partitions
    }
    for asset_partition in asset_partitions:
        if asset_partition.partition_key:
            asset_partition_keys[asset_partition.asset_key].add(asset_partition.partition_key)

    assets_to_reconcile_by_partitions_def_partition_keys: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[FrozenSet[str]]], Set[AssetKey]
    ] = defaultdict(set)

    # here we are grouping assets by their partitions def and partition keys selected.
    for asset_key, partition_keys in asset_partition_keys.items():
        assets_to_reconcile_by_partitions_def_partition_keys[
            asset_graph.get_partitions_def(asset_key),
            frozenset(partition_keys) if partition_keys else None,
        ].add(asset_key)

    for (
        partitions_def,
        partition_keys,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_keys.items():
        tags = {**(run_tags or {})}
        if partitions_def is None and partition_keys is not None:
            check.failed("Partition key provided for unpartitioned asset")
        if partitions_def is not None and partition_keys is None:
            check.failed("Partition key missing for partitioned asset")
        if partitions_def is None and partition_keys is None:
            # non partitioned assets will be backfilled in a single run
            run_requests.append(RunRequest(asset_selection=list(asset_keys), tags=tags))
        else:
            backfill_policies = {
                check.not_none(asset_graph.get_backfill_policy(asset_key))
                for asset_key in asset_keys
            }
            if len(backfill_policies) == 1:
                # if all backfill policies are the same, we can backfill them together
                backfill_policy = backfill_policies.pop()
                run_requests.extend(
                    _build_run_requests_with_backfill_policy(
                        list(asset_keys),
                        check.not_none(backfill_policy),
                        check.not_none(partition_keys),
                        check.not_none(partitions_def),
                        tags,
                        dynamic_partitions_store=dynamic_partitions_store,
                    )
                )
            else:
                # if backfill policies are different, we need to backfill them separately
                for asset_key in asset_keys:
                    backfill_policy = asset_graph.get_backfill_policy(asset_key)
                    run_requests.extend(
                        _build_run_requests_with_backfill_policy(
                            [asset_key],
                            check.not_none(backfill_policy),
                            check.not_none(partition_keys),
                            check.not_none(partitions_def),
                            tags,
                            dynamic_partitions_store=dynamic_partitions_store,
                        )
                    )
    return run_requests


def _build_run_requests_with_backfill_policy(
    asset_keys: Sequence[AssetKey],
    backfill_policy: BackfillPolicy,
    partition_keys: FrozenSet[str],
    partitions_def: PartitionsDefinition,
    tags: Dict[str, Any],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Sequence[RunRequest]:
    run_requests = []
    partition_subset = partitions_def.subset_with_partition_keys(partition_keys)
    partition_key_ranges = partition_subset.get_partition_key_ranges(
        partitions_def, dynamic_partitions_store=dynamic_partitions_store
    )
    for partition_key_range in partition_key_ranges:
        # We might resolve more than one partition key range for the given partition keys.
        # We can only apply chunking on individual partition key ranges.
        if backfill_policy.policy_type == BackfillPolicyType.SINGLE_RUN:
            run_requests.append(
                _build_run_request_for_partition_key_range(
                    asset_keys=list(asset_keys),
                    partition_range_start=partition_key_range.start,
                    partition_range_end=partition_key_range.end,
                    run_tags=tags,
                )
            )
        else:
            run_requests.extend(
                _build_run_requests_for_partition_key_range(
                    asset_keys=list(asset_keys),
                    partitions_def=partitions_def,
                    partition_key_range=partition_key_range,
                    max_partitions_per_run=check.int_param(
                        backfill_policy.max_partitions_per_run, "max_partitions_per_run"
                    ),
                    run_tags=tags,
                )
            )
    return run_requests


def _build_run_requests_for_partition_key_range(
    asset_keys: Sequence[AssetKey],
    partitions_def: PartitionsDefinition,
    partition_key_range: PartitionKeyRange,
    max_partitions_per_run: int,
    run_tags: Dict[str, str],
) -> Sequence[RunRequest]:
    """Builds multiple run requests for the given partition key range. Each run request will have at most
    max_partitions_per_run partitions.
    """
    partition_keys = partitions_def.get_partition_keys_in_range(partition_key_range)
    partition_range_start_index = partition_keys.index(partition_key_range.start)
    partition_range_end_index = partition_keys.index(partition_key_range.end)

    partition_chunk_start_index = partition_range_start_index
    run_requests = []
    while partition_chunk_start_index <= partition_range_end_index:
        partition_chunk_end_index = partition_chunk_start_index + max_partitions_per_run - 1
        if partition_chunk_end_index > partition_range_end_index:
            partition_chunk_end_index = partition_range_end_index
        partition_chunk_start_key = partition_keys[partition_chunk_start_index]
        partition_chunk_end_key = partition_keys[partition_chunk_end_index]
        run_requests.append(
            _build_run_request_for_partition_key_range(
                asset_keys, partition_chunk_start_key, partition_chunk_end_key, run_tags
            )
        )
        partition_chunk_start_index = partition_chunk_end_index + 1
    return run_requests


def _build_run_request_for_partition_key_range(
    asset_keys: Sequence[AssetKey],
    partition_range_start: str,
    partition_range_end: str,
    run_tags: Dict[str, str],
) -> RunRequest:
    """Builds a single run request for the given asset key and partition key range."""
    tags = {
        **(run_tags or {}),
        ASSET_PARTITION_RANGE_START_TAG: partition_range_start,
        ASSET_PARTITION_RANGE_END_TAG: partition_range_end,
    }
    return RunRequest(asset_selection=asset_keys, tags=tags)


def get_auto_observe_run_requests(
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float],
    current_timestamp: float,
    asset_graph: AssetGraph,
    run_tags: Optional[Mapping[str, str]],
    auto_observe_asset_keys: AbstractSet[AssetKey],
) -> Sequence[RunRequest]:
    assets_to_auto_observe: Set[AssetKey] = set()
    for asset_key in auto_observe_asset_keys:
        last_observe_request_timestamp = last_observe_request_timestamp_by_asset_key.get(asset_key)
        auto_observe_interval_minutes = asset_graph.get_auto_observe_interval_minutes(asset_key)

        if auto_observe_interval_minutes and (
            last_observe_request_timestamp is None
            or (
                last_observe_request_timestamp + auto_observe_interval_minutes * 60
                < current_timestamp
            )
        ):
            assets_to_auto_observe.add(asset_key)

    # create groups of asset keys that share the same repository AND the same partitions definition
    partitions_def_and_asset_key_groups: List[Sequence[AssetKey]] = []
    for repository_asset_keys in asset_graph.split_asset_keys_by_repository(assets_to_auto_observe):
        asset_keys_by_partitions_def = defaultdict(list)
        for asset_key in repository_asset_keys:
            partitions_def = asset_graph.get_partitions_def(asset_key)
            asset_keys_by_partitions_def[partitions_def].append(asset_key)
        partitions_def_and_asset_key_groups.extend(asset_keys_by_partitions_def.values())

    return [
        RunRequest(asset_selection=list(asset_keys), tags=run_tags)
        for asset_keys in partitions_def_and_asset_key_groups
        if len(asset_keys) > 0
    ]
