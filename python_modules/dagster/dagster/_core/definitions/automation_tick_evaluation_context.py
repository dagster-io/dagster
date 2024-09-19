import datetime
import logging
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

import dagster._check as check
from dagster import PartitionKeyRange
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.asset_key import AssetCheckKey, EntityKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType
from dagster._core.definitions.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.run_request import RunRequest
from dagster._core.instance import DynamicPartitionsStore
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class AutomationTickEvaluationContext:
    def __init__(
        self,
        evaluation_id: int,
        instance: "DagsterInstance",
        asset_graph: BaseAssetGraph,
        cursor: AssetDaemonCursor,
        materialize_run_tags: Mapping[str, str],
        observe_run_tags: Mapping[str, str],
        auto_observe_asset_keys: AbstractSet[AssetKey],
        asset_selection: AssetSelection,
        logger: logging.Logger,
        evaluation_time: Optional[datetime.datetime] = None,
    ):
        resolved_entity_keys = {
            entity_key
            # for now, all checks of a given asset will be evaluated at the same time as it
            for entity_key in asset_selection.resolve(asset_graph)
            | asset_selection.resolve_checks(asset_graph)
            if asset_graph.get(entity_key).automation_condition is not None
        }
        self._evaluation_id = evaluation_id
        self._evaluator = AutomationConditionEvaluator(
            entity_keys=resolved_entity_keys,
            instance=instance,
            asset_graph=asset_graph,
            cursor=cursor,
            evaluation_time=evaluation_time,
            logger=logger,
        )
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe_asset_keys = auto_observe_asset_keys or set()

    @property
    def cursor(self) -> AssetDaemonCursor:
        return self._evaluator.cursor

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self._evaluator.asset_graph

    def _legacy_build_auto_observe_run_requests(self) -> Sequence[RunRequest]:
        current_timestamp = self._evaluator.evaluation_time.timestamp()
        assets_to_auto_observe: Set[AssetKey] = set()
        for asset_key in self._auto_observe_asset_keys:
            last_observe_request_timestamp = (
                self.cursor.last_observe_request_timestamp_by_asset_key.get(asset_key)
            )
            auto_observe_interval_minutes = self.asset_graph.get(
                asset_key
            ).auto_observe_interval_minutes

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
        for repository_asset_keys in self.asset_graph.split_asset_keys_by_repository(
            assets_to_auto_observe
        ):
            asset_keys_by_partitions_def = defaultdict(list)
            for asset_key in repository_asset_keys:
                partitions_def = self.asset_graph.get(asset_key).partitions_def
                asset_keys_by_partitions_def[partitions_def].append(asset_key)
            partitions_def_and_asset_key_groups.extend(asset_keys_by_partitions_def.values())

        return [
            RunRequest(asset_selection=list(asset_keys), tags=self._observe_run_tags)
            for asset_keys in partitions_def_and_asset_key_groups
            if len(asset_keys) > 0
        ]

    def _build_run_requests(self, entity_subsets: Iterable[EntitySubset]) -> Sequence[RunRequest]:
        if self._evaluator.request_backfills:
            asset_subsets = cast(
                Iterable[EntitySubset[AssetKey]],
                [subset for subset in entity_subsets if isinstance(subset.key, AssetKey)],
            )

            run_requests = (
                [
                    RunRequest.for_asset_graph_subset(
                        asset_graph_subset=AssetGraphSubset.from_entity_subsets(asset_subsets),
                        tags=self._materialize_run_tags,
                    )
                ]
                if asset_subsets
                else []
            )
        else:
            run_requests = build_run_requests(
                entity_subsets=entity_subsets,
                asset_graph=self.asset_graph,
                run_tags=self._materialize_run_tags,
            )

        return run_requests

    def _get_updated_cursor(
        self, results: Iterable[AutomationResult], observe_run_requests: Iterable[RunRequest]
    ) -> AssetDaemonCursor:
        return self.cursor.with_updates(
            evaluation_id=self._evaluation_id,
            condition_cursors=[result.get_new_cursor() for result in results],
            newly_observe_requested_asset_keys=[
                asset_key
                for run_request in observe_run_requests
                for asset_key in cast(
                    Sequence[AssetKey],
                    run_request.asset_selection,  # auto-observe run requests always have asset_selection
                )
            ],
            evaluation_timestamp=self._evaluator.evaluation_time.timestamp(),
        )

    def _get_updated_evaluations(
        self, results: Iterable[AutomationResult]
    ) -> Sequence[AutomationConditionEvaluation[EntityKey]]:
        # only record evaluation results where something changed
        updated_evaluations = []
        for result in results:
            previous_cursor = self.cursor.get_previous_condition_cursor(result.key)
            if (
                previous_cursor is None
                or previous_cursor.result_value_hash != result.value_hash
                or not result.true_subset.is_empty
            ):
                updated_evaluations.append(result.serializable_evaluation)
        return updated_evaluations

    def evaluate(
        self,
    ) -> Tuple[
        Sequence[RunRequest], AssetDaemonCursor, Sequence[AutomationConditionEvaluation[EntityKey]]
    ]:
        observe_run_requests = self._legacy_build_auto_observe_run_requests()
        results, entity_subsets = self._evaluator.evaluate()

        return (
            [*self._build_run_requests(entity_subsets), *observe_run_requests],
            self._get_updated_cursor(results, observe_run_requests),
            self._get_updated_evaluations(results),
        )


