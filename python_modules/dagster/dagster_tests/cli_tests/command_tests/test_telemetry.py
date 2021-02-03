import json
import logging
import os
import tempfile
from difflib import SequenceMatcher

import mock
import pytest
import responses
from click.testing import CliRunner
from dagster.cli.pipeline import pipeline_execute_command
from dagster.cli.workspace.load import load_workspace_from_yaml_paths
from dagster.core.definitions.reconstructable import get_ephemeral_repository_name
from dagster.core.telemetry import (
    DAGSTER_TELEMETRY_URL,
    UPDATE_REPO_STATS,
    cleanup_telemetry_logger,
    get_dir_from_dagster_home,
    hash_name,
    log_workspace_stats,
    upload_logs,
)
from dagster.core.test_utils import environ, instance_for_test, instance_for_test_tempdir
from dagster.utils import file_relative_path, pushd, script_relative_path

EXPECTED_KEYS = set(
    [
        "action",
        "client_time",
        "elapsed_time",
        "event_id",
        "instance_id",
        "pipeline_name_hash",
        "num_pipelines_in_repo",
        "repo_hash",
        "python_version",
        "metadata",
        "version",
    ]
)


def path_to_file(path):
    return script_relative_path(os.path.join("./", path))


def test_dagster_telemetry_enabled(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": True}}):
        runner = CliRunner()
        with pushd(path_to_file("")):
            pipeline_attribute = "foo_pipeline"
            pipeline_name = "foo"
            result = runner.invoke(
                pipeline_execute_command,
                [
                    "-f",
                    path_to_file("test_cli_commands.py"),
                    "-a",
                    pipeline_attribute,
                ],
            )

            for record in caplog.records:
                message = json.loads(record.getMessage())
                if message.get("action") == UPDATE_REPO_STATS:
                    assert message.get("pipeline_name_hash") == hash_name(pipeline_name)
                    assert message.get("num_pipelines_in_repo") == str(1)
                    assert message.get("repo_hash") == hash_name(
                        get_ephemeral_repository_name(pipeline_name)
                    )
                assert set(message.keys()) == EXPECTED_KEYS
            assert len(caplog.records) == 5
            assert result.exit_code == 0


def test_dagster_telemetry_disabled(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": False}}):
        runner = CliRunner()
        with pushd(path_to_file("")):
            pipeline_name = "foo_pipeline"
            result = runner.invoke(
                pipeline_execute_command,
                [
                    "-f",
                    path_to_file("test_cli_commands.py"),
                    "-a",
                    pipeline_name,
                ],
            )

        assert not os.path.exists(os.path.join(get_dir_from_dagster_home("logs"), "event.log"))
        assert len(caplog.records) == 0
        assert result.exit_code == 0


def test_dagster_telemetry_unset(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(temp_dir):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            with pushd(path_to_file("")):
                pipeline_attribute = "foo_pipeline"
                pipeline_name = "foo"
                result = runner.invoke(
                    pipeline_execute_command,
                    ["-f", path_to_file("test_cli_commands.py"), "-a", pipeline_attribute],
                )

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    if message.get("action") == UPDATE_REPO_STATS:
                        assert message.get("pipeline_name_hash") == hash_name(pipeline_name)
                        assert message.get("num_pipelines_in_repo") == str(1)
                        assert message.get("repo_hash") == hash_name(
                            get_ephemeral_repository_name(pipeline_name)
                        )
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 5
                assert result.exit_code == 0


def test_repo_stats(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test_tempdir(temp_dir):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            with pushd(path_to_file("")):
                pipeline_name = "multi_mode_with_resources"
                result = runner.invoke(
                    pipeline_execute_command,
                    [
                        "-f",
                        file_relative_path(__file__, "../../general_tests/test_repository.py"),
                        "-a",
                        "dagster_test_repository",
                        "-p",
                        pipeline_name,
                        "--preset",
                        "add",
                        "--tags",
                        '{ "foo": "bar" }',
                    ],
                )

                assert result.exit_code == 0, result.stdout

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    if message.get("action") == UPDATE_REPO_STATS:
                        assert message.get("pipeline_name_hash") == hash_name(pipeline_name)
                        assert message.get("num_pipelines_in_repo") == str(4)
                        assert message.get("repo_hash") == hash_name("dagster_test_repository")
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 5
                assert result.exit_code == 0


def test_log_workspace_stats(caplog):
    with instance_for_test() as instance:
        with load_workspace_from_yaml_paths(
            [file_relative_path(__file__, "./multi_env_telemetry_workspace.yaml")]
        ) as workspace:
            log_workspace_stats(instance, workspace)

            for record in caplog.records:
                message = json.loads(record.getMessage())
                assert message.get("action") == UPDATE_REPO_STATS
                assert set(message.keys()) == EXPECTED_KEYS

            assert len(caplog.records) == 2


# Note that both environment must be set together. Otherwise, if env={"BUILDKITE": None} ran in the
# azure pipeline, then this test would fail, because TF_BUILD would be set implicitly, resulting in
# no logs being uploaded. The same applies in the reverse way, if only TF_BUILD is set to None.
@pytest.mark.parametrize("env", [{"BUILDKITE": None, "TF_BUILD": None}])
@responses.activate
def test_dagster_telemetry_upload(env):
    logger = logging.getLogger("dagster_telemetry_logger")
    for handler in logger.handlers:
        logger.removeHandler(handler)

    responses.add(responses.POST, DAGSTER_TELEMETRY_URL)

    with environ(env):
        with instance_for_test():
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
            assert responses.assert_call_count(DAGSTER_TELEMETRY_URL, 1)


@pytest.mark.parametrize("env", [{"BUILDKITE": "True"}, {"TF_BUILD": "True"}])
@responses.activate
def test_dagster_telemetry_no_test_env_upload(env):
    with environ(env):
        with instance_for_test():
            runner = CliRunner()
            with pushd(path_to_file("")):
                pipeline_attribute = "foo_pipeline"
                runner.invoke(
                    pipeline_execute_command,
                    ["-f", path_to_file("test_cli_commands.py"), "-a", pipeline_attribute],
                )

            upload_logs(mock.MagicMock())
            assert responses.assert_call_count(DAGSTER_TELEMETRY_URL, 0)


# Sanity check that the hash function maps these similar names to sufficiently dissimilar strings
# From the docs, SequenceMatcher `does not yield minimal edit sequences, but does tend to yield
# matches that "look right" to people. As a rule of thumb, a .ratio() value over 0.6 means the
# sequences are close matches`
# Other than above, 0.4 was picked arbitrarily.
def test_hash_name():
    pipelines = ["pipeline_1", "pipeline_2", "pipeline_3"]
    hashes = [hash_name(p) for p in pipelines]
    for h in hashes:
        assert len(h) == 64

    assert SequenceMatcher(None, hashes[0], hashes[1]).ratio() < 0.4
    assert SequenceMatcher(None, hashes[0], hashes[2]).ratio() < 0.4
    assert SequenceMatcher(None, hashes[1], hashes[2]).ratio() < 0.4
