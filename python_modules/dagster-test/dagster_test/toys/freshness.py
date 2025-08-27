from datetime import timedelta

import dagster as dg
from dagster._core.definitions.freshness import InternalFreshnessPolicy


@dg.asset(freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=60)))
def asset_with_time_window_freshness_60m():
    return 1


@dg.asset(freshness_policy=InternalFreshnessPolicy.time_window(fail_window=timedelta(minutes=30)))
def asset_with_time_window_freshness_30m():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=15), warn_window=timedelta(minutes=10)
    )
)
def asset_with_time_window_freshness_and_warning():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(seconds=120), warn_window=timedelta(seconds=60)
    )
)
def asset_with_time_window_freshness_fast_fail():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=1),
    )
)
def asset_with_cron_freshness_policy():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=10),
        timezone="America/New_York",
    )
)
def asset_with_cron_freshness_policy_with_timezone():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.cron(
        deadline_cron="*/5 * * * *",
        lower_bound_delta=timedelta(minutes=1),
    )
)
def asset_with_cron_freshness_policy_short_cron_interval():
    return 1


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.cron(
        deadline_cron="0 9,13,17 * * 1-5",  # 9am, 1pm, 5pm on weekdays
        lower_bound_delta=timedelta(minutes=30),
        timezone="Europe/Berlin",
    )
)
def asset_with_cron_freshness_policy_irregular_schedule():
    return 1


def get_freshness_assets():
    return [
        asset_with_time_window_freshness_60m,
        asset_with_time_window_freshness_30m,
        asset_with_time_window_freshness_and_warning,
        asset_with_time_window_freshness_fast_fail,
        asset_with_cron_freshness_policy,
        asset_with_cron_freshness_policy_with_timezone,
        asset_with_cron_freshness_policy_short_cron_interval,
        asset_with_cron_freshness_policy_irregular_schedule,
    ]
