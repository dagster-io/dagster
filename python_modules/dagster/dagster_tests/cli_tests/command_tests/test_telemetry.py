import json
import os
import tempfile
from difflib import SequenceMatcher
from unittest.mock import MagicMock

from click.testing import CliRunner
from dagster import (
    DailyPartitionsDefinition,
    Definitions,
    DynamicPartitionsDefinition,
    FreshnessPolicy,
    MultiPartitionsDefinition,
    SourceAsset,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    observable_source_asset,
    repository,
)
from dagster._cli.job import job_execute_command
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.reconstruct import get_ephemeral_repository_name
from dagster._core.host_representation.external import ExternalRepository
from dagster._core.host_representation.external_data import external_repository_data_from_def
from dagster._core.host_representation.handle import RepositoryHandle
from dagster._core.telemetry import (
    TELEMETRY_STR,
    UPDATE_REPO_STATS,
    cleanup_telemetry_logger,
    get_or_create_dir_from_dagster_home,
    get_or_set_instance_id,
    get_stats_from_external_repo,
    hash_name,
    log_workspace_stats,
    write_telemetry_log_line,
)
from dagster._core.test_utils import environ, instance_for_test
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import file_relative_path, pushd, script_relative_path

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
        "is_known_ci_env",
    ]
)


def path_to_file(path):
    return script_relative_path(os.path.join("./", path))


