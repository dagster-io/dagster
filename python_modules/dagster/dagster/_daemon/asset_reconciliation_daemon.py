import datetime
import itertools
from collections import defaultdict
from typing import (
    AbstractSet,
    Dict,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)
from dagster._core.definitions.assets_job import ASSET_BASE_JOB_PREFIX
from dagster._core.definitions.selector import PipelineSelector
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.instance import DagsterInstance, DynamicPartitionsStore
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import PARTITION_NAME_TAG

import pendulum

import dagster._check as check
from dagster import AssetKey, FreshnessPolicy
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_reconciliation_sensor import (
    allowable_time_window_for_partitions_def,
    candidates_unit_within_allowable_time_window,
    get_active_backfill_target_asset_graph_subset,
)
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKeyPartitionKey
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.partition import PartitionsDefinition, PartitionsSubset
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer
from dagster._utils.schedules import cron_string_iterator
import json

CURSOR_NAME = "ASSET_RECONCILIATION_DAEMON_CURSOR"


class AssetReconciliationCursor(NamedTuple):
    """Attributes:
    latest_storage_id: The latest observed storage ID across all assets. Useful for
        finding out what has happened since the last tick.
    materialized_or_requested_root_asset_keys: Every entry is a non-partitioned asset with no
        parents that has been requested by this sensor or has been materialized (even if not by
        this sensor).
    materialized_or_requested_root_partitions_by_asset_key: Every key is a partitioned root
        asset. Every value is the set of that asset's partitions that have been requested by
        this sensor or have been materialized (even if not by this sensor).
    """

    latest_storage_id: Optional[int]
    materialized_or_requested_root_asset_keys: AbstractSet[AssetKey]
    materialized_or_requested_root_partitions_by_asset_key: Mapping[AssetKey, PartitionsSubset]

    def was_previously_materialized_or_requested(self, asset_key: AssetKey) -> bool:
        return asset_key in self.materialized_or_requested_root_asset_keys

    def get_never_requested_never_materialized_partitions(
        self, asset_key: AssetKey, asset_graph, dynamic_partitions_store: DynamicPartitionsStore
    ) -> Iterable[str]:
        partitions_def = asset_graph.get_partitions_def(asset_key)

        materialized_or_requested_subset = (
            self.materialized_or_requested_root_partitions_by_asset_key.get(
                asset_key, partitions_def.empty_subset()
            )
        )

        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            allowable_time_window = allowable_time_window_for_partitions_def(partitions_def)
            if allowable_time_window is None:
                return []
            # for performance, only iterate over keys within the allowable time window
            return [
                partition_key
                for partition_key in partitions_def.get_partition_keys_in_time_window(
                    allowable_time_window
                )
                if partition_key not in materialized_or_requested_subset
            ]
        else:
            return materialized_or_requested_subset.get_partition_keys_not_in_subset(
                dynamic_partitions_store=dynamic_partitions_store
            )

    def with_updates(
        self,
        latest_storage_id: Optional[int],
        runs: Sequence[DagsterRun],
        newly_materialized_root_asset_keys: AbstractSet[AssetKey],
        newly_materialized_root_partitions_by_asset_key: Mapping[AssetKey, AbstractSet[str]],
        asset_graph: AssetGraph,
    ) -> "AssetReconciliationCursor":
        """Returns a cursor that represents this cursor plus the updates that have happened within the
        tick.
        """
        requested_root_partitions_by_asset_key: Dict[AssetKey, Set[str]] = defaultdict(set)
        requested_non_partitioned_root_assets: Set[AssetKey] = set()

        for run in runs:
            for asset_key in cast(Iterable[AssetKey], run.asset_selection):
                if not asset_graph.has_non_source_parents(asset_key):
                    if run.tags.get(PARTITION_NAME_TAG):
                        requested_root_partitions_by_asset_key[asset_key].add(
                            run.tags[PARTITION_NAME_TAG]
                        )
                    else:
                        requested_non_partitioned_root_assets.add(asset_key)

        result_materialized_or_requested_root_partitions_by_asset_key = {
            **self.materialized_or_requested_root_partitions_by_asset_key
        }
        for asset_key in set(newly_materialized_root_partitions_by_asset_key.keys()) | set(
            requested_root_partitions_by_asset_key.keys()
        ):
            prior_materialized_partitions = (
                self.materialized_or_requested_root_partitions_by_asset_key.get(asset_key)
            )
            if prior_materialized_partitions is None:
                prior_materialized_partitions = cast(
                    PartitionsDefinition, asset_graph.get_partitions_def(asset_key)
                ).empty_subset()

            result_materialized_or_requested_root_partitions_by_asset_key[
                asset_key
            ] = prior_materialized_partitions.with_partition_keys(
                itertools.chain(
                    newly_materialized_root_partitions_by_asset_key[asset_key],
                    requested_root_partitions_by_asset_key[asset_key],
                )
            )

        result_materialized_or_requested_root_asset_keys = (
            self.materialized_or_requested_root_asset_keys
            | newly_materialized_root_asset_keys
            | requested_non_partitioned_root_assets
        )

        if latest_storage_id and self.latest_storage_id:
            check.invariant(
                latest_storage_id >= self.latest_storage_id,
                "Latest storage ID should be >= previous latest storage ID",
            )

        return AssetReconciliationCursor(
            latest_storage_id=latest_storage_id or self.latest_storage_id,
            materialized_or_requested_root_asset_keys=result_materialized_or_requested_root_asset_keys,
            materialized_or_requested_root_partitions_by_asset_key=result_materialized_or_requested_root_partitions_by_asset_key,
        )

    @classmethod
    def empty(cls) -> "AssetReconciliationCursor":
        return AssetReconciliationCursor(
            latest_storage_id=None,
            materialized_or_requested_root_partitions_by_asset_key={},
            materialized_or_requested_root_asset_keys=set(),
        )

    @classmethod
    def from_serialized(cls, cursor: str, asset_graph: AssetGraph) -> "AssetReconciliationCursor":
        (
            latest_storage_id,
            serialized_materialized_or_requested_root_asset_keys,
            serialized_materialized_or_requested_root_partitions_by_asset_key,
        ) = json.loads(cursor)
        materialized_or_requested_root_partitions_by_asset_key = {}
        for (
            key_str,
            serialized_subset,
        ) in serialized_materialized_or_requested_root_partitions_by_asset_key.items():
            key = AssetKey.from_user_string(key_str)
            materialized_or_requested_root_partitions_by_asset_key[key] = cast(
                PartitionsDefinition, asset_graph.get_partitions_def(key)
            ).deserialize_subset(serialized_subset)
        return cls(
            latest_storage_id=latest_storage_id,
            materialized_or_requested_root_asset_keys={
                AssetKey.from_user_string(key_str)
                for key_str in serialized_materialized_or_requested_root_asset_keys
            },
            materialized_or_requested_root_partitions_by_asset_key=materialized_or_requested_root_partitions_by_asset_key,
        )

    def serialize(self) -> str:
        serializable_materialized_or_requested_root_partitions_by_asset_key = {
            key.to_user_string(): subset.serialize()
            for key, subset in self.materialized_or_requested_root_partitions_by_asset_key.items()
        }
        serialized = json.dumps(
            (
                self.latest_storage_id,
                [key.to_user_string() for key in self.materialized_or_requested_root_asset_keys],
                serializable_materialized_or_requested_root_partitions_by_asset_key,
            )
        )
        return serialized


