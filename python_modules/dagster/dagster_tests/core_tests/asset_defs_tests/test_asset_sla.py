import mock
import pendulum
import pytest

from dagster import CronSLA, StalenessSLA
from dagster._seven.compat.pendulum import create_pendulum_time


@pytest.mark.parametrize(
    ["sla", "materialization_time", "evaluation_time", "should_pass"],
    [
        (
            StalenessSLA(allowed_staleness_minutes=30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 0, 25),
            True,
        ),
        (
            StalenessSLA(allowed_staleness_minutes=120),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            True,
        ),
        (
            StalenessSLA(allowed_staleness_minutes=30),
            create_pendulum_time(2022, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 1),
            False,
        ),
        (
            StalenessSLA(allowed_staleness_minutes=500),
            None,
            create_pendulum_time(2022, 1, 1, 0, 25),
            False,
        ),
        # materialization happened before SLA
        (
            CronSLA(cron_schedule="@daily", allowed_staleness_minutes=15),
            create_pendulum_time(2022, 1, 1, 0, 5),
            create_pendulum_time(2022, 1, 1, 0, 10),
            True,
        ),
        # materialization happened after SLA, but is fine now
        (
            CronSLA(cron_schedule="@daily", allowed_staleness_minutes=15),
            create_pendulum_time(2022, 1, 1, 0, 30),
            create_pendulum_time(2022, 1, 1, 1, 0),
            True,
        ),
        # materialization for this data has not happened yet (day before)
        (
            CronSLA(cron_schedule="@daily", allowed_staleness_minutes=15),
            create_pendulum_time(2022, 1, 1, 23, 0),
            create_pendulum_time(2022, 1, 2, 1, 0),
            False,
        ),
        # weird one, basically want to have a materialization every hour no more than 5 hours after
        # that data arrives -- edge case probably not useful in practice?
        (
            CronSLA(cron_schedule="@hourly", allowed_staleness_minutes=60 * 5),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 4, 0),
            True,
        ),
        (
            CronSLA(cron_schedule="@hourly", allowed_staleness_minutes=60 * 5),
            create_pendulum_time(2022, 1, 1, 1, 0),
            create_pendulum_time(2022, 1, 1, 6, 30),
            False,
        ),
    ],
)
def test_slas(sla, materialization_time, evaluation_time, should_pass):
    if materialization_time:
        latest_asset_event = mock.Mock()
        latest_asset_event.event_log_entry.timestamp = materialization_time.timestamp()
    else:
        latest_asset_event = None

    with pendulum.test(evaluation_time):
        assert sla.is_passing(latest_asset_event) == should_pass
