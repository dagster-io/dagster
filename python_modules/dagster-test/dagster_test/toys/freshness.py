from datetime import timedelta

import dagster as dg
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@dg.asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=60))
)
def asset_with_time_window_freshness_60m():
    return 1


@dg.asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=30))
)
def asset_with_time_window_freshness_30m():
    return 1


@dg.asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=15), warn_window=timedelta(minutes=10)
    )
)
def asset_with_time_window_freshness_and_warning():
    return 1


@dg.asset(
    internal_freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(seconds=60), warn_window=timedelta(seconds=30)
    )
)
def asset_with_time_window_freshness_fast_fail():
    return 1


def get_freshness_assets():
    return [
        asset_with_time_window_freshness_60m,
        asset_with_time_window_freshness_30m,
        asset_with_time_window_freshness_and_warning,
        asset_with_time_window_freshness_fast_fail,
    ]
