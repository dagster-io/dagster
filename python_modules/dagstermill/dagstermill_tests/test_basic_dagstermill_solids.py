import os
import pickle
import tempfile

from contextlib import contextmanager

import pytest

from dagster import execute_pipeline, PipelineDefinition, RunConfig

from dagstermill import DagstermillError, define_dagstermill_solid
from dagstermill.examples.repository import (
    define_add_pipeline,
    define_error_pipeline,
    define_hello_world_explicit_yield_pipeline,
    define_hello_world_pipeline,
    define_hello_world_with_output_pipeline,
    define_no_repo_registration_error_pipeline,
    define_resource_pipeline,
    define_resource_with_exception_pipeline,
    define_test_notebook_dag_pipeline,
    define_tutorial_pipeline,
)

from dagster.core.definitions.events import PathMetadataEntryData


def get_path(materialization_event):
    for (
        metadata_entry
    ) in materialization_event.event_specific_data.materialization.metadata_entries:
        if isinstance(metadata_entry.entry_data, PathMetadataEntryData):
            return metadata_entry.entry_data.path


def cleanup_result_notebook(result):
    if not result:
        return
    materialization_events = [
        x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'
    ]
    for materialization_event in materialization_events:
        result_path = get_path(materialization_event)
        if os.path.exists(result_path):
            os.unlink(result_path)


@contextmanager
def exec_for_test(pipeline, env=None, **kwargs):
    result = None
    try:
        result = execute_pipeline(pipeline, env, **kwargs)
        yield result
    finally:
        if result:
            cleanup_result_notebook(result)


def test_hello_world():
    with exec_for_test(define_hello_world_pipeline()) as result:
        assert result.success


def test_hello_world_with_output():
    with exec_for_test(define_hello_world_with_output_pipeline()) as result:
        assert result.success
        assert result.result_for_solid('hello_world_output').result_value() == 'hello, world'


def test_hello_world_explicit_yield():
    with exec_for_test(define_hello_world_explicit_yield_pipeline()) as result:
        materializations = [
            x for x in result.event_list if x.event_type_value == 'STEP_MATERIALIZATION'
        ]
        assert len(materializations) == 2
        assert get_path(materializations[0]).startswith('/tmp/dagstermill/')
        assert get_path(materializations[1]) == '/path/to/file'


def test_add_pipeline():
    with exec_for_test(
        define_add_pipeline(), {'loggers': {'console': {'config': {'log_level': 'ERROR'}}}}
    ) as result:
        assert result.success
        assert result.result_for_solid('add_two_numbers').result_value() == 3


def test_notebook_dag():
    with exec_for_test(
        define_test_notebook_dag_pipeline(),
        {'solids': {'load_a': {'config': 1}, 'load_b': {'config': 2}}},
    ) as result:
        assert result.success
        assert result.result_for_solid('add_two').result_value() == 3
        assert result.result_for_solid('mult_two').result_value() == 6


def test_error_notebook():
    with pytest.raises(
        DagstermillError, match='Error occurred during the execution of Dagstermill solid'
    ) as exc:
        execute_pipeline(define_error_pipeline())
    assert 'Someone set up us the bomb' in exc.value.original_exc_info[1].args[0]

    with exec_for_test(
        define_error_pipeline(), run_config=RunConfig.nonthrowing_in_process()
    ) as result:
        assert not result.success
        assert result.step_event_list[1].event_type.value == 'STEP_MATERIALIZATION'
        assert result.step_event_list[2].event_type.value == 'STEP_FAILURE'


def test_tutorial_pipeline():
    with exec_for_test(
        define_tutorial_pipeline(), {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}}
    ) as result:
        assert result.success


def test_no_repo_registration_error():
    with pytest.raises(
        DagstermillError,
        match='Error occurred during the execution of Dagstermill solid no_repo_reg',
    ) as exc:
        execute_pipeline(define_no_repo_registration_error_pipeline())
    assert (
        'If Dagstermill solids have outputs that require serialization strategies'
        in exc.value.original_exc_info[1].args[0]
    )

    with exec_for_test(
        define_no_repo_registration_error_pipeline(), run_config=RunConfig.nonthrowing_in_process()
    ) as result:
        assert not result.success


def test_hello_world_reexecution():
    with exec_for_test(define_hello_world_pipeline()) as result:
        assert result.success

        output_notebook_path = get_path(
            [x for x in result.step_event_list if x.event_type_value == 'STEP_MATERIALIZATION'][0]
        )
        # .event_specific_data.materialization.path

        reexecution_solid = define_dagstermill_solid(
            'hello_world_reexecution', output_notebook_path
        )

        reexecution_pipeline = PipelineDefinition([reexecution_solid])

        with exec_for_test(reexecution_pipeline) as reexecution_result:
            assert reexecution_result.success


def test_resources_notebook():
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        with exec_for_test(
            define_resource_pipeline(), {'resources': {'list': {'config': path}}}
        ) as result:
            assert result.success

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == 'Opened'
            assert msgs[4] == msgs[5] == 'Closed'
            assert msgs[1] == 'Hello, solid!'
            assert msgs[3] == 'Hello, notebook!'
    finally:
        if os.path.exists(path):
            os.unlink(path)


def test_resources_notebook_with_exception():
    result = None
    with tempfile.NamedTemporaryFile() as fd:
        path = fd.name

    try:
        with exec_for_test(
            define_resource_with_exception_pipeline(),
            {'resources': {'list': {'config': path}}},
            run_config=RunConfig.nonthrowing_in_process(),
        ) as result:
            assert not result.success
            assert result.step_event_list[5].event_type.value == 'STEP_FAILURE'
            assert (
                'raise Exception()' in result.step_event_list[5].event_specific_data.error.message
            )

            # Expect something like:
            # ['e8d636: Opened', 'e8d636: Hello, solid!', '9d438e: Opened',
            #  '9d438e: Hello, notebook!', '9d438e: Closed', 'e8d636: Closed']
            with open(path, 'rb') as fd:
                messages = pickle.load(fd)

            messages = [message.split(': ') for message in messages]

            resource_ids = [x[0] for x in messages]
            assert len(set(resource_ids)) == 2
            assert resource_ids[0] == resource_ids[1] == resource_ids[5]
            assert resource_ids[2] == resource_ids[3] == resource_ids[4]

            msgs = [x[1] for x in messages]
            assert msgs[0] == msgs[2] == 'Opened'
            assert msgs[4] == msgs[5] == 'Closed'
            assert msgs[1] == 'Hello, solid!'
            assert msgs[3] == 'Hello, notebook!'

    finally:
        if os.path.exists(path):
            os.unlink(path)
