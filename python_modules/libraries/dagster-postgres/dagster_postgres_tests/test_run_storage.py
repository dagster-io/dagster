import uuid

from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus


def build_run(
    run_id, pipeline_name, mode='default', tags=None, status=PipelineRunStatus.NOT_STARTED
):
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


def test_add_get_postgres_run_storage(clean_storage):
    run_storage = clean_storage
    run_id = str(uuid.uuid4())
    run_to_add = build_run(pipeline_name='pipeline_name', run_id=run_id)
    added = run_storage.add_run(run_to_add)
    assert added

    fetched_run = run_storage.get_run_by_id(run_id)

    assert run_to_add == fetched_run

    assert run_storage.has_run(run_id)
    assert not run_storage.has_run(str(uuid.uuid4()))

    assert run_storage.all_runs() == [run_to_add]
    assert run_storage.get_runs_with_pipeline_name('pipeline_name') == [run_to_add]
    assert run_storage.get_runs_with_pipeline_name('nope') == []

    run_storage.wipe()
    assert run_storage.all_runs() == []


def test_handle_run_event_pipeline_success_test(clean_storage):
    run_storage = clean_storage

    run_id = str(uuid.uuid4())
    run_to_add = build_run(pipeline_name='pipeline_name', run_id=run_id)
    run_storage.add_run(run_to_add)

    dagster_pipeline_start_event = DagsterEvent(
        message='a message',
        event_type_value=DagsterEventType.PIPELINE_START.value,
        pipeline_name='pipeline_name',
        step_key=None,
        solid_handle=None,
        step_kind_value=None,
        logging_tags=None,
    )

    run_storage.handle_run_event(run_id, dagster_pipeline_start_event)

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        str(uuid.uuid4()),  # diff run
        DagsterEvent(
            message='a message',
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name='pipeline_name',
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.STARTED

    run_storage.handle_run_event(
        run_id,  # correct run
        DagsterEvent(
            message='a message',
            event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
            pipeline_name='pipeline_name',
            step_key=None,
            solid_handle=None,
            step_kind_value=None,
            logging_tags=None,
        ),
    )

    assert run_storage.get_run_by_id(run_id).status == PipelineRunStatus.SUCCESS


def test_clear(clean_storage):
    storage = clean_storage
    run_id = str(uuid.uuid4())
    storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 1
    storage.wipe()
    assert list(storage.all_runs()) == []


def test_delete(clean_storage):
    storage = clean_storage
    run_id = str(uuid.uuid4())
    storage.add_run(build_run(run_id=run_id, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 1
    storage.delete_run(run_id)
    assert list(storage.all_runs()) == []


def test_fetch_by_pipeline(clean_storage):
    storage = clean_storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    storage.add_run(build_run(run_id=one, pipeline_name='some_pipeline'))
    storage.add_run(build_run(run_id=two, pipeline_name='some_other_pipeline'))
    assert len(storage.all_runs()) == 2
    some_runs = storage.get_runs_with_pipeline_name('some_pipeline')
    assert len(some_runs) == 1
    assert some_runs[0].run_id == one


def test_fetch_count_by_tag(clean_storage):
    storage = clean_storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    three = str(uuid.uuid4())
    storage.add_run(
        build_run(
            run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello', 'mytag2': 'world'}
        )
    )
    storage.add_run(
        build_run(
            run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'goodbye', 'mytag2': 'world'}
        )
    )
    storage.add_run(build_run(run_id=three, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 3

    run_count = storage.get_run_count_with_matching_tags([('mytag', 'hello'), ('mytag2', 'world')])
    assert run_count == 1

    run_count = storage.get_run_count_with_matching_tags([('mytag2', 'world')])
    assert run_count == 2

    run_count = storage.get_run_count_with_matching_tags([])
    assert run_count == 3


def test_fetch_by_tags(clean_storage):
    storage = clean_storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    three = str(uuid.uuid4())
    storage.add_run(
        build_run(
            run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello', 'mytag2': 'world'}
        )
    )
    storage.add_run(
        build_run(
            run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'goodbye', 'mytag2': 'world'}
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


def test_slice(clean_storage):
    storage = clean_storage
    one, two, three = sorted([str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())])
    storage.add_run(build_run(run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello'}))
    storage.add_run(build_run(run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'hello'}))
    storage.add_run(build_run(run_id=three, pipeline_name='some_pipeline', tags={'mytag': 'hello'}))

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
    sliced_runs = storage.get_runs_with_matching_tags([('mytag', 'hello')], cursor=three, limit=1)
    assert len(sliced_runs) == 1
    assert sliced_runs[0].run_id == two


def test_fetch_by_status(clean_storage):
    storage = clean_storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    three = str(uuid.uuid4())
    four = str(uuid.uuid4())
    storage.add_run(
        build_run(run_id=one, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED)
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

    assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.NOT_STARTED)} == {
        one
    }

    assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.STARTED)} == {
        two,
        three,
    }

    assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.FAILURE)} == {four}

    assert {run.run_id for run in storage.get_runs_with_status(PipelineRunStatus.SUCCESS)} == set()


def test_fetch_by_status_cursored(clean_storage):
    storage = clean_storage
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
        build_run(run_id=three, pipeline_name='some_pipeline', status=PipelineRunStatus.NOT_STARTED)
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
