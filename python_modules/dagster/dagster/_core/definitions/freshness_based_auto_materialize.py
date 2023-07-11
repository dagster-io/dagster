"""Terms and concepts in lazy / freshness-based auto-materialize:
- data_time: see data_time.py
- effective_data_time: The data time that this asset would have if the most recent run succeeded.
    If the most recent run completed successfully / is not in progress or failed, then this is
    just the current data time of the asset.
- execution_period: The range of times in which it would be acceptable to materialize this asset,
    i.e. it`s late enough to pull in the required data time, and early enough to not go over the
    maximum lag minutes.
"""
import datetime
from collections import defaultdict
from typing import AbstractSet, Dict, Mapping, Optional, Set, Tuple, cast

import pendulum

from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._utils.schedules import cron_string_iterator

from .asset_graph import AssetGraph
from .auto_materialize_condition import (
    AutoMaterializeCondition,
    AutoMaterializeDecisionType,
    DownstreamFreshnessAutoMaterializeCondition,
    FreshnessAutoMaterializeCondition,
)


def get_execution_period_for_policy(
    freshness_policy: FreshnessPolicy,
    effective_data_time: Optional[datetime.datetime],
    current_time: datetime.datetime,
) -> pendulum.Period:
    if freshness_policy.cron_schedule:
        tick_iterator = cron_string_iterator(
            start_timestamp=current_time.timestamp(),
            cron_string=freshness_policy.cron_schedule,
            execution_timezone=freshness_policy.cron_schedule_timezone,
        )

        while True:
            # find the next tick that requires data after the current effective data time
            # (usually, this will be the next tick)
            tick = next(tick_iterator)
            required_data_time = tick - freshness_policy.maximum_lag_delta
            if effective_data_time is None or effective_data_time < required_data_time:
                return pendulum.Period(start=required_data_time, end=tick)

    else:
        # occurs when asset is missing
        if effective_data_time is None:
            return pendulum.Period(
                # require data from at most maximum_lag_delta ago
                start=current_time - freshness_policy.maximum_lag_delta,
                # this data should be available as soon as possible
                end=current_time,
            )
        return pendulum.Period(
            # we don't want to execute this too frequently
            start=effective_data_time + 0.9 * freshness_policy.maximum_lag_delta,
            end=max(effective_data_time + freshness_policy.maximum_lag_delta, current_time),
        )


