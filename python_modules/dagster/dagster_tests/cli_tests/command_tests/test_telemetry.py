import json
import os
import tempfile
from difflib import SequenceMatcher

from click.testing import CliRunner

from dagster._cli.pipeline import pipeline_execute_command
from dagster._utils import file_relative_path, pushd, script_relative_path
from dagster._core.definitions.reconstruct import get_ephemeral_repository_name
from dagster._core.telemetry import (
    TELEMETRY_STR,
    UPDATE_REPO_STATS,
    cleanup_telemetry_logger,
    get_or_create_dir_from_dagster_home,
    get_or_set_instance_id,
    hash_name,
    log_workspace_stats,
    write_telemetry_log_line,
)
from dagster._core.test_utils import environ, instance_for_test
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths

EXPECTED_KEYS = set(
    [
        "action",
        "client_time",
        "elapsed_time",
        "event_id",
        "instance_id",
        "run_storage_id",
        "python_version",
        "metadata",
        "os_desc",
        "os_platform",
        "dagster_version",
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
                    metadata = message.get("metadata")
                    assert metadata.get("pipeline_name_hash") == hash_name(pipeline_name)
                    assert metadata.get("num_pipelines_in_repo") == str(1)
                    assert metadata.get("repo_hash") == hash_name(
                        get_ephemeral_repository_name(pipeline_name)
                    )
                assert set(message.keys()) == EXPECTED_KEYS
            assert len(caplog.records) == 5
            assert result.exit_code == 0

        # Needed to avoid file contention issues on windows with the telemetry log file
        cleanup_telemetry_logger()


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

        assert not os.path.exists(
            os.path.join(get_or_create_dir_from_dagster_home("logs"), "event.log")
        )
        assert len(caplog.records) == 0
        assert result.exit_code == 0


def test_dagster_telemetry_unset(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir, overrides={"telemetry": {"enabled": True}}):
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
                        metadata = message.get("metadata")
                        assert metadata.get("pipeline_name_hash") == hash_name(pipeline_name)
                        assert metadata.get("num_pipelines_in_repo") == str(1)
                        assert metadata.get("repo_hash") == hash_name(
                            get_ephemeral_repository_name(pipeline_name)
                        )
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 5
                assert result.exit_code == 0

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()


def test_repo_stats(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir, overrides={"telemetry": {"enabled": True}}):
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
                        metadata = message.get("metadata")
                        assert metadata.get("pipeline_name_hash") == hash_name(pipeline_name)
                        assert metadata.get("num_pipelines_in_repo") == str(4)
                        assert metadata.get("repo_hash") == hash_name("dagster_test_repository")
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 5
                assert result.exit_code == 0

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()


def test_log_workspace_stats(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": True}}) as instance:
        with load_workspace_process_context_from_yaml_paths(
            instance, [file_relative_path(__file__, "./multi_env_telemetry_workspace.yaml")]
        ) as context:
            log_workspace_stats(instance, context)

            for record in caplog.records:
                message = json.loads(record.getMessage())
                assert message.get("action") == UPDATE_REPO_STATS
                assert set(message.keys()) == EXPECTED_KEYS

            assert len(caplog.records) == 2

        # Needed to avoid file contention issues on windows with the telemetry log file
        cleanup_telemetry_logger()


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


def test_write_telemetry_log_line_writes_to_dagster_home():
    # Ensures that if logging directory is deleted between writes, it can be re-created without failure.
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            write_telemetry_log_line({"foo": "bar"})
            with open(os.path.join(temp_dir, "logs", "event.log"), "r", encoding="utf8") as f:
                res = json.load(f)
                assert res == {"foo": "bar"}

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()

            os.remove(os.path.join(temp_dir, "logs", "event.log"))
            os.rmdir(os.path.join(temp_dir, "logs"))

            write_telemetry_log_line({"foo": "bar"})
            with open(os.path.join(temp_dir, "logs", "event.log"), "r", encoding="utf8") as f:
                res = json.load(f)
                assert res == {"foo": "bar"}

        # Needed to avoid file contention issues on windows with the telemetry log file
        cleanup_telemetry_logger()


def test_set_instance_id_from_empty_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        with environ({"DAGSTER_HOME": temp_dir}):
            # Write an empty file to the path
            open(
                os.path.join(get_or_create_dir_from_dagster_home(TELEMETRY_STR), "id.yaml"),
                "w",
                encoding="utf8",
            ).close()
            assert get_or_set_instance_id()
