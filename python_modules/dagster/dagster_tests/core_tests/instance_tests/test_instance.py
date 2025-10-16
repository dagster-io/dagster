import datetime
import json
import os
import re
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import dagster as dg
import pytest
import yaml
from dagster import (
    _check as check,
    seven,
)
from dagster._check import CheckError
from dagster._cli.utils import get_instance_for_cli
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.partitions.subset import KeyRangesPartitionsSubset
from dagster._core.errors import DagsterHomeNotSetError
from dagster._core.execution.api import create_execution_plan
from dagster._core.instance import DagsterInstance, InstanceRef
from dagster._core.instance.config import DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
from dagster._core.launcher import LaunchRunContext, RunLauncher
from dagster._core.remote_representation.external_data import PartitionsSnap
from dagster._core.secrets.env_file import PerProjectEnvFileLoader
from dagster._core.snap import create_execution_plan_snapshot_id, snapshot_from_execution_plan
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecordStatus
from dagster._core.storage.partition_status_cache import AssetPartitionStatus, AssetStatusCacheValue
from dagster._core.storage.sqlite_storage import (
    _event_logs_directory,
    _runs_directory,
    _schedule_directory,
)
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
    PARTITION_NAME_TAG,
)
from dagster._core.test_utils import (
    TestSecretsLoader,
    create_run_for_test,
    environ,
    mock_workspace_from_repos,
    new_cwd,
)
from dagster._daemon.asset_daemon import AssetDaemon
from dagster._daemon.controller import create_daemons_from_instance
from dagster._serdes import ConfigurableClass, deserialize_value
from dagster._serdes.config_class import ConfigurableClassData
from dagster._utils import file_relative_path
from typing_extensions import Self

from dagster_tests.api_tests.utils import get_bar_workspace


def test_get_run_by_id():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    run = create_run_for_test(instance, job_name="foo_job")

    assert instance.get_runs() == [run]

    assert instance.get_run_by_id(run.run_id) == run


def do_test_single_write_read(instance):
    @dg.job
    def job_def():
        pass

    run = instance.create_run_for_job(job_def=job_def)
    stored_run = instance.get_run_by_id(run.run_id)
    assert run.run_id == stored_run.run_id
    assert run.job_name == "job_def"
    assert list(instance.get_runs()) == [run]
    instance.wipe()
    assert list(instance.get_runs()) == []


def test_filesystem_persist_one_run(tmpdir):
    with dg.instance_for_test(temp_dir=str(tmpdir)) as instance:
        do_test_single_write_read(instance)


def test_partial_storage(tmpdir):
    with dg.instance_for_test(
        overrides={
            "run_storage": {
                "module": "dagster._core.storage.runs",
                "class": "SqliteRunStorage",
                "config": {
                    "base_dir": str(tmpdir),
                },
            }
        }
    ) as _instance:
        pass


def test_unified_storage(tmpdir):
    with dg.instance_for_test(
        overrides={
            "storage": {
                "sqlite": {
                    "base_dir": str(tmpdir),
                }
            }
        }
    ) as _instance:
        pass


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Windows paths formatted differently")
def test_unified_storage_env_var(tmpdir):
    with environ({"SQLITE_STORAGE_BASE_DIR": str(tmpdir)}):
        with dg.instance_for_test(
            overrides={
                "storage": {
                    "sqlite": {
                        "base_dir": {"env": "SQLITE_STORAGE_BASE_DIR"},
                    }
                }
            }
        ) as instance:
            assert _runs_directory(str(tmpdir)) in instance.run_storage._conn_string  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
            assert (
                _event_logs_directory(str(tmpdir)) == instance.event_log_storage._base_dir + "/"  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
            )
            assert (
                _schedule_directory(str(tmpdir)) in instance.schedule_storage._conn_string  # noqa: SLF001  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
            )


def test_implicit_secrets_manager():
    with (
        dg.instance_for_test() as instance,
        tempfile.TemporaryDirectory() as temp_dir,
        environ({"DAGSTER_PROJECT_ENV_FILE_PATHS": json.dumps({"test_location": temp_dir})}),
    ):
        assert isinstance(instance._secrets_loader, PerProjectEnvFileLoader)  # noqa: SLF001
        (Path(temp_dir) / ".env").write_text("FOO=BAR")
        assert instance._secrets_loader.get_secrets_for_environment("test_location") == {  # noqa: SLF001
            "FOO": "BAR"
        }
        assert instance._secrets_loader.get_secrets_for_environment("other_location") == {}  # noqa: SLF001


