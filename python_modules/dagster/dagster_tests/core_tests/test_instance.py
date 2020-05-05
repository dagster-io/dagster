from dagster import PipelineDefinition, execute_pipeline, pipeline, solid
from dagster.core.execution.api import create_execution_plan
from dagster.core.instance import DagsterInstance
from dagster.core.snap import (
    create_execution_plan_snapshot_id,
    create_pipeline_snapshot_id,
    snapshot_from_execution_plan,
)


def test_get_run_by_id():
    instance = DagsterInstance.ephemeral()

    assert instance.get_runs() == []
    pipeline_run = instance.create_run(
        pipeline_name='foo_pipeline', run_id='new_run', pipeline_snapshot=None
    )

    assert instance.get_runs() == [pipeline_run]

    assert instance.get_run_by_id(pipeline_run.run_id) == pipeline_run


def do_test_single_write_read(instance):
    run_id = 'some_run_id'
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
    instance.create_run_for_pipeline(pipeline_def=pipeline_def, run_id=run_id)
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


def test_create_execution_plan_snapshot():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    instance = DagsterInstance.local_temp()

    execution_plan = create_execution_plan(noop_pipeline)

    ep_snapshot = snapshot_from_execution_plan(
        execution_plan, noop_pipeline.get_pipeline_snapshot_id()
    )
    ep_snapshot_id = create_execution_plan_snapshot_id(ep_snapshot)

    result = execute_pipeline(noop_pipeline, instance=instance)
    assert result.success

    run = instance.get_run_by_id(result.run_id)

    assert run.execution_plan_snapshot_id == ep_snapshot_id
    assert run.execution_plan_snapshot_id == create_execution_plan_snapshot_id(ep_snapshot)
