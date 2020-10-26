import os
from contextlib import contextmanager

import pytest
from dagster import Int, execute_pipeline, pipeline, seven, solid
from dagster.core.errors import DagsterAddressIOError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.execution.resolve_versions import resolve_step_output_versions
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.runs_coordinator import LaunchImmediateRunsCoordinator
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import EnvironmentConfig


def get_instance(temp_dir, event_log_storage):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=event_log_storage,
        compute_log_manager=NoOpComputeLogManager(),
        runs_coordinator=LaunchImmediateRunsCoordinator(),
        run_launcher=SyncInMemoryRunLauncher(),
    )


@contextmanager
def create_in_memory_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        event_storage = InMemoryEventLogStorage()
        instance = get_instance(temp_dir, event_storage)
        yield [instance, event_storage]


@contextmanager
def create_consolidated_sqlite_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        event_storage = ConsolidatedSqliteEventLogStorage(temp_dir)
        instance = get_instance(temp_dir, event_storage)
        yield [instance, event_storage]


versioned_storage_test = pytest.mark.parametrize(
    "version_storing_context",
    [create_in_memory_event_log_instance, create_consolidated_sqlite_event_log_instance],
)


def default_mode_output_versions(pipeline_def):
    return resolve_step_output_versions(
        create_execution_plan(pipeline_def),
        EnvironmentConfig.build(pipeline_def, {}, "default"),
        pipeline_def.get_mode_definition("default"),
    )


@versioned_storage_test
def test_addresses_for_version(version_storing_context):
    @solid(version="abc")
    def solid1(_):
        return 5

    @solid(version="123")
    def solid2(_, _input1):
        pass

    @pipeline
    def my_pipeline():
        solid2(solid1())

    with version_storing_context() as ctx:
        instance, _ = ctx
        execute_pipeline(instance=instance, pipeline=my_pipeline)

        step_output_handle = StepOutputHandle("solid1.compute", "result")
        output_version = default_mode_output_versions(my_pipeline)[step_output_handle]
        assert instance.get_addresses_for_step_output_versions(
            {("my_pipeline", step_output_handle): output_version}
        ) == {("my_pipeline", step_output_handle): "/intermediates/solid1.compute/result"}


@versioned_storage_test
def test_version_based_memoization(version_storing_context):
    with seven.TemporaryDirectory() as tmpdir:

        def define_pipeline(solid2_version):
            @solid(version="abc")
            def solid1(_):
                return 5

            @solid(version=solid2_version)
            def solid2(_, input1):
                return input1 + 1

            @pipeline
            def my_pipeline():
                solid2(solid1())

            return my_pipeline

        run_config = {"storage": {"filesystem": {"config": {"base_dir": tmpdir}}}}

        with version_storing_context() as ctx:
            instance, _ = ctx
            execute_pipeline(
                instance=instance, pipeline=define_pipeline("1"), run_config=run_config
            )
            result = execute_pipeline(
                instance=instance,
                pipeline=define_pipeline("2"),
                run_config=run_config,
                tags={MEMOIZED_RUN_TAG: "true"},
            )
            assert result.result_for_solid("solid2").output_values["result"] == 6
            assert "solid1" not in result.events_by_step_key


def test_address_operation_using_intermediates_file_system():
    with seven.TemporaryDirectory() as tmpdir_path:
        output_address = os.path.join(tmpdir_path, "solid1.output")
        output_value = 5

        instance = DagsterInstance.ephemeral()
        intermediate_storage = build_fs_intermediate_storage(
            instance.intermediates_directory, run_id="some_run_id"
        )

        object_operation_result = intermediate_storage.set_intermediate_to_address(
            context=None,
            dagster_type=Int,
            step_output_handle=StepOutputHandle("solid1.compute"),
            value=output_value,
            address=output_address,
        )

        assert object_operation_result.key == output_address
        assert object_operation_result.obj == output_value

        assert (
            intermediate_storage.get_intermediate_from_address(
                context=None,
                dagster_type=Int,
                step_output_handle=StepOutputHandle("solid1.compute"),
                address=output_address,
            ).obj
            == output_value
        )

        with pytest.raises(DagsterAddressIOError):
            intermediate_storage.set_intermediate_to_address(
                context=None,
                dagster_type=Int,
                step_output_handle=StepOutputHandle("solid1.compute"),
                value=1,
                address="invalid_address",
            )

        with pytest.raises(DagsterAddressIOError):
            intermediate_storage.get_intermediate_from_address(
                context=None,
                dagster_type=Int,
                step_output_handle=StepOutputHandle("solid1.compute"),
                address=os.path.join(tmpdir_path, "invalid.output"),
            )
