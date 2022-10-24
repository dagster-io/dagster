import pytest

from dagster import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._seven.compat.pendulum import create_pendulum_time


@pytest.mark.parametrize(
    ["sla", "materialization_time", "evaluation_time", "should_pass"],
    [
        (
            FreshnessPolicy.minimum_freshness(30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 0, 25),
            True,
        ),
        (
            FreshnessPolicy.minimum_freshness(120),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            True,
        ),
        (
            FreshnessPolicy.minimum_freshness(30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            False,
        ),
        (
            FreshnessPolicy.minimum_freshness(500),
            None,
            create_pendulum_time(2022, 1, 1, 0, 25),
            False,
        ),
        # materialization happened before SLA
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 0, 5),
            create_pendulum_time(2022, 1, 1, 0, 10),
            True,
        ),
        # materialization happened after SLA, but is fine now
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 0, 30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            True,
        ),
        # materialization for this data has not happened yet (day before)
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@daily", minimum_freshness_minutes=15
            ),
            create_pendulum_time(2022, 1, 1, 23, 0),
            create_pendulum_time(2022, 1, 2, 1, 0),
            False,
        ),
        # weird one, basically want to have a materialization every hour no more than 5 hours after
        # that data arrives -- edge case probably not useful in practice?
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@hourly", minimum_freshness_minutes=60 * 5
            ),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 4, 0),
            True,
        ),
        (
            FreshnessPolicy.cron_minimum_freshness(
                cron_schedule="@hourly", minimum_freshness_minutes=60 * 5
            ),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 6, 30),
            False,
        ),
    ],
)
def test_slas(sla, materialization_time, evaluation_time, should_pass):
    if materialization_time:
        upstream_materialization_times = {AssetKey("root"): materialization_time.timestamp()}
    else:
        upstream_materialization_times = {AssetKey("root"): None}

    assert (
        sla.is_passing(
            current_timestamp=evaluation_time.timestamp(),
            upstream_materialization_timestamps=upstream_materialization_times,
        )
        == should_pass
    )
