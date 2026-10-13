import os
from unittest import mock

import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    EnvVar,
    build_run_status_sensor_context,
    job,
    op,
    repository,
)
from dagster._core.test_utils import environ
from dagster_slack.sensors import make_slack_on_run_failure_sensor


def test_slack_run_failure_sensor_def():
    with environ({"SLACK_TOKEN": "blah"}):
        sensor_name = "my_failure_sensor"

        my_sensor = make_slack_on_run_failure_sensor(
            channel="#foo",
            slack_token=os.getenv("SLACK_TOKEN"),  # ty: ignore[invalid-argument-type]
            name=sensor_name,
        )
        assert my_sensor.name == sensor_name

        @repository
        def my_repo():
            return [my_sensor]

        assert my_repo.has_sensor_def(sensor_name)


def _build_run_failure_context():
    @op
    def will_fail():
        raise Exception("boom")

    @job
    def failing_job():
        will_fail()

    instance = DagsterInstance.ephemeral()
    result = failing_job.execute_in_process(instance=instance, raise_on_error=False)
    return build_run_status_sensor_context(
        sensor_name="slack_on_run_failure",
        dagster_instance=instance,
        dagster_run=result.dagster_run,
        dagster_event=result.get_run_failure_event(),
    ).for_run_failure()


def test_slack_run_failure_sensor_resolves_env_var_token():
    context = _build_run_failure_context()
    with mock.patch("dagster_slack.sensors.WebClient") as mock_web_client:
        my_sensor = make_slack_on_run_failure_sensor(
            channel="#foo", slack_token=EnvVar("SLACK_TOKEN_FOR_TEST")
        )
        with environ({"SLACK_TOKEN_FOR_TEST": "xoxb-real-token"}):
            my_sensor(context)

    mock_web_client.assert_called_once_with(token="xoxb-real-token")
    mock_web_client.return_value.chat_postMessage.assert_called_once()
    assert mock_web_client.return_value.chat_postMessage.call_args.kwargs["channel"] == "#foo"


def test_slack_run_failure_sensor_unset_env_var_token():
    context = _build_run_failure_context()
    assert "UNSET_SLACK_TOKEN_FOR_TEST" not in os.environ
    with mock.patch("dagster_slack.sensors.WebClient") as mock_web_client:
        my_sensor = make_slack_on_run_failure_sensor(
            channel="#foo", slack_token=EnvVar("UNSET_SLACK_TOKEN_FOR_TEST")
        )
        with pytest.raises(DagsterInvariantViolationError, match="UNSET_SLACK_TOKEN_FOR_TEST"):
            my_sensor(context)

    mock_web_client.return_value.chat_postMessage.assert_not_called()


def test_slack_run_failure_sensor_plain_token():
    context = _build_run_failure_context()
    with mock.patch("dagster_slack.sensors.WebClient") as mock_web_client:
        my_sensor = make_slack_on_run_failure_sensor(channel="#foo", slack_token="xoxb-plain-token")
        my_sensor(context)

    mock_web_client.assert_called_once_with(token="xoxb-plain-token")
    mock_web_client.return_value.chat_postMessage.assert_called_once()