def test_custom_per_project_secrets_manager():
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        dg.instance_for_test(
            overrides={
                "secrets": {
                    "custom": {
                        "module": "dagster._core.secrets.env_file",
                        "class": "PerProjectEnvFileLoader",
                        "config": {"location_paths": {"test_location": str(temp_dir)}},
                    }
                }
            }
        ) as instance,
    ):
        assert isinstance(instance._secrets_loader, PerProjectEnvFileLoader)  # noqa: SLF001
        (Path(temp_dir) / ".env").write_text("FOO=BAR")
        assert instance._secrets_loader.get_secrets_for_environment("test_location") == {  # noqa: SLF001
            "FOO": "BAR"
        }
        assert instance._secrets_loader.get_secrets_for_environment("other_location") == {}  # noqa: SLF001


def test_custom_secrets_manager():
    with dg.instance_for_test(
        overrides={
            "secrets": {
                "custom": {
                    "module": "dagster._core.test_utils",
                    "class": "TestSecretsLoader",
                    "config": {"env_vars": {"FOO": "BAR"}},
                }
            }
        }
    ) as instance:
        assert isinstance(instance._secrets_loader, TestSecretsLoader)  # noqa: SLF001
        assert instance._secrets_loader.env_vars == {"FOO": "BAR"}  # noqa: SLF001


def test_run_queue_key():
    tag_rules = [
        {
            "key": "database",
            "value": "redshift",
            "limit": 2,
        }
    ]

    config = {"max_concurrent_runs": 50, "tag_concurrency_limits": tag_rules}

    with dg.instance_for_test(overrides={"run_queue": config}) as instance:
        assert isinstance(instance.run_coordinator, dg.QueuedRunCoordinator)
        run_queue_config = instance.get_concurrency_config().run_queue_config
        assert run_queue_config
        assert run_queue_config.max_concurrent_runs == 50
        assert run_queue_config.tag_concurrency_limits == tag_rules

    with dg.instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster.core.run_coordinator",
                "class": "QueuedRunCoordinator",
                "config": config,
            }
        }
    ) as instance:
        assert isinstance(instance.run_coordinator, dg.QueuedRunCoordinator)
        run_queue_config = instance.get_concurrency_config().run_queue_config
        assert run_queue_config
        assert run_queue_config.max_concurrent_runs == 50
        assert run_queue_config.tag_concurrency_limits == tag_rules

    # Can't combine them though
    with pytest.raises(
        dg.DagsterInvalidConfigError,
        match=(
            "Found config for `run_queue` which is incompatible with `run_coordinator` config"
            " entry."
        ),
    ):
        with dg.instance_for_test(
            overrides={
                "run_queue": config,
                "run_coordinator": {
                    "module": "dagster.core.run_coordinator",
                    "class": "QueuedRunCoordinator",
                    "config": config,
                },
            }
        ):
            pass


def test_run_coordinator_key():
    tag_rules = [
        {
            "key": "database",
            "value": "redshift",
            "limit": 2,
        }
    ]

    with dg.instance_for_test(
        overrides={"run_queue": {"max_concurrent_runs": 50, "tag_concurrency_limits": tag_rules}}
    ) as instance:
        assert isinstance(instance.run_coordinator, dg.QueuedRunCoordinator)
        run_queue_config = instance.get_concurrency_config().run_queue_config
        assert run_queue_config
        assert run_queue_config.max_concurrent_runs == 50
        assert run_queue_config.tag_concurrency_limits == tag_rules


def test_in_memory_persist_one_run():
    with DagsterInstance.ephemeral() as instance:
        do_test_single_write_read(instance)


@dg.op
def noop_op(_):
    pass


@dg.job
def noop_job():
    noop_op()


@dg.asset(partitions_def=dg.StaticPartitionsDefinition(["bar", "baz", "foo"]))
def noop_asset():
    pass


@dg.asset(partitions_def=dg.DailyPartitionsDefinition(start_date=datetime.datetime(2025, 1, 1)))
def noop_time_window_asset():
    pass