_PartitionsDefKeyAssetKeyMapping = Dict[
    Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
]
_AssetKeyCheckKeysMapping = Dict[AssetKey, Set[AssetCheckKey]]


def _get_mappings_from_asset_partitions(
    asset_partitions: AbstractSet[AssetKeyPartitionKey], asset_graph: BaseAssetGraph
) -> Tuple[_PartitionsDefKeyAssetKeyMapping, _AssetKeyCheckKeysMapping]:
    asset_mapping: _PartitionsDefKeyAssetKeyMapping = defaultdict(set)

    for asset_partition in asset_partitions:
        asset_mapping[
            asset_graph.get(asset_partition.asset_key).partitions_def, asset_partition.partition_key
        ].add(asset_partition.asset_key)

    return asset_mapping, {}


def _get_mappings_from_entity_subsets(
    entity_subsets: Iterable[EntitySubset], asset_graph: BaseAssetGraph
) -> Tuple[_PartitionsDefKeyAssetKeyMapping, _AssetKeyCheckKeysMapping]:
    asset_mapping: _PartitionsDefKeyAssetKeyMapping = defaultdict(set)
    asset_check_mapping: _AssetKeyCheckKeysMapping = defaultdict(set)

    for subset in entity_subsets:
        if isinstance(subset.key, AssetCheckKey):
            if not subset.is_empty:
                asset_check_mapping[subset.key.asset_key].add(subset.key)
        elif isinstance(subset.key, AssetKey):
            partitions_def = asset_graph.get(subset.key).partitions_def
            for asset_partition in subset.expensively_compute_asset_partitions():
                asset_mapping[partitions_def, asset_partition.partition_key].add(
                    asset_partition.asset_key
                )

    return asset_mapping, asset_check_mapping


