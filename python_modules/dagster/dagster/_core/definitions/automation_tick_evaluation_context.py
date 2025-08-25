import datetime
import logging
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, cast  # noqa: UP035

import dagster._check as check
from dagster import PartitionKeyRange
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_key import AssetCheckKey, EntityKey
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.graph.asset_graph_subset import AssetGraphSubset
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
from dagster._core.definitions.backfill_policy import BackfillPolicy, BackfillPolicyType
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
    AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_condition_evaluator import (
    AutomationConditionEvaluator,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionEvaluation,
)
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.partitions.context import use_partition_loading_context
from dagster._core.definitions.partitions.definition import PartitionsDefinition
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
        emit_backfills: bool,
        default_condition: Optional[AutomationCondition] = None,
        evaluation_time: Optional[datetime.datetime] = None,
    ):
        resolved_entity_keys = {
            entity_key
            for entity_key in (
                asset_selection.resolve(asset_graph) | asset_selection.resolve_checks(asset_graph)
            )
            if default_condition or asset_graph.get(entity_key).automation_condition is not None
        }
        self._total_keys = len(resolved_entity_keys)
        self._evaluation_id = evaluation_id
        self._evaluator = AutomationConditionEvaluator(
            entity_keys=resolved_entity_keys,
            default_condition=default_condition,
            instance=instance,
            asset_graph=asset_graph,
            emit_backfills=emit_backfills,
            cursor=cursor,
            evaluation_time=evaluation_time,
            logger=logger,
        )
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe_asset_keys = auto_observe_asset_keys or set()
        self._partition_loading_context = self._evaluator.asset_graph_view.partition_loading_context

    @property
    def cursor(self) -> AssetDaemonCursor:
        return self._evaluator.cursor

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self._evaluator.asset_graph

    @property
    def total_keys(self) -> int:
        return self._total_keys

    def _legacy_build_auto_observe_run_requests(self) -> Sequence[RunRequest]:
        current_timestamp = self._evaluator.evaluation_time.timestamp()
        assets_to_auto_observe: set[AssetKey] = set()
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
        partitions_def_and_asset_key_groups: list[Sequence[AssetKey]] = []
        for repository_asset_keys in self.asset_graph.split_entity_keys_by_repository(
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

    def _build_run_requests(self, entity_subsets: Sequence[EntitySubset]) -> Sequence[RunRequest]:
        return build_run_requests(
            entity_subsets=entity_subsets,
            asset_graph=self.asset_graph,
            run_tags=self._materialize_run_tags,
            emit_backfills=self._evaluator.emit_backfills,
        )

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
                    "Sequence[AssetKey]",
                    run_request.asset_selection,  # auto-observe run requests always have asset_selection
                )
            ],
            evaluation_timestamp=self._evaluator.evaluation_time.timestamp(),
            asset_graph=self.asset_graph,
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

    @use_partition_loading_context
    async def async_evaluate(
        self,
    ) -> tuple[
        Sequence[RunRequest], AssetDaemonCursor, Sequence[AutomationConditionEvaluation[EntityKey]]
    ]:
        observe_run_requests = self._legacy_build_auto_observe_run_requests()
        results, entity_subsets = await self._evaluator.async_evaluate()

        return (
            [*self._build_run_requests(entity_subsets), *observe_run_requests],
            self._get_updated_cursor(results, observe_run_requests),
            self._get_updated_evaluations(results),
        )

    @use_partition_loading_context
    def evaluate(
        self,
    ) -> tuple[
        Sequence[RunRequest], AssetDaemonCursor, Sequence[AutomationConditionEvaluation[EntityKey]]
    ]:
        observe_run_requests = self._legacy_build_auto_observe_run_requests()
        results, entity_subsets = self._evaluator.evaluate()

        return (
            [*self._build_run_requests(entity_subsets), *observe_run_requests],
            self._get_updated_cursor(results, observe_run_requests),
            self._get_updated_evaluations(results),
        )


_PartitionsDefKeyMapping = dict[
    tuple[Optional[PartitionsDefinition], Optional[str]], set[EntityKey]
]