def get_execution_period_and_conditions_for_policies(
    local_policy: Optional[FreshnessPolicy],
    policies: AbstractSet[FreshnessPolicy],
    effective_data_time: Optional[datetime.datetime],
    current_time: datetime.datetime,
) -> Tuple[Optional[pendulum.Period], AbstractSet[AutoMaterializeCondition]]:
    """Determines a range of times for which you can kick off an execution of this asset to solve
    the most pressing constraint, alongside a maximum number of additional constraints.
    """
    merged_period = None
    conditions = set()
    for period, policy in sorted(
        (
            (get_execution_period_for_policy(policy, effective_data_time, current_time), policy)
            for policy in policies
        ),
        # sort execution periods by most pressing
        key=lambda pp: pp[0].end,
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

        if policy == local_policy:
            conditions.add(FreshnessAutoMaterializeCondition())
        else:
            conditions.add(DownstreamFreshnessAutoMaterializeCondition())

    return merged_period, conditions


def determine_asset_partitions_to_auto_materialize_for_freshness(
    data_time_resolver: "CachingDataTimeResolver",
    asset_graph: AssetGraph,
    target_asset_keys: AbstractSet[AssetKey],
    target_asset_keys_and_parents: AbstractSet[AssetKey],
    current_time: datetime.datetime,
) -> Mapping[AssetKeyPartitionKey, Set[AutoMaterializeCondition]]:
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies, as well as a set of AssetKeyPartitionKeys which will be materialized at
    some point within the plan window.

    Attempts to minimize the total number of asset executions.
    """
    from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

    # now we have a full set of constraints, we can find solutions for them as we move down
    conditions_by_asset_partition: Mapping[
        AssetKeyPartitionKey, Set[AutoMaterializeCondition]
    ] = defaultdict(set)
    waiting_to_materialize: Set[AssetKey] = set()
    expected_data_time_by_key: Dict[AssetKey, Optional[datetime.datetime]] = {}

    for level in asset_graph.toposort_asset_keys():
        for key in level:
            if (
                key not in target_asset_keys_and_parents
                or key not in asset_graph.materializable_asset_keys
                or not asset_graph.get_downstream_freshness_policies(asset_key=key)
            ):
                continue

            parents = asset_graph.get_parents(key)

            if any(p in waiting_to_materialize for p in parents):
                # we can't materialize this asset yet, because we're waiting on a parent
                waiting_to_materialize.add(key)
                continue

            # if we're going to materialize a parent of this asset that's in a different repository,
            # then we need to wait
            if isinstance(asset_graph, ExternalAssetGraph):
                repo = asset_graph.get_repository_handle(key)
                if any(
                    AssetKeyPartitionKey(p, None) in conditions_by_asset_partition
                    and asset_graph.get_repository_handle(p) is not repo
                    for p in parents
                ):
                    waiting_to_materialize.add(key)
                    continue

            # figure out the current contents of this asset with respect to its constraints
            current_data_time = data_time_resolver.get_current_data_time(key, current_time)

            # figure out the expected data time of this asset if it were to be executed on this tick
            # for root assets, this would just be the current time
            expected_data_time = (
                min(
                    (
                        cast(datetime.datetime, expected_data_time_by_key[k])
                        for k in parents
                        if k in expected_data_time_by_key
                        and expected_data_time_by_key[k] is not None
                    ),
                    default=None,
                )
                if asset_graph.has_non_source_parents(key)
                else current_time
            )

            # currently, freshness logic has no effect on partitioned assets
            if key in target_asset_keys and not asset_graph.is_partitioned(key):
                # calculate the data times you would expect after all currently-executing runs
                # were to successfully complete
                in_progress_data_time = data_time_resolver.get_in_progress_data_time(
                    key, current_time
                )

                # calculate the data times you would have expected if the most recent run succeeded
                failed_data_time = data_time_resolver.get_ignored_failure_data_time(
                    key, current_time
                )

                effective_data_time = max(
                    filter(None, (current_data_time, in_progress_data_time, failed_data_time)),
                    default=None,
                )

                # figure out a time period that you can execute this asset within to solve a maximum
                # number of constraints
                (
                    execution_period,
                    execution_conditions,
                ) = get_execution_period_and_conditions_for_policies(
                    local_policy=asset_graph.freshness_policies_by_key.get(key),
                    policies=asset_graph.get_downstream_freshness_policies(asset_key=key),
                    effective_data_time=effective_data_time,
                    current_time=current_time,
                )
            else:
                execution_period, execution_conditions = None, set()

            # a key may already be in conditions by the time we get here if a required
            # neighbor was selected to be updated
            asset_partition = AssetKeyPartitionKey(key, None)
            if asset_partition in conditions_by_asset_partition and all(
                condition.decision_type == AutoMaterializeDecisionType.MATERIALIZE
                for condition in conditions_by_asset_partition[asset_partition]
            ):
                expected_data_time_by_key[key] = expected_data_time
            elif (
                execution_period is not None
                and execution_period.start <= current_time
                and expected_data_time is not None
                # if this is False, then executing it would still leave the asset overdue
                and expected_data_time >= execution_period.start
                and all(
                    condition.decision_type == AutoMaterializeDecisionType.MATERIALIZE
                    for condition in execution_conditions
                )
            ):
                expected_data_time_by_key[key] = expected_data_time
                conditions_by_asset_partition[asset_partition].update(execution_conditions)
                # all required neighbors will be updated on the same tick
                for required_key in asset_graph.get_required_multi_asset_keys(key):
                    conditions_by_asset_partition[
                        (AssetKeyPartitionKey(required_key, None))
                    ].update(execution_conditions)
            else:
                # if downstream assets consume this, they should expect data time equal to the
                # current time for this asset, as it's not going to be updated
                expected_data_time_by_key[key] = current_data_time

    return conditions_by_asset_partition
