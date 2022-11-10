import pytest

from dagster import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._seven.compat.pendulum import create_pendulum_time


@pytest.mark.parametrize(
    [
        "policy",
        "used_data_time",
        "evaluation_time",
        "expected_minutes_late",
    ],
    [
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 0, 25),
            0,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=120),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            0,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            30,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=500),
            None,
            create_pendulum_time(2022, 1, 1, 0, 25),
            None,
        ),
        # materialization happened before SLA
        (
            FreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=15),
            create_pendulum_time(2022, 1, 1, 23, 55),
            create_pendulum_time(2022, 1, 2, 0, 10),
            0,
        ),
        # materialization happened after SLA, but is fine now
        (
            FreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=15),
            create_pendulum_time(2022, 1, 1, 0, 30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            0,
        ),
        # materialization for this data has not happened yet (day before)
        (
            FreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=60),
            create_pendulum_time(2022, 1, 1, 22, 0),
            create_pendulum_time(2022, 1, 2, 2, 0),
            # by midnight, expected data from up to 2022-01-02T23:00, but actual data is from
            # 2022-01-01T22:00, so you are 1 hour late
            60,
        ),
        # weird one: at the end of each hour, your data should be no more than 5 hours old
        (
            FreshnessPolicy(cron_schedule="@hourly", maximum_lag_minutes=60 * 5),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 4, 0),
            0,
        ),
        (
            FreshnessPolicy(cron_schedule="@hourly", maximum_lag_minutes=60 * 5),
            create_pendulum_time(2022, 1, 1, 1, 15),
            create_pendulum_time(2022, 1, 1, 7, 45),
            # schedule is evaluated on the hour, so most recent schedule tick is 7AM. At this point
            # in time, we expect to have the data from at least 5 hours ago (so 2AM), but we only
            # have data from 1:15, so we're 45 minutes late
            45,
        ),
    ],
)
def test_policies_available_equals_evaluation_time(
    policy,
    used_data_time,
    evaluation_time,
    expected_minutes_late,
):
    used_data_times = {AssetKey("root"): used_data_time}
    available_data_times = {AssetKey("root"): evaluation_time}

    minutes_late = policy.minutes_late(
        evaluation_time=evaluation_time,
        used_data_times=used_data_times,
        available_data_times=available_data_times,
    )

    assert minutes_late == expected_minutes_late


@pytest.mark.parametrize(
    [
        "policy",
        "used_data_time",
        "available_data_time",
        "evaluation_time",
        "expected_minutes_late",
    ],
    [
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            None,
            create_pendulum_time(2022, 1, 1, 3, 0),
            # No data available for the upstream, so it's undefined if you're out of date
            None,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 1, 15),
            create_pendulum_time(2022, 1, 1, 1, 15),
            create_pendulum_time(2022, 1, 1, 3, 0),
            # Have incorporated the latest data already, so you're not out of date
            0,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 1, 15),
            create_pendulum_time(2022, 1, 1, 1, 30),
            create_pendulum_time(2022, 1, 1, 1, 55),
            # There's newer data available as of 1:30, but it's only 1:55, so you're not out of
            # date yet
            0,
        ),
        (
            FreshnessPolicy(maximum_lag_minutes=30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 2, 0),
            create_pendulum_time(2022, 1, 1, 3, 30),
            # Expected to have 2:00 data by 2:30, but now it's 3:30, so you're 1hr out of date
            60,
        ),
    ],
)
def test_policies_varied_available_time(
    policy,
    used_data_time,
    available_data_time,
    evaluation_time,
    expected_minutes_late,
):
    used_data_times = {AssetKey("root"): used_data_time}
    available_data_times = {AssetKey("root"): available_data_time}

    minutes_late = policy.minutes_late(
        evaluation_time=evaluation_time,
        used_data_times=used_data_times,
        available_data_times=available_data_times,
    )
    assert minutes_late == expected_minutes_late
