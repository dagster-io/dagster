from contextlib import contextmanager

import os
import tempfile
import time
import shutil

from dagster import PipelineDefinition, solid, execute_pipeline
from dagster.core.storage.runs import (
    DagsterRunMeta,
    FileSystemRunStorage,
    InMemoryRunStorage,
    base_runs_directory,
)


@contextmanager
def temp_run_storage():
    try:
        base_dir = tempfile.mkdtemp()
        yield FileSystemRunStorage(base_dir)
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
        assert isinstance(context.get_system_context().run_storage, FileSystemRunStorage)

    pipeline = PipelineDefinition(name='default_run_storage_test', solid_defs=[check_run_storage])

    result = execute_pipeline(pipeline, environment_dict={'storage': {'filesystem': {}}})

    assert result.success

    assert os.path.exists(os.path.join(base_runs_directory(), result.run_id))


def test_empty_storage():
    with temp_run_storage() as run_storage:
        assert run_storage.get_run_ids() == []


def test_filesystem_persist_one_run():
    with temp_run_storage() as run_storage:
        do_test_single_write_read(run_storage)


def test_in_memory_persist_one_run():
    do_test_single_write_read(InMemoryRunStorage())


def do_test_single_write_read(run_storage):
    run_id = 'some_run_id'
    current_time = time.time()
    run_storage.write_dagster_run_meta(
        DagsterRunMeta(run_id=run_id, timestamp=current_time, pipeline_name='some_pipeline')
    )

    run_meta = run_storage.get_run_meta(run_id)

    assert run_meta.run_id == run_id
    assert run_meta.timestamp == current_time
    assert run_meta.pipeline_name == 'some_pipeline'

    assert run_storage.get_run_metas() == [run_meta]

    run_storage.nuke()

    assert run_storage.get_run_metas() == []