@dg.asset(partitions_def=dg.DynamicPartitionsDefinition(name="my_dynamic"))
def noop_dynamic_partitions_asset():
    pass


noop_asset_defs = dg.Definitions(
    assets=[noop_asset, noop_time_window_asset, noop_dynamic_partitions_asset],
    jobs=[
        dg.define_asset_job("noop_asset_job", [noop_asset]),
        dg.define_asset_job("noop_time_window_asset_job", [noop_time_window_asset]),
        dg.define_asset_job("noop_dynamic_partitions_asset_job", [noop_dynamic_partitions_asset]),
    ],
)

noop_asset_job = noop_asset_defs.resolve_job_def("noop_asset_job")
noop_time_window_asset_job: dg.JobDefinition = noop_asset_defs.resolve_job_def(
    "noop_time_window_asset_job"
)
noop_dynamic_partitions_asset_job = noop_asset_defs.resolve_job_def(
    "noop_dynamic_partitions_asset_job"
)


def test_create_job_snapshot():
    with dg.instance_for_test() as instance:
        result = dg.execute_job(dg.reconstructable(noop_job), instance=instance)
        assert result.success

        run = instance.get_run_by_id(result.run_id)

        assert run.job_snapshot_id == noop_job.get_job_snapshot().snapshot_id  # pyright: ignore[reportOptionalMemberAccess]


def test_create_execution_plan_snapshot():
    with dg.instance_for_test() as instance:
        execution_plan = create_execution_plan(noop_job)

        ep_snapshot = snapshot_from_execution_plan(execution_plan, noop_job.get_job_snapshot_id())
        ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)

        result = dg.execute_job(dg.reconstructable(noop_job), instance=instance)
        assert result.success

        run = instance.get_run_by_id(result.run_id)

        assert run.execution_plan_snapshot_id == ep_snapshot_id  # pyright: ignore[reportOptionalMemberAccess]
        assert run.execution_plan_snapshot_id == create_execution_plan_snapshot_id(ep_snapshot)  # pyright: ignore[reportOptionalMemberAccess]


def test_submit_run():
    with dg.instance_for_test(
        overrides={
            "run_coordinator": {
                "module": "dagster._core.test_utils",
                "class": "MockedRunCoordinator",
            }
        }
    ) as instance:
        with get_bar_workspace(instance) as workspace:
            remote_job = (
                workspace.get_code_location("bar_code_location")
                .get_repository("bar_repo")
                .get_full_job("foo")
            )

            run = create_run_for_test(
                instance=instance,
                job_name=remote_job.name,
                remote_job_origin=remote_job.get_remote_origin(),
                job_code_origin=remote_job.get_python_origin(),
            )

            instance.submit_run(run.run_id, workspace)

            assert len(instance.run_coordinator.queue()) == 1  # pyright: ignore[reportAttributeAccessIssue]
            assert instance.run_coordinator.queue()[0].run_id == run.run_id  # pyright: ignore[reportAttributeAccessIssue]


def test_create_run_without_asset_execution_type_on_snapshot():
    # verify that even runs created on older versions of dagster still store the
    # execution type on the execution plan snapshot
    with dg.instance_for_test() as instance:
        with open(
            file_relative_path(__file__, "./execution_plan_snapshot_without_execution_type.json")
        ) as f:
            ep_snapshot = deserialize_value(f.read())

        workspace = mock_workspace_from_repos([noop_asset_defs.get_repository_def()])

        asset_graph = workspace.asset_graph

        run = create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_asset_job.get_job_snapshot(),
            tags={ASSET_PARTITION_RANGE_START_TAG: "bar", ASSET_PARTITION_RANGE_END_TAG: "foo"},
            remote_job_origin=(
                next(
                    iter(
                        check.not_none(
                            next(iter(workspace.code_location_entries.values())).code_location
                        )
                        .get_repositories()
                        .values()
                    )
                )
                .get_full_job(noop_asset_job.name)
                .get_remote_origin()
            ),
            asset_graph=asset_graph,
        )

        assert run.execution_plan_snapshot_id is not None

        stored_snapshot = instance.get_execution_plan_snapshot(run.execution_plan_snapshot_id)

        assert all(
            check.not_none(output.properties).asset_execution_type
            == AssetExecutionType.MATERIALIZATION
            for step in stored_snapshot.steps
            for output in step.outputs
        )


