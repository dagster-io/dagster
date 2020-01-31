from contextlib import contextmanager

import pytest

from dagster import PipelineDefinition, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage
from dagster.utils.test.run_storage import TestRunStorage


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


@contextmanager
def create_sqlite_run_storage():
    with seven.TemporaryDirectory() as tempdir:
        yield SqliteRunStorage.from_local(tempdir)


@contextmanager
def create_in_memory_storage():
    yield InMemoryRunStorage()


TestRunStorage.__test__ = False


class TestMyStorageImplementation(TestRunStorage):
    __test__ = True

    @pytest.fixture(name='storage', params=[create_sqlite_run_storage, create_in_memory_storage])
    def run_storage(self, request):
        with request.param() as s:
            yield s
