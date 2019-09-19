import os

import pytest
import yaml

from dagster import (
    DagsterEventType,
    DagsterInvalidConfigError,
    DagsterInvariantViolationError,
    RunConfig,
    execute_pipeline,
    lambda_solid,
    pipeline,
    seven,
)
from dagster.core.instance import DagsterInstance, InstanceType, LocalInstanceRef
from dagster.core.storage.event_log import FilesystemEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.runs import FilesystemRunStorage


def test_fs_stores():
    @pipeline
    def simple():
        @lambda_solid
        def easy():
            return 'easy'

        easy()

    with seven.TemporaryDirectory() as temp_dir:
        run_store = FilesystemRunStorage(temp_dir)
        event_store = FilesystemEventLogStorage(temp_dir)
        compute_log_manager = LocalComputeLogManager(temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.LOCAL,
            root_storage_dir=temp_dir,
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=compute_log_manager,
        )

        run = RunConfig()
        execute_pipeline(simple, run_config=run, instance=instance)

        assert run_store.has_run(run.run_id)
        assert run_store.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
        assert DagsterEventType.PIPELINE_SUCCESS in [
            event.dagster_event.event_type for event in event_store.get_logs_for_run(run.run_id)
        ]


def test_init_compute_log_with_bad_config():
    with seven.TemporaryDirectory() as tmpdir_path:
        with open(os.path.join(tmpdir_path, 'dagster.yaml'), 'w') as fd:
            yaml.dump({'compute_logs': {'garbage': 'flargh'}}, fd)
        with pytest.raises(DagsterInvalidConfigError, match='Undefined field "garbage"'):
            DagsterInstance.from_ref(LocalInstanceRef(tmpdir_path))


def test_init_compute_log_with_bad_config_mpdule():
    with seven.TemporaryDirectory() as tmpdir_path:
        with open(os.path.join(tmpdir_path, 'dagster.yaml'), 'w') as fd:
            yaml.dump({'compute_logs': {'module': 'flargh', 'class': 'Woble', 'config': {}}}, fd)
        with pytest.raises(
            DagsterInvariantViolationError,
            match='returning a valid instance of `ComputeLogManager`',
        ):
            DagsterInstance.from_ref(LocalInstanceRef(tmpdir_path))
