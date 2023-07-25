import datetime
import itertools
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import pendulum

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.time_window_partitions import (
    get_time_partitions_def,
)
from dagster._utils.backcompat import deprecation_warning

from .asset_daemon_cursor import AssetDaemonCursor
from .asset_graph import AssetGraph
from .asset_selection import AssetSelection
from .auto_materialize_condition import (
    AutoMaterializeAssetEvaluation,
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    MaxMaterializationsExceededAutoMaterializeCondition,
    MissingAutoMaterializeCondition,
    ParentMaterializedAutoMaterializeCondition,
    ParentOutdatedAutoMaterializeCondition,
)
from .decorators.sensor_decorator import sensor
from .freshness_based_auto_materialize import (
    determine_asset_partitions_to_auto_materialize_for_freshness,
)
from .partition import (
    PartitionsDefinition,
    ScheduleType,
)
from .run_request import RunRequest
from .sensor_definition import DefaultSensorStatus, SensorDefinition
from .utils import check_valid_name

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import


def get_implicit_auto_materialize_policy(
    asset_graph: AssetGraph, asset_key: AssetKey
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
        return AutoMaterializePolicy(
            on_missing=True,
            on_new_parent_data=not bool(
                asset_graph.get_downstream_freshness_policies(asset_key=asset_key)
            ),
            for_freshness=True,
            max_materializations_per_minute=max_materializations_per_minute,
        )
    return auto_materialize_policy


def find_never_handled_root_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetDaemonCursor,
    target_asset_keys: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
) -> Tuple[
    Iterable[AssetKeyPartitionKey], AbstractSet[AssetKey], Mapping[AssetKey, AbstractSet[str]]
]:
    """Finds asset partitions that have never been materialized or requested and that have no
    parents.

    Returns:
    - Asset (partition)s that have never been materialized or requested.
    - Non-partitioned assets that had never been materialized or requested up to the previous cursor
        but are now materialized.
    - Asset (partition)s that had never been materialized or requested up to the previous cursor but
        are now materialized.
    """
    never_handled = set()
    newly_materialized_root_asset_keys = set()
    newly_materialized_root_partitions_by_asset_key = defaultdict(set)

    for asset_key in target_asset_keys & asset_graph.root_asset_keys:
        if asset_graph.is_partitioned(asset_key):
            for partition_key in cursor.get_unhandled_partitions(
                asset_key,
                asset_graph,
                dynamic_partitions_store=instance_queryer,
                current_time=instance_queryer.evaluation_time,
            ):
                asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                if instance_queryer.asset_partition_has_materialization_or_observation(
                    asset_partition
                ):
                    newly_materialized_root_partitions_by_asset_key[asset_key].add(partition_key)
                else:
                    never_handled.add(asset_partition)
        else:
            if not cursor.was_previously_handled(asset_key):
                asset_partition = AssetKeyPartitionKey(asset_key)
                if instance_queryer.asset_partition_has_materialization_or_observation(
                    asset_partition
                ):
                    newly_materialized_root_asset_keys.add(asset_key)
                else:
                    never_handled.add(asset_partition)

    return (
        never_handled,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    )


def _will_materialize_for_conditions(
    conditions: Optional[AbstractSet[AutoMaterializeCondition]],
) -> bool:
    """Based on a set of conditions, determine if the asset will be materialized."""
    return (
        AutoMaterializeDecisionType.from_conditions(conditions)
        == AutoMaterializeDecisionType.MATERIALIZE
    )


