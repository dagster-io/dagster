import json
import os
import tempfile
from difflib import SequenceMatcher
from typing import Any

import pytest
from click.testing import CliRunner
from dagster import (
    ConfigurableIOManager,
    ConfigurableResource,
    DailyPartitionsDefinition,
    Definitions,
    DynamicPartitionsDefinition,
    FreshnessPolicy,
    MultiPartitionsDefinition,
    PipesSubprocessClient,
    SourceAsset,
    StaticPartitionsDefinition,
    asset,
    asset_check,
    define_asset_job,
    io_manager,
    observable_source_asset,
    repository,
    resource,
)
from dagster._cli.job import job_execute_command
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.reconstruct import get_ephemeral_repository_name
from dagster._core.definitions.resource_definition import dagster_maintained_resource
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.remote_representation.external import RemoteRepository
from dagster._core.remote_representation.external_data import RepositorySnap
from dagster._core.remote_representation.handle import RepositoryHandle
from dagster._core.storage.io_manager import dagster_maintained_io_manager
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


@pytest.fixture
def instance():
    with instance_for_test() as instance:
        return instance


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


def test_get_stats_from_external_repo_partitions(instance):
    @asset(partitions_def=StaticPartitionsDefinition(["foo", "bar"]))
    def asset1(): ...

    @asset(partitions_def=DailyPartitionsDefinition(start_date="2022-01-01"))
    def asset2(): ...

    @asset
    def asset3(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[asset1, asset2, asset3]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_partitioned_assets_in_repo"] == "2"


def test_get_stats_from_external_repo_multi_partitions(instance):
    @asset(
        partitions_def=MultiPartitionsDefinition(
            {
                "dim1": StaticPartitionsDefinition(["foo", "bar"]),
                "dim2": DailyPartitionsDefinition(start_date="2022-01-01"),
            }
        )
    )
    def multi_partitioned_asset(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[multi_partitioned_asset]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_multi_partitioned_assets_in_repo"] == "1"
    assert stats["num_partitioned_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_source_assets(instance):
    source_asset1 = SourceAsset("source_asset1")

    @asset
    def asset1(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[source_asset1, asset1]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_source_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_observable_source_assets(instance):
    source_asset1 = SourceAsset("source_asset1")

    @observable_source_asset
    def source_asset2(): ...

    @asset
    def asset1(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(assets=[source_asset1, source_asset2, asset1]).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_source_assets_in_repo"] == "2"
    assert stats["num_observable_source_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_freshness_policies(instance):
    @asset(freshness_policy=FreshnessPolicy(maximum_lag_minutes=30))
    def asset1(): ...

    @asset
    def asset2(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_freshness_policies_in_repo"] == "1"


# TODO: FOU-243
@pytest.mark.skip("obsolete EAGER vs. LAZY distinction")
def test_get_status_from_external_repo_auto_materialize_policy(instance):
    @asset(auto_materialize_policy=AutoMaterializePolicy.lazy())
    def asset1(): ...

    @asset
    def asset2(): ...

    @asset(auto_materialize_policy=AutoMaterializePolicy.eager())
    def asset3(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[asset1, asset2, asset3]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_eager_auto_materialize_policies_in_repo"] == "1"
    assert stats["num_assets_with_lazy_auto_materialize_policies_in_repo"] == "1"


def test_get_stats_from_external_repo_code_versions(instance):
    @asset(code_version="hello")
    def asset1(): ...

    @asset
    def asset2(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_assets_with_code_versions_in_repo"] == "1"


def test_get_stats_from_external_repo_code_checks(instance):
    @asset
    def my_asset(): ...

    @asset_check(asset=my_asset)
    def my_check(): ...

    @asset_check(asset=my_asset)
    def my_check_2(): ...

    @asset
    def my_other_asset(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                assets=[my_asset, my_other_asset], asset_checks=[my_check, my_check_2]
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_asset_checks"] == "2"
    assert stats["num_assets_with_checks"] == "1"


def test_get_stats_from_external_repo_dbt(instance):
    @asset(compute_kind="dbt")
    def asset1(): ...

    @asset
    def asset2(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(Definitions(assets=[asset1, asset2]).get_repository_def()),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["num_dbt_assets_in_repo"] == "1"


def test_get_stats_from_external_repo_resources(instance):
    class MyResource(ConfigurableResource):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

    class CustomResource(ConfigurableResource):
        baz: str

    @asset
    def asset1(my_resource: MyResource, custom_resource: CustomResource): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                assets=[asset1],
                resources={
                    "my_resource": MyResource(foo="bar"),
                    "custom_resource": CustomResource(baz="qux"),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyResource"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_external_repo_io_managers(instance):
    class MyIOManager(ConfigurableIOManager):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    class CustomIOManager(ConfigurableIOManager):
        baz: str

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    @asset
    def asset1(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                assets=[asset1],
                resources={
                    "my_io_manager": MyIOManager(foo="bar"),
                    "custom_io_manager": CustomIOManager(baz="qux"),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyIOManager"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_external_repo_functional_resources(instance):
    @dagster_maintained_resource
    @resource(config_schema={"foo": str})
    def my_resource():
        return 1

    @resource(config_schema={"baz": str})
    def custom_resource():
        return 2

    @asset(required_resource_keys={"my_resource", "custom_resource"})
    def asset1(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                assets=[asset1],
                resources={
                    "my_resource": my_resource.configured({"foo": "bar"}),
                    "custom_resource": custom_resource.configured({"baz": "qux"}),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "my_resource"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_external_repo_functional_io_managers(instance):
    @dagster_maintained_io_manager
    @io_manager(config_schema={"foo": str})
    def my_io_manager():
        return 1

    @io_manager(config_schema={"baz": str})
    def custom_io_manager():
        return 2

    @asset
    def asset1(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                assets=[asset1],
                resources={
                    "my_io_manager": my_io_manager.configured({"foo": "bar"}),
                    "custom_io_manager": custom_io_manager.configured({"baz": "qux"}),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "my_io_manager"}
    ]
    assert stats["has_custom_resources"] == "True"


def test_get_stats_from_external_repo_pipes_client(instance):
    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
                resources={
                    "pipes_subprocess_client": PipesSubprocessClient(),
                },
            ).get_repository_def()
        ),
        repository_handle=RepositoryHandle.for_test(),
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster", "class_name": "PipesSubprocessClient"}
    ]
    assert stats["has_custom_resources"] == "False"


def test_get_stats_from_external_repo_delayed_resource_configuration(instance):
    class MyResource(ConfigurableResource):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

    class MyIOManager(ConfigurableIOManager):
        foo: str

        @classmethod
        def _is_dagster_maintained(cls) -> bool:
            return True

        def handle_output(self, context: OutputContext, obj: Any) -> None:
            return None

        def load_input(self, context: InputContext) -> Any:
            return 1

    @dagster_maintained_resource
    @resource(config_schema={"foo": str})
    def my_resource():
        return 1

    @dagster_maintained_io_manager
    @io_manager(config_schema={"foo": str})
    def my_io_manager():
        return 1

    @asset
    def asset1(my_resource: MyResource): ...

    @asset(required_resource_keys={"my_other_resource"})
    def asset2(): ...

    external_repo = RemoteRepository(
        RepositorySnap.from_def(
            Definitions(
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
        instance=instance,
    )
    stats = get_stats_from_external_repo(external_repo)
    assert stats["dagster_resources"] == [
        {"module_name": "dagster_tests", "class_name": "MyIOManager"},
        {"module_name": "dagster_tests", "class_name": "my_io_manager"},
        {"module_name": "dagster_tests", "class_name": "my_resource"},
        {"module_name": "dagster_tests", "class_name": "MyResource"},
    ]
    assert stats["has_custom_resources"] == "False"


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
