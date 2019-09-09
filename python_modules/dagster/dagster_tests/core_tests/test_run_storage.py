import uuid

from dagster import PipelineDefinition, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.runs import SqliteRunStorage


def test_filesystem_persist_one_run():
    with seven.TemporaryDirectory() as temp_dir:
        do_test_single_write_read(DagsterInstance.local_temp(temp_dir))


def test_in_memory_persist_one_run():
    do_test_single_write_read(DagsterInstance.ephemeral())


# need fuzzy matching for floats in py2
EPSILON = 0.1


def assert_timestamp(expected, actual):
    assert expected > (actual - EPSILON) and expected < (actual + EPSILON)


def do_test_single_write_read(instance):
    run_id = 'some_run_id'
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])

    instance.create_empty_run(run_id=run_id, pipeline_name=pipeline_def.name)

    run = instance.get_run(run_id)

    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'

    assert list(instance.all_runs) == [run]

    instance.wipe()

    assert list(instance.all_runs) == []


def test_sqlite_mem_storage():
    storage = SqliteRunStorage.mem()

    assert storage

    run_id = str(uuid.uuid4())

    storage.add_run(PipelineRun.create_empty_run(run_id=run_id, pipeline_name='some_pipeline'))

    assert len(storage.all_runs) == 1

    run = storage.all_runs[0]

    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'

    fetched_run = storage.get_run_by_id(run_id)
    assert fetched_run.run_id == run_id
    assert fetched_run.pipeline_name == 'some_pipeline'


def test_nuke():
    storage = SqliteRunStorage.mem()

    assert storage
    run_id = str(uuid.uuid4())

    storage.add_run(PipelineRun.create_empty_run(run_id=run_id, pipeline_name='some_pipeline'))

    assert len(storage.all_runs) == 1

    storage.wipe()

    assert list(storage.all_runs) == []