def test_create_run_with_asset_partitions():
    with dg.instance_for_test() as instance:
        execution_plan = create_execution_plan(noop_asset_job)

        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, noop_asset_job.get_job_snapshot_id()
        )

        with pytest.raises(
            Exception,
            match=(
                "Cannot have dagster/asset_partition_range_start or"
                " dagster/asset_partition_range_end set without the other"
            ),
        ):
            create_run_for_test(
                instance=instance,
                job_name="foo",
                execution_plan_snapshot=ep_snapshot,
                job_snapshot=noop_asset_job.get_job_snapshot(),
                tags={ASSET_PARTITION_RANGE_START_TAG: "partition_0"},
                asset_graph=noop_asset_job.asset_layer.asset_graph,
            )

        with pytest.raises(
            Exception,
            match=(
                "Cannot have dagster/asset_partition_range_start or"
                " dagster/asset_partition_range_end set without the other"
            ),
        ):
            create_run_for_test(
                instance=instance,
                job_name="foo",
                execution_plan_snapshot=ep_snapshot,
                job_snapshot=noop_asset_job.get_job_snapshot(),
                tags={ASSET_PARTITION_RANGE_END_TAG: "partition_0"},
                asset_graph=noop_asset_job.asset_layer.asset_graph,
            )

        create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_asset_job.get_job_snapshot(),
            tags={ASSET_PARTITION_RANGE_START_TAG: "bar", ASSET_PARTITION_RANGE_END_TAG: "foo"},
            asset_graph=noop_asset_job.asset_layer.asset_graph,
        )


def test_create_run_with_partitioned_asset_stores_partitions_snapshot():
    with dg.instance_for_test() as instance:
        execution_plan = create_execution_plan(noop_time_window_asset_job)

        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, noop_time_window_asset_job.get_job_snapshot_id()
        )

        # ranged run
        run = create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_time_window_asset_job.get_job_snapshot(),
            tags={
                ASSET_PARTITION_RANGE_START_TAG: "2025-1-1",
                ASSET_PARTITION_RANGE_END_TAG: "2025-1-4",
            },
            asset_graph=noop_time_window_asset_job.asset_layer.asset_graph,
        )
        partitions_def = noop_time_window_asset_job.asset_layer.asset_graph.get(
            dg.AssetKey("noop_time_window_asset")
        ).partitions_def
        assert partitions_def is not None

        assert run.partitions_subset is not None
        assert run.partitions_subset == partitions_def.subset_with_partition_keys(
            partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(
                    "2025-1-1",
                    "2025-1-4",
                )
            )
        )

        # single partition
        run = create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_time_window_asset_job.get_job_snapshot(),
            tags={
                PARTITION_NAME_TAG: "2025-1-1",
            },
            asset_graph=noop_time_window_asset_job.asset_layer.asset_graph,
        )
        partitions_def = noop_time_window_asset_job.asset_layer.asset_graph.get(
            dg.AssetKey("noop_time_window_asset")
        ).partitions_def
        assert partitions_def is not None

        assert run.partitions_subset is not None
        assert run.partitions_subset == partitions_def.subset_with_partition_keys(
            partitions_def.get_partition_keys_in_range(
                PartitionKeyRange(
                    "2025-1-1",
                    "2025-1-1",
                )
            )
        )

        # a run created with no partition key but targeting a partitioned asset should not store a
        # partitions subset
        run = create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_time_window_asset_job.get_job_snapshot(),
            tags={},
            asset_graph=noop_time_window_asset_job.asset_layer.asset_graph,
        )
        assert run.partitions_subset is None

        # assets with non-time window partitions do not store the partitions definition on the run
        execution_plan = create_execution_plan(noop_asset_job)

        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, noop_asset_job.get_job_snapshot_id()
        )

        run = create_run_for_test(
            instance=instance,
            job_name="foo",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_asset_job.get_job_snapshot(),
            tags={
                ASSET_PARTITION_RANGE_START_TAG: "foo",
                ASSET_PARTITION_RANGE_END_TAG: "bar",
            },
            asset_graph=noop_asset_job.asset_layer.asset_graph,
        )
        assert run.partitions_subset is None