def determine_asset_partitions_to_auto_materialize(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetDaemonCursor,
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
    conditions_by_asset_partition_for_freshness: Mapping[
        AssetKeyPartitionKey, Set[AutoMaterializeCondition]
    ],
) -> Tuple[
    Mapping[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]],
    AbstractSet[AssetKey],
    Mapping[AssetKey, AbstractSet[str]],
    Optional[int],
]:
    evaluation_time = instance_queryer.evaluation_time

    (
        never_handled_roots,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    ) = find_never_handled_root_asset_partitions(
        instance_queryer=instance_queryer,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        asset_graph=asset_graph,
    )

    # initialize conditions with the conditions_for_freshness
    conditions_by_asset_partition: Dict[
        AssetKeyPartitionKey, Set[AutoMaterializeCondition]
    ] = defaultdict(set, conditions_by_asset_partition_for_freshness)
    materialization_requests_by_asset_key: Dict[AssetKey, Set[AssetKeyPartitionKey]] = defaultdict(
        set
    )

    def can_reconcile_candidate(candidate: AssetKeyPartitionKey) -> bool:
        """A filter for eliminating candidates from consideration for auto-materialization."""
        auto_materialize_policy = get_implicit_auto_materialize_policy(
            asset_graph=asset_graph, asset_key=candidate.asset_key
        )

        return not (
            # must have an auto_materialize_policy
            auto_materialize_policy is None
            # must be in the taget set
            or candidate.asset_key not in target_asset_keys
            # must not be currently backfilled
            or candidate in instance_queryer.get_active_backfill_target_asset_graph_subset()
            # must not have invalid parent partitions
            or len(
                asset_graph.get_parents_partitions(
                    instance_queryer,
                    instance_queryer.evaluation_time,
                    candidate.asset_key,
                    candidate.partition_key,
                ).required_but_nonexistent_parents_partitions
            )
            > 0
        )

    (
        stale_candidates,
        latest_storage_id,
    ) = instance_queryer.asset_partitions_with_newly_updated_parents_and_new_latest_storage_id(
        latest_storage_id=cursor.latest_storage_id,
        target_asset_keys=frozenset(target_asset_keys),
        target_asset_keys_and_parents=frozenset(target_asset_keys_and_parents),
        can_reconcile_fn=can_reconcile_candidate,
        map_old_time_partitions=False,
    )

    def get_waiting_on_asset_keys(candidate: AssetKeyPartitionKey) -> FrozenSet[AssetKey]:
        """Returns the set of ancestor asset keys that must be materialized before this asset can be
        materialized.
        """
        from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

        unreconciled_ancestors = set()
        for parent in asset_graph.get_parents_partitions(
            instance_queryer,
            instance_queryer.evaluation_time,
            candidate.asset_key,
            candidate.partition_key,
        ).parent_partitions:
            # parent will not be materialized this tick
            if not (
                _will_materialize_for_conditions(conditions_by_asset_partition.get(parent))
                # the parent must have the same partitioning / partition key to be materialized
                # alongside the candidate
                and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                and parent.partition_key == candidate.partition_key
                # the parent must be in the same repository to be materialized alongside the candidate
                and (
                    not isinstance(asset_graph, ExternalAssetGraph)
                    or asset_graph.get_repository_handle(candidate.asset_key)
                    == asset_graph.get_repository_handle(parent.asset_key)
                )
            ):
                unreconciled_ancestors.update(
                    instance_queryer.get_root_unreconciled_ancestors(asset_partition=parent)
                )
        return frozenset(unreconciled_ancestors)

    def conditions_for_candidate(
        candidate: AssetKeyPartitionKey,
    ) -> AbstractSet[AutoMaterializeCondition]:
        """Returns a set of AutoMaterializeConditions that apply to a given candidate."""
        auto_materialize_policy = check.not_none(
            get_implicit_auto_materialize_policy(
                asset_graph=asset_graph, asset_key=candidate.asset_key
            )
        )
        conditions = set()

        # if this asset is missing
        if (
            auto_materialize_policy.on_missing
            and not instance_queryer.asset_partition_has_materialization_or_observation(
                asset_partition=candidate
            )
        ):
            conditions.add(MissingAutoMaterializeCondition())

        # if parent data has been updated or will update
        elif auto_materialize_policy.on_new_parent_data:
            if not asset_graph.is_source(candidate.asset_key):
                parent_asset_partitions = asset_graph.get_parents_partitions(
                    dynamic_partitions_store=instance_queryer,
                    current_time=evaluation_time,
                    asset_key=candidate.asset_key,
                    partition_key=candidate.partition_key,
                ).parent_partitions

                (
                    updated_parent_asset_partitions,
                    _,
                ) = instance_queryer.get_updated_and_missing_parent_asset_partitions(
                    candidate, parent_asset_partitions
                )
                updated_parents = {parent.asset_key for parent in updated_parent_asset_partitions}

                will_update_parents = set()
                for parent in parent_asset_partitions:
                    if _will_materialize_for_conditions(conditions_by_asset_partition.get(parent)):
                        will_update_parents.add(parent.asset_key)

                if updated_parents or will_update_parents:
                    conditions.add(
                        ParentMaterializedAutoMaterializeCondition(
                            updated_asset_keys=frozenset(updated_parents),
                            will_update_asset_keys=frozenset(will_update_parents),
                        )
                    )

        # if the parents will not be resolved this tick
        waiting_on_asset_keys = get_waiting_on_asset_keys(candidate)
        if waiting_on_asset_keys:
            conditions.add(
                ParentOutdatedAutoMaterializeCondition(waiting_on_asset_keys=waiting_on_asset_keys)
            )

        if (
            # would be materialized
            _will_materialize_for_conditions(conditions)
            # has a rate limit
            and auto_materialize_policy.max_materializations_per_minute is not None
            # would exceed the rate limit
            and len(materialization_requests_by_asset_key[candidate.asset_key].union({candidate}))
            > auto_materialize_policy.max_materializations_per_minute
        ):
            conditions.add(MaxMaterializationsExceededAutoMaterializeCondition())

        return conditions

    def should_reconcile(
        asset_graph: AssetGraph,
        candidates_unit: Iterable[AssetKeyPartitionKey],
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        if any(not can_reconcile_candidate(candidate) for candidate in candidates_unit):
            return False
        # collect all conditions that apply to any candidate in the unit
        unit_conditions = set().union(
            *(conditions_for_candidate(candidate) for candidate in candidates_unit)
        )
        will_materialize = _will_materialize_for_conditions(unit_conditions)
        # for now, all candidates in the unit share the same conditions
        for candidate in candidates_unit:
            conditions_by_asset_partition[candidate].update(unit_conditions)
            if will_materialize:
                materialization_requests_by_asset_key[candidate.asset_key].add(candidate)
        return will_materialize

    # will update conditions
    asset_graph.bfs_filter_asset_partitions(
        instance_queryer,
        lambda candidates_unit, to_reconcile: should_reconcile(
            asset_graph, candidates_unit, to_reconcile
        ),
        set(itertools.chain(never_handled_roots, stale_candidates)),
        evaluation_time,
    )

    return (
        conditions_by_asset_partition,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def reconcile(
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    instance: "DagsterInstance",
    cursor: AssetDaemonCursor,
    materialize_run_tags: Optional[Mapping[str, str]],
    observe_run_tags: Optional[Mapping[str, str]],
    auto_observe: bool,
) -> Tuple[Sequence[RunRequest], AssetDaemonCursor, Sequence[AutoMaterializeAssetEvaluation],]:
    from dagster._utils.caching_instance_queryer import CachingInstanceQueryer  # expensive import

    current_time = pendulum.now("UTC")

    instance_queryer = CachingInstanceQueryer(
        instance=instance, asset_graph=asset_graph, evaluation_time=current_time
    )

    target_parent_asset_keys = {
        parent
        for target_asset_key in target_asset_keys
        for parent in asset_graph.get_parents(target_asset_key)
    }
    target_asset_keys_and_parents = target_asset_keys | target_parent_asset_keys

    # fetch some data in advance to batch some queries
    target_asset_keys_and_parents_list = list(target_asset_keys_and_parents)
    instance_queryer.prefetch_asset_records(
        [key for key in target_asset_keys_and_parents_list if not asset_graph.is_source(key)]
    )
    instance_queryer.prefetch_asset_partition_counts(
        [
            key
            for key in target_asset_keys_and_parents_list
            if asset_graph.is_partitioned(key) and not asset_graph.is_source(key)
        ],
        after_cursor=cursor.latest_storage_id,
    )

    conditions_by_asset_partition_for_freshness = (
        determine_asset_partitions_to_auto_materialize_for_freshness(
            data_time_resolver=CachingDataTimeResolver(instance_queryer=instance_queryer),
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            target_asset_keys_and_parents=target_asset_keys_and_parents,
            current_time=current_time,
        )
    )

    (
        conditions_by_asset_partition,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    ) = determine_asset_partitions_to_auto_materialize(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        target_asset_keys_and_parents=target_asset_keys_and_parents,
        current_time=current_time,
        conditions_by_asset_partition_for_freshness=conditions_by_asset_partition_for_freshness,
    )

    observe_request_timestamp = pendulum.now().timestamp()
    auto_observe_run_requests = (
        get_auto_observe_run_requests(
            asset_graph=asset_graph,
            last_observe_request_timestamp_by_asset_key=cursor.last_observe_request_timestamp_by_asset_key,
            current_timestamp=observe_request_timestamp,
            run_tags=observe_run_tags,
        )
        if auto_observe
        else []
    )
    run_requests = [
        *build_run_requests(
            asset_partitions={
                asset_partition
                for asset_partition, conditions in conditions_by_asset_partition.items()
                if _will_materialize_for_conditions(conditions)
            },
            asset_graph=asset_graph,
            run_tags=materialize_run_tags,
        ),
        *auto_observe_run_requests,
    ]

    return (
        run_requests,
        cursor.with_updates(
            latest_storage_id=latest_storage_id,
            conditions_by_asset_partition=conditions_by_asset_partition,
            asset_graph=asset_graph,
            newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
            newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
            evaluation_id=cursor.evaluation_id + 1,
            newly_observe_requested_asset_keys=[
                asset_key
                for run_request in auto_observe_run_requests
                for asset_key in cast(Sequence[AssetKey], run_request.asset_selection)
            ],
            observe_request_timestamp=observe_request_timestamp,
        ),
        build_auto_materialize_asset_evaluations(
            asset_graph, conditions_by_asset_partition, dynamic_partitions_store=instance_queryer
        ),
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


def build_auto_materialize_asset_evaluations(
    asset_graph: AssetGraph,
    conditions_by_asset_partition: Mapping[
        AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]
    ],
    dynamic_partitions_store: "DynamicPartitionsStore",
) -> Sequence[AutoMaterializeAssetEvaluation]:
    """Bundles up the conditions into AutoMaterializeAssetEvaluations."""
    conditions_by_asset_key: Dict[
        AssetKey, Dict[AssetKeyPartitionKey, AbstractSet[AutoMaterializeCondition]]
    ] = defaultdict(dict)

    # split into sub-dictionaries that hold only the conditions specific to each asset
    for asset_partition, conditions in conditions_by_asset_partition.items():
        conditions_by_asset_key[asset_partition.asset_key][asset_partition] = conditions

    return [
        AutoMaterializeAssetEvaluation.from_conditions(
            asset_graph, asset_key, conditions, dynamic_partitions_store
        )
        for asset_key, conditions in conditions_by_asset_key.items()
    ]


@experimental
def build_asset_reconciliation_sensor(
    asset_selection: AssetSelection,
    name: str = "asset_reconciliation_sensor",
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    run_tags: Optional[Mapping[str, str]] = None,
) -> SensorDefinition:
    r"""Constructs a sensor that will monitor the provided assets and launch materializations to
    "reconcile" them.

    An asset is considered "unreconciled" if any of:

    - This sensor has never tried to materialize it and it has never been materialized.

    - Any of its parents have been materialized more recently than it has.

    - Any of its parents are unreconciled.

    - It is not currently up to date with respect to its freshness policy.

    The sensor won't try to reconcile any assets before their parents are reconciled. When multiple
    FreshnessPolicies require data from the same upstream assets, this sensor will attempt to
    launch a minimal number of runs of that asset to satisfy all constraints.

    Args:
        asset_selection (AssetSelection): The group of assets you want to keep up-to-date
        name (str): The name to give the sensor.
        minimum_interval_seconds (Optional[int]): The minimum amount of time that should elapse between sensor invocations.
        description (Optional[str]): A description for the sensor.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        run_tags (Optional[Mapping[str, str]): Dictionary of tags to pass to the RunRequests launched by this sensor

    Returns:
        SensorDefinition

    Example:
        If you have the following asset graph, with no freshness policies:

        .. code-block:: python

            a       b       c
             \     / \     /
                d       e
                 \     /
                    f

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.assets(d, e, f),
                name="my_reconciliation_sensor",
            )

        You will observe the following behavior:
            * If ``a``, ``b``, and ``c`` are all materialized, then on the next sensor tick, the sensor will see that ``d`` and ``e`` can
              be materialized. Since ``d`` and ``e`` will be materialized, ``f`` can also be materialized. The sensor will kick off a
              run that will materialize ``d``, ``e``, and ``f``.
            * If, on the next sensor tick, none of ``a``, ``b``, and ``c`` have been materialized again, the sensor will not launch a run.
            * If, before the next sensor tick, just asset ``a`` and ``b`` have been materialized, the sensor will launch a run to
              materialize ``d``, ``e``, and ``f``, because they're downstream of ``a`` and ``b``.
              Even though ``c`` hasn't been materialized, the downstream assets can still be
              updated, because ``c`` is still considered "reconciled".

    Example:
        If you have the following asset graph, with the following freshness policies:
            * ``c: FreshnessPolicy(maximum_lag_minutes=120, cron_schedule="0 2 \* \* \*")``, meaning
              that by 2AM, c needs to be materialized with data from a and b that is no more than 120
              minutes old (i.e. all of yesterday's data).

        .. code-block:: python

            a     b
             \   /
               c

        and create the sensor:

        .. code-block:: python

            build_asset_reconciliation_sensor(
                AssetSelection.all(),
                name="my_reconciliation_sensor",
            )

        Assume that ``c`` currently has incorporated all source data up to ``2022-01-01 23:00``.

        You will observe the following behavior:
            * At any time between ``2022-01-02 00:00`` and ``2022-01-02 02:00``, the sensor will see that
              ``c`` will soon require data from ``2022-01-02 00:00``. In order to satisfy this
              requirement, there must be a materialization for both ``a`` and ``b`` with time >=
              ``2022-01-02 00:00``. If such a materialization does not exist for one of those assets,
              the missing asset(s) will be executed on this tick, to help satisfy the constraint imposed
              by ``c``. Materializing ``c`` in the same run as those assets will satisfy its
              required data constraint, and so the sensor will kick off a run for ``c`` alongside
              whichever upstream assets did not have up-to-date data.
            * On the next tick, the sensor will see that a run is currently planned which will
              satisfy that constraint, so no runs will be kicked off.
            * Once that run completes, a new materialization event will exist for ``c``, which will
              incorporate all of the required data, so no new runs will be kicked off until the
              following day.


    """
    check_valid_name(name)
    check.opt_mapping_param(run_tags, "run_tags", key_type=str, value_type=str)
    deprecation_warning(
        "build_asset_reconciliation_sensor", "1.4", "Use AutoMaterializePolicys instead."
    )

    @sensor(
        name=name,
        asset_selection=asset_selection,
        minimum_interval_seconds=minimum_interval_seconds,
        description=description,
        default_status=default_status,
    )
    def _sensor(context):
        asset_graph = context.repository_def.asset_graph
        cursor = (
            AssetDaemonCursor.from_serialized(context.cursor, asset_graph)
            if context.cursor
            else AssetDaemonCursor.empty()
        )

        # if there is a auto materialize policy set in the selection, filter down to that. Otherwise, use the
        # whole selection
        target_asset_keys = asset_selection.resolve(asset_graph)
        for target_key in target_asset_keys:
            check.invariant(
                asset_graph.get_auto_materialize_policy(target_key) is None,
                (
                    f"build_asset_reconciliation_sensor: Asset '{target_key.to_user_string()}' has"
                    " an AutoMaterializePolicy set. This asset will be automatically materialized"
                    " by the AssetDaemon, and should not be passed to this sensor. It's"
                    " recommended to remove this sensor once you have migrated to the"
                    " AutoMaterializePolicy api."
                ),
            )

        run_requests, updated_cursor, _ = reconcile(
            asset_graph=asset_graph,
            target_asset_keys=target_asset_keys,
            instance=context.instance,
            cursor=cursor,
            materialize_run_tags=run_tags,
            observe_run_tags=None,
            auto_observe=False,
        )

        context.update_cursor(updated_cursor.serialize())
        return run_requests

    return _sensor


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

    return [
        RunRequest(asset_selection=list(asset_keys), tags=run_tags)
        for asset_keys in asset_graph.split_asset_keys_by_repository(assets_to_auto_observe)
        if len(asset_keys) > 0
    ]
