import pytest

from dagster import PipelineDefinition, execute_pipeline, pipeline, solid
from dagster.core.errors import DagsterRunConflict
from dagster.core.instance import DagsterInstance
from dagster.core.snap.pipeline_snapshot import create_pipeline_snapshot_id
from dagster.core.storage.pipeline_run import PipelineRun


def test_get_or_create_run():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    pipeline_run = PipelineRun.create_empty_run('foo_pipeline', 'new_run')
    assert instance.get_or_create_run(pipeline_run) == pipeline_run

    assert instance.get_runs() == [pipeline_run]

    assert instance.get_or_create_run(pipeline_run) == pipeline_run

    assert instance.get_runs() == [pipeline_run]

    conflicting_pipeline_run = PipelineRun.create_empty_run('bar_pipeline', 'new_run')

    with pytest.raises(DagsterRunConflict, match='Found conflicting existing run with same id.'):
        instance.get_or_create_run(conflicting_pipeline_run)


def do_test_single_write_read(instance):
    run_id = 'some_run_id'
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
    instance.create_empty_run(run_id=run_id, pipeline_name=pipeline_def.name)
    run = instance.get_run_by_id(run_id)
    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'
    assert list(instance.get_runs()) == [run]
    instance.wipe()
    assert list(instance.get_runs()) == []


def test_filesystem_persist_one_run(tmpdir):
    do_test_single_write_read(DagsterInstance.local_temp(str(tmpdir)))


def test_in_memory_persist_one_run():
    do_test_single_write_read(DagsterInstance.ephemeral())


def test_create_pipeline_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    instance = DagsterInstance.local_temp()

    result = execute_pipeline(noop_pipeline, instance=instance)
    assert result.success

    run = instance.get_run_by_id(result.run_id)

    assert run.pipeline_snapshot_id == create_pipeline_snapshot_id(
        noop_pipeline.get_pipeline_snapshot()
    )