def test_create_run_with_dynamic_partitioned_asset_stores_partitions_snapshot():
    with dg.instance_for_test() as instance:
        instance.add_dynamic_partitions("my_dynamic", ["a", "b", "c", "d"])

        execution_plan = create_execution_plan(noop_dynamic_partitions_asset_job)

        ep_snapshot = snapshot_from_execution_plan(
            execution_plan, noop_dynamic_partitions_asset_job.get_job_snapshot_id()
        )

        # ranged run
        run = create_run_for_test(
            instance=instance,
            job_name="noop_dynamic_partitions_asset_job",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_dynamic_partitions_asset_job.get_job_snapshot(),
            tags={
                ASSET_PARTITION_RANGE_START_TAG: "a",
                ASSET_PARTITION_RANGE_END_TAG: "c",
            },
            asset_graph=noop_dynamic_partitions_asset_job.asset_layer.asset_graph,
        )
        partitions_def = noop_dynamic_partitions_asset_job.asset_layer.asset_graph.get(
            dg.AssetKey("noop_dynamic_partitions_asset")
        ).partitions_def
        assert isinstance(partitions_def, dg.DynamicPartitionsDefinition)

        assert run.partitions_subset is not None
        assert run.partitions_subset == KeyRangesPartitionsSubset(
            key_ranges=[PartitionKeyRange("a", "c")],
            partitions_snap=PartitionsSnap.from_def(partitions_def),
        )

        # single partition
        run = create_run_for_test(
            instance=instance,
            job_name="noop_dynamic_partitions_asset_job",
            execution_plan_snapshot=ep_snapshot,
            job_snapshot=noop_dynamic_partitions_asset_job.get_job_snapshot(),
            tags={
                PARTITION_NAME_TAG: "b",
            },
            asset_graph=noop_dynamic_partitions_asset_job.asset_layer.asset_graph,
        )
        partitions_def = noop_dynamic_partitions_asset_job.asset_layer.asset_graph.get(
            dg.AssetKey("noop_dynamic_partitions_asset")
        ).partitions_def
        assert partitions_def is not None

        assert run.partitions_subset is not None
        assert run.partitions_subset == KeyRangesPartitionsSubset(
            key_ranges=[PartitionKeyRange("b", "b")],
            partitions_snap=PartitionsSnap.from_def(partitions_def),
        )


def test_get_required_daemon_types():
    from dagster._daemon.daemon import (
        BackfillDaemon,
        MonitoringDaemon,
        SchedulerDaemon,
        SensorDaemon,
    )
    from dagster._daemon.freshness import FreshnessDaemon
    from dagster._daemon.run_coordinator import QueuedRunCoordinatorDaemon

    with dg.instance_for_test() as instance:
        assert instance.get_required_daemon_types() == [
            SensorDaemon.daemon_type(),
            BackfillDaemon.daemon_type(),
            SchedulerDaemon.daemon_type(),
            QueuedRunCoordinatorDaemon.daemon_type(),
            AssetDaemon.daemon_type(),
        ]

    with dg.instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": {"enabled": True},
            "freshness": {"enabled": True},
        }
    ) as instance:
        assert instance.get_required_daemon_types() == [
            SensorDaemon.daemon_type(),
            BackfillDaemon.daemon_type(),
            SchedulerDaemon.daemon_type(),
            QueuedRunCoordinatorDaemon.daemon_type(),
            MonitoringDaemon.daemon_type(),
            AssetDaemon.daemon_type(),
            FreshnessDaemon.daemon_type(),
        ]
        assert len(create_daemons_from_instance(instance)) == 7

    with dg.instance_for_test(
        overrides={
            "auto_materialize": {"enabled": False, "use_sensors": False},
        }
    ) as instance:
        assert instance.get_required_daemon_types() == [
            SensorDaemon.daemon_type(),
            BackfillDaemon.daemon_type(),
            SchedulerDaemon.daemon_type(),
            QueuedRunCoordinatorDaemon.daemon_type(),
        ]


