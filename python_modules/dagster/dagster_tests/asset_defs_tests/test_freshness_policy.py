import datetime
import os

import dagster as dg
import pytest
from dagster._check import ParameterCheckError
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._serdes import deserialize_value, serialize_value
from dagster._time import create_datetime


@pytest.mark.parametrize(
    [
        "policy",
        "used_data_time",
        "evaluation_time",
        "expected_minutes_overdue",
        "expected_minutes_lag",
    ],
    [
        (
            LegacyFreshnessPolicy(maximum_lag_minutes=30),
            create_datetime(2022, 1, 1, 0),
            create_datetime(2022, 1, 1, 0, 25),
            0,
            25,
        ),
        (
            LegacyFreshnessPolicy(maximum_lag_minutes=120),
            create_datetime(2022, 1, 1, 0),
            create_datetime(2022, 1, 1, 1),
            0,
            60,
        ),
        (
            LegacyFreshnessPolicy(maximum_lag_minutes=30),
            create_datetime(2022, 1, 1, 0),
            create_datetime(2022, 1, 1, 1),
            30,
            60,
        ),
        (
            LegacyFreshnessPolicy(maximum_lag_minutes=500),
            None,
            create_datetime(2022, 1, 1, 0, 25),
            None,
            None,
        ),
        # materialization happened before SLA
        (
            LegacyFreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=15),
            create_datetime(2022, 1, 1, 23, 55),
            create_datetime(2022, 1, 2, 0, 10),
            0,
            5,
        ),
        # materialization happened after SLA, but is fine now
        (
            LegacyFreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=15),
            create_datetime(2022, 1, 1, 0, 30),
            create_datetime(2022, 1, 1, 1, 0),
            0,
            0,
        ),
        # materialization for this data has not happened yet (day before)
        (
            LegacyFreshnessPolicy(cron_schedule="@daily", maximum_lag_minutes=60),
            create_datetime(2022, 1, 1, 22, 0),
            create_datetime(2022, 1, 2, 2, 0),
            # by midnight, expected data from up to 2022-01-02T23:00, but actual data is from
            # 2022-01-01T22:00, so you are 1 hour late
            60,
            120,
        ),
        # weird one: at the end of each hour, your data should be no more than 5 hours old
        (
            LegacyFreshnessPolicy(cron_schedule="@hourly", maximum_lag_minutes=60 * 5),
            create_datetime(2022, 1, 1, 1, 0),
            create_datetime(2022, 1, 1, 4, 0),
            0,
            180,
        ),
        (
            LegacyFreshnessPolicy(cron_schedule="@hourly", maximum_lag_minutes=60 * 5),
            create_datetime(2022, 1, 1, 1, 15),
            create_datetime(2022, 1, 1, 7, 45),
            # schedule is evaluated on the hour, so most recent schedule tick is 7AM. At this point
            # in time, we expect to have the data from at least 5 hours ago (so 2AM), but we only
            # have data from 1:15, so we're 45 minutes late
            45,
            45 + 60 * 5,
        ),
        # timezone tests
        (
            LegacyFreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_datetime(2022, 1, 1, 1, 0, tz="America/Los_Angeles"),
            create_datetime(2022, 1, 1, 3, 15, tz="America/Los_Angeles"),
            # only have data up to 1AM in this timezone, but we need up to 2AM, so we're 1hr late
            60,
            120,
        ),
        (
            # same as above, but specifying the input to the function in UTC
            LegacyFreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_datetime(2022, 1, 1, 1, 0, tz="America/Los_Angeles").astimezone(
                datetime.timezone.utc
            ),
            create_datetime(2022, 1, 1, 3, 15, tz="America/Los_Angeles").astimezone(
                datetime.timezone.utc
            ),
            # only have data up to 1AM in this timezone, but we need up to 2AM, so we're 1hr late
            60,
            120,
        ),
        (
            LegacyFreshnessPolicy(
                cron_schedule="0 3 * * *",
                cron_schedule_timezone="America/Los_Angeles",
                maximum_lag_minutes=60,
            ),
            create_datetime(2022, 1, 1, 0, 0, tz="America/Los_Angeles"),
            create_datetime(2022, 1, 1, 2, 15, tz="America/Los_Angeles"),
            # it's not yet 3AM in this timezone, so we're not late
            0,
            0,
        ),
    ],
)
def test_policies_available_equals_evaluation_time(
    policy,
    used_data_time,
    evaluation_time,
    expected_minutes_overdue,
    expected_minutes_lag,
):
    result = policy.minutes_overdue(
        data_time=used_data_time,
        evaluation_time=evaluation_time,
    )

    assert getattr(result, "overdue_minutes", None) == expected_minutes_overdue
    assert getattr(result, "lag_minutes", None) == expected_minutes_lag


