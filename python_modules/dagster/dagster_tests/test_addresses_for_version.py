from contextlib import contextmanager

import pytest

from dagster import Output, execute_pipeline, pipeline, seven, solid
from dagster.core.execution.plan.objects import StepOutputHandle
from dagster.core.instance import DagsterInstance, InstanceType
from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
from dagster.core.storage.event_log import (
    ConsolidatedSqliteEventLogStorage,
    InMemoryEventLogStorage,
)
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
        run_launcher=SyncInMemoryRunLauncher(),
    )


@contextmanager
def create_in_memory_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        asset_storage = InMemoryEventLogStorage()
        instance = get_instance(temp_dir, asset_storage)
        yield [instance, asset_storage]


@contextmanager
def create_consolidated_sqlite_event_log_instance():
    with seven.TemporaryDirectory() as temp_dir:
        asset_storage = ConsolidatedSqliteEventLogStorage(temp_dir)
        instance = get_instance(temp_dir, asset_storage)
        yield [instance, asset_storage]


versioned_storage_test = pytest.mark.parametrize(
    "version_storing_context", [create_in_memory_event_log_instance],
)


@versioned_storage_test
def test_addresses_for_version(version_storing_context):
    @solid(version="abc")
    def solid1(_):
        yield Output(5, address="some_address")

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
    assert instance.get_addresses_for_step_output_versions(
        {("my_pipeline", step_output_handle): "abc"}
    ) == {("my_pipeline", step_output_handle): "some_address"}