class TestNonResumeRunLauncher(RunLauncher, ConfigurableClass):
    def __init__(self, inst_data: Optional[ConfigurableClassData] = None):
        self._inst_data = inst_data
        super().__init__()

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {}

    @classmethod
    def from_config_value(
        cls, inst_data: ConfigurableClassData, config_value: Mapping[str, Any]
    ) -> Self:
        return cls(inst_data=inst_data)

    def launch_run(self, context):
        raise NotImplementedError()

    def join(self, timeout=30):
        raise NotImplementedError()

    def terminate(self, run_id):
        raise NotImplementedError()

    @property
    def supports_check_run_worker_health(self):
        return True


def test_grpc_default_settings():
    with dg.instance_for_test() as instance:
        assert (
            instance.code_server_process_startup_timeout
            == DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )


def test_grpc_override_settings():
    with dg.instance_for_test(
        overrides={"code_servers": {"local_startup_timeout": 60}}
    ) as instance:
        assert instance.code_server_process_startup_timeout == 60


def test_run_monitoring(capsys):
    with dg.instance_for_test(
        overrides={
            "run_monitoring": {"enabled": True},
        }
    ) as instance:
        assert instance.run_monitoring_enabled

    settings = {"enabled": True}
    with dg.instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": settings,
        }
    ) as instance:
        assert instance.run_monitoring_enabled
        assert instance.run_monitoring_settings == settings
        assert instance.run_monitoring_max_resume_run_attempts == 0

    settings = {"enabled": True, "max_resume_run_attempts": 5}
    with dg.instance_for_test(
        overrides={
            "run_launcher": {
                "module": "dagster_tests.daemon_tests.test_monitoring_daemon",
                "class": "TestRunLauncher",
            },
            "run_monitoring": settings,
        }
    ) as instance:
        assert instance.run_monitoring_enabled
        assert instance.run_monitoring_settings == settings
        assert instance.run_monitoring_max_resume_run_attempts == 5

    with pytest.raises(CheckError):
        with dg.instance_for_test(
            overrides={
                "run_launcher": {
                    "module": "dagster_tests.core_tests.instance_tests.test_instance",
                    "class": "TestNonResumeRunLauncher",
                },
                "run_monitoring": {"enabled": True, "max_resume_run_attempts": 10},
            },
        ) as _:
            pass


def test_cancellation_thread():
    with dg.instance_for_test(
        overrides={
            "run_monitoring": {"cancellation_thread_poll_interval_seconds": 300},
        }
    ) as instance:
        assert instance.cancellation_thread_poll_interval_seconds == 300

    with dg.instance_for_test() as instance:
        assert instance.cancellation_thread_poll_interval_seconds == 10


def test_dagster_home_not_set():
    with environ({"DAGSTER_HOME": ""}):
        with pytest.raises(
            DagsterHomeNotSetError,
            match=r"The environment variable \$DAGSTER_HOME is not set\.",
        ):
            DagsterInstance.get()


def test_invalid_configurable_class():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't find class MadeUpRunLauncher in module when attempting to "
            "load the configurable class dagster.MadeUpRunLauncher"
        ),
    ):
        with dg.instance_for_test(
            overrides={"run_launcher": {"module": "dagster", "class": "MadeUpRunLauncher"}}
        ) as instance:
            print(instance.run_launcher)  # noqa: T201


def test_invalid_configurable_module():
    with pytest.raises(
        check.CheckError,
        match=re.escape(
            "Couldn't import module made_up_module when attempting to load "
            "the configurable class made_up_module.MadeUpRunLauncher",
        ),
    ):
        with dg.instance_for_test(
            overrides={
                "run_launcher": {
                    "module": "made_up_module",
                    "class": "MadeUpRunLauncher",
                }
            }
        ) as instance:
            print(instance.run_launcher)  # noqa: T201


@pytest.mark.parametrize("dirname", (".", ".."))
def test_dagster_home_not_abspath(dirname):
    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match=re.escape(f'$DAGSTER_HOME "{dirname}" must be an absolute path.'),
        ):
            DagsterInstance.get()


