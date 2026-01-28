import json
import os
import tempfile
from collections.abc import Iterator
from difflib import SequenceMatcher
from typing import Any, TypeAlias
from unittest import mock

import dagster as dg
import pytest
from click.testing import CliRunner
from dagster._cli.job import job_execute_command
from dagster._core.definitions.reconstruct import get_ephemeral_repository_name
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from dagster._core.storage.runs import SqlRunStorage
from dagster._core.telemetry import (
    TELEMETRY_STR,
    UPDATE_REPO_STATS,
    get_or_set_instance_id,
    get_or_set_user_id,
    get_stats_from_remote_repo,
    hash_name,
    log_action,
    log_workspace_stats,
    write_telemetry_log_line,
)
from dagster._core.test_utils import environ
from dagster._core.workspace.load import load_workspace_process_context_from_yaml_paths
from dagster._utils import pushd, script_relative_path
from dagster_shared.telemetry import (
    cleanup_telemetry_logger,
    get_or_create_dir_from_dagster_home,
    get_telemetry_logger,
)
from dagster_test.utils.data_factory import remote_repository

EXPECTED_KEYS = set(
    [
        "action",
        "client_time",
        "elapsed_time",
        "event_id",
        "instance_id",
        "user_id",
        "run_storage_id",
        "python_version",
        "metadata",
        "os_desc",
        "os_platform",
        "dagster_version",
        "is_known_ci_env",
    ]
)

Telemetry: TypeAlias = tuple[dg.DagsterInstance, pytest.LogCaptureFixture]


@pytest.fixture
def enabled_instance():
    with dg.instance_for_test(overrides={"telemetry": {"enabled": True}}) as instance:
        yield instance


# use stacked fixtures to ensure telemetry logger file is cleaned up before we close the temp instance
@pytest.fixture
def enabled_telemetry(
    caplog,
    enabled_instance,
) -> Iterator[Telemetry]:
    # telemetry logger doesn't propagate to the root logger, so need to attach the caplog handler
    get_telemetry_logger().addHandler(caplog.handler)
    yield enabled_instance, caplog
    get_telemetry_logger().removeHandler(caplog.handler)
    cleanup_telemetry_logger()


@pytest.fixture
def disabled_instance():
    with dg.instance_for_test(overrides={"telemetry": {"enabled": False}}) as instance:
        yield instance


@pytest.fixture
def disabled_telemetry(
    caplog,
    disabled_instance,
) -> Iterator[Telemetry]:
    yield disabled_instance, caplog


def path_to_file(path):
    return script_relative_path(os.path.join("./", path))


def test_dagster_telemetry_enabled(enabled_telemetry: Telemetry):
    _, telemetry_caplog = enabled_telemetry
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

        for record in telemetry_caplog.records:
            message = json.loads(record.getMessage())
            if message.get("action") == UPDATE_REPO_STATS:
                metadata = message.get("metadata")
                assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                assert metadata.get("num_pipelines_in_repo") == str(1)
                assert metadata.get("repo_hash") == hash_name(
                    get_ephemeral_repository_name(job_name)
                )
            assert set(message.keys()) == EXPECTED_KEYS
        assert len(telemetry_caplog.records) == 9
        assert result.exit_code == 0


def test_dagster_telemetry_disabled_avoids_run_storage_query(disabled_telemetry: Telemetry):
    """Verify that when telemetry is disabled, we don't query run_storage_id."""
    instance, _ = disabled_telemetry
    # Ensure the instance uses SqlRunStorage for the mock target to be relevant
    assert isinstance(instance.run_storage, SqlRunStorage)

    with mock.patch.object(
        SqlRunStorage, "get_run_storage_id", wraps=instance.run_storage.get_run_storage_id
    ) as mock_get_id:
        # Call a function that triggers the telemetry info check
        log_action(instance, "TEST_ACTION")

        # Assert that the run storage ID was not queried
        mock_get_id.assert_not_called()


def test_dagster_telemetry_disabled_uses_run_storage_query(enabled_telemetry: Telemetry):
    # Double check: enable telemetry and ensure it *is* called
    instance_enabled, _ = enabled_telemetry
    assert isinstance(instance_enabled.run_storage, SqlRunStorage)
    with mock.patch.object(
        SqlRunStorage,
        "get_run_storage_id",
        wraps=instance_enabled.run_storage.get_run_storage_id,
    ) as mock_get_id_enabled:
        log_action(instance_enabled, "TEST_ACTION_ENABLED")
        mock_get_id_enabled.assert_called_once()


