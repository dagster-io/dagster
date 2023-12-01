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
)

import dagster._check as check
from dagster._core.definitions.asset_automation_evaluator import (
    ConditionEvaluation,
    ConditionEvaluationResult,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DynamicPartitionsStore

from ... import PartitionKeyRange
from ..storage.tags import ASSET_PARTITION_RANGE_END_TAG, ASSET_PARTITION_RANGE_START_TAG
from .asset_automation_condition import AssetAutomationEvaluationContext
from .asset_daemon_cursor import AssetDaemonCursor
from .asset_graph import AssetGraph
from .backfill_policy import BackfillPolicy, BackfillPolicyType
from .partition import PartitionsDefinition

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


class AssetDaemonContext:
    def __init__(
        self,
        evaluation_id: int,
        instance: "DagsterInstance",
        asset_graph: AssetGraph,
        cursor: AssetDaemonCursor,
        materialize_run_tags: Optional[Mapping[str, str]],
        observe_run_tags: Optional[Mapping[str, str]],
        auto_observe: bool,
        target_asset_keys: Optional[AbstractSet[AssetKey]],
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
        self._target_asset_keys = target_asset_keys or {
            key
            for key, policy in self.asset_graph.auto_materialize_policies_by_key.items()
            if policy is not None
        }
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe = auto_observe
        self._respect_materialization_data_versions = respect_materialization_data_versions
        self._logger = logger

        # fetch some data in advance to batch some queries
        self.instance_queryer.prefetch_asset_records(
            [
                key
                for key in self.target_asset_keys_and_parents
                if not self.asset_graph.is_source(key)
            ]
        )

        self._verbose_log_fn = (
            self._logger.info if os.getenv("ASSET_DAEMON_VERBOSE_LOGS") else self._logger.debug
        )

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
    def target_asset_keys(self) -> AbstractSet[AssetKey]:
        return self._target_asset_keys

    @property
    def target_asset_keys_and_parents(self) -> AbstractSet[AssetKey]:
        return {
            parent
            for asset_key in self.target_asset_keys
            for parent in self.asset_graph.get_parents(asset_key)
        } | self.target_asset_keys

    def for_asset(
        self,
        asset_key: AssetKey,
        evaluation_results_by_key: Mapping[AssetKey, ConditionEvaluationResult],
    ) -> AssetAutomationEvaluationContext:
        return AssetAutomationEvaluationContext(
            asset_key=asset_key,
            asset_cursor=self.cursor.get_asset_cursor(asset_key),
            instance_queryer=self.instance_queryer,
            data_time_resolver=self.data_time_resolver,
            evaluation_results_by_key=evaluation_results_by_key,
        )

    def get_evaluation_results(self) -> Sequence[ConditionEvaluationResult]:
        """Returns a mapping from asset key to the result of evaluating the asset's conditions."""
        evaluation_results_by_key: Dict[AssetKey, ConditionEvaluationResult] = {}
        visited_multi_asset_keys = set()

        num_checked_assets = 0
        num_target_asset_keys = len(self.target_asset_keys)

        for asset_key in itertools.chain(*self.asset_graph.toposort_asset_keys()):
            if asset_key not in self.target_asset_keys:
                continue

            num_checked_assets = num_checked_assets + 1
            start_time = time.time()
            self._verbose_log_fn(
                "Evaluating asset"
                f" {asset_key.to_user_string()} ({num_checked_assets}/{num_target_asset_keys})"
            )

            # an asset may have already been visited if it was part of a non-subsettable multi-asset
            if asset_key in visited_multi_asset_keys:
                self._verbose_log_fn(f"Asset {asset_key.to_user_string()} already visited")
                continue

            condition = (
                check.not_none(self.asset_graph.get_auto_materialize_policy(asset_key))
                .to_auto_materialize_policy_evaluator()
                .condition
            )
            result: ConditionEvaluationResult = condition.evaluate(
                context=self.for_asset(asset_key, evaluation_results_by_key)
            )

            log_fn = self._logger.info if result.true_subset.size else self._logger.debug
            log_fn(
                f"Asset {asset_key.to_user_string()} evaluation result: {result.true_subset.size}"
                f" ({format(time.time()-start_time, '.3f')} seconds)"
            )

        return list(evaluation_results_by_key.values())

    def evaluate(
        self
    ) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[ConditionEvaluation]]:
        evaluation_results = self.get_evaluation_results()

        run_requests = build_run_requests(
            asset_partitions=set().union(
                *(result.true_subset.asset_partitions for result in evaluation_results)
            ),
            asset_graph=self.asset_graph,
            run_tags=self._materialize_run_tags,
        )

        return (
            run_requests,
            AssetDaemonCursor(
                evaluation_id=self._evaluation_id + 1,
                asset_cursors=[result.to_asset_cursor() for result in evaluation_results],
            ),
            # only record evaluations where something changed
            [
                result.evaluation
                for result in evaluation_results
                if not result.evaluation.is_equivalent(
                    self.cursor.get_latest_evaluation(result.asset_key)
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
) -> Sequence[RunRequest]:
    assets_to_auto_observe: Set[AssetKey] = set()
    for asset_key in asset_graph.source_asset_keys:
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