def build_run_requests_from_asset_partitions(
    asset_partitions: AbstractSet[AssetKeyPartitionKey],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    return _build_run_requests_from_partitions_def_mapping(
        _get_mappings_from_asset_partitions(asset_partitions, asset_graph),
        asset_graph,
        run_tags,
    )


def build_run_requests(
    entity_subsets: Iterable[EntitySubset[EntityKey]],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    return _build_run_requests_from_partitions_def_mapping(
        _get_mappings_from_entity_subsets(entity_subsets, asset_graph),
        asset_graph,
        run_tags,
    )


def _build_run_requests_from_partitions_def_mapping(
    mappings: Tuple[_PartitionsDefKeyAssetKeyMapping, _AssetKeyCheckKeysMapping],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    run_requests = []

    partitions_def_mapping, check_keys_to_execute_by_key = mappings

    for (
        partitions_def,
        partition_key,
    ), asset_keys in partitions_def_mapping.items():
        tags = {**(run_tags or {})}
        if partition_key is not None:
            if partitions_def is None:
                check.failed("Partition key provided for unpartitioned asset")
            tags.update({**partitions_def.get_tags_for_partition_key(partition_key)})

        for asset_keys_in_repo in asset_graph.split_asset_keys_by_repository(asset_keys):
            # get all checks that are attached to a selected asset
            asset_check_keys = set()
            for ak in asset_keys_in_repo:
                if ak in check_keys_to_execute_by_key:
                    asset_check_keys.union(check_keys_to_execute_by_key[ak])
                    del check_keys_to_execute_by_key[ak]

            run_requests.append(
                # Do not call run_request.with_resolved_tags_and_config as the partition key is
                # valid and there is no config.
                # Calling with_resolved_tags_and_config is costly in asset reconciliation as it
                # checks for valid partition keys.
                RunRequest(
                    asset_selection=list(asset_keys_in_repo),
                    partition_key=partition_key,
                    tags=tags,
                    asset_check_keys=list(asset_check_keys),
                )
            )

    # asset checks that are not being executed alongside any assets
    remaining_check_keys = set().union(*check_keys_to_execute_by_key.values())
    if remaining_check_keys:
        run_requests.append(RunRequest(tags=run_tags, asset_check_keys=list(remaining_check_keys)))

    # We don't make public guarantees about sort order, but make an effort to provide a consistent
    # ordering that puts earlier time partitions before later time partitions. Note that, with dates
    # formatted like 12/7/2023, the run requests won't end up in time order. Sorting by converting
    # to time windows seemed more risky from a perf perspective, so we didn't include it here, but
    # it could make sense to actually benchmark that in the future.
    return sorted(run_requests, key=lambda x: x.partition_key if x.partition_key else "")


def build_run_requests_with_backfill_policies(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: BaseAssetGraph,
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

    assets_to_reconcile_by_partitions_def_partition_keys_backfill_policy: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[FrozenSet[str]], Optional[BackfillPolicy]],
        Set[AssetKey],
    ] = defaultdict(set)

    # here we are grouping assets by their partitions def, selected partition keys, and backfill policy.
    for asset_key, partition_keys in asset_partition_keys.items():
        assets_to_reconcile_by_partitions_def_partition_keys_backfill_policy[
            asset_graph.get(asset_key).partitions_def,
            frozenset(partition_keys) if partition_keys else None,
            asset_graph.get(asset_key).backfill_policy,
        ].add(asset_key)

    for (
        partitions_def,
        partition_keys,
        backfill_policy,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_keys_backfill_policy.items():
        if partitions_def is None and partition_keys is not None:
            check.failed("Partition key provided for unpartitioned asset")
        if partitions_def is not None and partition_keys is None:
            check.failed("Partition key missing for partitioned asset")
        if partitions_def is None and partition_keys is None:
            # non partitioned assets will be backfilled in a single run
            run_requests.append(RunRequest(asset_selection=list(asset_keys), tags={}))
        else:
            run_requests.extend(
                _build_run_requests_with_backfill_policy(
                    list(asset_keys),
                    check.not_none(backfill_policy),
                    check.not_none(partition_keys),
                    check.not_none(partitions_def),
                    tags={},
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
                    dynamic_partitions_store=dynamic_partitions_store,
                )
            )
    return run_requests


def _build_run_requests_for_partition_key_range(
    asset_keys: Sequence[AssetKey],
    partitions_def: PartitionsDefinition,
    partition_key_range: PartitionKeyRange,
    max_partitions_per_run: int,
    run_tags: Dict[str, str],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Sequence[RunRequest]:
    """Builds multiple run requests for the given partition key range. Each run request will have at most
    max_partitions_per_run partitions.
    """
    partition_keys = partitions_def.get_partition_keys_in_range(
        partition_key_range, dynamic_partitions_store=dynamic_partitions_store
    )
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
    partition_key = partition_range_start if partition_range_start == partition_range_end else None
    return RunRequest(asset_selection=asset_keys, partition_key=partition_key, tags=tags)