def get_execution_period_for_policy(
    freshness_policy: FreshnessPolicy,
    effective_data_time: Optional[datetime.datetime],
    evaluation_time: datetime.datetime,
) -> pendulum.Period:
    if effective_data_time is None:
        return pendulum.Period(start=evaluation_time, end=evaluation_time)

    if freshness_policy.cron_schedule:
        tick_iterator = cron_string_iterator(
            start_timestamp=evaluation_time.timestamp(),
            cron_string=freshness_policy.cron_schedule,
            execution_timezone=freshness_policy.cron_schedule_timezone,
        )

        while True:
            # find the next tick tick that requires data after the current effective data time
            # (usually, this will be the next tick)
            tick = next(tick_iterator)
            required_data_time = tick - freshness_policy.maximum_lag_delta
            if effective_data_time is None or effective_data_time < required_data_time:
                return pendulum.Period(start=required_data_time, end=tick)

    else:
        return pendulum.Period(
            # we don't want to execute this too frequently
            start=effective_data_time + 0.9 * freshness_policy.maximum_lag_delta,
            end=max(effective_data_time + freshness_policy.maximum_lag_delta, evaluation_time),
        )


def get_execution_period_for_policies(
    policies: AbstractSet[FreshnessPolicy],
    effective_data_time: Optional[datetime.datetime],
    evaluation_time: datetime.datetime,
) -> Optional[pendulum.Period]:
    """Determines a range of times for which you can kick off an execution of this asset to solve
    the most pressing constraint, alongside a maximum number of additional constraints.
    """
    merged_period = None
    for period in sorted(
        (
            get_execution_period_for_policy(policy, effective_data_time, evaluation_time)
            for policy in policies
        ),
        # sort execution periods by most pressing
        key=lambda period: period.end,
    ):
        if merged_period is None:
            merged_period = period
        elif period.start <= merged_period.end:
            merged_period = pendulum.Period(
                start=max(period.start, merged_period.start),
                end=period.end,
            )
        else:
            break

    return merged_period


