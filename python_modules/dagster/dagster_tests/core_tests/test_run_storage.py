import uuid
from contextlib import contextmanager

import pytest

from dagster import PipelineDefinition, seven
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.runs import InMemoryRunStorage, SqliteRunStorage


def do_test_single_write_read(instance):
    run_id = 'some_run_id'
    pipeline_def = PipelineDefinition(name='some_pipeline', solid_defs=[])
    instance.create_empty_run(run_id=run_id, pipeline_name=pipeline_def.name)
    run = instance.get_run_by_id(run_id)
    assert run.run_id == run_id
    assert run.pipeline_name == 'some_pipeline'
    assert list(instance.all_runs()) == [run]
    instance.wipe()
    assert list(instance.all_runs()) == []


def build_run(
    run_id, pipeline_name, mode='default', tags=None, status=PipelineRunStatus.NOT_STARTED
):
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
        status=status,
    )


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


run_storage_test = pytest.mark.parametrize(
    'run_storage_factory_cm_fn', [create_sqlite_run_storage, create_in_memory_storage]
)


@run_storage_test
def test_basic_storage(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
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


@run_storage_test
def test_clear(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        run_id = str(uuid.uuid4())
        storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
        assert len(storage.all_runs()) == 1
        storage.wipe()
        assert list(storage.all_runs()) == []


@run_storage_test
def test_fetch_by_pipeline(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one = str(uuid.uuid4())
        two = str(uuid.uuid4())
        storage.add_run(build_run(run_id=one, pipeline_name='some_pipeline'))
        storage.add_run(build_run(run_id=two, pipeline_name='some_other_pipeline'))
        assert len(storage.all_runs()) == 2
        some_runs = storage.get_runs_with_pipeline_name('some_pipeline')
        assert len(some_runs) == 1
        assert some_runs[0].run_id == one


@run_storage_test
def test_fetch_count_by_tag(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one = str(uuid.uuid4())
        two = str(uuid.uuid4())
        three = str(uuid.uuid4())
        storage.add_run(
            build_run(
                run_id=one,
                pipeline_name='some_pipeline',
                tags={'mytag': 'hello', 'mytag2': 'world'},
            )
        )
        storage.add_run(
            build_run(
                run_id=two,
                pipeline_name='some_pipeline',
                tags={'mytag': 'goodbye', 'mytag2': 'world'},
            )
        )
        storage.add_run(build_run(run_id=three, pipeline_name='some_pipeline'))
        assert len(storage.all_runs()) == 3

        run_count = storage.get_run_count_with_matching_tags(
            [('mytag', 'hello'), ('mytag2', 'world')]
        )
        assert run_count == 1

        run_count = storage.get_run_count_with_matching_tags([('mytag2', 'world')])
        assert run_count == 2

        run_count = storage.get_run_count_with_matching_tags([])
        assert run_count == 3

        assert storage.get_run_tags() == [('mytag', {'hello', 'goodbye'}), ('mytag2', {'world'})]


@run_storage_test
def test_fetch_by_tags(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one = str(uuid.uuid4())
        two = str(uuid.uuid4())
        three = str(uuid.uuid4())
        storage.add_run(
            build_run(
                run_id=one,
                pipeline_name='some_pipeline',
                tags={'mytag': 'hello', 'mytag2': 'world'},
            )
        )
        storage.add_run(
            build_run(
                run_id=two,
                pipeline_name='some_pipeline',
                tags={'mytag': 'goodbye', 'mytag2': 'world'},
            )
        )
        storage.add_run(build_run(run_id=three, pipeline_name='some_pipeline'))
        assert len(storage.all_runs()) == 3

        some_runs = storage.get_runs_with_matching_tags([('mytag', 'hello'), ('mytag2', 'world')])
        assert len(some_runs) == 1
        assert some_runs[0].run_id == one

        some_runs = storage.get_runs_with_matching_tags([('mytag2', 'world')])
        assert len(some_runs) == 2
        assert any(x.run_id == one for x in some_runs)
        assert any(x.run_id == two for x in some_runs)

        some_runs = storage.get_runs_with_matching_tags([])
        assert len(some_runs) == 3


@run_storage_test
def test_paginated_fetch(run_storage_factory_cm_fn):
    storage = InMemoryRunStorage()
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one, two, three = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
        storage.add_run(
            build_run(run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello'})
        )
        storage.add_run(
            build_run(run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'hello'})
        )
        storage.add_run(
            build_run(run_id=three, pipeline_name='some_pipeline', tags={'mytag': 'hello'})
        )

        all_runs = storage.all_runs()
        assert len(all_runs) == 3
        sliced_runs = storage.all_runs(cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs_with_pipeline_name('some_pipeline')
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs_with_pipeline_name('some_pipeline', cursor=three, limit=1)
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two

        all_runs = storage.get_runs_with_matching_tags([('mytag', 'hello')])
        assert len(all_runs) == 3
        sliced_runs = storage.get_runs_with_matching_tags(
            [('mytag', 'hello')], cursor=three, limit=1
        )
        assert len(sliced_runs) == 1
        assert sliced_runs[0].run_id == two


@run_storage_test
def test_fetch_by_status(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one = str(uuid.uuid4())
        two = str(uuid.uuid4())
        three = str(uuid.uuid4())
        four = str(uuid.uuid4())
        storage.add_run(
            build_run(
                run_id=one, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            build_run(run_id=two, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED)
        )
        storage.add_run(
            build_run(run_id=three, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED)
        )
        storage.add_run(
            build_run(run_id=four, pipeline_name='some_pipeline', status=PipelineRunStatus.FAILURE)
        )

        assert {
            run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.NOT_STARTED)
        } == {one}

        assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.STARTED)} == {
            two,
            three,
        }

        assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.FAILURE)} == {
            four
        }

        assert {
            run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.SUCCESS)
        } == set()


@run_storage_test
def test_fetch_by_status_cursored(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        one = str(uuid.uuid4())
        two = str(uuid.uuid4())
        three = str(uuid.uuid4())
        four = str(uuid.uuid4())
        storage.add_run(
            build_run(run_id=one, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED)
        )
        storage.add_run(
            build_run(run_id=two, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED)
        )
        storage.add_run(
            build_run(
                run_id=three, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED
            )
        )
        storage.add_run(
            build_run(run_id=four, pipeline_name='some_pipeline', status=PipelineRunStatus.STARTED)
        )

        cursor_four_runs = storage.get_runs_with_status(PipelineRunStatus.STARTED, cursor=four)
        assert len(cursor_four_runs) == 2
        assert {run.run_id for run in cursor_four_runs} == {one, two}

        cursor_two_runs = storage.get_runs_with_status(PipelineRunStatus.STARTED, cursor=two)
        assert len(cursor_two_runs) == 1
        assert {run.run_id for run in cursor_two_runs} == {one}

        cursor_one_runs = storage.get_runs_with_status(PipelineRunStatus.STARTED, cursor=one)
        assert not cursor_one_runs

        cursor_four_limit_one = storage.get_runs_with_status(
            PipelineRunStatus.STARTED, cursor=four, limit=1
        )
        assert len(cursor_four_limit_one) == 1
        assert cursor_four_limit_one[0].run_id == two


@run_storage_test
def test_delete(run_storage_factory_cm_fn):
    with run_storage_factory_cm_fn() as storage:
        assert storage
        run_id = str(uuid.uuid4())
        storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
        assert len(storage.all_runs()) == 1
        storage.delete_run(run_id)
        assert list(storage.all_runs()) == []
