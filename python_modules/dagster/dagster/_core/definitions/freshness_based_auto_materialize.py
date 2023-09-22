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
from typing import TYPE_CHECKING, AbstractSet, Mapping, Optional, Tuple

import pendulum

from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._utils.schedules import cron_string_iterator

from .asset_graph import AssetGraph

if TYPE_CHECKING:
    from dagster._core.definitions.data_time import CachingDataTimeResolver

    from .auto_materialize_rule import RuleEvaluationResults, TextRuleEvaluationData


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


def get_execution_period_and_evaluation_data_for_policies(
    local_policy: Optional[FreshnessPolicy],
    policies: AbstractSet[FreshnessPolicy],
    effective_data_time: Optional[datetime.datetime],
    current_time: datetime.datetime,
) -> Tuple[Optional[pendulum.Period], Optional["TextRuleEvaluationData"]]:
    """Determines a range of times for which you can kick off an execution of this asset to solve
    the most pressing constraint, alongside a maximum number of additional constraints.
    """
    from .auto_materialize_rule import TextRuleEvaluationData

    merged_period = None
    contains_local = False
    contains_downstream = False
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
            contains_local = True
        else:
            contains_downstream = True

    if not contains_local and not contains_downstream:
        evaluation_data = None
    elif not contains_local:
        evaluation_data = TextRuleEvaluationData("Required by downstream asset's policy")
    elif not contains_downstream:
        evaluation_data = TextRuleEvaluationData("Required by this asset's policy")
    else:
        evaluation_data = TextRuleEvaluationData(
            "Required by this asset's policy and downstream asset's policy"
        )

    return merged_period, evaluation_data


def get_expected_data_time_for_asset_key(
    asset_graph: AssetGraph,
    asset_key: AssetKey,
    will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
    data_time_resolver: "CachingDataTimeResolver",
    current_time: datetime.datetime,
    will_materialize: bool,
) -> Optional[datetime.datetime]:
    """Returns the data time that you would expect this asset to have if you were to execute it
    on this tick.
    """
    from dagster._core.definitions.external_asset_graph import ExternalAssetGraph

    # don't bother calculating if no downstream assets have freshness policies
    if not asset_graph.get_downstream_freshness_policies(asset_key=asset_key):
        return None
    # if asset will not be materialized, just return the current time
    elif not will_materialize:
        return data_time_resolver.get_current_data_time(asset_key, current_time)
    elif asset_graph.has_non_source_parents(asset_key):
        expected_data_time = None
        for parent_key in asset_graph.get_parents(asset_key):
            # if the parent will be materialized on this tick, and it's not in the same repo, then
            # we must wait for this asset to be materialized
            if (
                isinstance(asset_graph, ExternalAssetGraph)
                and AssetKeyPartitionKey(parent_key) in will_materialize_mapping[parent_key]
            ):
                parent_repo = asset_graph.get_repository_handle(parent_key)
                if parent_repo != asset_graph.get_repository_handle(asset_key):
                    return data_time_resolver.get_current_data_time(asset_key, current_time)
            # find the minimum non-None data time of your parents
            parent_expected_data_time = expected_data_time_mapping.get(
                parent_key
            ) or data_time_resolver.get_current_data_time(parent_key, current_time)
            expected_data_time = min(
                filter(None, [expected_data_time, parent_expected_data_time]),
                default=None,
            )
        return expected_data_time
    # for root assets, this would just be the current time
    else:
        return current_time


def freshness_evaluation_results_for_asset_key(
    asset_key: AssetKey,
    data_time_resolver: "CachingDataTimeResolver",
    asset_graph: AssetGraph,
    current_time: datetime.datetime,
    will_materialize_mapping: Mapping[AssetKey, AbstractSet[AssetKeyPartitionKey]],
    expected_data_time_mapping: Mapping[AssetKey, Optional[datetime.datetime]],
) -> "RuleEvaluationResults":
    """Returns a set of AssetKeyPartitionKeys to materialize in order to abide by the given
    FreshnessPolicies.

    Attempts to minimize the total number of asset executions.
    """
    if not asset_graph.get_downstream_freshness_policies(
        asset_key=asset_key
    ) or asset_graph.is_partitioned(asset_key):
        return []

    # figure out the current contents of this asset
    current_data_time = data_time_resolver.get_current_data_time(asset_key, current_time)

    # figure out the data time you would expect if you were to execute this asset on this tick
    expected_data_time = get_expected_data_time_for_asset_key(
        asset_graph=asset_graph,
        asset_key=asset_key,
        will_materialize_mapping=will_materialize_mapping,
        expected_data_time_mapping=expected_data_time_mapping,
        data_time_resolver=data_time_resolver,
        current_time=current_time,
        will_materialize=True,
    )

    # if executing the asset on this tick would not change its data time, then return
    if current_data_time == expected_data_time:
        return []

    # calculate the data times you would expect after all currently-executing runs
    # were to successfully complete
    in_progress_data_time = data_time_resolver.get_in_progress_data_time(asset_key, current_time)

    # calculate the data times you would have expected if the most recent run succeeded
    failed_data_time = data_time_resolver.get_ignored_failure_data_time(asset_key, current_time)

    effective_data_time = max(
        filter(None, (current_data_time, in_progress_data_time, failed_data_time)),
        default=None,
    )

    # figure out a time period that you can execute this asset within to solve a maximum
    # number of constraints
    (
        execution_period,
        evaluation_data,
    ) = get_execution_period_and_evaluation_data_for_policies(
        local_policy=asset_graph.freshness_policies_by_key.get(asset_key),
        policies=asset_graph.get_downstream_freshness_policies(asset_key=asset_key),
        effective_data_time=effective_data_time,
        current_time=current_time,
    )

    asset_partition = AssetKeyPartitionKey(asset_key, None)
    if (
        execution_period is not None
        and execution_period.start <= current_time
        and expected_data_time is not None
        # if this is False, then executing it would still leave the asset overdue
        and expected_data_time >= execution_period.start
        and evaluation_data is not None
    ):
        return [(evaluation_data, {asset_partition})]
    else:
        return []
