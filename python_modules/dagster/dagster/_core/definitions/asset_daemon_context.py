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

import pendulum

import dagster._check as check
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._core.definitions.declarative_automation.automation_condition import AutomationResult
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.time_window_partitions import get_time_partitions_def
from dagster._core.instance import DynamicPartitionsStore

from ... import PartitionKeyRange
from ..storage.tags import ASSET_PARTITION_RANGE_END_TAG, ASSET_PARTITION_RANGE_START_TAG
from .asset_daemon_cursor import AssetDaemonCursor
from .auto_materialize_rule import AutoMaterializeRule
from .backfill_policy import BackfillPolicy, BackfillPolicyType
from .base_asset_graph import BaseAssetGraph
from .declarative_automation.serialized_objects import AssetConditionEvaluation
from .partition import PartitionsDefinition, ScheduleType

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


def get_implicit_auto_materialize_policy(
    asset_key: AssetKey, asset_graph: BaseAssetGraph
) -> Optional[AutoMaterializePolicy]:
    """For backcompat with pre-auto materialize policy graphs, assume a default scope of 1 day."""
    auto_materialize_policy = asset_graph.get(asset_key).auto_materialize_policy
    if auto_materialize_policy is None:
        time_partitions_def = get_time_partitions_def(asset_graph.get(asset_key).partitions_def)
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
        asset_graph: BaseAssetGraph,
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

        stale_resolver = CachingStaleStatusResolver(
            instance=instance, asset_graph=asset_graph, instance_queryer=self.instance_queryer
        )
        self._asset_graph_view = AssetGraphView(
            temporal_context=TemporalContext(
                effective_dt=self.instance_queryer.evaluation_time,
                last_event_id=instance.event_log_storage.get_maximum_record_id(),
            ),
            stale_resolver=stale_resolver,
        )
        self._data_time_resolver = CachingDataTimeResolver(self.instance_queryer)
        self._cursor = cursor
        self._auto_materialize_asset_keys = auto_materialize_asset_keys or set()
        self._materialize_run_tags = materialize_run_tags
        self._observe_run_tags = observe_run_tags
        self._auto_observe_asset_keys = auto_observe_asset_keys or set()
        self._respect_materialization_data_versions = respect_materialization_data_versions
        self._logger = logger

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def instance_queryer(self) -> "CachingInstanceQueryer":
        return self._instance_queryer

    @property
    def data_time_resolver(self) -> CachingDataTimeResolver:
        return self._data_time_resolver

    @property
    def asset_graph_view(self) -> AssetGraphView:
        return self._asset_graph_view

    @property
    def cursor(self) -> AssetDaemonCursor:
        return self._cursor

    @property
    def asset_graph(self) -> BaseAssetGraph:
        return self.instance_queryer.asset_graph

    @property
    def auto_materialize_asset_keys(self) -> AbstractSet[AssetKey]:
        return self._auto_materialize_asset_keys

    @property
    def respect_materialization_data_versions(self) -> bool:
        return self._respect_materialization_data_versions

    @property
    def auto_materialize_run_tags(self) -> Mapping[str, str]:
        return self._materialize_run_tags or {}

    def get_asset_condition_evaluations(
        self,
    ) -> Tuple[Sequence[AutomationResult], AbstractSet[AssetKeyPartitionKey]]:
        """Returns a mapping from asset key to the AutoMaterializeAssetEvaluation for that key, a
        sequence of new per-asset cursors, and the set of all asset partitions that should be
        materialized or discarded this tick.
        """
        from .declarative_automation.automation_condition_evaluator import (
            AutomationConditionEvaluator,
        )

        evaluator = AutomationConditionEvaluator(
            asset_graph=self.asset_graph,
            asset_keys=self.auto_materialize_asset_keys,
            asset_graph_view=self.asset_graph_view,
            logger=self._logger,
            cursor=self.cursor,
            data_time_resolver=self.data_time_resolver,
            respect_materialization_data_versions=self.respect_materialization_data_versions,
            auto_materialize_run_tags=self.auto_materialize_run_tags,
        )
        return evaluator.evaluate()

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

        results, to_request = self.get_asset_condition_evaluations()

        run_requests = [
            *build_run_requests(
                asset_partitions=to_request,
                asset_graph=self.asset_graph,
                run_tags=self.auto_materialize_run_tags,
            ),
            *auto_observe_run_requests,
        ]

        # only record evaluation results where something changed
        updated_evaluations = []
        for result in results:
            previous_cursor = self.cursor.get_previous_condition_cursor(result.asset_key)
            if (
                previous_cursor is None
                or previous_cursor.result_value_hash != result.value_hash
                or not result.true_slice.is_empty
            ):
                updated_evaluations.append(result.serializable_evaluation)

        return (
            run_requests,
            self.cursor.with_updates(
                evaluation_id=self._evaluation_id,
                condition_cursors=[result.get_new_cursor() for result in results],
                newly_observe_requested_asset_keys=[
                    asset_key
                    for run_request in auto_observe_run_requests
                    for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
                ],
                evaluation_timestamp=self.instance_queryer.evaluation_time.timestamp(),
            ),
            updated_evaluations,
        )


def build_run_requests(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
) -> Sequence[RunRequest]:
    assets_to_reconcile_by_partitions_def_partition_key: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
    ] = defaultdict(set)

    for asset_partition in asset_partitions:
        assets_to_reconcile_by_partitions_def_partition_key[
            asset_graph.get(asset_partition.asset_key).partitions_def, asset_partition.partition_key
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

    # We don't make public guarantees about sort order, but make an effort to provide a consistent
    # ordering that puts earlier time partitions before later time partitions. Note that, with dates
    # formatted like 12/7/2023, the run requests won't end up in time order. Sorting by converting
    # to time windows seemed more risky from a perf perspective, so we didn't include it here, but
    # it could make sense to actually benchmark that in the future.
    return sorted(run_requests, key=lambda x: x.partition_key if x.partition_key else "")


def build_run_requests_with_backfill_policies(
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: BaseAssetGraph,
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
        tags = {**(run_tags or {})}
        if partitions_def is None and partition_keys is not None:
            check.failed("Partition key provided for unpartitioned asset")
        if partitions_def is not None and partition_keys is None:
            check.failed("Partition key missing for partitioned asset")
        if partitions_def is None and partition_keys is None:
            # non partitioned assets will be backfilled in a single run
            run_requests.append(RunRequest(asset_selection=list(asset_keys), tags=tags))
        else:
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


def get_auto_observe_run_requests(
    last_observe_request_timestamp_by_asset_key: Mapping[AssetKey, float],
    current_timestamp: float,
    asset_graph: BaseAssetGraph,
    run_tags: Optional[Mapping[str, str]],
    auto_observe_asset_keys: AbstractSet[AssetKey],
) -> Sequence[RunRequest]:
    assets_to_auto_observe: Set[AssetKey] = set()
    for asset_key in auto_observe_asset_keys:
        last_observe_request_timestamp = last_observe_request_timestamp_by_asset_key.get(asset_key)
        auto_observe_interval_minutes = asset_graph.get(asset_key).auto_observe_interval_minutes

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
            partitions_def = asset_graph.get(asset_key).partitions_def
            asset_keys_by_partitions_def[partitions_def].append(asset_key)
        partitions_def_and_asset_key_groups.extend(asset_keys_by_partitions_def.values())

    return [
        RunRequest(asset_selection=list(asset_keys), tags=run_tags)
        for asset_keys in partitions_def_and_asset_key_groups
        if len(asset_keys) > 0
    ]