def test_dagster_telemetry_disabled(disabled_telemetry: Telemetry):
    _, telemetry_caplog = disabled_telemetry
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
    assert len(telemetry_caplog.records) == 0
    assert result.exit_code == 0


def test_dagster_telemetry_unset(enabled_telemetry: Telemetry):
    _, telemetry_caplog = enabled_telemetry
    runner = CliRunner()
    with pushd(path_to_file("")):
        job_attribute = "qux_job"
        job_name = "qux"
        result = runner.invoke(
            job_execute_command,
            ["-f", path_to_file("test_cli_commands.py"), "-a", job_attribute],
        )

        for record in telemetry_caplog.records:
            message = json.loads(record.getMessage())
            if message.get("action") == UPDATE_REPO_STATS:
                metadata = message.get("metadata")
                assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                assert metadata.get("num_pipelines_in_repo") == str(1)
                assert metadata.get("repo_hash") == hash_name(
                    get_ephemeral_repository_name(job_name)
                )
            assert set(message.keys()) == EXPECTED_KEYS

        assert len(telemetry_caplog.records) == 9
        assert result.exit_code == 0


def get_dynamic_partitioned_asset_repo():
    @dg.asset(partitions_def=dg.DynamicPartitionsDefinition(name="fruit"))
    def my_asset(_):
        pass

    @dg.repository
    def my_repo():
        return [dg.define_asset_job("dynamic_job"), my_asset]

    return my_repo


def test_update_repo_stats_dynamic_partitions(enabled_telemetry: Telemetry):
    instance, telemetry_caplog = enabled_telemetry
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

        for record in telemetry_caplog.records:
            message = json.loads(record.getMessage())
            if message.get("action") == UPDATE_REPO_STATS:
                metadata = message.get("metadata")
                assert metadata.get("num_pipelines_in_repo") == str(2)
                assert metadata.get("num_dynamic_partitioned_assets_in_repo") == str(1)
        assert result.exit_code == 0


