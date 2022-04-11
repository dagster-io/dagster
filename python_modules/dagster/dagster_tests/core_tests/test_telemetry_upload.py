import logging
import os

import mock
import pytest
import responses
from click.testing import CliRunner

from dagster.cli.pipeline import pipeline_execute_command
from dagster.core.telemetry import cleanup_telemetry_logger
from dagster.core.telemetry_upload import get_dagster_telemetry_url, upload_logs
from dagster.core.test_utils import environ, instance_for_test
from dagster.utils import pushd, script_relative_path


def path_to_file(path):
    return script_relative_path(os.path.join("./", path))


# Note that both environment must be set together. Otherwise, if env={"BUILDKITE": None} ran in the
# azure pipeline, then this test would fail, because TF_BUILD would be set implicitly, resulting in
# no logs being uploaded. The same applies in the reverse way, if only TF_BUILD is set to None.
@pytest.mark.parametrize(
    "env", [{"BUILDKITE": None, "TF_BUILD": None, "DAGSTER_DISABLE_TELEMETRY": None}]
)
@responses.activate
def test_dagster_telemetry_upload(env):
    logger = logging.getLogger("dagster_telemetry_logger")
    for handler in logger.handlers:
        logger.removeHandler(handler)

    responses.add(responses.POST, get_dagster_telemetry_url())

    with instance_for_test(overrides={"telemetry": {"enabled": True}}):
        with environ(env):
            runner = CliRunner()
            with pushd(path_to_file("")):
                pipeline_attribute = "foo_pipeline"
                runner.invoke(
                    pipeline_execute_command,
                    ["-f", path_to_file("test_cli_commands.py"), "-a", pipeline_attribute],
                )

            mock_stop_event = mock.MagicMock()
            mock_stop_event.is_set.return_value = False

            def side_effect(_):
                mock_stop_event.is_set.return_value = True

            mock_stop_event.wait.side_effect = side_effect

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()

            upload_logs(mock_stop_event, raise_errors=True)
            assert responses.assert_call_count(get_dagster_telemetry_url(), 1)


@pytest.mark.parametrize(
    "env",
    [
        {"BUILDKITE": "True", "DAGSTER_DISABLE_TELEMETRY": None},
        {"TF_BUILD": "True", "DAGSTER_DISABLE_TELEMETRY": None},
        {"DAGSTER_DISABLE_TELEMETRY": "True"},
    ],
)
@responses.activate
def test_dagster_telemetry_no_test_env_upload(env):
    with instance_for_test():
        with environ(env):
            runner = CliRunner()
            with pushd(path_to_file("")):
                pipeline_attribute = "foo_pipeline"
                runner.invoke(
                    pipeline_execute_command,
                    ["-f", path_to_file("test_cli_commands.py"), "-a", pipeline_attribute],
                )

            upload_logs(mock.MagicMock())
            assert responses.assert_call_count(get_dagster_telemetry_url(), 0)