def test_dagster_home_not_dir():
    dirname = "/this/path/does/not/exist"

    with environ({"DAGSTER_HOME": dirname}):
        with pytest.raises(
            dg.DagsterInvariantViolationError,
            match=re.escape(f'$DAGSTER_HOME "{dirname}" is not a directory or does not exist.'),
        ):
            DagsterInstance.get()


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Windows paths formatted differently")
def test_dagster_env_vars_from_dotenv_file():
    with (
        tempfile.TemporaryDirectory() as working_dir,
        tempfile.TemporaryDirectory() as dagster_home,
    ):
        # Create a dagster.yaml file in the dagster_home folder that requires SQLITE_STORAGE_BASE_DIR to be set
        # (and DAGSTER_HOME to be set in order to find the dagster.yaml file)
        with open(os.path.join(dagster_home, "dagster.yaml"), "w", encoding="utf8") as fd:
            yaml.dump(
                {
                    "storage": {
                        "sqlite": {
                            "base_dir": {"env": "SQLITE_STORAGE_BASE_DIR"},
                        }
                    }
                },
                fd,
                default_flow_style=False,
            )

        with new_cwd(working_dir):
            with environ({"DAGSTER_HOME": None}):  # pyright: ignore[reportArgumentType]
                # without .env file with a DAGSTER_HOME, loading fails
                with pytest.raises(DagsterHomeNotSetError):
                    with get_instance_for_cli():
                        pass

                storage_dir = os.path.join(dagster_home, "my_storage")
                # with DAGSTER_HOME and SQLITE_STORAGE_BASE_DIR set in a .env file, DagsterInstacne succeeds
                with open(os.path.join(working_dir, ".env"), "w", encoding="utf8") as fd:
                    fd.write(f"DAGSTER_HOME={dagster_home}\n")
                    fd.write(f"SQLITE_STORAGE_BASE_DIR={storage_dir}\n")

                with get_instance_for_cli() as instance:
                    assert (
                        _runs_directory(str(storage_dir)) in instance.run_storage._conn_string  # noqa: SLF001  # pyright: ignore[reportAttributeAccessIssue]
                    )


class TestInstanceSubclass(dg.DagsterInstance):
    def __init__(self, *args, foo=None, baz=None, **kwargs):
        self._foo = foo
        self._baz = baz
        super().__init__(*args, **kwargs)

    def foo(self):
        return self._foo

    @property
    def baz(self):
        return self._baz

    @classmethod
    def config_schema(cls):
        return {
            "foo": dg.Field(str, is_required=True),
            "baz": dg.Field(str, is_required=False),
        }

    @staticmethod
    def config_defaults(base_dir):
        defaults = InstanceRef.config_defaults(base_dir)
        defaults["run_coordinator"] = ConfigurableClassData(  # pyright: ignore[reportIndexIssue]
            "dagster._core.run_coordinator.queued_run_coordinator",
            "QueuedRunCoordinator",
            yaml.dump({}),
        )
        return defaults


def test_instance_subclass():
    with dg.instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_tests.core_tests.instance_tests.test_instance",
                "class": "TestInstanceSubclass",
            },
            "foo": "bar",
        }
    ) as subclass_instance:
        assert isinstance(subclass_instance, dg.DagsterInstance)

        # isinstance(subclass_instance, TestInstanceSubclass) does not pass
        # Likely because the imported/dynamically loaded class is different from the local one

        assert subclass_instance.__class__.__name__ == "TestInstanceSubclass"
        assert subclass_instance.foo() == "bar"  # pyright: ignore[reportAttributeAccessIssue]
        assert subclass_instance.baz is None  # pyright: ignore[reportAttributeAccessIssue]

        assert isinstance(subclass_instance.run_coordinator, dg.QueuedRunCoordinator)

    with dg.instance_for_test(
        overrides={
            "instance_class": {
                "module": "dagster_tests.core_tests.instance_tests.test_instance",
                "class": "TestInstanceSubclass",
            },
            "foo": "bar",
            "baz": "quux",
        }
    ) as subclass_instance:
        assert isinstance(subclass_instance, dg.DagsterInstance)

        assert subclass_instance.__class__.__name__ == "TestInstanceSubclass"
        assert subclass_instance.foo() == "bar"  # pyright: ignore[reportAttributeAccessIssue]
        assert subclass_instance.baz == "quux"  # pyright: ignore[reportAttributeAccessIssue]

    # omitting foo leads to a config schema validation error

    with pytest.raises(dg.DagsterInvalidConfigError):
        with dg.instance_for_test(
            overrides={
                "instance_class": {
                    "module": "dagster_tests.core_tests.instance_tests.test_instance",
                    "class": "TestInstanceSubclass",
                },
                "baz": "quux",
            }
        ) as subclass_instance:
            pass