def test_get_stats_from_remote_repo_partitions():
    @dg.asset(partitions_def=dg.StaticPartitionsDefinition(["foo", "bar"]))
    def asset1(): ...

    @dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset2(): ...

    @dg.asset
    def asset3(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(assets=[asset1, asset2, asset3]).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_partitioned_assets_in_repo"] == "2"


def test_get_stats_from_remote_repo_multi_partitions(enabled_telemetry: Telemetry):
    instance, _ = enabled_telemetry

    @dg.asset(
        partitions_def=dg.MultiPartitionsDefinition(
            {
                "dim1": dg.StaticPartitionsDefinition(["foo", "bar"]),
                "dim2": dg.DailyPartitionsDefinition(start_date="2022-01-01"),
            }
        )
    )
    def multi_partitioned_asset(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(assets=[multi_partitioned_asset]).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_multi_partitioned_assets_in_repo"] == "1"
    assert stats["num_partitioned_assets_in_repo"] == "1"


def test_get_stats_from_remote_repo_source_assets():
    source_asset1 = dg.SourceAsset("source_asset1")

    @dg.asset
    def asset1(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(assets=[source_asset1, asset1]).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_source_assets_in_repo"] == "1"


def test_get_stats_from_remote_repo_observable_source_assets():
    source_asset1 = dg.SourceAsset("source_asset1")

    @dg.observable_source_asset
    def source_asset2(): ...

    @dg.asset
    def asset1(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(assets=[source_asset1, source_asset2, asset1]).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_source_assets_in_repo"] == "2"
    assert stats["num_observable_source_assets_in_repo"] == "1"


def test_get_stats_from_remote_repo_freshness_policies():
    @dg.asset(legacy_freshness_policy=dg.LegacyFreshnessPolicy(maximum_lag_minutes=30))
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(dg.Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_assets_with_freshness_policies_in_repo"] == "1"


def test_get_stats_from_remote_repo_code_versions():
    @dg.asset(code_version="hello")
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(dg.Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_assets_with_code_versions_in_repo"] == "1"


def test_get_stats_from_remote_repo_code_checks():
    @dg.asset
    def my_asset(): ...

    @dg.asset_check(asset=my_asset)  # pyright: ignore[reportArgumentType]
    def my_check(): ...

    @dg.asset_check(asset=my_asset)  # pyright: ignore[reportArgumentType]
    def my_check_2(): ...

    @dg.asset
    def my_other_asset(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[my_asset, my_other_asset], asset_checks=[my_check, my_check_2]
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_asset_checks"] == "2"
    assert stats["num_assets_with_checks"] == "1"


def test_get_stats_from_remote_repo_dbt():
    @dg.asset(compute_kind="dbt")
    def asset1(): ...

    @dg.asset
    def asset2(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(dg.Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["num_dbt_assets_in_repo"] == "1"


def test_get_stats_from_remote_repo_resources():
    class MyResource(dg.ConfigurableResource):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

    class CustomResource(dg.ConfigurableResource):
        baz: str

    @dg.asset
    def asset1(my_resource: MyResource, custom_resource: CustomResource): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[asset1],
                resources={
                    "my_resource": MyResource(foo="bar"),
                    "custom_resource": CustomResource(baz="qux"),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyResource"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_remote_repo_io_managers():
    class MyIOManager(dg.ConfigurableIOManager):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    class CustomIOManager(dg.ConfigurableIOManager):
        baz: str

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    @dg.asset
    def asset1(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[asset1],
                resources={
                    "my_io_manager": MyIOManager(foo="bar"),
                    "custom_io_manager": CustomIOManager(baz="qux"),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyIOManager"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_remote_repo_functional_resources():
    @dagster_maintained_resource
    @dg.resource(config_schema={"foo": str})
    def my_resource():
        return 1

    @dg.resource(config_schema={"baz": str})
    def custom_resource():
        return 2

    @dg.asset(required_resource_keys={"my_resource", "custom_resource"})
    def asset1(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[asset1],
                resources={
                    "my_resource": my_resource.configured({"foo": "bar"}),
                    "custom_resource": custom_resource.configured({"baz": "qux"}),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "my_resource"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_remote_repo_functional_io_managers():
    @dagster_maintained_io_manager
    @dg.io_manager(config_schema={"foo": str})  # pyright: ignore[reportArgumentType]
    def my_io_manager():
        return 1

    @dg.io_manager(config_schema={"baz": str})  # pyright: ignore[reportArgumentType]
    def custom_io_manager():
        return 2

    @dg.asset
    def asset1(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[asset1],
                resources={
                    "my_io_manager": my_io_manager.configured({"foo": "bar"}),
                    "custom_io_manager": custom_io_manager.configured({"baz": "qux"}),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "my_io_manager"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_remote_repo_pipes_client():
    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                resources={
                    "pipes_subprocess_client": dg.PipesSubprocessClient(),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster", "class_name": "PipesSubprocessClient"}
    ]
    assert stats["has_custom_resources"] == "False"


def test_get_stats_from_remote_repo_delayed_resource_configuration():
    class MyResource(dg.ConfigurableResource):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

    class MyIOManager(dg.ConfigurableIOManager):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    @dagster_maintained_resource
    @dg.resource(config_schema={"foo": str})
    def my_resource():
        return 1

    @dagster_maintained_io_manager
    @dg.io_manager(config_schema={"foo": str})  # pyright: ignore[reportArgumentType]
    def my_io_manager():
        return 1

    @dg.asset
    def asset1(my_resource: MyResource): ...

    @dg.asset(required_resource_keys={"my_other_resource"})
    def asset2(): ...

    remote_repo = remote_repository(
        RepositorySnap.from_def(
            dg.Definitions(
                assets=[asset1, asset2],
                resources={
                    "my_io_manager": MyIOManager.configure_at_launch(),
                    "my_other_io_manager": my_io_manager,
                    "my_resource": MyResource.configure_at_launch(),
                    "my_other_resource": my_resource,
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
    )
    stats = get_stats_from_remote_repo(remote_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyIOManager"},
        {"module_name": "dagster_tests", "class_name": "my_io_manager"},
        {"module_name": "dagster_tests", "class_name": "my_resource"},
        {"module_name": "dagster_tests", "class_name": "MyResource"},
    ]
    assert stats["has_custom_resources"] == "False"


# TODO - not sure what this test is testing for, so unclear as to how to update it to jobs
def test_repo_stats(enabled_telemetry: Telemetry):
    _, telemetry_caplog = enabled_telemetry
    runner = CliRunner()
    with pushd(path_to_file("")):
        job_name = "double_adder_job"
        result = runner.invoke(
            job_execute_command,
            [
                "-f",
                dg.file_relative_path(__file__, "../../general_tests/test_repository.py"),
                "-a",
                "dagster_test_repository",
                "--config",
                dg.file_relative_path(__file__, "../../environments/double_adder_job.yaml"),
                "-j",
                job_name,
                "--tags",
                '{ "foo": "bar" }',
            ],
        )

        assert result.exit_code == 0, result.stdout

        for record in telemetry_caplog.records:
            message = json.loads(record.getMessage())
            if message.get("action") == UPDATE_REPO_STATS:
                metadata = message.get("metadata")
                assert metadata.get("pipeline_name_hash") == hash_name(job_name)
                assert metadata.get("num_pipelines_in_repo") == str(6)
                assert metadata.get("repo_hash") == hash_name("dagster_test_repository")
            assert set(message.keys()) == EXPECTED_KEYS

        assert len(telemetry_caplog.records) == 7
        assert result.exit_code == 0


def test_log_workspace_stats(enabled_telemetry: Telemetry):
    instance, telemetry_caplog = enabled_telemetry
    with load_workspace_process_context_from_yaml_paths(
        instance, [dg.file_relative_path(__file__, "./multi_env_telemetry_workspace.yaml")]
    ) as context:
        log_workspace_stats(instance, context)

        for record in telemetry_caplog.records:
            message = json.loads(record.getMessage())
            assert message.get("action") == UPDATE_REPO_STATS
            assert set(message.keys()) == EXPECTED_KEYS

        assert len(telemetry_caplog.records) == 2


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
            with open(os.path.join(temp_dir, "logs", "event.log"), encoding="utf8") as f:
                res = json.load(f)
                assert res == {"foo": "bar"}

            # Needed to avoid file contention issues on windows with the telemetry log file
            cleanup_telemetry_logger()

            os.remove(os.path.join(temp_dir, "logs", "event.log"))
            os.rmdir(os.path.join(temp_dir, "logs"))

            write_telemetry_log_line({"foo": "bar"})
            with open(os.path.join(temp_dir, "logs", "event.log"), encoding="utf8") as f:
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


def test_user_id_ignores_dagster_home():
    """Test that user_id is always stored in the user telemetry dir regardless of $DAGSTER_HOME."""
    import yaml

    with tempfile.TemporaryDirectory() as fake_user_telemetry_dir:
        user_id_path = os.path.join(fake_user_telemetry_dir, "user_id.yaml")

        # Mock get_or_create_user_telemetry_dir to avoid touching real ~/.dagster/.telemetry/
        with mock.patch(
            "dagster_shared.telemetry.get_or_create_user_telemetry_dir",
            return_value=fake_user_telemetry_dir,
        ):
            # Set DAGSTER_HOME to a different directory
            with tempfile.TemporaryDirectory() as temp_dagster_home:
                with environ({"DAGSTER_HOME": temp_dagster_home}):
                    # Get or create user_id
                    user_id = get_or_set_user_id()
                    assert user_id

                    # Verify the user_id was NOT stored in $DAGSTER_HOME
                    dagster_home_user_id_path = os.path.join(
                        temp_dagster_home, TELEMETRY_STR, "user_id.yaml"
                    )
                    assert not os.path.exists(dagster_home_user_id_path)

                    # Verify the user_id WAS stored in the user telemetry dir
                    assert os.path.exists(user_id_path)
                    with open(user_id_path, encoding="utf8") as f:
                        data = yaml.safe_load(f)
                        assert data["user_id"] == user_id


def test_user_id_consistent_across_dagster_homes():
    """Test that user_id remains the same regardless of $DAGSTER_HOME changes."""
    with tempfile.TemporaryDirectory() as fake_user_telemetry_dir:
        # Mock get_or_create_user_telemetry_dir to avoid touching real ~/.dagster/.telemetry/
        with mock.patch(
            "dagster_shared.telemetry.get_or_create_user_telemetry_dir",
            return_value=fake_user_telemetry_dir,
        ):
            # Get user_id with one DAGSTER_HOME
            with tempfile.TemporaryDirectory() as temp_dir_1:
                with environ({"DAGSTER_HOME": temp_dir_1}):
                    user_id_1 = get_or_set_user_id()

            # Get user_id with a different DAGSTER_HOME
            with tempfile.TemporaryDirectory() as temp_dir_2:
                with environ({"DAGSTER_HOME": temp_dir_2}):
                    user_id_2 = get_or_set_user_id()

            # User IDs should be the same
            assert user_id_1 == user_id_2
