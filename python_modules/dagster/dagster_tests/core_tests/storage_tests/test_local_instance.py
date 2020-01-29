import os
import types

import pytest
import yaml

from dagster import (
    DagsterEventType,
    DagsterInvalidConfigError,
    RunConfig,
    check,
    execute_pipeline,
    pipeline,
    seven,
    solid,
)
from dagster.core.instance import DagsterInstance, InstanceRef, InstanceType
from dagster.core.storage.event_log import SqliteEventLogStorage
from dagster.core.storage.local_compute_log_manager import LocalComputeLogManager
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.root import LocalArtifactStorage
from dagster.core.storage.runs import SqliteRunStorage


def test_fs_stores():
    @pipeline
    def simple():
        @solid
        def easy(context):
            context.log.info('easy')
            return 'easy'

        easy()

    with seven.TemporaryDirectory() as temp_dir:
        run_store = SqliteRunStorage.from_local(temp_dir)
        event_store = SqliteEventLogStorage(temp_dir)
        compute_log_manager = LocalComputeLogManager(temp_dir)
        instance = DagsterInstance(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=LocalArtifactStorage(temp_dir),
            run_storage=run_store,
            event_storage=event_store,
            compute_log_manager=compute_log_manager,
        )

        run = RunConfig()
        execute_pipeline(simple, run_config=run, instance=instance)

        assert run_store.has_run(run.run_id)
        assert run_store.get_run_by_id(run.run_id).status == PipelineRunStatus.SUCCESS
        assert DagsterEventType.PIPELINE_SUCCESS in [
            event.dagster_event.event_type
            for event in event_store.get_logs_for_run(run.run_id)
            if event.is_dagster_event
        ]
        stats = event_store.get_stats_for_run(run.run_id)
        assert stats.steps_succeeded == 1
        assert stats.end_time is not None


def test_init_compute_log_with_bad_config():
    with seven.TemporaryDirectory() as tmpdir_path:
        with open(os.path.join(tmpdir_path, 'dagster.yaml'), 'w') as fd:
            yaml.dump({'compute_logs': {'garbage': 'flargh'}}, fd, default_flow_style=False)
        with pytest.raises(DagsterInvalidConfigError, match='Undefined field "garbage"'):
            DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))


def test_init_compute_log_with_bad_config_override():
    with seven.TemporaryDirectory() as tmpdir_path:
        with pytest.raises(DagsterInvalidConfigError, match='Undefined field "garbage"'):
            DagsterInstance.from_ref(
                InstanceRef.from_dir(tmpdir_path, overrides={'compute_logs': {'garbage': 'flargh'}})
            )


def test_init_compute_log_with_bad_config_module():
    with seven.TemporaryDirectory() as tmpdir_path:
        with open(os.path.join(tmpdir_path, 'dagster.yaml'), 'w') as fd:
            yaml.dump(
                {'compute_logs': {'module': 'flargh', 'class': 'Woble', 'config': {}}},
                fd,
                default_flow_style=False,
            )
        with pytest.raises(check.CheckError, match='Couldn\'t import module'):
            DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))


MOCK_HAS_RUN_CALLED = False


def test_get_or_create_run():
    with seven.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))
        run = PipelineRun.create_empty_run('foo_pipeline', 'bar_run')
        assert instance.get_or_create_run(run) == run
        assert instance.has_run(run.run_id)
        assert instance.get_or_create_run(run) == run

    # Run is created after we check whether it exists
    with seven.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))
        run = PipelineRun.create_empty_run('foo_pipeline', 'bar_run')

        def _has_run(self, run_id):
            # This is uglier than we would like because there is no nonlocal keyword in py2
            global MOCK_HAS_RUN_CALLED  # pylint: disable=global-statement
            # pylint: disable=protected-access
            if not self._run_storage.has_run(run_id) and not MOCK_HAS_RUN_CALLED:
                self._run_storage.add_run(PipelineRun.create_empty_run('foo_pipeline', run_id))
                return False
            else:
                return self._run_storage.has_run(run_id)

        instance.has_run = types.MethodType(_has_run, instance)
        assert instance.get_or_create_run(run) == run

    # Run is created after we check whether it exists, but deleted before we can get it
    global MOCK_HAS_RUN_CALLED  # pylint:disable=global-statement
    MOCK_HAS_RUN_CALLED = False
    with seven.TemporaryDirectory() as tmpdir_path:
        instance = DagsterInstance.from_ref(InstanceRef.from_dir(tmpdir_path))
        run = PipelineRun.create_empty_run('foo_pipeline', 'bar_run')

        def _has_run(self, run_id):
            global MOCK_HAS_RUN_CALLED  # pylint: disable=global-statement
            # pylint: disable=protected-access
            if not self._run_storage.has_run(run_id) and not MOCK_HAS_RUN_CALLED:
                self._run_storage.add_run(PipelineRun.create_empty_run('foo_pipeline', run_id))
                MOCK_HAS_RUN_CALLED = True
                return False
            elif self._run_storage.has_run(run_id) and MOCK_HAS_RUN_CALLED:
                MOCK_HAS_RUN_CALLED = False
                return True
            else:
                return False

        instance.has_run = types.MethodType(_has_run, instance)
        with pytest.raises(check.CheckError, match='Inconsistent run storage'):
            instance.get_or_create_run(run)
