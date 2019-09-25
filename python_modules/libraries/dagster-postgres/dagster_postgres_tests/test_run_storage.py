import uuid

import pytest
from dagster_postgres.run_storage import PostgresRunStorage
from dagster_postgres.test import get_test_conn_string, implement_postgres_fixture

from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils import script_relative_path


# pylint: disable=redefined-outer-name,unused-argument
@pytest.fixture(scope='session')
def pg_db():
    with implement_postgres_fixture(script_relative_path('.')):
        yield


def create_empty_run(run_id, pipeline_name, mode='default', tags=None):
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


def test_add_get_postgres_run_storage(pg_db):
    run_storage = PostgresRunStorage.create_nuked_storage(get_test_conn_string())

    run_id = str(uuid.uuid4())
    run_to_add = create_empty_run(pipeline_name='pipeline_name', run_id=run_id)
    added = run_storage.add_run(run_to_add)
    assert added

    fetched_run = run_storage.get_run_by_id(run_id)

    assert run_to_add == fetched_run

    assert run_storage.has_run(run_id)
    assert not run_storage.has_run(str(uuid.uuid4()))

    assert run_storage.all_runs() == [run_to_add]
    assert run_storage.all_runs_for_pipeline('pipeline_name') == [run_to_add]
    assert run_storage.all_runs_for_pipeline('nope') == []

    run_storage.wipe()
    assert run_storage.all_runs() == []


def test_handle_run_event_pipeline_success_test():

    run_storage = PostgresRunStorage.create_nuked_storage(get_test_conn_string())

    run_id = str(uuid.uuid4())
    run_to_add = create_empty_run(pipeline_name='pipeline_name', run_id=run_id)
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


def test_nuke():
    storage = PostgresRunStorage.create_nuked_storage(get_test_conn_string())
    assert storage
    run_id = str(uuid.uuid4())
    storage.add_run(create_empty_run(run_id=run_id, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 1
    storage.wipe()
    assert list(storage.all_runs()) == []


def test_fetch_by_pipeline():
    storage = PostgresRunStorage.create_nuked_storage(get_test_conn_string())
    assert storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    storage.add_run(create_empty_run(run_id=one, pipeline_name='some_pipeline'))
    storage.add_run(create_empty_run(run_id=two, pipeline_name='some_other_pipeline'))
    assert len(storage.all_runs()) == 2
    some_runs = storage.all_runs_for_pipeline('some_pipeline')
    assert len(some_runs) == 1
    assert some_runs[0].run_id == one


def test_fetch_by_tag():
    storage = PostgresRunStorage.create_nuked_storage(get_test_conn_string())
    assert storage
    one = str(uuid.uuid4())
    two = str(uuid.uuid4())
    three = str(uuid.uuid4())
    storage.add_run(
        create_empty_run(run_id=one, pipeline_name='some_pipeline', tags={'mytag': 'hello'})
    )
    storage.add_run(
        create_empty_run(run_id=two, pipeline_name='some_pipeline', tags={'mytag': 'goodbye'})
    )
    storage.add_run(create_empty_run(run_id=three, pipeline_name='some_pipeline'))
    assert len(storage.all_runs()) == 3
    some_runs = storage.all_runs_for_tag('mytag', 'hello')
    assert len(some_runs) == 1
    assert some_runs[0].run_id == one
