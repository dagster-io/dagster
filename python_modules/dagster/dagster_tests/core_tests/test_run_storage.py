import uuid

from dagster import PipelineDefinition
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.runs import SqliteRunStorage


def do_test_single_write_read(instance):
    run_id = 'some_run_id'
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
    instance.create_empty_run(run_id=run_id, pipeline_name=pipeline_def.name)
    run = instance.get_run(run_id)
    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'
    assert list(instance.all_runs()) == [run]
    instance.wipe()
    assert list(instance.all_runs()) == []


def build_run(run_id, pipeline_name, mode='default', tags=None):
    from dagster.core.definitions.pipeline import ExecutionSelector

    return PipelineRun(
        pipeline_name=pipeline_name,
        run_id=run_id,
        environment_dict=None,
        mode=mode,
        selector=ExecutionSelector(pipeline_name),
        reexecution_config=None,
        step_keys_to_execute=None,
        tags=tags,
        status=PipelineRunStatus.NOT_STARTED,
    )


def test_filesystem_persist_one_run(tmpdir):
    do_test_single_write_read(DagsterInstance.local_temp(str(tmpdir)))


def test_in_memory_persist_one_run():
    do_test_single_write_read(DagsterInstance.ephemeral())


def test_basic_storage(tmpdir):
    storage = SqliteRunStorage.from_local(str(tmpdir))
    assert storage
    run_id = str(uuid.uuid4())
    added = storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
    assert added
    runs = storage.all_runs()
    assert len(runs) == 1
    run = runs[0]
    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'
    assert storage.has_run(run_id)
    fetched_run = storage.get_run_by_id(run_id)
    assert fetched_run.run_id == run_id
    assert fetched_run.pipeline_name == 'some_pipeline'


def test_nuke(tmpdir):
    storage = SqliteRunStorage.from_local(str(tmpdir))
    assert storage
    run_id = str(uuid.uuid4())
    storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 1
    storage.wipe()
    assert list(storage.all_runs()) == []


def test_fetch_by_pipeline(tmpdir):
    storage = SqliteRunStorage.from_local(str(tmpdir))
    assert storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    storage.add_run(build_run(run_id=one, pipeline_name='some_pipeline'))
    storage.add_run(build_run(run_id=two, pipeline_name='some_other_pipeline'))
    assert len(storage.all_runs()) == 2
    some_runs = storage.all_runs_for_pipeline('some_pipeline')
    assert len(some_runs) == 1
    assert some_runs[0].run_id == one


def test_fetch_by_tag(tmpdir):
    storage = SqliteRunStorage.from_local(str(tmpdir))
    assert storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    three = str(uuid.uuid4())
    storage.add_run(build_run(run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello'}))
    storage.add_run(build_run(run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'goodbye'}))
    storage.add_run(build_run(run_id=three, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 3
    some_runs = storage.all_runs_for_tag('mytag', 'hello')
    assert len(some_runs) == 1
    assert some_runs[0].run_id == one