def test_invalid_freshness_policies():
    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid cron schedule"):
        LegacyFreshnessPolicy(cron_schedule="xyz-123-bad-schedule", maximum_lag_minutes=60)

    with pytest.raises(DagsterInvalidDefinitionError, match="Invalid cron schedule timezone"):
        LegacyFreshnessPolicy(
            cron_schedule="0 1 * * *",
            maximum_lag_minutes=60,
            cron_schedule_timezone="Not/ATimezone",
        )

    with pytest.raises(ParameterCheckError, match="without a cron_schedule"):
        LegacyFreshnessPolicy(maximum_lag_minutes=0, cron_schedule_timezone="America/Los_Angeles")


def test_legacy_freshness_backcompat():
    """We've renamed FreshnessPolicy to LegacyFreshnessPolicy in the latest version of Dagster.
    Can host cloud on latest Dagster version deserialize an asset snap that was created on an older Dagster version
    for an asset with legacy freshness policy?
    """
    this_dir = os.path.dirname(os.path.abspath(__file__))

    @dg.asset(
        legacy_freshness_policy=dg.LegacyFreshnessPolicy(
            maximum_lag_minutes=1,
            cron_schedule="0 1 * * *",
            cron_schedule_timezone="America/Los_Angeles",
        )
    )
    def foo():
        pass

    defs = dg.Definitions(
        assets=[foo],
    )
    new_snap = RepositorySnap.from_def(defs.get_repository_def())
    with open(
        os.path.join(this_dir, "snapshots", "repo_with_asset_with_legacy_freshness.json")
    ) as f:
        old_snap_serialized = f.read()

    # First, check that both serialized snapshots are the same
    with open(
        os.path.join(this_dir, "snapshots", "repo_with_asset_with_legacy_freshness_new.json"), "w"
    ) as f:
        f.write(serialize_value(new_snap))

    # Then, check that we can deserialize the old snapshot with new Dagster version
    old_snap_deserialized = deserialize_value(old_snap_serialized, RepositorySnap)

    # Then, check that the deserialized policies match
    assert (
        old_snap_deserialized.asset_nodes[0].legacy_freshness_policy
        == new_snap.asset_nodes[0].legacy_freshness_policy
    )
    assert new_snap.asset_nodes[0].legacy_freshness_policy
    assert new_snap.asset_nodes[0].legacy_freshness_policy.maximum_lag_minutes == 1
    assert new_snap.asset_nodes[0].legacy_freshness_policy.cron_schedule == "0 1 * * *"
    assert (
        new_snap.asset_nodes[0].legacy_freshness_policy.cron_schedule_timezone
        == "America/Los_Angeles"
    )


def test_freshness_policy_deprecated_import():
    """We should be able to import FreshnessPolicy from `dagster.deprecated` and use it to define a freshness policy on an asset."""
    from dagster.deprecated import FreshnessPolicy

    policy = FreshnessPolicy(maximum_lag_minutes=1)
    assert isinstance(policy, LegacyFreshnessPolicy)

    @dg.asset(legacy_freshness_policy=policy)
    def foo():
        pass

    dg.Definitions(assets=[foo])


def test_freshness_policy_metadata_backcompat():
    """We should be able to deserialize freshness policy from an asset spec that stores the policy in its metadata."""
    from dagster._core.definitions.freshness import TimeWindowFreshnessPolicy

    this_dir = os.path.dirname(os.path.abspath(__file__))
    with open(
        os.path.join(
            this_dir, "snapshots", "repo_with_asset_with_internal_freshness_in_metadata.json"
        )
    ) as f:
        snap_with_metadata_policy = deserialize_value(f.read(), RepositorySnap)

    policy = snap_with_metadata_policy.asset_nodes[0].freshness_policy
    assert policy is not None
    assert isinstance(policy, TimeWindowFreshnessPolicy)
    assert policy.fail_window.to_timedelta() == datetime.timedelta(hours=24)
    assert policy.warn_window
    assert policy.warn_window.to_timedelta() == datetime.timedelta(hours=12)
