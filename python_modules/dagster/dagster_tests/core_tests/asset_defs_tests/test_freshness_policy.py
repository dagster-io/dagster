import pytest

from dagster import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._seven.compat.pendulum import create_pendulum_time


@pytest.mark.parametrize(
    ["policy", "materialization_time", "evaluation_time", "expected_minutes_late"],
    [
        (
            FreshnessPolicy.minimum_freshness(30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 0, 25),
            0,
        ),
        (
            FreshnessPolicy.minimum_freshness(120),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            0,
        ),
        (
            FreshnessPolicy.minimum_freshness(30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            30,
        ),
        (
            FreshnessPolicy.minimum_freshness(500),
            None,
            create_pendulum_time(2022, 1, 1, 0, 25),
            None,
        ),
        # materialization happened before SLA
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 0, 5),
            create_pendulum_time(2022, 1, 1, 0, 10),
            0,
        ),
        # materialization happened after SLA, but is fine now
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 0, 30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            0,
        ),
        # materialization for this data has not happened yet (day before)
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 23, 0),
            create_pendulum_time(2022, 1, 2, 2, 0),
            # expected data by is 2022-01-02T00:15, so you are 1 hour, 45 minutes late
            60 + 45,
        ),
        # weird one, basically want to have a materialization every hour no more than 5 hours after
        # that data arrives -- edge case probably not useful in practice?
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@hourly", minimum_freshness_minutes=60 * 5
            ),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 4, 0),
            0,
        ),
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@hourly", minimum_freshness_minutes=60 * 5
            ),
            create_pendulum_time(2022, 1, 1, 1, 15),
            create_pendulum_time(2022, 1, 1, 7, 45),
            # the data for 2AM is considered missing if it is not there by 7AM (5 hours later).
            # we evaluate at 7:45, so at this point it is 45 minutes late
            45,
        ),
    ],
)
def test_policies(policy, materialization_time, evaluation_time, expected_minutes_late):
    if materialization_time:
        upstream_materialization_times = {AssetKey("root"): materialization_time}
    else:
        upstream_materialization_times = {AssetKey("root"): None}
    minutes_late = policy.minutes_late(
        evaluation_time=evaluation_time,
        upstream_materialization_times=upstream_materialization_times,
    )

    assert minutes_late == expected_minutes_late