# class that doesn't implement needed methods on ConfigurableClass
class InvalidRunLauncher(RunLauncher, ConfigurableClass):
    def launch_run(self, context: LaunchRunContext) -> None:
        pass

    def terminate(self, run_id):  # pyright: ignore[reportIncompatibleMethodOverride]
        pass


def test_configurable_class_missing_methods():
    with pytest.raises(
        NotImplementedError,
        match="InvalidRunLauncher must implement the config_type classmethod",
    ):
        with dg.instance_for_test(
            overrides={
                "run_launcher": {
                    "module": "dagster_tests.core_tests.instance_tests.test_instance",
                    "class": "InvalidRunLauncher",
                }
            }
        ) as instance:
            print(instance.run_launcher)  # noqa: T201


@patch("dagster._core.storage.partition_status_cache.get_and_update_asset_status_cache_value")
def test_get_status_by_partition(mock_get_and_update):
    mock_cached_value = MagicMock(spec=AssetStatusCacheValue)
    mock_cached_value.deserialize_materialized_partition_subsets.return_value = [
        "2023-06-01",
        "2023-06-02",
    ]
    mock_cached_value.deserialize_failed_partition_subsets.return_value = ["2023-06-15"]
    mock_cached_value.deserialize_in_progress_partition_subsets.return_value = ["2023-07-01"]
    mock_get_and_update.return_value = mock_cached_value
    with dg.instance_for_test() as instance:
        partition_status = instance.get_status_by_partition(
            dg.AssetKey("test-asset"),
            ["2023-07-01"],
            dg.DailyPartitionsDefinition(start_date="2023-06-01"),
        )
        assert partition_status == {"2023-07-01": AssetPartitionStatus.IN_PROGRESS}


def test_report_runless_asset_event() -> None:
    with dg.instance_for_test() as instance:
        my_asset_key = dg.AssetKey("my_asset")

        instance.report_runless_asset_event(dg.AssetMaterialization(my_asset_key))
        mats = instance.get_latest_materialization_events([my_asset_key])
        assert mats[my_asset_key]

        instance.report_runless_asset_event(dg.AssetObservation(my_asset_key))
        records = instance.fetch_observations(my_asset_key, limit=1).records
        assert len(records) == 1

        my_check = "my_check"
        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset_key,
                check_name=my_check,
                passed=True,
                metadata={},
            )
        )
        records = instance.event_log_storage.get_asset_check_execution_history(
            check_key=dg.AssetCheckKey(asset_key=my_asset_key, name=my_check),
            limit=1,
        )
        assert len(records) == 1
        assert records[0].status == AssetCheckExecutionRecordStatus.SUCCEEDED

        instance.report_runless_asset_event(
            dg.AssetCheckEvaluation(
                asset_key=my_asset_key,
                check_name=my_check,
                passed=False,
                metadata={},
            )
        )
        records = instance.event_log_storage.get_asset_check_execution_history(
            check_key=dg.AssetCheckKey(asset_key=my_asset_key, name=my_check),
            limit=1,
        )
        assert len(records) == 1
        assert records[0].status == AssetCheckExecutionRecordStatus.FAILED


def test_report_runless_asset_event_freshness_state_change() -> None:
    """Test that report_runless_asset_event accepts FreshnessStateChange events."""
    from dagster._core.definitions.freshness import FreshnessState, FreshnessStateChange

    with dg.instance_for_test() as instance:
        my_asset_key = dg.AssetKey("my_asset")
        freshness_change = FreshnessStateChange(
            key=my_asset_key,
            new_state=FreshnessState.FAIL,
            previous_state=FreshnessState.UNKNOWN,
            state_change_timestamp=1234567890.0,
        )

        # This should not raise an exception - this is the main test
        # Previously this would have raised DagsterInvariantViolationError
        instance.report_runless_asset_event(freshness_change)


def test_invalid_run_id():
    with dg.instance_for_test() as instance:
        with pytest.raises(
            CheckError,
            match="run_id must be a valid UUID. Got invalid_run_id",
        ):
            create_run_for_test(instance, job_name="foo_job", run_id="invalid_run_id")
