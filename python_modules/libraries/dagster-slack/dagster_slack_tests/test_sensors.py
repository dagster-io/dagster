import os
from typing import Optional
from unittest.mock import patch

import pytest
from dagster import (
    AssetKey,
    AssetSelection,
    FreshnessPolicy,
    build_freshness_policy_sensor_context,
    repository,
)
from dagster._core.test_utils import environ
from dagster_slack.sensors import (
    make_slack_on_freshness_policy_status_change_sensor,
    make_slack_on_run_failure_sensor,
)
from slack_sdk.web.client import WebClient


def test_slack_run_failure_sensor_def():
    with environ({"SLACK_TOKEN": "blah"}):
        sensor_name = "my_failure_sensor"

        my_sensor = make_slack_on_run_failure_sensor(
            channel="#foo", slack_token=os.getenv("SLACK_TOKEN"), name=sensor_name
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)


@pytest.mark.parametrize(
    [
        "minutes_overdue",
        "previous_minutes_overdue",
        "warn_after_minutes",
        "notify_when_back_on_time",
        "should_output",
    ],
    [
        (None, None, 0, False, False),
        # should notify because you're now > 0 minutes late
        (1, 0, 0, False, True),
        # should not notify because you previously did
        (2, 1, 0, False, False),
        # should not notify because you're not > 10 minutes late
        (8, 0, 10, False, False),
        # should notify because you're now > 10 minutes late
        (11, 8, 10, False, True),
        # should not notify because notify_when_back_on_time=False
        (0, 1, 0, False, False),
        # should notify because notify_when_back_on_time=True
        (0, 1, 0, True, True),
        # should not notify because you previously did
        (0, 0, 0, True, False),
    ],
)
def test_slack_freshness_polciy_status(
    minutes_overdue: Optional[float],
    previous_minutes_overdue: Optional[float],
    warn_after_minutes: float,
    notify_when_back_on_time: bool,
    should_output: bool,
):
    with patch.object(WebClient, "chat_postMessage", return_value=None) as mocked_post:
        my_sensor = make_slack_on_freshness_policy_status_change_sensor(
            channel="#foo",
            slack_token="blah",
            asset_selection=AssetSelection.all(),
            warn_after_minutes_overdue=warn_after_minutes,
            notify_when_back_on_time=notify_when_back_on_time,
        )
        my_sensor(
            build_freshness_policy_sensor_context(
                "slack_on_freshness_policy",
                asset_key=AssetKey(["foo", "bar"]),
                freshness_policy=FreshnessPolicy(maximum_lag_minutes=5),
                minutes_overdue=minutes_overdue,
                previous_minutes_overdue=previous_minutes_overdue,
            )
        )
        if should_output:
            mocked_post.assert_called_once()
        else:
            mocked_post.assert_not_called()