def _get_mapping_from_entity_subsets(
    entity_subsets: Iterable[EntitySubset], asset_graph: BaseAssetGraph
) -> _PartitionsDefKeyMapping:
    mapping: _PartitionsDefKeyMapping = defaultdict(set)

    entity_subsets_by_key = {es.key: es for es in entity_subsets}
    for key in entity_subsets_by_key:
        if isinstance(key, AssetCheckKey) and key.asset_key in entity_subsets_by_key:
            # all asset checks are currently unpartitioned, so ensure that they get grouped
            # into a run with the asset they check if that asset is being requested this
            # tick
            partitions_def = asset_graph.get(key.asset_key).partitions_def
            subset = entity_subsets_by_key[key.asset_key]
        else:
            partitions_def = asset_graph.get(key).partitions_def
            subset = entity_subsets_by_key[key]

        if partitions_def:
            for asset_partition in subset.expensively_compute_asset_partitions():
                mapping[partitions_def, asset_partition.partition_key].add(key)
        else:
            mapping[partitions_def, None].add(key)

    return mapping


def _build_backfill_request(
    entity_subsets: Sequence[EntitySubset[EntityKey]],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> tuple[Optional[RunRequest], Sequence[EntitySubset[EntityKey]]]:
    """Determines a set of entity subsets that can be executed using a backfill.
    If any entity subset has size greater than 1, then it and all assets connected
    to it will be grouped into the backfill. Returns the corresponding backfill
    run request, and all entity subsets not handled in this process.
    """
    entity_subsets_by_key = {es.key: es for es in entity_subsets}
    visited: set[EntityKey] = set()
    backfill_subsets: list[EntitySubset[AssetKey]] = []

    def _flood_fill_asset_subsets(k: EntityKey):
        if k in visited or k not in entity_subsets_by_key:
            return []
        visited.add(k)
        if isinstance(k, AssetKey):
            node = asset_graph.get(k)
            if not node.is_materializable:
                # if the asset is not materializable, it cannot be included in a backfill
                return
            subset = cast("EntitySubset[AssetKey]", entity_subsets_by_key.pop(k))
            backfill_subsets.append(subset)
            for sk in [
                # include all parent and child assets
                *node.parent_keys,
                *node.child_keys,
                # include all asset keys and check keys that must be executed alongside
                # this asset key
                *asset_graph.get_execution_set_asset_and_check_keys(k),
            ]:
                _flood_fill_asset_subsets(sk)
        else:
            # if we get an asset check in this code path, it must have been part of
            # the required execution set of an asset that is being backfilled, and
            # therefore the backfill daemon will handle executing it without being
            # explicitly told to, so just remove it from the set of things to consider
            entity_subsets_by_key.pop(k)

    # list() here because we modify the dict in flood_fill
    for k, es in list(entity_subsets_by_key.items()):
        if k in visited or es.size <= 1 or isinstance(k, AssetCheckKey):
            continue
        # this entity subset should be backfilled, as should all of its
        # attached assets
        _flood_fill_asset_subsets(k)

    backfill_request = (
        RunRequest.for_asset_graph_subset(
            asset_graph_subset=AssetGraphSubset.from_entity_subsets(backfill_subsets),
            tags=run_tags,
        )
        if backfill_subsets
        else None
    )
    return backfill_request, list(entity_subsets_by_key.values())


def build_run_requests(
    entity_subsets: Sequence[EntitySubset],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
    emit_backfills: bool,
) -> Sequence[RunRequest]:
    """For a single asset in a given tick, the asset will only be part of a run or a backfill, not both.
    If the asset is targetd by a backfill, there will only be one backfill that targets the asset.
    """
    if emit_backfills:
        backfill_run_request, entity_subsets = _build_backfill_request(
            entity_subsets, asset_graph, run_tags
        )
    else:
        backfill_run_request = None

    run_requests = _build_run_requests_from_partitions_def_mapping(
        _get_mapping_from_entity_subsets(entity_subsets, asset_graph),
        asset_graph,
        run_tags,
    )
    if backfill_run_request:
        run_requests = [backfill_run_request, *run_requests]

    return run_requests


def _build_run_requests_from_partitions_def_mapping(
    mapping: _PartitionsDefKeyMapping,
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    run_requests = []

    for (partitions_def, partition_key), entity_keys in mapping.items():
        tags = {**(run_tags or {})}
        if partition_key is not None:
            if partitions_def is None:
                check.failed("Partition key provided for unpartitioned entity")
            tags.update({**partitions_def.get_tags_for_partition_key(partition_key)})

        for entity_keys_for_repo in asset_graph.split_entity_keys_by_repository(entity_keys):
            asset_check_keys = [k for k in entity_keys_for_repo if isinstance(k, AssetCheckKey)]
            run_requests.append(
                # Do not call run_request.with_resolved_tags_and_config as the partition key is
                # valid and there is no config.
                # Calling with_resolved_tags_and_config is costly in asset reconciliation as it
                # checks for valid partition keys.
                RunRequest(
                    asset_selection=[k for k in entity_keys_for_repo if isinstance(k, AssetKey)],
                    partition_key=partition_key,
                    tags=tags,
                    # if selecting no asset_check_keys, just pass in `None` to allow required
                    # checks to be included
                    asset_check_keys=asset_check_keys or None,
                )
            )

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
    """Build run requests for a selection of asset partitions based on the associated BackfillPolicies."""
    run_requests = []

    asset_partition_keys: Mapping[AssetKey, set[str]] = {
        asset_key_partition.asset_key: set() for asset_key_partition in asset_partitions
    }
    for asset_partition in asset_partitions:
        if asset_partition.partition_key:
            asset_partition_keys[asset_partition.asset_key].add(asset_partition.partition_key)

    assets_to_reconcile_by_partitions_def_partition_keys_backfill_policy: Mapping[
        tuple[Optional[PartitionsDefinition], Optional[frozenset[str]], Optional[BackfillPolicy]],
        set[AssetKey],
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
        asset_check_keys = asset_graph.get_check_keys_for_assets(asset_keys)
        if partitions_def is None and partition_keys is not None:
            check.failed("Partition key provided for unpartitioned asset")
        elif partitions_def is not None and partition_keys is None:
            check.failed("Partition key missing for partitioned asset")
        elif partitions_def is None and partition_keys is None:
            # non partitioned assets will be backfilled in a single run
            run_requests.append(
                RunRequest(
                    asset_selection=list(asset_keys),
                    asset_check_keys=list(asset_check_keys),
                    tags={},
                )
            )
        elif backfill_policy is None:
            # just use the normal single-partition behavior
            entity_keys = cast("set[EntityKey]", asset_keys)
            mapping: _PartitionsDefKeyMapping = {
                (partitions_def, pk): entity_keys for pk in (partition_keys or [None])
            }
            run_requests.extend(
                _build_run_requests_from_partitions_def_mapping(mapping, asset_graph, run_tags={})
            )
        else:
            run_requests.extend(
                _build_run_requests_with_backfill_policy(
                    list(asset_keys),
                    list(asset_check_keys),
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
    asset_check_keys: Sequence[AssetCheckKey],
    backfill_policy: BackfillPolicy,
    partition_keys: frozenset[str],
    partitions_def: PartitionsDefinition,
    tags: dict[str, Any],
    dynamic_partitions_store: DynamicPartitionsStore,
) -> Sequence[RunRequest]:
    run_requests = []
    partition_subset = partitions_def.subset_with_partition_keys(partition_keys)
    partition_key_ranges = partition_subset.get_partition_key_ranges(partitions_def)
    for partition_key_range in partition_key_ranges:
        # We might resolve more than one partition key range for the given partition keys.
        # We can only apply chunking on individual partition key ranges.
        if backfill_policy.policy_type == BackfillPolicyType.SINGLE_RUN:
            run_requests.append(
                _build_run_request_for_partition_key_range(
                    asset_keys=list(asset_keys),
                    asset_check_keys=list(asset_check_keys),
                    partition_range_start=partition_key_range.start,
                    partition_range_end=partition_key_range.end,
                    run_tags=tags,
                )
            )
        else:
            run_requests.extend(
                _build_run_requests_for_partition_key_range(
                    asset_keys=list(asset_keys),
                    asset_check_keys=list(asset_check_keys),
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
    asset_check_keys: Sequence[AssetCheckKey],
    partitions_def: PartitionsDefinition,
    partition_key_range: PartitionKeyRange,
    max_partitions_per_run: int,
    run_tags: dict[str, str],
    dynamic_partitions_store: DynamicPartitionsStore,
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
                asset_keys,
                asset_check_keys,
                partition_chunk_start_key,
                partition_chunk_end_key,
                run_tags,
            )
        )
        partition_chunk_start_index = partition_chunk_end_index + 1
    return run_requests


def _build_run_request_for_partition_key_range(
    asset_keys: Sequence[AssetKey],
    asset_check_keys: Sequence[AssetCheckKey],
    partition_range_start: str,
    partition_range_end: str,
    run_tags: dict[str, str],
) -> RunRequest:
    """Builds a single run request for the given asset key and partition key range."""
    tags = {
        **(run_tags or {}),
        ASSET_PARTITION_RANGE_START_TAG: partition_range_start,
        ASSET_PARTITION_RANGE_END_TAG: partition_range_end,
    }
    return RunRequest(
        asset_selection=asset_keys,
        partition_key=None,
        tags=tags,
        asset_check_keys=asset_check_keys,
    )
