import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager

from dagster import PipelineDefinition, execute_pipeline, solid
from dagster.core.storage.config import base_runs_directory
from dagster.core.storage.runs import FilesystemRunStorage, InMemoryRunStorage, SqliteRunStorage


@contextmanager
def temp_run_storage():
    try:
        base_dir = tempfile.mkdtemp()
        yield FilesystemRunStorage(base_dir=base_dir)
    finally:
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)


def test_default_run_storage():
    @solid
    def check_run_storage(context):
        assert isinstance(context.get_system_context().run_storage, InMemoryRunStorage)

    pipeline = PipelineDefinition(name='default_run_storage_test', solid_defs=[check_run_storage])

    result = execute_pipeline(pipeline)

    assert result.success

    assert not os.path.exists(os.path.join(base_runs_directory(), result.run_id))


def test_config_specified_filesystem_run_storage():
    @solid
    def check_run_storage(context):
        assert isinstance(context.get_system_context().run_storage, FilesystemRunStorage)

    pipeline = PipelineDefinition(name='default_run_storage_test', solid_defs=[check_run_storage])

    result = execute_pipeline(pipeline, environment_dict={'storage': {'filesystem': {}}})

    assert result.success

    assert os.path.exists(os.path.join(base_runs_directory(), result.run_id))


def test_empty_storage():
    with temp_run_storage() as run_storage:
        assert list(run_storage.all_runs) == []


def test_filesystem_persist_one_run():
    with temp_run_storage() as run_storage:
        do_test_single_write_read(run_storage)


def test_in_memory_persist_one_run():
    do_test_single_write_read(InMemoryRunStorage())


# need fuzzy matching for floats in py2
EPSILON = 0.1


def assert_timestamp(expected, actual):
    assert expected > (actual - EPSILON) and expected < (actual + EPSILON)


def do_test_single_write_read(run_storage):
    run_id = 'some_run_id'
    # current_time = time.time()
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
    run_storage.create_run(run_id=run_id, pipeline_name=pipeline_def.name)

    run = run_storage.get_run_by_id(run_id)

    assert run.run_id == run_id
    # assert run.timestamp == current_time
    assert run.pipeline_name == 'some_pipeline'

    assert list(run_storage.all_runs) == [run]

    run_storage.wipe()

    assert list(run_storage.all_runs) == []


def test_sqlite_mem_storage():
    storage = SqliteRunStorage.mem()

    assert storage

    run_id = str(uuid.uuid4())

    storage.create_run(run_id=run_id, pipeline_name='some_pipeline')

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

    storage.create_run(run_id=run_id, pipeline_name='some_pipeline')

    assert len(storage.all_runs) == 1

    storage.wipe()

    assert list(storage.all_runs) == []