def determine_asset_partitions_to_reconcile_for_freshness(
    data_time_resolver: CachingDataTimeResolver,
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
) -> Tuple[AbstractSet[AssetKeyPartitionKey], AbstractSet[AssetKeyPartitionKey]]:
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies, as well as a set of AssetKeyPartitionKeys which will be materialized at
    some point within the plan window.

    Attempts to minimize the total number of asset executions.
    """
    evaluation_time = pendulum.now(tz=pendulum.UTC)

    # now we have a full set of constraints, we can find solutions for them as we move down
    to_materialize: Set[AssetKeyPartitionKey] = set()
    eventually_materialize: Set[AssetKeyPartitionKey] = set()
    expected_data_time_by_key: Dict[AssetKey, Optional[datetime.datetime]] = {}
    for level in asset_graph.toposort_asset_keys():
        for key in level:
            if asset_graph.is_source(key) or not asset_graph.get_downstream_freshness_policies(
                asset_key=key
            ):
                continue

            # figure out the current contents of this asset with respect to its constraints
            current_data_time = data_time_resolver.get_current_data_time(key)

            # figure out the expected data time of this asset if it were to be executed on this tick
            expected_data_time = min(
                (
                    cast(datetime.datetime, expected_data_time_by_key[k])
                    for k in asset_graph.get_parents(key)
                    if k in expected_data_time_by_key and expected_data_time_by_key[k] is not None
                ),
                default=evaluation_time,
            )

            if key in target_asset_keys:
                # calculate the data times you would expect after all currently-executing runs
                # were to successfully complete
                in_progress_data_time = data_time_resolver.get_in_progress_data_time(
                    key, evaluation_time
                )

                # calculate the data times you would have expected if the most recent run succeeded
                failed_data_time = data_time_resolver.get_ignored_failure_data_time(key)

                effective_data_time = max(
                    filter(None, (current_data_time, in_progress_data_time, failed_data_time)),
                    default=None,
                )

                # figure out a time period that you can execute this asset within to solve a maximum
                # number of constraints
                execution_period = get_execution_period_for_policies(
                    policies=asset_graph.get_downstream_freshness_policies(asset_key=key),
                    effective_data_time=effective_data_time,
                    evaluation_time=evaluation_time,
                )
                if execution_period:
                    eventually_materialize.add(AssetKeyPartitionKey(key, None))

            else:
                execution_period = None

            # a key may already be in to_materialize by the time we get here if a required
            # neighbor was selected to be updated
            asset_key_partition_key = AssetKeyPartitionKey(key, None)
            if asset_key_partition_key in to_materialize:
                expected_data_time_by_key[key] = expected_data_time
            elif (
                execution_period is not None
                and execution_period.start <= evaluation_time
                and expected_data_time is not None
                and expected_data_time >= execution_period.start
            ):
                to_materialize.add(asset_key_partition_key)
                expected_data_time_by_key[key] = expected_data_time
                # all required neighbors will be updated on the same tick
                for required_key in asset_graph.get_required_multi_asset_keys(key):
                    to_materialize.add(AssetKeyPartitionKey(required_key, None))
            else:
                # if downstream assets consume this, they should expect data time equal to the
                # current time for this asset, as it's not going to be updated
                expected_data_time_by_key[key] = current_data_time

    return to_materialize, eventually_materialize


def find_never_materialized_or_requested_root_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
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
    never_materialized_or_requested = set()
    newly_materialized_root_asset_keys = set()
    newly_materialized_root_partitions_by_asset_key = defaultdict(set)

    for asset_key in target_asset_keys:
        if asset_graph.is_partitioned(asset_key):
            for partition_key in cursor.get_never_requested_never_materialized_partitions(
                asset_key, asset_graph, instance_queryer
            ):
                asset_partition = AssetKeyPartitionKey(asset_key, partition_key)
                if instance_queryer.get_latest_materialization_record(asset_partition, None):
                    newly_materialized_root_partitions_by_asset_key[asset_key].add(partition_key)
                else:
                    never_materialized_or_requested.add(asset_partition)
        else:
            if not cursor.was_previously_materialized_or_requested(asset_key):
                asset = AssetKeyPartitionKey(asset_key)
                if instance_queryer.get_latest_materialization_record(asset, None):
                    newly_materialized_root_asset_keys.add(asset_key)
                else:
                    never_materialized_or_requested.add(asset)

    return (
        never_materialized_or_requested,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    )


def find_parent_materialized_asset_partitions(
    instance_queryer: "CachingInstanceQueryer",
    latest_storage_id: Optional[int],
    target_asset_keys: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
) -> Tuple[AbstractSet[AssetKeyPartitionKey], Optional[int]]:
    """Finds asset partitions in the given selection whose parents have been materialized since
    latest_storage_id.

    Returns:
        - A set of asset partitions.
        - The latest observed storage_id across all relevant assets. Can be used to avoid scanning
            the same events the next time this function is called.
    """
    result_asset_partitions: Set[AssetKeyPartitionKey] = set()
    result_latest_storage_id = latest_storage_id

    target_parent_asset_keys = target_asset_keys  # TODO fix this

    for asset_key in target_parent_asset_keys:
        if asset_graph.is_source(asset_key):
            continue

        latest_record = instance_queryer.get_latest_materialization_record(
            asset_key, after_cursor=latest_storage_id
        )
        if latest_record is None:
            continue

        for child in asset_graph.get_children_partitions(
            instance_queryer,
            asset_key,
            latest_record.partition_key,
        ):
            if (
                child.asset_key in target_asset_keys
                and not instance_queryer.is_asset_planned_for_run(latest_record.run_id, child)
            ):
                result_asset_partitions.add(child)

        if result_latest_storage_id is None or latest_record.storage_id > result_latest_storage_id:
            result_latest_storage_id = latest_record.storage_id

        # for partitioned assets, we'll want a count of all asset partitions that have been
        # materialized since the latest_storage_id, not just the most recent
        if asset_graph.is_partitioned(asset_key):
            for partition_key in instance_queryer.get_materialized_partitions(
                asset_key, after_cursor=latest_storage_id
            ):
                for child in asset_graph.get_children_partitions(
                    instance_queryer,
                    asset_key,
                    partition_key,
                ):
                    result_asset_partitions.add(child)

    return (result_asset_partitions, result_latest_storage_id)


def determine_asset_partitions_to_reconcile(
    instance_queryer: "CachingInstanceQueryer",
    cursor: AssetReconciliationCursor,
    target_asset_keys: AbstractSet[AssetKey],
    asset_graph: AssetGraph,
    eventual_asset_partitions_to_reconcile_for_freshness: AbstractSet[AssetKeyPartitionKey],
) -> Tuple[
    AbstractSet[AssetKeyPartitionKey],
    AbstractSet[AssetKey],
    Mapping[AssetKey, AbstractSet[str]],
    Optional[int],
]:
    (
        never_materialized_or_requested_roots,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
    ) = find_never_materialized_or_requested_root_asset_partitions(
        instance_queryer=instance_queryer,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        asset_graph=asset_graph,
    )

    stale_candidates, latest_storage_id = find_parent_materialized_asset_partitions(
        instance_queryer=instance_queryer,
        latest_storage_id=cursor.latest_storage_id,
        target_asset_keys=target_asset_keys,
        asset_graph=asset_graph,
    )

    backfill_target_asset_graph_subset = get_active_backfill_target_asset_graph_subset(
        asset_graph=asset_graph,
        instance=instance_queryer.instance,
    )

    def parents_will_be_reconciled(
        candidate: AssetKeyPartitionKey,
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        return all(
            (
                (
                    parent in to_reconcile
                    # if they don't have the same partitioning, then we can't launch a run that
                    # targets both, so we need to wait until the parent is reconciled before
                    # launching a run for the child
                    and asset_graph.have_same_partitioning(parent.asset_key, candidate.asset_key)
                    and parent.partition_key == candidate.partition_key
                )
                or (instance_queryer.is_reconciled(asset_partition=parent, asset_graph=asset_graph))
            )
            for parent in asset_graph.get_parents_partitions(
                instance_queryer,
                candidate.asset_key,
                candidate.partition_key,
            )
        )

    def should_reconcile(
        candidates_unit: Iterable[AssetKeyPartitionKey],
        to_reconcile: AbstractSet[AssetKeyPartitionKey],
    ) -> bool:
        if not candidates_unit_within_allowable_time_window(asset_graph, candidates_unit):
            return False

        if any(
            # do not reconcile assets if the freshness system will update them
            candidate in eventual_asset_partitions_to_reconcile_for_freshness
            # do not reconcile assets if an active backfill will update them
            or candidate in backfill_target_asset_graph_subset
            # do not reconcile assets if they are not in the target selection
            or candidate.asset_key not in target_asset_keys
            for candidate in candidates_unit
        ):
            return False

        return all(
            parents_will_be_reconciled(candidate, to_reconcile) for candidate in candidates_unit
        ) and any(
            not instance_queryer.is_reconciled(asset_partition=candidate, asset_graph=asset_graph)
            for candidate in candidates_unit
        )

    to_reconcile = asset_graph.bfs_filter_asset_partitions(
        instance_queryer,
        should_reconcile,
        set(itertools.chain(never_materialized_or_requested_roots, stale_candidates)),
    )

    return (
        to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    )


def create_and_launch_runs(
    instance: DagsterInstance,
    workspace,
    asset_partitions: Iterable[AssetKeyPartitionKey],
    asset_graph: ExternalAssetGraph,
) -> Sequence[DagsterRun]:
    assets_to_reconcile_by_partitions_def_partition_key: Mapping[
        Tuple[Optional[PartitionsDefinition], Optional[str]], Set[AssetKey]
    ] = defaultdict(set)

    for asset_partition in asset_partitions:
        assets_to_reconcile_by_partitions_def_partition_key[
            asset_graph.get_partitions_def(asset_partition.asset_key), asset_partition.partition_key
        ].add(asset_partition.asset_key)

    runs = []
    for (
        partitions_def,
        partition_key,
    ), asset_keys in assets_to_reconcile_by_partitions_def_partition_key.items():
        tags = {}
        if partition_key is not None:
            if partitions_def is None:
                check.failed("Partition key provided for unpartitioned asset")
            tags.update({**partitions_def.get_tags_for_partition_key(partition_key)})

        # launch run
        asset_key_in_set = next(iter(asset_keys))
        repo_handle = asset_graph.get_repository_handle(asset_key_in_set)
        location_name = repo_handle.code_location_origin.location_name
        repo_name = repo_handle.repository_name

        pipeline_selector = PipelineSelector(
            location_name=location_name,
            repository_name=repo_name,
            pipeline_name=check.not_none(asset_graph.get_implicit_job_name_for_assets(asset_keys)),
            solid_selection=None,
            asset_selection=list(asset_keys),
        )
        code_location = workspace.get_code_location(location_name)
        external_pipeline = code_location.get_external_pipeline(pipeline_selector)

        run = instance.create_run(
            pipeline_name=external_pipeline.name,
            run_id=None,
            run_config=None,
            mode=None,
            solids_to_execute=None,
            step_keys_to_execute=None,
            status=DagsterRunStatus.NOT_STARTED,
            solid_selection=None,
            root_run_id=None,
            parent_run_id=None,
            tags=tags,
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=None,
            parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
            asset_selection=frozenset(asset_keys),
        )
        instance.submit_run(run.run_id, workspace)
        runs.append(run)
    return runs


def execute_reconciliation_loop(
    instance, workspace, asset_graph, cursor
) -> AssetReconciliationCursor:
    instance_queryer = CachingInstanceQueryer(instance=instance)

    target_asset_keys = asset_graph.all_asset_keys
    print(target_asset_keys)
    assert target_asset_keys

    (
        asset_partitions_to_reconcile_for_freshness,
        eventual_asset_partitions_to_reconcile_for_freshness,
    ) = determine_asset_partitions_to_reconcile_for_freshness(
        data_time_resolver=CachingDataTimeResolver(
            instance_queryer=instance_queryer, asset_graph=asset_graph
        ),
        asset_graph=asset_graph,
        target_asset_keys=target_asset_keys,
    )

    (
        asset_partitions_to_reconcile,
        newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key,
        latest_storage_id,
    ) = determine_asset_partitions_to_reconcile(
        instance_queryer=instance_queryer,
        asset_graph=asset_graph,
        cursor=cursor,
        target_asset_keys=target_asset_keys,
        eventual_asset_partitions_to_reconcile_for_freshness=eventual_asset_partitions_to_reconcile_for_freshness,
    )

    runs = create_and_launch_runs(
        instance,
        workspace,
        asset_partitions_to_reconcile | asset_partitions_to_reconcile_for_freshness,
        asset_graph,
    )

    return cursor.with_updates(
        latest_storage_id=latest_storage_id,
        runs=runs,
        asset_graph=asset_graph,
        newly_materialized_root_asset_keys=newly_materialized_root_asset_keys,
        newly_materialized_root_partitions_by_asset_key=newly_materialized_root_partitions_by_asset_key,
    )


class AssetReconciliationDaemon(IntervalDaemon):
    @classmethod
    def daemon_type(cls) -> str:
        return "ASSET"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> DaemonIterator:
        yield
        instance = workspace_process_context.instance
        workspace = workspace_process_context.create_request_context()
        asset_graph = ExternalAssetGraph.from_workspace(workspace)

        raw_cursor = instance.run_storage.kvs_get({CURSOR_NAME}).get(CURSOR_NAME)
        cursor = (
            AssetReconciliationCursor.from_serialized(raw_cursor, asset_graph)
            if raw_cursor
            else AssetReconciliationCursor.empty()
        )

        new_cursor = execute_reconciliation_loop(instance, workspace, asset_graph, cursor)

        instance.run_storage.kvs_set({CURSOR_NAME: new_cursor.serialize()})