def test_dagster_telemetry_enabled(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": True}}):
        runner = CliRunner()
        with pushd(path_to_file("")):
            job_attribute = "qux_job"
            job_name = "qux"
            result = runner.invoke(
                job_execute_command,
                [
                    "-f",
                    path_to_file("test_cli_commands.py"),
                    "-a",
                    job_attribute,
                ],
            )

            for record in caplog.records:
                message = json.loads(record.getMessage())
                if message.get("action") == UPDATE_REPO_STATS:
                    metadata = message.get("metadata")
                    assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                    assert metadata.get("num_pipelines_in_repo") == str(1)
                    assert metadata.get("repo_hash") == hash_name(
                        get_ephemeral_repository_name(job_name)
                    )
                assert set(message.keys()) == EXPECTED_KEYS
            assert len(caplog.records) == 9
            assert result.exit_code == 0

        # Needed to avoid file contention issues on windows with the telemetry log file
        cleanup_telemetry_logger()


def test_dagster_telemetry_disabled(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": False}}):
        runner = CliRunner()
        with pushd(path_to_file("")):
            job_name = "qux_job"
            result = runner.invoke(
                job_execute_command,
                [
                    "-f",
                    path_to_file("test_cli_commands.py"),
                    "-a",
                    job_name,
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
                job_attribute = "qux_job"
                job_name = "qux"
                result = runner.invoke(
                    job_execute_command,
                    ["-f", path_to_file("test_cli_commands.py"), "-a", job_attribute],
                )

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    if message.get("action") == UPDATE_REPO_STATS:
                        metadata = message.get("metadata")
                        assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                        assert metadata.get("num_pipelines_in_repo") == str(1)
                        assert metadata.get("repo_hash") == hash_name(
                            get_ephemeral_repository_name(job_name)
                        )
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 9
                assert result.exit_code == 0

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()


def get_dynamic_partitioned_asset_repo():
    @asset(partitions_def=DynamicPartitionsDefinition(name="fruit"))
    def my_asset(_):
        pass

    @repository
    def my_repo():
        return [define_asset_job("dynamic_job"), my_asset]

    return my_repo


def test_update_repo_stats_dynamic_partitions(caplog):
    with instance_for_test(overrides={"telemetry": {"enabled": True}}) as instance:
        instance.add_dynamic_partitions("fruit", ["apple"])
        runner = CliRunner()
        with pushd(path_to_file("")):
            job_attribute = "get_dynamic_partitioned_asset_repo"
            job_name = "dynamic_job"
            result = runner.invoke(
                job_execute_command,
                [
                    "-f",
                    __file__,
                    "-a",
                    job_attribute,
                    "--job",
                    job_name,
                    "--tags",
                    '{"dagster/partition": "apple"}',
                ],
            )

            for record in caplog.records:
                message = json.loads(record.getMessage())
                if message.get("action") == UPDATE_REPO_STATS:
                    metadata = message.get("metadata")
                    assert metadata.get("num_pipelines_in_repo") == str(2)
                    assert metadata.get("num_dynamic_partitioned_assets_in_repo") == str(1)
            assert result.exit_code == 0

        # Needed to avoid file contention issues on windows with the telemetry log file
        cleanup_telemetry_logger()


def test_get_stats_from_external_repo_partitions():
    @asset(partitions_def=StaticPartitionsDefinition(["foo", "bar"]))
    def asset1():
        ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset2():
        ...

    @asset
    def asset3():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[asset1, asset2, asset3]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_partitioned_assets_in_repo"] == "2"


def test_get_stats_from_external_repo_multi_partitions():
    @asset(
        partitions_def=MultiPartitionsDefinition(
            {
                "dim1": StaticPartitionsDefinition(["foo", "bar"]),
                "dim2": DailyPartitionsDefinition(start_date="2022-01-01"),
            }
        )
    )
    def multi_partitioned_asset():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[multi_partitioned_asset]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_multi_partitioned_assets_in_repo"] == "1"
    assert stats["num_partitioned_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_source_assets():
    source_asset1 = SourceAsset("source_asset1")

    @asset
    def asset1():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[source_asset1, asset1]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_source_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_observable_source_assets():
    source_asset1 = SourceAsset("source_asset1")

    @observable_source_asset
    def source_asset2():
        ...

    @asset
    def asset1():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[source_asset1, source_asset2, asset1]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_source_assets_in_repo"] == "2"
    assert stats["num_observable_source_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_freshness_policies():
    @asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=30))
    def asset1():
        ...

    @asset
    def asset2():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[asset1, asset2]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_freshness_policies_in_repo"] == "1"


def test_get_status_from_external_repo_auto_materialize_policy():
    @asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
    def asset1():
        ...

    @asset
    def asset2():
        ...

    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset3():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[asset1, asset2, asset3]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_eager_auto_materialize_policies_in_repo"] == "1"
    assert stats["num_assets_with_lazy_auto_materialize_policies_in_repo"] == "1"


def test_get_stats_from_external_repo_code_versions():
    @asset(code_version="hello")
    def asset1():
        ...

    @asset
    def asset2():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[asset1, asset2]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_code_versions_in_repo"] == "1"


def test_get_stats_from_external_repo_dbt():
    @asset(compute_kind="dbt")
    def asset1():
        ...

    @asset
    def asset2():
        ...

    external_repo = ExternalRepository(
        external_repository_data_from_def(
            Definitions(assets=[asset1, asset2]).get_repository_def()
        ),
        repository_handle=MagicMock(spec=RepositoryHandle),
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_dbt_assets_in_repo"] == "1"


# TODO - not sure what this test is testing for, so unclear as to how to update it to jobs
def test_repo_stats(caplog):
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir, overrides={"telemetry": {"enabled": True}}):
            runner = CliRunner(env={"DAGSTER_HOME": temp_dir})
            with pushd(path_to_file("")):
                job_name = "double_adder_job"
                result = runner.invoke(
                    job_execute_command,
                    [
                        "-f",
                        file_relative_path(__file__, "../../general_tests/test_repository.py"),
                        "-a",
                        "dagster_test_repository",
                        "--config",
                        file_relative_path(__file__, "../../environments/double_adder_job.yaml"),
                        "-j",
                        job_name,
                        "--tags",
                        '{ "foo": "bar" }',
                    ],
                )

                assert result.exit_code == 0, result.stdout

                for record in caplog.records:
                    message = json.loads(record.getMessage())
                    if message.get("action") == UPDATE_REPO_STATS:
                        metadata = message.get("metadata")
                        assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                        assert metadata.get("num_pipelines_in_repo") == str(6)
                        assert metadata.get("repo_hash") == hash_name("dagster_test_repository")
                    assert set(message.keys()) == EXPECTED_KEYS

                assert len(caplog.records) == 7
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
    jobs = ["job_1", "job_2", "job_3"]
    hashes = [hash_name(p) for p in jobs]
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
