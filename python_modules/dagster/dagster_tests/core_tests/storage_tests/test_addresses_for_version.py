import os
from contextlib import contextmanager

import pytest
from dagster import Int, seven
from dagster.core.errors import DagsterAddressIOError
from dagster.core.execution.api import create_execution_plan
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.run_coordinator import DefaultRunCoordinator
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import InMemoryRunStorage


def get_instance(temp_dir, event_log_storage):
    return DagsterInstance(
        instance_type=InstanceType.EPHEMERAL,
        local_artifact_storage=LocalArtifactStorage(temp_dir),
        run_storage=InMemoryRunStorage(),
        event_storage=event_log_storage,
        compute_log_manager=NoOpComputeLogManager(),
        run_coordinator=DefaultRunCoordinator(),
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
    return create_execution_plan(
        pipeline_def, run_config={}, mode="default"
    ).resolve_step_output_versions()


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
