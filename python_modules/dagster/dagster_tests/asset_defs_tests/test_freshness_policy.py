import pytest
from dagster._check import ParameterCheckError
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.errors import DagsterInvalidDefinitionError
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
        # timezone tests
        (
            FreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_pendulum_time(2022, 1, 1, 1, 0, tz="America/Los_Angeles"),
            create_pendulum_time(2022, 1, 1, 3, 15, tz="America/Los_Angeles"),
            # only have data up to 1AM in this timezone, but we need up to 2AM, so we're 1hr late
            60,
        ),
        (
            # same as above, but specifying the input to the function in UTC
            FreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_pendulum_time(2022, 1, 1, 1, 0, tz="America/Los_Angeles").in_tz("UTC"),
            create_pendulum_time(2022, 1, 1, 3, 15, tz="America/Los_Angeles").in_tz("UTC"),
            # only have data up to 1AM in this timezone, but we need up to 2AM, so we're 1hr late
            60,
        ),
        (
            FreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_pendulum_time(2022, 1, 1, 0, 0, tz="America/Los_Angeles"),
            create_pendulum_time(2022, 1, 1, 2, 15, tz="America/Los_Angeles"),
            # it's not yet 3AM in this timezone, so we're not late
            0,
        ),
    ],
)
def test_policies_available_equals_evaluation_time(
    policy,
    used_data_time,
    evaluation_time,
    expected_minutes_late,
):
    minutes_late = policy.minutes_overdue(
        data_time=used_data_time,
        evaluation_time=evaluation_time,
    )

    assert minutes_late == expected_minutes_late


def test_invalid_freshness_policies():
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid cron schedule"):
        FreshnessPolicy(cron_schedule="xyz-123-bad-schedule", maximum_lag_minutes=60)

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid cron schedule timezone"):
        FreshnessPolicy(
            cron_schedule="0 1 * * *",
            maximum_lag_minutes=60,
            cron_schedule_timezone="Not/ATimezone",
        )

    with pytest.raises(ParameterCheckError, match="without a cron_schedule"):
        FreshnessPolicy(maximum_lag_minutes=0, cron_schedule_timezone="America/Los_Angeles")
